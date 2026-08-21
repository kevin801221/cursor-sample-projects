/**
 * Tool: search_knowledge_base —— 搜尋公司知識庫。
 *
 * 鐵律 2（回傳精簡）：只回 {id, title, tag, excerpt}，excerpt 砍到 200 字。
 * 整篇 content 對模型沒有用，只會把 context 塞爆。
 */
import { z } from "zod";
import { readFileSync } from "node:fs";
import { dataPath } from "../paths.js";

/** 紙條格式規則：模型送進來的參數必須長這樣，不合格 Zod 直接退件。 */
export const searchParamsSchema = z.object({
  query: z.string({ error: "query 必填，請給搜尋關鍵字" }).min(1, "搜尋字串不能空白"),
  limit: z.number().int().min(1, "limit 至少 1").max(20, "limit 最多 20").default(10),
  offset: z.number().int().min(0, "offset 不能是負數").default(0),
  tag: z
    .enum(["security", "infrastructure", "process"], {
      error: "tag 只能是 security、infrastructure 或 process",
    })
    .optional(),
});

export type SearchParams = z.infer<typeof searchParamsSchema>;

interface Article {
  id: string;
  title: string;
  content: string;
  tag: string;
  created_at: string;
}

export interface SearchResult {
  articles: Array<{ id: string; title: string; tag: string; excerpt: string }>;
  total: number;
  offset: number;
  hasMore: boolean;
}

/** 相關度：標題命中 2 分、內文命中 1 分，兩邊都中就是 3 分。 */
function score(article: Article, query: string): number {
  const q = query.toLowerCase();
  return (
    (article.title.toLowerCase().includes(q) ? 2 : 0) +
    (article.content.toLowerCase().includes(q) ? 1 : 0)
  );
}

export async function searchKnowledgeBase(params: unknown): Promise<SearchResult> {
  // 1. Zod 驗證參數（第一道防線）
  const { query, limit, offset, tag } = searchParamsSchema.parse(params);

  // 2. 讀知識庫
  const all: Article[] = JSON.parse(readFileSync(dataPath("knowledge.json"), "utf-8"));

  // 3. 過濾 tag → 算相關度 → 排序
  const ranked = all
    .filter((a) => !tag || a.tag === tag)
    .map((a) => ({ article: a, score: score(a, query) }))
    .filter((x) => x.score > 0)
    .sort((x, y) => y.score - x.score);

  // 4. 分頁（offset / limit）後回傳精簡版
  const page = ranked.slice(offset, offset + limit);
  return {
    articles: page.map(({ article }) => ({
      id: article.id,
      title: article.title,
      tag: article.tag,
      excerpt: article.content.slice(0, 200),
    })),
    total: ranked.length,
    offset,
    hasMore: offset + page.length < ranked.length,
  };
}
