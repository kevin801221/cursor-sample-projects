# 前端：知識圖譜視覺化 + Copilot 對話介面

目標體驗：左邊聊天、右邊力導向圖譜、**底部一條影片時間軸**。
機器人回答的瞬間，相關節點在圖上變琥珀色，同時時間軸上亮出「證據來自影片的
哪幾個位置」。

## 設計主張（上課要講的，比程式碼重要）

這不是「聊天機器人配一張裝飾用的圖」。整個專案的核心主張是
**引用必須可回溯**——所以介面的職責，是把這件事變成看得見的。

| 視圖 | 回答什麼問題 |
|---|---|
| 對話 | 答案是什麼 |
| 圖譜 | 這個答案牽涉到哪些概念、它們怎麼連 |
| **時間軸** | 這些話是從影片的哪幾個位置撈出來的 |

三個視圖是**同一次檢索的三種投影**。時間軸是這個介面的簽名元素——
一般的 RAG demo 只會給你一串連結，你不會「看見」證據的分布。

配色只有兩個強調色，而且各有語意職責，不是拿來裝飾的：

| 色 | 意義 |
|---|---|
| 琥珀 `#FFB454` | 證據——時間戳、命中刻度、與本次回答相關的節點 |
| 青 `#52D1E8` | 結構——知識圖譜的實體 |

暗底不是跟流行，是因為要投影在教室螢幕上，而力導向圖在暗底最清楚。

## 技術選型（上課要講理由）

| 元件 | 選擇 | 理由 |
|---|---|---|
| 圖譜渲染 | `react-force-graph-2d` | 力導向圖最直觀、API 簡單、效能好；3D 版一行切換 |
| 樣式 | 純 CSS + 設計 tokens | **零 UI 套件**。保底版的職責是「先讓所有同學都能動」 |
| 對話介面 | **CopilotKit**（AG-UI 協定） | 升級路線，見文末；用它的 MCP 查最新 API |

## 建置步驟

```bash
npm create vite@latest frontend -- --template react
cd frontend && npm i && npm i react-force-graph-2d
```

然後**整份取代**這兩個檔案（內容在下面）：`src/index.css`、`src/App.jsx`。
`src/App.css` 用不到，樣板 `App.jsx` 裡的 `import './App.css'` 一併移除。

> **為什麼一定要整份取代 `index.css`**：Vite 的 React 樣板附了一份示範 CSS，
> 裡面有 `#root { width: 1126px; margin: 0 auto; border-inline: 1px solid ...;
> text-align: center }`。它會把全螢幕版面**卡死在 1126px**、在畫面中間多畫一條
> 莫名的直線、讓整頁文字置中，然後生出橫向捲軸。
> 實測踩過：只覆蓋 `max-width` 沒有用，因為樣板寫的是 `width`。
> **跟樣板 CSS 打架時，刪掉比覆蓋便宜**——這句話本身也值得對同學講。

後端要在 8010 埠跑（8000 常被佔）。時間軸需要 `GET /chunks` 端點，
`04_chatbot_server.py` 已內建。

## `src/index.css`

```css
/* ============================================================
   GraphRAG 教學介面 — 設計 tokens
   投影在教室螢幕上看，所以：高對比、大字級、暗底（力導向圖在暗底最清楚）
   兩個強調色各有語意職責，不是裝飾：
     琥珀 = 證據（來自影片的哪個時間點）
     青   = 結構（知識圖譜的實體與關係）
   ============================================================ */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

:root {
  --ink:    #0A0D14;
  --panel:  #10151F;
  --raise:  #161C29;
  --line:   #232B3D;
  --text:   #E8ECF4;
  --muted:  #7E8CA6;
  --amber:  #FFB454;
  --cyan:   #52D1E8;

  --sans: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;

  --sidebar: 460px;
  --slate: 52px;
  --ribbon: 76px;
}

* { box-sizing: border-box; }

html, body, #root {
  margin: 0; padding: 0; width: 100%; height: 100%;
  background: var(--ink); color: var(--text);
  font-family: var(--sans);
}

body { overflow: hidden; }

::selection { background: var(--amber); color: var(--ink); }

:focus-visible { outline: 2px solid var(--cyan); outline-offset: 2px; }

/* ---------- 版面骨架 ---------- */
.app { display: grid; height: 100%;
       grid-template-rows: var(--slate) 1fr var(--ribbon);
       grid-template-columns: var(--sidebar) 1fr; }

/* ---------- 場記板：頂端狀態列 ---------- */
.slate {
  grid-column: 1 / -1;
  display: flex; align-items: center; gap: 20px;
  padding: 0 20px;
  background: var(--panel);
  border-bottom: 1px solid var(--line);
  font-family: var(--mono);
}
.slate-mark {
  font-size: 13px; font-weight: 600; letter-spacing: .22em;
  text-transform: uppercase; color: var(--text);
}
.slate-mark span { color: var(--amber); }
.slate-title {
  flex: 1; min-width: 0;
  font-family: var(--sans); font-size: 13px; color: var(--muted);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.stat { font-size: 11px; letter-spacing: .1em; color: var(--muted); text-transform: uppercase; }
.stat b { color: var(--cyan); font-weight: 600; }
.stat.ev b { color: var(--amber); }

/* ---------- 左側：對話 ---------- */
.chat { display: flex; flex-direction: column; min-height: 0;
        background: var(--panel); border-right: 1px solid var(--line); }
.log { flex: 1; overflow-y: auto; padding: 22px 20px 8px; scrollbar-width: thin;
       scrollbar-color: var(--line) transparent; }

.empty { color: var(--muted); font-size: 14px; line-height: 1.75; padding-top: 4px; }
.empty h2 { font-family: var(--mono); font-size: 12px; letter-spacing: .2em;
            text-transform: uppercase; color: var(--text); margin: 0 0 12px; }
.empty ul { margin: 14px 0 0; padding: 0; list-style: none; }
.empty li { padding: 9px 0; border-top: 1px solid var(--line); cursor: pointer;
            color: var(--text); transition: color .15s, padding-left .15s; }
.empty li:hover { color: var(--amber); padding-left: 6px; }
.empty li::before { content: "→ "; color: var(--muted); }

.turn { margin-bottom: 26px; }
.who { font-family: var(--mono); font-size: 10px; font-weight: 600;
       letter-spacing: .2em; text-transform: uppercase; margin-bottom: 8px; }
.turn.you .who { color: var(--muted); }
.turn.bot .who { color: var(--cyan); }
.said { font-size: 15px; line-height: 1.7; }
.turn.you .said { color: var(--text); font-weight: 500;
                  border-left: 2px solid var(--line); padding-left: 12px; }
.said strong { color: #fff; font-weight: 600; }
.said p { margin: 0 0 10px; }
.said p:last-child { margin-bottom: 0; }

/* 行內引用標記：連回它在時間軸上的位置 */
.cite {
  font-family: var(--mono); font-size: 10px; font-weight: 600;
  color: var(--amber); background: rgba(255,180,84,.12);
  border: 1px solid rgba(255,180,84,.35); border-radius: 3px;
  padding: 1px 5px; margin: 0 2px; text-decoration: none;
  vertical-align: 1px; white-space: nowrap;
}
.cite:hover { background: var(--amber); color: var(--ink); }

/* 證據列 */
.evidence { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); }
.evidence-label { font-family: var(--mono); font-size: 10px; letter-spacing: .2em;
                  text-transform: uppercase; color: var(--muted); margin-bottom: 9px; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-family: var(--mono); font-size: 12px; color: var(--amber);
  background: transparent; border: 1px solid rgba(255,180,84,.35);
  border-radius: 3px; padding: 4px 9px; text-decoration: none;
  transition: background .15s, color .15s;
}
.chip:hover { background: var(--amber); color: var(--ink); }

/* 思考中 */
.thinking { display: flex; align-items: center; gap: 9px;
            font-family: var(--mono); font-size: 11px; letter-spacing: .16em;
            text-transform: uppercase; color: var(--muted); }
.thinking i { width: 5px; height: 5px; border-radius: 50%; background: var(--amber);
              animation: pulse 1.1s ease-in-out infinite; }
.thinking i:nth-child(2) { animation-delay: .18s; }
.thinking i:nth-child(3) { animation-delay: .36s; }
@keyframes pulse { 0%,100% { opacity: .2; transform: scale(.8); }
                   50% { opacity: 1; transform: scale(1); } }

/* 輸入 */
.ask { display: flex; gap: 8px; padding: 14px 20px 18px;
       border-top: 1px solid var(--line); background: var(--panel); }
.ask input {
  flex: 1; min-width: 0; background: var(--raise); color: var(--text);
  border: 1px solid var(--line); border-radius: 4px;
  padding: 11px 13px; font-family: var(--sans); font-size: 14px;
}
.ask input::placeholder { color: var(--muted); }
.ask input:focus { outline: none; border-color: var(--cyan); }
.ask button {
  background: var(--amber); color: var(--ink); border: 0; border-radius: 4px;
  padding: 0 18px; font-family: var(--mono); font-size: 12px; font-weight: 600;
  letter-spacing: .12em; text-transform: uppercase; cursor: pointer;
  transition: opacity .15s;
}
.ask button:disabled { opacity: .35; cursor: default; }

/* ---------- 右側：圖譜 ---------- */
.stage { position: relative; overflow: hidden; background: var(--ink); }
.legend { position: absolute; left: 18px; bottom: 16px; z-index: 2;
          display: flex; gap: 16px; font-family: var(--mono); font-size: 10px;
          letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.legend b { display: inline-block; width: 7px; height: 7px; border-radius: 50%;
            margin-right: 6px; vertical-align: 0px; }
.hint { position: absolute; right: 18px; bottom: 16px; z-index: 2;
        font-family: var(--mono); font-size: 10px; letter-spacing: .12em;
        text-transform: uppercase; color: var(--muted); }

/* ---------- Signature：時間軸緞帶 ---------- */
.ribbon { grid-column: 1 / -1; background: var(--panel);
          border-top: 1px solid var(--line); padding: 12px 20px;
          display: flex; flex-direction: column; justify-content: center; }
.ribbon-head { display: flex; justify-content: space-between; align-items: baseline;
               font-family: var(--mono); font-size: 10px; letter-spacing: .2em;
               text-transform: uppercase; color: var(--muted); margin-bottom: 9px; }
.ribbon-head em { font-style: normal; color: var(--amber); }
.track { position: relative; height: 26px; border-left: 1px solid var(--line);
         border-right: 1px solid var(--line); }
.track::before { content: ""; position: absolute; left: 0; right: 0; top: 50%;
                 height: 1px; background: var(--line); }
.tick { position: absolute; top: 3px; width: 2px; height: 20px; margin-left: -1px;
        background: var(--line); border-radius: 1px; }
.tick.hot { background: var(--amber); box-shadow: 0 0 10px rgba(255,180,84,.75);
            top: 0; height: 26px; width: 3px;
            animation: rise .45s cubic-bezier(.2,.8,.2,1) backwards; }
.tick.hot:hover { cursor: pointer; }
@keyframes rise { from { transform: scaleY(.15); opacity: 0; } }
.scale { display: flex; justify-content: space-between;
         font-family: var(--mono); font-size: 10px; color: var(--muted); margin-top: 6px; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
```

## `src/App.jsx`

```jsx
// App.jsx — 完整取代 src/App.jsx
// 相依只有 react-force-graph-2d，樣式全在 index.css，不需要任何 UI 套件。
import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import ForceGraph2D from "react-force-graph-2d";

const API = "http://localhost:8010";
const SIDEBAR = 460, SLATE = 52, RIBBON = 76;
const CYAN = "#52D1E8", AMBER = "#FFB454", DIM = "#2A3348";

const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

/* 後端 prompt 已要求純文字 + 用 [片段 N] 引用，所以這裡只做兩件事：
   把 [片段 N] 換成可點的時間戳標籤、把段落切開。
   剩下的 **粗體** / * 項目符號是防禦性清理——LLM 偶爾還是會手滑。
   ponytail: 天花板是「只認得我們自己 prompt 產出的格式」，
   要支援完整 markdown 就換成 react-markdown。 */
function render(text, sources = []) {
  const paras = text.split(/\n{2,}|\n(?=\s*\d+[.、]\s)/).map(p => p.trim()).filter(Boolean);
  return paras.map((para, pi) => {
    const clean = para.replace(/^\s*[*-]\s+/, "").replace(/\*\*/g, "");
    const out = [];
    let last = 0, m;
    // 一個中括號裡可能有多個編號（「[片段 3, 片段 4]」），全部抓出來各給一個標籤
    const re = /\[[^\]]*片段[^\]]*\]/g;
    while ((m = re.exec(clean))) {
      if (m.index > last) out.push(clean.slice(last, m.index));
      const nums = [...m[0].matchAll(/\d+/g)].map(x => +x[0]);
      nums.forEach(n => {
        const src = sources[n - 1];
        out.push(src
          ? <a key={out.length} className="cite" href={src.url} target="_blank" rel="noreferrer"
               title={`片段 ${n}`}>{src.url.includes("youtu") ? mmss(src.start) : `p.${src.start}`}</a>
          : <span key={out.length} className="cite">片段 {n}</span>);
      });
      last = m.index + m[0].length;
    }
    if (last < clean.length) out.push(clean.slice(last));
    return <p key={pi}>{out}</p>;
  });
}

const SEEDS = [
  "注意力機制是怎麼運作的",
  "什麼是 embedding，它為什麼有意義",
  "Transformer 跟之前的語言模型差在哪",
];

export default function App() {
  const [graph, setGraph] = useState({ nodes: [], links: [] });
  const [chunks, setChunks] = useState([]);
  const [hot, setHot] = useState([]);          // 本次答案的證據時間點
  const [highlight, setHighlight] = useState(new Set());
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [title, setTitle] = useState("");
  // 坑 4: ForceGraph2D 不給 width/height 會用整個視窗寬，被側欄一擠就被裁掉
  const [size, setSize] = useState({ w: 0, h: 0 });
  const fgRef = useRef();
  const logRef = useRef();

  useEffect(() => {
    const fit = () => setSize({
      w: window.innerWidth - SIDEBAR,
      h: window.innerHeight - SLATE - RIBBON,
    });
    fit();
    window.addEventListener("resize", fit);
    fetch(`${API}/graph`).then(r => r.json()).then(setGraph);
    fetch(`${API}/chunks`).then(r => r.json()).then(d => {
      setChunks(d.chunks || []);
      setTitle(d.chunks?.[0]?.url?.includes("youtu") ? "YouTube 逐字稿" : (d.chunks?.[0]?.url || ""));
    }).catch(() => {});
    return () => window.removeEventListener("resize", fit);
  }, []);

  // 力的參數：預設值會把 276 個節點攤得很開。收緊一點，畫面才聚得起來。
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

  // 節點連結數：決定畫多大、標籤何時出現。是結構資訊，不是裝飾。
  const degree = useMemo(() => {
    const d = {};
    graph.links.forEach(l => {
      const s = l.source.id ?? l.source, t = l.target.id ?? l.target;
      d[s] = (d[s] || 0) + 1; d[t] = (d[t] || 0) + 1;
    });
    return d;
  }, [graph.links]);

  const span = Math.max(...chunks.map(c => c.start), ...hot, 60) * 1.02;

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
      setHighlight(new Set(res.graph_nodes.map(n => n.id)));
      setHot(res.sources.map(s => s.start));
      fgRef.current?.d3ReheatSimulation();   // 高亮變了，讓圖動一下告訴使用者它換了狀態
    } catch {
      setMessages(m => [...m, { role: "bot", text: `連不上後端 ${API}。確認 uvicorn 還在跑。` }]);
    } finally { setBusy(false); }
  }, [input, busy]);

  const expandNode = useCallback(async (node) => {
    // 點節點 -> 載入鄰居子圖並合併進畫面
    const sub = await fetch(`${API}/graph/${encodeURIComponent(node.id)}`).then(r => r.json());
    setGraph(g => {
      const ids = new Set(g.nodes.map(n => n.id));
      // 坑 1: 渲染後 link.source 會從字串變成節點物件，去重要寫 .id ?? 本身
      const key = l => `${l.source.id ?? l.source}->${l.target.id ?? l.target}`;
      const linkSet = new Set(g.links.map(key));
      return {
        nodes: [...g.nodes, ...sub.nodes.filter(n => !ids.has(n.id))],
        links: [...g.links, ...sub.links.filter(l => !linkSet.has(key(l)))],
      };
    });
    setHighlight(new Set(sub.nodes.map(n => n.id)));
    fgRef.current?.d3ReheatSimulation();
  }, []);

  const radius = useCallback(
    (id, scale) => (3.6 + Math.min(degree[id] || 0, 10) * 0.9) / scale, [degree]);

  /* 只畫圓。關鍵：半徑除以 scale，所以節點在「螢幕上」永遠是同樣大小，
     不會因為 zoomToFit 縮小就變成看不見的小點。 */
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

  /* 標籤分開畫，畫在所有節點與連線之上。
     兩件事讓它可讀：
       1. 排序 —— 高亮的先畫、連結多的次之，重要的先搶到位置
       2. 碰撞偵測 —— 已被佔走的矩形就跳過，寧可少幾個標籤也不要疊成一團
     （在 nodeCanvasObject 裡做不到，因為那是逐節點呼叫、順序由資料決定。） */
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

  return (
    <div className="app">
      <header className="slate">
        <div className="slate-mark">GRAPH<span>·</span>RAG</div>
        <div className="slate-title">{title || "載入中…"}</div>
        <div className="stat">節點 <b>{graph.nodes.length}</b></div>
        <div className="stat">關係 <b>{graph.links.length}</b></div>
        <div className="stat ev">片段 <b>{chunks.length}</b></div>
      </header>

      <section className="chat">
        <div className="log" ref={logRef}>
          {messages.length === 0 && (
            <div className="empty">
              <h2>問影片裡的內容</h2>
              回答只根據逐字稿，並附上可以點回影片的時間戳。
              右邊圖譜會亮出相關概念，下方時間軸會標出證據在影片的哪個位置。
              <ul>{SEEDS.map(s => <li key={s} onClick={() => send(s)}>{s}</li>)}</ul>
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
                         onMouseEnter={() => setHot([s.start])}
                         onMouseLeave={() => setHot(m.sources.map(x => x.start))}>
                        ▸ {s.url.includes("youtu") ? mmss(s.start) : `第 ${s.start} 頁`}
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
                 placeholder="問影片內容…" />
          <button onClick={() => send()} disabled={busy || !input.trim()}>送出</button>
        </div>
      </section>

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
          // 讓布局「看得出來在動」：預設收斂太快，一載入就是靜止畫面
          d3AlphaDecay={0.012}
          d3VelocityDecay={0.28}
          cooldownTime={25000}
          onEngineStop={() => fgRef.current?.zoomToFit(700, 90)}
        />
        <div className="legend">
          <span><b style={{ background: CYAN }} />概念</span>
          <span><b style={{ background: AMBER }} />與這次回答相關</span>
        </div>
        <div className="hint">點節點展開鄰居 · 可拖曳</div>
      </section>

      <footer className="ribbon">
        <div className="ribbon-head">
          <span>影片時間軸 · 證據位置</span>
          <span>{hot.length ? <em>{hot.length} 處命中</em> : `${chunks.length} 個片段`}</span>
        </div>
        <div className="track">
          {chunks.map((c, i) => (
            <span key={i} className="tick" style={{ left: `${(c.start / span) * 100}%` }} />
          ))}
          {hot.map((s, i) => (
            <a key={`h${i}`} className="tick hot" title={mmss(s)}
               href={chunks.find(c => c.start === s)?.url || "#"}
               target="_blank" rel="noreferrer"
               style={{ left: `${(s / span) * 100}%`, animationDelay: `${i * 60}ms` }} />
          ))}
        </div>
        <div className="scale"><span>0:00</span><span>{mmss(span)}</span></div>
      </footer>
    </div>
  );
}
```

## 已知坑（都在上面程式碼裡處理了，講解時點出來）

1. **react-force-graph 會改寫 links**：渲染後 `link.source` 從字串變成節點
   物件，所以合併子圖去重時要寫 `l.source.id ?? l.source`。漏掉這個會出現
   重複邊或 crash——這是這個套件最經典的坑。
2. **節點合併去重**：直接 concat 會出現重複 id，力導向圖會抖動。
3. **CORS**：後端已開 `allow_origins=["*"]`（僅教學用）。
4. **畫布尺寸**：不給 `width`/`height` 就會用整個視窗寬，被左側聊天欄一擠，
   圖的右半邊直接被切出畫面外——投影幕上特別明顯。上面用 resize 監聽明確餵尺寸。
5. **節點在螢幕上的大小要除以 `scale`**：`zoomToFit` 之後縮放比例可能很小，
   固定的圖座標半徑會變成看不見的小點。除以 `scale` 讓節點維持固定的**螢幕**大小。
6. **沒 `zoomToFit` 就是一坨**：力導向布局的初始縮放跟節點數無關。實測 276 個
   節點不做 `zoomToFit` 就是畫面正中央一小團。要等模擬收斂後再縮放。
7. **標籤一定要做碰撞偵測**：24 個高亮節點聚在一起時，標籤會疊成完全讀不出來的
   一團。所以標籤不在 `nodeCanvasObject` 裡畫（那是逐節點呼叫、順序由資料決定），
   而是在 `onRenderFramePost` 統一畫：先依「高亮 > 連結數」排序，再用矩形碰撞
   偵測跳過重疊的。**寧可少幾個標籤，也不要疊成一團。**
8. **預設參數會讓圖看起來是靜止的**：`d3AlphaDecay` 預設收斂很快，一載入就不動了。
   調低它 + 拉長 `cooldownTime`，才看得出來布局在自己找位置——這對「圖是活的」
   這個感受影響很大。互動後記得 `d3ReheatSimulation()`。

## markdown 是在後端解決的，不是前端

一開始 `04_chatbot_server.py` 把 context 標成 `[片段 1｜{網址}]`，
LLM 就照抄這個格式，答案裡塞滿 `**粗體**` 和裸網址，前端畫面很醜。

在前端用正則去擦是徒勞的。**正確做法是改 prompt**：片段標頭不放網址、
明確要求純文字、引用只寫 `[片段 N]`，網址由介面自己補。
實測改完之後：殘留 `**` 歸零、裸網址歸零。

> 教學重點：**輸出格式的問題，優先在生成端解決，不要在渲染端補救。**
> LLM 會模仿你給它的 context 長什麼樣子——這個現象本身就值得講。

## 升級路線：CopilotKit 版

保底版能動之後，把左側聊天欄換成 CopilotKit：

1. 用 CopilotKit MCP 查目前的安裝指令與 `CopilotKit` provider 用法。
2. 後端 `/chat` 保持不變；以 CopilotKit 的自訂 agent 端點接上。
3. 用 `useCopilotAction` 註冊一個 `highlightNodes` 前端動作，讓 agent 回答時
   主動呼叫它高亮圖譜節點——這就是 AG-UI「agent 操作前端」的核心賣點，
   也是課程最好的高潮示範點。

具體 API 簽名以 MCP 查到的當前文件為準，不要照舊版教學抄。
