/**
 * Tool: create_ticket —— 建立支援工單（有副作用的動作）。
 *
 * 三個教學重點：
 * 1. Zod 驗證參數（紙條格式規則）
 * 2. AbortController 逾時控制：8 秒沒回就放棄，讓 Agent 知道「換個辦法」
 * 3. 錯誤回自然語言，不回 stack trace（鐵律 2）
 *
 * 離線設計：DEMO_OFFLINE=1（預設值）時把 fetch 換成 localTicketApi，
 * 走的仍然是同一條程式碼路徑——一樣的 AbortController、一樣的 response.ok
 * 判斷、一樣的 catch。課堂上不需要任何外部 API 也能演完整流程。
 */
import { z } from "zod";
import { readFileSync, writeFileSync } from "node:fs";
import { dataPath } from "../paths.js";

export const createTicketSchema = z.object({
  title: z.string({ error: "title 必填，請寫一句話說明問題" }).min(1, "標題不能空白").max(200, "標題最多 200 字"),
  description: z
    .string({ error: "description 必填，請描述問題與已經試過的做法" })
    .min(1, "描述不能空白")
    .max(2000, "描述最多 2000 字"),
  priority: z.enum(["low", "medium", "high"], { error: "priority 只能是 low、medium 或 high" }),
});

export type CreateTicketParams = z.infer<typeof createTicketSchema>;

export interface Ticket {
  id: string;
  title: string;
  description: string;
  status: "open" | "in_progress" | "closed";
  priority: "low" | "medium" | "high";
  created_at: string;
}

/** fetch 與離線 provider 共用的最小介面——換 provider 不用改呼叫端。 */
type Fetcher = (
  url: string,
  init: { method: string; headers: Record<string, string>; body: string; signal: AbortSignal },
) => Promise<{ ok: boolean; status: number; json: () => Promise<any> }>;

export function readTickets(): Ticket[] {
  return JSON.parse(readFileSync(dataPath("tickets.json"), "utf-8"));
}

function nextTicketId(tickets: Ticket[]): string {
  const max = tickets.reduce((acc, t) => Math.max(acc, Number(t.id.replace("TKT-", "")) || 0), 0);
  return `TKT-${String(max + 1).padStart(4, "0")}`;
}

/** 可被 AbortSignal 中斷的等待——模擬「API 很慢」。 */
function sleepOrAbort(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        const error = new Error("This operation was aborted");
        error.name = "AbortError";
        reject(error);
      },
      { once: true },
    );
  });
}

/**
 * 離線版的 Ticket API：行為跟真的 HTTP API 一樣（會慢、會失敗、會回 201 + id），
 * 差別只在資料寫進 data/tickets.json 而不是遠端資料庫。
 * DEMO_TICKET_DELAY_MS 調延遲、DEMO_TICKET_FAIL=1 模擬 API 掛掉。
 */
const localTicketApi: Fetcher = async (_url, init) => {
  await sleepOrAbort(Number(process.env.DEMO_TICKET_DELAY_MS ?? 150), init.signal);

  if (process.env.DEMO_TICKET_FAIL === "1") {
    return { ok: false, status: 503, json: async () => ({}) };
  }

  const payload: CreateTicketParams = JSON.parse(init.body);
  const tickets = readTickets();
  const ticket: Ticket = {
    id: nextTicketId(tickets),
    title: payload.title,
    description: payload.description,
    status: "open",
    priority: payload.priority,
    created_at: new Date().toISOString(),
  };
  tickets.push(ticket);
  writeFileSync(dataPath("tickets.json"), JSON.stringify(tickets, null, 2) + "\n", "utf-8");

  return { ok: true, status: 201, json: async () => ({ id: ticket.id }) };
};

export async function createTicket(params: unknown): Promise<Record<string, string>> {
  // 1. Zod 驗證
  const validated = createTicketSchema.parse(params);

  // 2. AbortController：預設 8 秒逾時
  const timeoutMs = Number(process.env.TICKET_TIMEOUT_MS ?? 8000);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  // 3. 選 provider：離線（預設）走 localTicketApi，DEMO_OFFLINE=0 才打真的 API
  const offline = process.env.DEMO_OFFLINE !== "0";
  const send: Fetcher = offline ? localTicketApi : (fetch as unknown as Fetcher);
  const apiUrl = `${process.env.KNOWLEDGE_API_URL ?? "https://api.tickets.local"}/create`;

  try {
    const response = await send(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(validated),
      signal: controller.signal,
    });

    if (!response.ok) {
      return {
        error: `Ticket API 回傳 ${response.status}，工單沒有建立。請確認標題是否重複，或稍後再試一次。`,
      };
    }

    const data = await response.json();
    return {
      ticketId: data.id,
      message: `Ticket ${data.id} created successfully`,
    };
  } catch (e: any) {
    // 錯誤要「可讀」：模型看得懂才知道下一步該做什麼
    if (e?.name === "AbortError") {
      return {
        error: `Ticket API 連線逾時（${Math.round(timeoutMs / 1000)} 秒）。工單尚未建立，請稍候再試，或檢查 VPN／網路連線。`,
      };
    }
    return { error: `系統錯誤：${e?.message ?? e}。工單尚未建立，請聯繫管理員。` };
  } finally {
    clearTimeout(timeout);
  }
}
