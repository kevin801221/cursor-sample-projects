#!/usr/bin/env python3
"""
chatbot_server.py
=================
強 RAG (Hybrid GraphRAG) + FastAPI 後端服務
提供：
- POST /chat : 問答（Multi-Query + 向量檢索 + RRF + 圖譜擴展 + 時間戳引用）
- GET  /graph : 讀取知識圖譜
- GET  /graph/{name} : 取得節點一階鄰居與時間出處
- GET  /chunks : 取得所有片段與時間軸刻度
- GET  /status : 取得當前圖譜統計與影片/文件資訊
- POST /ingest : 支援 YouTube URL 或 網頁 URL 端到端入庫
- POST /ingest/file : 支援 PDF / DOCX 檔案上傳入庫
"""
import json
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ingest_pipeline import run_full_pipeline

CHAT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")

state: dict = {}


def init_state():
    from langchain_chroma import Chroma
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from neo4j import GraphDatabase

    state["llm"] = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)
    state["vectordb"] = Chroma(
        collection_name=os.environ.get("COLLECTION", "yt_rag"),
        embedding_function=GoogleGenerativeAIEmbeddings(model=EMBED_MODEL),
        persist_directory=os.environ.get("CHROMA_DIR", "./chroma_db"),
    )
    state["neo4j"] = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_state()
    yield
    if "neo4j" in state:
        state["neo4j"].close()


app = FastAPI(title="GraphRAG Teaching Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class ChatRequest(BaseModel):
    question: str


class IngestUrlRequest(BaseModel):
    url: str
    engine: Optional[str] = None  # "tavily", "llamaparse", None


# ---------- 強 RAG 檢索與生成邏輯 ----------

def multi_query(question: str) -> list[str]:
    prompt = (
        "把使用者問題改寫成 3 個不同角度的檢索查詢（術語版/白話版/相關背景版），"
        '嚴格只輸出 JSON: {"queries": ["...", "...", "..."]}\n問題: ' + question
    )
    try:
        raw = state["llm"].invoke(prompt).text.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```")
        return [question] + json.loads(raw)["queries"]
    except Exception:
        return [question]


# 相對距離門檻：距離超過最相關片段 DIST_RATIO 倍的候選視為「top-N 補位雜訊」丟掉。
# 語料裡只有少數 chunk 真的相關時（多來源常見），固定取 5 個會把不相干來源的
# chunk 拉進 context，汙染 sources 與圖譜高亮。
# 1.7 是用 gemini-embedding-001 實測校準的：同主題片段比值 ≤1.65、跨主題雜訊 ≥1.9。
# ponytail: 換嵌入模型要重新校準這個值
DIST_RATIO = 1.7


def rrf_fuse(result_lists: list[list], k: int = 60, top_n: int = 5) -> list:
    scores: dict[str, float] = {}
    doc_map: dict[str, object] = {}
    best_dist: dict[str, float] = {}
    for results in result_lists:
        for rank, (doc, dist) in enumerate(results):
            key = doc.page_content
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            doc_map[key] = doc
            best_dist[key] = min(dist, best_dist.get(key, dist))
    ranked = sorted(scores, key=scores.get, reverse=True)[:top_n]
    if ranked:
        anchor = min(best_dist[key] for key in ranked)
        ranked = [key for key in ranked if best_dist[key] <= anchor * DIST_RATIO]
    return [doc_map[key] for key in ranked]


def _chunk_index(doc) -> Optional[int]:
    return doc.metadata.get("chunk_index")


def graph_expand(docs: list) -> tuple[str, list[dict]]:
    chunk_ids = [
        f"{d.metadata['video_id']}_{i}" for d in docs
        for i in [_chunk_index(d)] if i is not None
    ]
    facts, nodes = [], []
    with state["neo4j"].session() as s:
        recs = s.run(
            """MATCH (e:Entity)-[:MENTIONED_IN]->(ck:Chunk)
               WHERE ck.id IN $ids
                  OR (ck.video_id IN $vids AND ck.start IN $starts)
               MATCH (e)-[r:REL]-(nb:Entity)
               RETURN DISTINCT e.name AS a, r.type AS rel, nb.name AS b LIMIT 30""",
            ids=chunk_ids,
            vids=list({d.metadata["video_id"] for d in docs if "video_id" in d.metadata}),
            starts=[d.metadata["start"] for d in docs if "start" in d.metadata],
        )
        seen = set()
        for rec in recs:
            facts.append(f"({rec['a']}) -[{rec['rel']}]-> ({rec['b']})")
            for name in (rec["a"], rec["b"]):
                if name not in seen:
                    seen.add(name)
                    nodes.append({"id": name, "label": name})
    return "\n".join(facts), nodes


# ---------- API 端點 ----------

@app.post("/chat")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="問題不可為空")

    queries = multi_query(req.question)
    result_lists = [state["vectordb"].similarity_search_with_score(q, k=4) for q in queries]
    docs = rrf_fuse(result_lists)
    graph_facts, nodes = graph_expand(docs)

    context = "\n\n".join(
        f"[片段 {i+1}]\n{d.page_content}" for i, d in enumerate(docs)
    )
    prompt = f"""你是內容問答助手。只根據以下資料回答，資料中沒有的就說不知道。

輸出格式規則（嚴格遵守）：
- 純文字，不要用任何 markdown 語法：不要 **粗體**、不要 # 標題、不要 * 或 - 項目符號。
- 要分點時直接用「1. 」「2. 」開頭，每點自成一段。
- 引用時在句尾標 [片段 N]（N 是下面的片段編號），不要貼網址——網址由介面自己補。

# 原文片段
{context}

# 知識圖譜關係
{graph_facts or "（無）"}

# 問題
{req.question}"""
    answer = state["llm"].invoke(prompt).text
    return {
        "answer": answer,
        "sources": [
            {
                "text": d.page_content[:120],
                "url": d.metadata.get("url_at_time", ""),
                "start": d.metadata.get("start", 0),
            }
            for d in docs
        ],
        "graph_nodes": nodes,
    }


@app.get("/graph")
def full_graph(limit: int = 300):
    with state["neo4j"].session() as s:
        recs = s.run(
            "MATCH (a:Entity)-[r:REL]->(b:Entity) "
            "RETURN a.name AS a, r.type AS rel, b.name AS b LIMIT $limit",
            limit=limit,
        )
        links, node_set = [], set()
        for rec in recs:
            links.append({"source": rec["a"], "target": rec["b"], "label": rec["rel"]})
            node_set.update((rec["a"], rec["b"]))
    return {"nodes": [{"id": n, "label": n} for n in node_set], "links": links}


@app.get("/graph/{name}")
def neighbors(name: str):
    with state["neo4j"].session() as s:
        recs = s.run(
            """MATCH (e:Entity {name: $name})-[r:REL]-(nb:Entity)
               OPTIONAL MATCH (e)-[:MENTIONED_IN]->(ck:Chunk)
               RETURN nb.name AS nb, r.type AS rel,
                      collect(DISTINCT ck.url_at_time)[..3] AS sources""",
            name=name,
        )
        links, node_set, sources = [], {name}, set()
        for rec in recs:
            links.append({"source": name, "target": rec["nb"], "label": rec["rel"]})
            node_set.add(rec["nb"])
            sources.update(u for u in rec["sources"] if u)
    return {
        "nodes": [{"id": n, "label": n} for n in node_set],
        "links": links,
        "video_sources": sorted(sources),
    }


@app.get("/chunks")
def all_chunks():
    with state["neo4j"].session() as s:
        recs = s.run(
            "MATCH (c:Chunk) RETURN c.start AS start, c.url_at_time AS url ORDER BY c.start"
        )
        return {"chunks": [{"start": r["start"], "url": r["url"]} for r in recs]}


@app.get("/status")
def get_status():
    with state["neo4j"].session() as s:
        entities = s.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
        relations = s.run("MATCH ()-[r:REL]->() RETURN count(r) AS c").single()["c"]
        chunks = s.run("MATCH (k:Chunk) RETURN count(k) AS c").single()["c"]
        video_rec = s.run("MATCH (v:Video) RETURN v.title AS title, v.url AS url, v.source_type AS st LIMIT 1").data()
        video_info = video_rec[0] if video_rec else {}
    return {
        "entities_count": entities,
        "relations_count": relations,
        "chunks_count": chunks,
        "title": video_info.get("title", "未命名來源"),
        "url": video_info.get("url", ""),
        "source_type": video_info.get("st", "unknown"),
    }


@app.post("/ingest")
def ingest_url(req: IngestUrlRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL 不可為空")
    # 只收 http(s)：fetch_source_data 會把非網址當本機路徑開，
    # 若不擋掉，這個端點就是任意本機檔案讀取的破口
    if not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="只接受 http(s) 網址；本機檔案請走 /ingest/file 上傳")
    try:
        res = run_full_pipeline(url, engine=req.engine)
        init_state()  # 重新刷新 ChromaDB 與連接
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...), engine: Optional[str] = Form(None)):
    suffix = Path(file.filename).suffix.lower()
    if suffix == ".doc":
        raise HTTPException(status_code=400, detail="舊版 .doc 格式無法解析，請先用 Word 另存為 .docx")
    if suffix not in (".pdf", ".docx"):
        raise HTTPException(status_code=400, detail=f"不支援的檔案格式: {suffix} (僅支援 .pdf 與 .docx)")

    # 存進 uploads/ 而非暫存檔：引用 (file://...#page=N) 要在入庫後仍可回溯，
    # 暫存檔請求結束就刪，引用會全變死連結
    uploads_dir = Path(os.environ.get("UPLOADS_DIR", "./uploads"))
    uploads_dir.mkdir(exist_ok=True)
    dest = uploads_dir / Path(file.filename).name  # .name 去掉路徑，防目錄跳脫
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        res = run_full_pipeline(dest, engine=engine, custom_title=file.filename)
        init_state()  # 重新刷新 ChromaDB 與連接
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset")
def reset_database():
    with state["neo4j"].session() as s:
        s.run("MATCH (n) DETACH DELETE n")
    chroma_dir = os.environ.get("CHROMA_DIR", "./chroma_db")
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir, ignore_errors=True)
    init_state()
    return {"status": "reset_completed"}
