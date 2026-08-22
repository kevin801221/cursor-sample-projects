#!/usr/bin/env python3
"""
Step 4: 強 RAG（Hybrid GraphRAG）+ FastAPI 聊天機器人後端
==========================================================
需安裝: uv sync
需環境變數: GOOGLE_API_KEY, NEO4J_PASSWORD（NEO4J_URI / NEO4J_USER 有預設）

「強 RAG」在這裡指的 pipeline（上課逐一講解每步為什麼存在）:
  Query -> Multi-Query 改寫(3 個視角) -> 向量檢索(每個 query top-4)
        -> RRF 融合去重 -> 圖譜擴展(從命中 chunk 找 Entity 鄰居)
        -> 組合 context(原文證據 + 圖譜關係) -> 生成(附時間戳引用)

API:
  POST /chat          {"question": "..."}  -> 答案 + 引用 + 相關圖譜節點
  GET  /graph/{name}  -> 該節點的鄰居子圖（前端點節點瞬間載入用）
  GET  /graph         -> 整張圖（前端初始渲染用）

啟動:
  cp scripts/04_chatbot_server.py chatbot_server.py   # 模組名不能數字開頭
  uv run uvicorn chatbot_server:app --reload --port 8000
"""
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

CHAT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# ---------- 全域資源（lifespan 內初始化，避免每請求重連） ----------
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_chroma import Chroma
    from neo4j import GraphDatabase

    state["llm"] = ChatGoogleGenerativeAI(model=CHAT_MODEL, temperature=0)
    state["vectordb"] = Chroma(
        collection_name=os.environ.get("COLLECTION", "yt_rag"),
        # 嵌入模型必須與 Phase 2 入庫時完全相同，否則向量空間對不上
        embedding_function=GoogleGenerativeAIEmbeddings(model=EMBED_MODEL),
        persist_directory=os.environ.get("CHROMA_DIR", "./chroma_db"),
    )
    state["neo4j"] = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )
    yield
    state["neo4j"].close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(  # 教學環境全開；正式部署要鎖 origin
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ChatRequest(BaseModel):
    question: str


# ---------- 強 RAG 各元件 ----------
def multi_query(question: str) -> list[str]:
    """一個問題改寫成 3 個檢索視角，涵蓋術語/白話/上下文三種表述。"""
    prompt = (
        "把使用者問題改寫成 3 個不同角度的檢索查詢（術語版/白話版/相關背景版），"
        '嚴格只輸出 JSON: {"queries": ["...", "...", "..."]}\n問題: ' + question
    )
    # .text 而非 .content：LangChain 1.x 的 .content 是 content blocks 的 list
    raw = state["llm"].invoke(prompt).text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```")
    try:
        return [question] + json.loads(raw)["queries"]
    except (json.JSONDecodeError, KeyError):
        return [question]  # 改寫失敗就退回原問題，pipeline 不能因加強元件而變脆弱


def rrf_fuse(result_lists: list[list], k: int = 60, top_n: int = 5) -> list:
    """Reciprocal Rank Fusion: score = Σ 1/(k+rank)。以 chunk 內容去重。"""
    scores: dict[str, float] = {}
    doc_map: dict[str, object] = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = doc.page_content
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            doc_map[key] = doc
    ranked = sorted(scores, key=scores.get, reverse=True)[:top_n]
    return [doc_map[key] for key in ranked]


def graph_expand(docs: list) -> tuple[str, list[dict]]:
    """從命中 chunks 反查 Entity 及其一階鄰居 -> (文字化關係, 節點列表給前端)"""
    chunk_ids = [
        f"{d.metadata['video_id']}_{i}" for d in docs
        for i in [_chunk_index(d)] if i is not None
    ]
    # 教學簡化：chunk_id 若對不上（index 遺失），改用 start 比對。
    # 但 start 在不同來源代表不同東西（影片=秒、PDF=頁、DOCX=段序），
    # 光比 start 會讓 YouTube 的 start=1 撞上 PDF 的 page=1 而撈進別份文件的實體，
    # 所以 fallback 一定要連 video_id 一起限定。
    facts, nodes = [], []
    with state["neo4j"].session() as s:
        recs = s.run(
            """MATCH (e:Entity)-[:MENTIONED_IN]->(ck:Chunk)
               WHERE ck.id IN $ids
                  OR (ck.video_id IN $vids AND ck.start IN $starts)
               MATCH (e)-[r:REL]-(nb:Entity)
               RETURN DISTINCT e.name AS a, r.type AS rel, nb.name AS b LIMIT 30""",
            ids=chunk_ids,
            vids=list({d.metadata["video_id"] for d in docs}),
            starts=[d.metadata["start"] for d in docs],
        )
        seen = set()
        for rec in recs:
            facts.append(f"({rec['a']}) -[{rec['rel']}]-> ({rec['b']})")
            for name in (rec["a"], rec["b"]):
                if name not in seen:
                    seen.add(name)
                    nodes.append({"id": name, "label": name})
    return "\n".join(facts), nodes


def _chunk_index(doc) -> int | None:
    return doc.metadata.get("chunk_index")  # 若 Step 2 未寫入則回 None，走 start 比對


@app.post("/chat")
def chat(req: ChatRequest):
    queries = multi_query(req.question)
    result_lists = [state["vectordb"].similarity_search(q, k=4) for q in queries]
    docs = rrf_fuse(result_lists)
    graph_facts, nodes = graph_expand(docs)

    # 片段標頭刻意不放網址：LLM 會照抄 context 的格式，標頭放什麼、
    # 答案裡就會出現什麼。想要乾淨的引用，就要先給它乾淨的範本。
    context = "\n\n".join(
        f"[片段 {i+1}]\n{d.page_content}" for i, d in enumerate(docs)
    )
    prompt = f"""你是影片內容問答助手。只根據以下資料回答，資料中沒有的就說不知道。

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
            {"text": d.page_content[:120], "url": d.metadata["url_at_time"],
             "start": d.metadata["start"]} for d in docs
        ],
        "graph_nodes": nodes,  # 前端拿這個瞬間高亮/載入相關節點
    }


@app.get("/graph")
def full_graph(limit: int = 200):
    with state["neo4j"].session() as s:
        recs = s.run(
            "MATCH (a:Entity)-[r:REL]->(b:Entity) "
            "RETURN a.name AS a, r.type AS rel, b.name AS b LIMIT $limit", limit=limit)
        links, node_set = [], set()
        for rec in recs:
            links.append({"source": rec["a"], "target": rec["b"], "label": rec["rel"]})
            node_set.update((rec["a"], rec["b"]))
    return {"nodes": [{"id": n, "label": n} for n in node_set], "links": links}


@app.get("/chunks")
def all_chunks():
    """全部 chunk 的位置——前端用來畫「整支影片的證據地圖」時間軸。

    有了它，回答時就能讓使用者看見「答案是從影片哪幾個位置撈出來的」，
    而不只是給一串連結。這是把「引用可回溯」從功能變成畫面。
    """
    with state["neo4j"].session() as s:
        recs = s.run(
            "MATCH (c:Chunk) RETURN c.start AS start, c.url_at_time AS url "
            "ORDER BY c.start")
        return {"chunks": [{"start": r["start"], "url": r["url"]} for r in recs]}


@app.get("/graph/{name}")
def neighbors(name: str):
    """點擊節點 -> 瞬間載入一階鄰居子圖 + 原文出處（含影片時間戳）。"""
    with state["neo4j"].session() as s:
        recs = s.run(
            """MATCH (e:Entity {name: $name})-[r:REL]-(nb:Entity)
               OPTIONAL MATCH (e)-[:MENTIONED_IN]->(ck:Chunk)
               RETURN nb.name AS nb, r.type AS rel,
                      collect(DISTINCT ck.url_at_time)[..3] AS sources""", name=name)
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
