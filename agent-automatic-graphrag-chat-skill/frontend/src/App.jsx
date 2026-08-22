// App.jsx — 完整 GraphRAG 教學與實戰介面
// 支援 YouTube URL、Web URL、PDF、DOCX 端到端入庫與問答
import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import ForceGraph2D from "react-force-graph-2d";

const API = "http://localhost:8000";
const SIDEBAR = 460, SLATE = 56, RIBBON = 76;
const CYAN = "#52D1E8", AMBER = "#FFB454", DIM = "#2A3348";

const mmss = (s) => {
  if (typeof s !== "number" || isNaN(s)) return "0:00";
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
};

function render(text, sources = []) {
  if (!text) return null;
  const paras = text.split(/\n{2,}|\n(?=\s*\d+[.、]\s)/).map(p => p.trim()).filter(Boolean);
  return paras.map((para, pi) => {
    const clean = para.replace(/^\s*[*-]\s+/, "").replace(/\*\*/g, "");
    const out = [];
    let last = 0, m;
    const re = /\[[^\]]*片段[^\]]*\]/g;
    while ((m = re.exec(clean))) {
      if (m.index > last) out.push(clean.slice(last, m.index));
      const nums = [...m[0].matchAll(/\d+/g)].map(x => +x[0]);
      nums.forEach(n => {
        const src = sources[n - 1];
        out.push(src
          ? <a key={out.length} className="cite" href={src.url} target="_blank" rel="noreferrer"
               title={`片段 ${n}`}>{src.url?.includes("youtu") ? mmss(src.start) : (src.url?.includes("#page=") ? `p.${src.start}` : `片段 ${n}`)}</a>
          : <span key={out.length} className="cite">片段 {n}</span>);
      });
      last = m.index + m[0].length;
    }
    if (last < clean.length) out.push(clean.slice(last));
    return <p key={pi}>{out}</p>;
  });
}

const DEFAULT_SEEDS = [
  "這份資料的核心主題與結論是什麼？",
  "牽涉到哪些關鍵概念與實體關係？",
  "有什麼特別需要注意的論點或細節？",
];

export default function App() {
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [chunks, setChunks] = useState([]);
  const [hot, setHot] = useState([]);
  const [highlight, setHighlight] = useState(new Set());
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState("unknown");
  const [size, setSize] = useState({ w: 0, h: 0 });

  // Modal 狀態
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("youtube"); // youtube, url, pdf, docx
  const [urlInput, setUrlInput] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [engine, setEngine] = useState("free"); // free, llamaparse, tavily
  const [ingestStatus, setIngestStatus] = useState({ state: "idle", msg: "", step: 0 });

  const fgRef = useRef();
  const logRef = useRef();
  const fileInputRef = useRef();

  const refreshData = useCallback(async () => {
    try {
      const gRes = await fetch(`${API}/graph`).then(r => r.json());
      setGraph(gRes);
    } catch (e) { console.error("fetch graph error", e); }

    try {
      const cRes = await fetch(`${API}/chunks`).then(r => r.json());
      setChunks(cRes.chunks || []);
    } catch (e) { console.error("fetch chunks error", e); }

    try {
      const sRes = await fetch(`${API}/status`).then(r => r.json());
      setTitle(sRes.title || "GraphRAG 知識庫");
      setSourceType(sRes.source_type || "unknown");
    } catch (e) { console.error("fetch status error", e); }
  }, []);

  useEffect(() => {
    const fit = () => setSize({
      w: window.innerWidth - SIDEBAR,
      h: window.innerHeight - SLATE - RIBBON,
    });
    fit();
    window.addEventListener("resize", fit);
    refreshData();
    return () => window.removeEventListener("resize", fit);
  }, [refreshData]);

  // 力的參數微調
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg || !graph.nodes.length) return;
    fg.d3Force("charge")?.strength(-70).distanceMax(320);
    fg.d3Force("link")?.distance(38);
    fg.d3ReheatSimulation();
    const t = setTimeout(() => fg.zoomToFit(700, 90), 1500);
    return () => clearTimeout(t);
  }, [graph.nodes.length]);

  useEffect(() => { logRef.current?.scrollTo({ top: 1e6, behavior: "smooth" }); }, [messages, busy]);

  const degree = useMemo(() => {
    const d = {};
    graph.links.forEach(l => {
      const s = l.source.id ?? l.source, t = l.target.id ?? l.target;
      d[s] = (d[s] || 0) + 1; d[t] = (d[t] || 0) + 1;
    });
    return d;
  }, [graph.links]);

  const span = Math.max(...(chunks.map(c => Number(c.start) || 0)), ...hot, 60) * 1.02;

  const send = useCallback(async (q) => {
    q = (q ?? input).trim();
    if (!q || busy) return;
    setInput(""); setBusy(true);
    setMessages(m => [...m, { role: "you", text: q }]);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      }).then(r => r.json());
      setMessages(m => [...m, { role: "bot", text: res.answer, sources: res.sources }]);
      setHighlight(new Set((res.graph_nodes || []).map(n => n.id)));
      setHot((res.sources || []).map(s => Number(s.start) || 0));
      fgRef.current?.d3ReheatSimulation();
    } catch {
      setMessages(m => [...m, { role: "bot", text: `連不上後端 ${API}。確認 uvicorn 是否正常運作。` }]);
    } finally { setBusy(false); }
  }, [input, busy]);

  const expandNode = useCallback(async (node) => {
    try {
      const sub = await fetch(`${API}/graph/${encodeURIComponent(node.id)}`).then(r => r.json());
      setGraph(g => {
        const ids = new Set(g.nodes.map(n => n.id));
        const key = l => `${l.source.id ?? l.source}->${l.target.id ?? l.target}`;
        const linkSet = new Set(g.links.map(key));
        return {
          nodes: [...g.nodes, ...sub.nodes.filter(n => !ids.has(n.id))],
          links: [...g.links, ...sub.links.filter(l => !linkSet.has(key(l)))],
        };
      });
      setHighlight(new Set(sub.nodes.map(n => n.id)));
      fgRef.current?.d3ReheatSimulation();
    } catch (e) {
      console.error("expandNode error:", e);
    }
  }, []);

  const handleIngest = async () => {
    setIngestStatus({ state: "processing", msg: "正在開始端到端解析與圖譜建構...", step: 1 });
    try {
      if (activeTab === "youtube" || activeTab === "url") {
        if (!urlInput.trim()) {
          alert("請輸入有效的網址");
          setIngestStatus({ state: "idle", msg: "", step: 0 });
          return;
        }
        setIngestStatus({ state: "processing", msg: "正在擷取資料並切塊 (Chroma 嵌入 & Gemini 抽取中)...", step: 2 });
        const res = await fetch(`${API}/ingest`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: urlInput.trim(),
            engine: engine !== "free" ? engine : undefined,
          }),
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "入庫失敗");
        }
      } else {
        if (!selectedFile) {
          alert("請先選擇要上傳的檔案");
          setIngestStatus({ state: "idle", msg: "", step: 0 });
          return;
        }
        setIngestStatus({ state: "processing", msg: "正在解析文件並切塊 (Chroma 嵌入 & Gemini 抽取中)...", step: 2 });
        const formData = new FormData();
        formData.append("file", selectedFile);
        if (engine !== "free") formData.append("engine", engine);

        const res = await fetch(`${API}/ingest/file`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "檔案上傳入庫失敗");
        }
      }

      setIngestStatus({ state: "success", msg: "知識圖譜建構完成！正在重整圖譜與時間軸...", step: 4 });
      await refreshData();
      setMessages([]);
      setTimeout(() => {
        setIsModalOpen(false);
        setIngestStatus({ state: "idle", msg: "", step: 0 });
        setUrlInput("");
        setSelectedFile(null);
      }, 1200);
    } catch (err) {
      setIngestStatus({ state: "error", msg: `錯誤: ${err.message}`, step: 0 });
    }
  };

  const radius = useCallback(
    (id, scale) => (3.6 + Math.min(degree[id] || 0, 10) * 0.9) / scale, [degree]);

  const drawNode = useCallback((node, ctx, scale) => {
    const on = highlight.has(node.id);
    const r = radius(node.id, scale);
    if (on) {
      ctx.beginPath(); ctx.arc(node.x, node.y, r * 2.2, 0, 2 * Math.PI);
      ctx.fillStyle = "rgba(255,180,84,.15)"; ctx.fill();
    }
    ctx.beginPath(); ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = on ? AMBER : highlight.size ? DIM : CYAN;
    ctx.fill();
  }, [radius, highlight]);

  const drawLabels = useCallback((ctx, scale) => {
    if (!graph.nodes.length) return;
    const fs = 12 / scale;
    ctx.font = `500 ${fs}px "IBM Plex Sans", sans-serif`;
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    const pad = 3 / scale;
    const boxes = [];
    const cands = graph.nodes
      .filter(n => n.x != null)
      .map(n => ({ n, deg: degree[n.id] || 0, on: highlight.has(n.id) }))
      .filter(c => c.on || c.deg >= 4 || scale > 1.6)
      .sort((a, b) => (b.on - a.on) || (b.deg - a.deg));

    for (const { n, deg, on } of cands) {
      const label = n.label ?? n.id;
      const w = ctx.measureText(label).width;
      const x = n.x, y = n.y + radius(n.id, scale) + fs * 0.35;
      const box = [x - w / 2 - pad, y - pad, x + w / 2 + pad, y + fs + pad];
      if (boxes.some(b => box[0] < b[2] && box[2] > b[0] && box[1] < b[3] && box[3] > b[1])) continue;
      boxes.push(box);
      ctx.fillStyle = on ? "#FFD9A0" : highlight.size ? "#48546F" : "#A6B6D0";
      ctx.fillText(label, x, y);
    }
  }, [graph.nodes, degree, highlight, radius]);

  const getBadgeClass = (st) => {
    if (st === "youtube") return "youtube";
    if (st === "pdf") return "pdf";
    if (st === "docx") return "docx";
    if (st === "url") return "url";
    return "";
  };

  return (
    <div className="app">
      {/* 頂端狀態列 */}
      <header className="slate">
        <div className="slate-mark">GRAPH<span>·</span>RAG</div>
        {sourceType !== "unknown" && (
          <span className={`source-badge ${getBadgeClass(sourceType)}`}>
            {sourceType}
          </span>
        )}
        <div className="slate-title" title={title}>{title || "載入中…"}</div>
        <div className="stat-group">
          <div className="stat">實體 <b>{graph.nodes.length}</b></div>
          <div className="stat">關係 <b>{graph.links.length}</b></div>
          <div className="stat ev">片段 <b>{chunks.length}</b></div>
        </div>
        <div className="slate-actions">
          <button className="btn-primary" onClick={() => setIsModalOpen(true)}>
            + 匯入新來源
          </button>
          <button className="btn-secondary" onClick={refreshData} title="重新整理圖譜">
            ⟳ 刷新
          </button>
        </div>
      </header>

      {/* 左側對話區 */}
      <section className="chat">
        <div className="log" ref={logRef}>
          {messages.length === 0 && (
            <div className="empty">
              <h2>知識庫問答</h2>
              回答依據檢索到的原文段落與圖譜關聯，並提供精確來源引用。
              右側圖譜即時高亮相關概念，下方時間軸標記證據分布。
              <ul>
                {DEFAULT_SEEDS.map(s => <li key={s} onClick={() => send(s)}>{s}</li>)}
              </ul>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`turn ${m.role}`}>
              <div className="who">{m.role === "you" ? "你" : "回答"}</div>
              <div className="said">{m.role === "you" ? m.text : render(m.text, m.sources)}</div>
              {m.sources?.length > 0 && (
                <div className="evidence">
                  <div className="evidence-label">出處 · {m.sources.length} 個片段</div>
                  <div className="chips">
                    {m.sources.map((s, j) => (
                      <a key={j} className="chip" href={s.url} target="_blank" rel="noreferrer"
                         onMouseEnter={() => setHot([Number(s.start) || 0])}
                         onMouseLeave={() => setHot(m.sources.map(x => Number(x.start) || 0))}>
                        ▸ {s.url?.includes("youtu") ? mmss(Number(s.start)) : (s.url?.includes("#page=") ? `第 ${s.start} 頁` : `片段 ${j + 1}`)}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {busy && <div className="thinking"><i /><i /><i /> 檢索中</div>}
        </div>
        <div className="ask">
          <input value={input} onChange={e => setInput(e.target.value)}
                 onKeyDown={e => e.key === "Enter" && send()}
                 placeholder="問內容相關問題…" />
          <button onClick={() => send()} disabled={busy || !input.trim()}>送出</button>
        </div>
      </section>

      {/* 右側圖譜區 */}
      <section className="stage">
        <ForceGraph2D
          ref={fgRef}
          width={size.w} height={size.h}
          graphData={graph}
          backgroundColor="#0A0D14"
          nodeLabel="label"
          nodeCanvasObject={drawNode}
          onRenderFramePost={drawLabels}
          nodePointerAreaPaint={(n, color, ctx, scale = 1) => {
            ctx.fillStyle = color;
            ctx.beginPath(); ctx.arc(n.x, n.y, 10 / scale, 0, 2 * Math.PI); ctx.fill();
          }}
          linkColor={l => {
            const a = l.source.id ?? l.source, b = l.target.id ?? l.target;
            return highlight.has(a) && highlight.has(b) ? "rgba(255,180,84,.6)" : "rgba(46,57,80,.85)";
          }}
          linkWidth={l => {
            const a = l.source.id ?? l.source, b = l.target.id ?? l.target;
            return highlight.has(a) && highlight.has(b) ? 2 : 1;
          }}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          onNodeClick={expandNode}
          onNodeDragEnd={() => fgRef.current?.d3ReheatSimulation()}
          d3AlphaDecay={0.012}
          d3VelocityDecay={0.28}
          cooldownTime={25000}
          onEngineStop={() => fgRef.current?.zoomToFit(700, 90)}
        />
        <div className="legend">
          <span><b style={{ background: CYAN }} />概念實體</span>
          <span><b style={{ background: AMBER }} />本次回答相關</span>
        </div>
        <div className="hint">點擊節點展開鄰居子圖 · 支援拖曳縮放</div>
      </section>

      {/* 底部時間軸緞帶 */}
      <footer className="ribbon">
        <div className="ribbon-head">
          <span>證據時間軸 · 內容分布</span>
          <span>{hot.length ? <em>{hot.length} 處命中</em> : `${chunks.length} 個片段`}</span>
        </div>
        <div className="track">
          {chunks.map((c, i) => {
            const st = Number(c.start) || 0;
            return (
              <span key={i} className="tick" style={{ left: `${(st / (span || 1)) * 100}%` }} />
            );
          })}
          {hot.map((s, i) => (
            <a key={`h${i}`} className="tick hot" title={mmss(s)}
               href={chunks.find(c => Number(c.start) === s)?.url || "#"}
               target="_blank" rel="noreferrer"
               style={{ left: `${(s / (span || 1)) * 100}%`, animationDelay: `${i * 60}ms` }} />
          ))}
        </div>
        <div className="scale">
          <span>0:00</span>
          <span>{sourceType === "youtube" ? mmss(span) : `總計 ${chunks.length} 段`}</span>
        </div>
      </footer>

      {/* 新增來源 Modal */}
      {isModalOpen && (
        <div className="modal-overlay" onClick={() => !ingestStatus.step && setIsModalOpen(false)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>匯入新知識來源 (GraphRAG Ingest)</h3>
              {!ingestStatus.step && (
                <button className="modal-close" onClick={() => setIsModalOpen(false)}>✕</button>
              )}
            </div>

            <div className="modal-tabs">
              <button className={`tab-btn ${activeTab === "youtube" ? "active" : ""}`}
                      onClick={() => { setActiveTab("youtube"); setEngine("free"); }}>
                <span>🎥 YouTube</span>
                <small>影片字幕</small>
              </button>
              <button className={`tab-btn ${activeTab === "url" ? "active" : ""}`}
                      onClick={() => { setActiveTab("url"); setEngine("free"); }}>
                <span>🌐 網頁文章</span>
                <small>URL 抓取</small>
              </button>
              <button className={`tab-btn ${activeTab === "pdf" ? "active" : ""}`}
                      onClick={() => { setActiveTab("pdf"); setEngine("free"); }}>
                <span>📄 PDF 文件</span>
                <small>PyMuPDF/OCR</small>
              </button>
              <button className={`tab-btn ${activeTab === "docx" ? "active" : ""}`}
                      onClick={() => { setActiveTab("docx"); setEngine("free"); }}>
                <span>📝 Word DOCX</span>
                <small>段落與表格</small>
              </button>
            </div>

            <div className="modal-body">
              {ingestStatus.step > 0 ? (
                <div className="ingest-progress">
                  <div className={`progress-step ${ingestStatus.step >= 1 ? (ingestStatus.step === 1 ? "active" : "done") : ""}`}>
                    <span className="step-icon">{ingestStatus.step > 1 ? "✓" : "1"}</span>
                    <span>擷取原始內容 (字幕 / 文件 / 網頁文字)</span>
                  </div>
                  <div className={`progress-step ${ingestStatus.step >= 2 ? (ingestStatus.step === 2 ? "active" : "done") : ""}`}>
                    <span className="step-icon">{ingestStatus.step > 2 ? "✓" : "2"}</span>
                    <span>語意聚合切塊 & Chroma 向量嵌入</span>
                  </div>
                  <div className={`progress-step ${ingestStatus.step >= 3 ? (ingestStatus.step === 3 ? "active" : "done") : ""}`}>
                    <span className="step-icon">{ingestStatus.step > 3 ? "✓" : "3"}</span>
                    <span>Gemini 抽取知識圖譜三元組 & 寫入 Neo4j</span>
                  </div>
                  <div className={`progress-step ${ingestStatus.step >= 4 ? "done" : ""}`}>
                    <span className="step-icon">{ingestStatus.step >= 4 ? "✓" : "4"}</span>
                    <span>{ingestStatus.msg}</span>
                  </div>
                </div>
              ) : (
                <>
                  {activeTab === "youtube" && (
                    <div className="form-group">
                      <label>YouTube 影片連結</label>
                      <input
                        className="form-input"
                        placeholder="https://www.youtube.com/watch?v=..."
                        value={urlInput}
                        onChange={e => setUrlInput(e.target.value)}
                      />
                      <small style={{ color: "var(--muted)", fontSize: "11px" }}>
                        支援自動抓取官方字幕 / 自動產生字幕 (ASR)。
                      </small>
                    </div>
                  )}

                  {activeTab === "url" && (
                    <div className="form-group">
                      <label>網頁文章 URL</label>
                      <input
                        className="form-input"
                        placeholder="https://example.com/article"
                        value={urlInput}
                        onChange={e => setUrlInput(e.target.value)}
                      />
                      <label style={{ marginTop: "10px" }}>解析引擎</label>
                      <div className="engine-select">
                        <div className={`engine-chip ${engine === "free" ? "active" : ""}`}
                             onClick={() => setEngine("free")}>
                          免費地端 (Trafilatura)
                        </div>
                        <div className={`engine-chip ${engine === "tavily" ? "active" : ""}`}
                             onClick={() => setEngine("tavily")}>
                          付費雲端 (Tavily Extract)
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === "pdf" && (
                    <div className="form-group">
                      <label>選擇 PDF 檔案</label>
                      <input
                        type="file"
                        accept=".pdf"
                        ref={fileInputRef}
                        style={{ display: "none" }}
                        onChange={e => setSelectedFile(e.target.files?.[0] || null)}
                      />
                      <div className="file-dropzone" onClick={() => fileInputRef.current?.click()}>
                        <span className="drop-icon">📄</span>
                        <span className="drop-text">{selectedFile ? selectedFile.name : "點擊此處選擇 PDF 檔案"}</span>
                        <span className="drop-hint">支援繁中/簡中/英文 PDF 文件</span>
                      </div>
                      <label style={{ marginTop: "10px" }}>解析引擎</label>
                      <div className="engine-select">
                        <div className={`engine-chip ${engine === "free" ? "active" : ""}`}
                             onClick={() => setEngine("free")}>
                          免費地端 (PyMuPDF)
                        </div>
                        <div className={`engine-chip ${engine === "llamaparse" ? "active" : ""}`}
                             onClick={() => setEngine("llamaparse")}>
                          付費雲端 (LlamaParse OCR)
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === "docx" && (
                    <div className="form-group">
                      <label>選擇 Word DOCX 檔案</label>
                      <input
                        type="file"
                        accept=".docx,.doc"
                        ref={fileInputRef}
                        style={{ display: "none" }}
                        onChange={e => setSelectedFile(e.target.files?.[0] || null)}
                      />
                      <div className="file-dropzone" onClick={() => fileInputRef.current?.click()}>
                        <span className="drop-icon">📝</span>
                        <span className="drop-text">{selectedFile ? selectedFile.name : "點擊此處選擇 DOCX 檔案"}</span>
                        <span className="drop-hint">自動擷取所有段落與表格資料</span>
                      </div>
                    </div>
                  )}

                  {ingestStatus.state === "error" && (
                    <div style={{ color: "var(--rose)", fontSize: "12px", fontFamily: "var(--mono)", background: "rgba(251,113,133,0.1)", padding: "8px 12px", borderRadius: "4px" }}>
                      {ingestStatus.msg}
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" disabled={ingestStatus.step > 0} onClick={() => setIsModalOpen(false)}>
                取消
              </button>
              <button className="btn-primary" disabled={ingestStatus.step > 0} onClick={handleIngest}>
                {ingestStatus.step > 0 ? "建構中..." : "開始建構 GraphRAG"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
