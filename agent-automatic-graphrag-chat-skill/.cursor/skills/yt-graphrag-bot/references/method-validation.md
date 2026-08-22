# 方法驗證：SOTA 對齊迴圈 + Decision Record

本文件是 Phase 4.5 的執行細節。目標：讓 agent 產出一份**可辯護的證據**，
證明現行 RAG/Graph 方法在「當前狀態」下是最好的選擇。

## 「最好」的可辯護定義（先講清楚，這是方法論教學）

一個方法可以宣稱「目前最好」，若且唯若同時滿足三條件：
1. **文獻對齊**：與官方文件/近期文獻的最佳實務不衝突，或衝突處有明確理由。
2. **實測勝出**：在自己的評估集上，數據上不輸給所有已測候選方法。
3. **紀錄在案**：每個被否決的候選都留有否決證據（decision record）。

缺任何一條都只是「我覺得不錯」。這個定義本身就值得一頁投影片。

## Agent 執行迴圈

```
┌─> 1. 調查: Langchain-docs MCP 查官方 retrieval/RAG 最佳實務
│         + web search 近 6 個月的 RAG/GraphRAG survey 與技術文章
│   2. 列候選: 找出「文獻推薦、但現行 pipeline 沒有」的技術
│         （典型候選: reranker、HyDE、parent-document、句子視窗、
│           社群偵測式 GraphRAG、hybrid BM25+dense）
│   3. 挑戰: 選 1 個最有希望的候選，實作進 pipeline 分支
│   4. 實測: uv run python scripts/05_evaluate_rag.py --run（同一評估集 A/B）
│   5. 裁決:
│        候選勝 -> 併入主線，回到 1（新的「現行方法」要重新受挑戰）
└─────── 候選敗/平 -> 寫入 decision record 的否決欄，測下一個候選
    6. 終止: 所有合理候選都測過且無一勝出
       -> 產出結論:「現行方法在目前評估集與文獻範圍內為最佳」+ 全部證據
```

迴圈紀律（防止 agent 走偏）:
- 一次只測**一個**變因，否則勝負無法歸因。
- 評估集在迴圈開始前定版，中途不得改題（改題 = 重跑全部）。
- 候選實作放分支/獨立函式，敗了要能乾淨移除。
- 設迭代上限（建議 3~4 輪），教學場景點到為止即可。

## 調查階段的具體查詢

用 Langchain-docs MCP 查（自然語言即可）:
- 「目前官方推薦的 retrieval 強化技術有哪些」
- 「MultiQueryRetriever / ContextualCompressionRetriever 的當前用法」
- 「LangChain 官方對 GraphRAG / graph retriever 的支援現況」

用 web search 查（記得帶年份找新資料）:
- RAG survey、GraphRAG 論文（如 Microsoft GraphRAG 的社群摘要路線）、
  reranker 比較（cross-encoder vs LLM rerank）
- 注意：技術部落格常有推銷成分，優先引官方文件與論文，
  部落格結論要交叉驗證。

## Decision Record 範本（每個候選一筆）

```markdown
### DR-{編號}: {候選技術名}
- 日期 / 評估集版本: {date} / eval_set v{n}（{題數} 題）
- 來源: {官方文件連結或論文}
- 假說: 加入後預期改善 {哪個維度}，因為 {機制}
- 實作: {改了哪支腳本的哪個函式，一句話}
- 結果: baseline {分數} vs +候選 {分數}（faithfulness/completeness/citation）
- 裁決: 採用 / 否決
- 否決理由: {數據不顯著 / 延遲成本 / 複雜度不值得}
- 附件: eval_report_{編號}.json
```

## 誠實條款（結論必寫的限制聲明）

最終結論必須附上適用範圍，否則就是過度宣稱:
- 「最佳」僅在**此評估集**（單支影片、N 題）與**已測候選集合**內成立。
- LLM-as-judge 有噪音：勝負差距小於 ~0.3 分視為平手，不宣稱勝出。
  更嚴謹可每題評 3 次取中位數（成本 x3，教學可略）。
- **judge 與受測 pipeline 同級模型**：本課程預設兩邊都用 Gemini Flash。
  這省成本，但 judge 沒有比受測系統更強的判斷力，且兩邊同源會有
  self-preference bias（模型偏好自己家族的輸出風格）。因此本設定下的
  勝負只能當「方向性訊號」，不能當強證據。要升級成強證據就
  `export GEMINI_JUDGE_MODEL=<更強的模型>` 重跑，並在 decision record
  註明用了哪支 judge。
  ——把這條寫出來本身就是教學重點：**知道自己的證據有多強，比證據看起來
  多漂亮更重要**。
- 換影片類型（如從教學片換成訪談）需重跑評估，結論不自動遷移。

這個限制聲明不是弱點，是專業度的展現——帶同學體會
「有邊界的強結論」比「無邊界的空話」有價值得多。
