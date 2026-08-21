#!/usr/bin/env node
/**
 * 最小可跑的自我檢查（不架測試框架，就是一堆 assert）。
 * 跑的是編譯後的 dist/，所以它同時驗證了「build 有沒有壞」。
 *
 * 用法：npm run build && node scripts/check.mjs
 */
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import * as path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TICKETS = path.join(ROOT, "data", "tickets.json");

const useColor = !process.env.NO_COLOR;
const ok = (s) => (useColor ? `\x1b[32m✔\x1b[0m ${s}` : `✔ ${s}`);
const bad = (s) => (useColor ? `\x1b[31;1m✘ ${s}\x1b[0m` : `✘ ${s}`);
const say = (s) => process.stdout.write(`${s}\n`);

const { searchKnowledgeBase } = await import("../dist/tools/search.js");
const { createTicket, readTickets } = await import("../dist/tools/tickets.js");
const { getTicketsResource } = await import("../dist/resources/tickets-resource.js");

// create_ticket 會真的寫檔，先備份、最後還原
const backup = readFileSync(TICKETS, "utf-8");

let failed = 0;
async function it(name, fn) {
  try {
    await fn();
    say(ok(name));
  } catch (e) {
    failed++;
    say(bad(`${name}\n    ${e.message.split("\n")[0]}`));
  }
}

await it("search：query=VPN 找得到 KB-001，摘要不超過 200 字", async () => {
  const r = await searchKnowledgeBase({ query: "VPN" });
  assert.ok(r.articles.length > 0, "應該至少找到一篇");
  assert.ok(r.articles.some((a) => a.id === "KB-001"));
  for (const a of r.articles) {
    assert.ok(a.excerpt.length <= 200, `excerpt 超過 200 字：${a.excerpt.length}`);
    assert.deepEqual(Object.keys(a).sort(), ["excerpt", "id", "tag", "title"]);
  }
});

await it("search：tag 過濾只回該分類（鐵律 2 的精簡＋正確）", async () => {
  const r = await searchKnowledgeBase({ query: "密碼", tag: "security" });
  assert.ok(r.articles.length > 0);
  assert.ok(r.articles.every((a) => a.tag === "security"));
});

await it("search：分頁 offset 不重複、total 不變", async () => {
  const p1 = await searchKnowledgeBase({ query: "工單", limit: 2, offset: 0 });
  const p2 = await searchKnowledgeBase({ query: "工單", limit: 2, offset: 2 });
  assert.equal(p1.total, p2.total);
  assert.equal(p1.hasMore, true);
  const overlap = p1.articles.filter((a) => p2.articles.some((b) => b.id === a.id));
  assert.equal(overlap.length, 0, "兩頁不該有重複文章");
});

await it("Zod：空 query 被擋，訊息是「搜尋字串不能空白」", async () => {
  await assert.rejects(() => searchKnowledgeBase({ query: "" }), /搜尋字串不能空白/);
});

await it("Zod：limit=100 被擋（上限 20）", async () => {
  await assert.rejects(() => searchKnowledgeBase({ query: "VPN", limit: 100 }), /limit 最多 20/);
});

await it("Zod：priority 只吃 low/medium/high", async () => {
  await assert.rejects(
    () => createTicket({ title: "t", description: "d", priority: "urgent" }),
    /priority 只能是/,
  );
});

await it("create_ticket：成功建票並寫進 data/tickets.json", async () => {
  const before = readTickets().length;
  const r = await createTicket({ title: "自我檢查用工單", description: "check.mjs 建立", priority: "low" });
  assert.match(r.ticketId ?? "", /^TKT-\d{4}$/, `沒拿到工單編號：${JSON.stringify(r)}`);
  assert.equal(readTickets().length, before + 1);
});

await it("Resource tickets://all：只暴露 5 個欄位，且是合法 JSON", async () => {
  const rows = JSON.parse(await getTicketsResource());
  assert.ok(rows.length > 0);
  for (const row of rows) {
    assert.deepEqual(Object.keys(row).sort(), ["created_at", "id", "priority", "status", "title"]);
  }
});

await it("AbortController：API 太慢時回「逾時」的人話，不是 stack trace", async () => {
  process.env.TICKET_TIMEOUT_MS = "300";
  process.env.DEMO_TICKET_DELAY_MS = "5000";
  const before = readTickets().length;
  const r = await createTicket({ title: "逾時測試", description: "模擬 API 沒回應", priority: "high" });
  assert.match(r.error ?? "", /逾時/);
  assert.ok(!/Error:|at .*\.js:/.test(r.error), "錯誤訊息不該長得像 stack trace");
  assert.equal(readTickets().length, before, "逾時不該留下半張工單");
  delete process.env.TICKET_TIMEOUT_MS;
  delete process.env.DEMO_TICKET_DELAY_MS;
});

await it("API 回 5xx：回可讀訊息並說明工單沒有建立", async () => {
  process.env.DEMO_TICKET_FAIL = "1";
  const r = await createTicket({ title: "API 故障測試", description: "模擬 503", priority: "medium" });
  assert.match(r.error ?? "", /503/);
  assert.match(r.error ?? "", /沒有建立/);
  delete process.env.DEMO_TICKET_FAIL;
});

await it("鐵律 3：src/ 沒有任何 console.log 呼叫（註解裡提到不算）", async () => {
  const walk = (dir) =>
    readdirSync(dir).flatMap((name) => {
      const full = path.join(dir, name);
      return statSync(full).isDirectory() ? walk(full) : [full];
    });
  const hits = walk(path.join(ROOT, "src"))
    .filter((f) => f.endsWith(".ts"))
    .filter((f) => /console\s*\.\s*log\s*\(/.test(readFileSync(f, "utf-8")));
  assert.deepEqual(hits, [], `這些檔案有 console.log：${hits.join(", ")}`);
});

// 還原資料，讓下次 demo 從乾淨狀態開始
writeFileSync(TICKETS, backup, "utf-8");

say("");
if (failed === 0) {
  say(useColor ? "\x1b[32;1m全部檢查通過。\x1b[0m data/tickets.json 已還原成原始狀態。" : "全部檢查通過。data/tickets.json 已還原成原始狀態。");
  process.exit(0);
}
say(bad(`有 ${failed} 項檢查沒過`));
process.exit(1);
