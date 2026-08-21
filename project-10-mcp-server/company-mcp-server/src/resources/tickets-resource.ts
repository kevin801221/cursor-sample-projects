/**
 * Resource: tickets://all —— 工單清單（唯讀）。
 *
 * Tools 是「請做一件事」，Resources 是「給我看現在的狀態」。
 * 這裡一樣遵守鐵律 2：只給 5 個欄位，description 全文不進來。
 */
import { readTickets } from "../tools/tickets.js";

export const TICKETS_URI = "tickets://all";

export async function getTicketsResource(): Promise<string> {
  const simplified = readTickets().map((t) => ({
    id: t.id,
    title: t.title,
    status: t.status,
    priority: t.priority,
    created_at: t.created_at,
  }));

  return JSON.stringify(simplified, null, 2);
}
