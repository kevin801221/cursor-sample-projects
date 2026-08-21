/**
 * company-knowledge-mcp —— MCP stdio server 主程式。
 *
 * 鐵律 3：這個檔案（以及整個 src/）不存在任何 console.log。
 * stdout 唯一合法的內容是 JSON-RPC 訊息，除錯一律 console.error 走 stderr。
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  GetPromptRequestSchema,
  ListPromptsRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { searchKnowledgeBase } from "./tools/search.js";
import { createTicket } from "./tools/tickets.js";
import { getTicketsResource, TICKETS_URI } from "./resources/tickets-resource.js";

const server = new Server(
  { name: "company-knowledge-mcp", version: "1.0.0" },
  { capabilities: { tools: {}, resources: {}, prompts: {} } },
);

// ────────────────────────────────────────────────────────────
// Tools：數量克制，只有兩個核心動作（鐵律 2 的「數量克制」）
// ────────────────────────────────────────────────────────────
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "search_knowledge_base",
      description:
        "搜尋公司內部知識庫（VPN、SSO、部署、請假等）。回傳精簡結果：id、title、tag、前 200 字摘要。可用 tag 過濾：security / infrastructure / process。結果多時用 offset 翻頁。",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "搜尋字串，例如「VPN 逾時」" },
          limit: { type: "number", description: "回傳筆數，預設 10，最多 20", default: 10 },
          offset: { type: "number", description: "分頁起點，預設 0", default: 0 },
          tag: {
            type: "string",
            enum: ["security", "infrastructure", "process"],
            description: "分類篩選（選填）",
          },
        },
        required: ["query"],
      },
    },
    {
      name: "create_ticket",
      description:
        "建立支援工單。這是有副作用的動作——請先用 search_knowledge_base 查過知識庫，確認沒有現成答案再開票。",
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string", description: "工單標題，1-200 字" },
          description: { type: "string", description: "問題描述，1-2000 字" },
          priority: {
            type: "string",
            enum: ["low", "medium", "high"],
            description: "優先級",
          },
        },
        required: ["title", "description", "priority"],
      },
    },
  ],
}));

/** ZodError 轉成模型看得懂的人話——不是丟 stack trace（鐵律 2）。 */
function readableError(error: unknown): string {
  if (error instanceof z.ZodError) {
    const lines = error.issues.map((i) => `- ${i.path.join(".") || "(參數)"}：${i.message}`);
    return `參數不合格，請修正後重試：\n${lines.join("\n")}`;
  }
  return `工具執行失敗：${(error as Error)?.message ?? String(error)}`;
}

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    let result: unknown;
    if (name === "search_knowledge_base") {
      result = await searchKnowledgeBase(args);
    } else if (name === "create_ticket") {
      result = await createTicket(args);
    } else {
      return {
        content: [{ type: "text", text: `沒有這個工具：${name}。可用工具：search_knowledge_base、create_ticket。` }],
        isError: true,
      };
    }
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error) {
    return { content: [{ type: "text", text: readableError(error) }], isError: true };
  }
});

// ────────────────────────────────────────────────────────────
// Resources：唯讀資料，Agent 想看就拉
// ────────────────────────────────────────────────────────────
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: TICKETS_URI,
      name: "公司工單清單",
      description: "所有已建立的工單（id / title / status / priority / created_at）",
      mimeType: "application/json",
    },
  ],
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri !== TICKETS_URI) {
    throw new Error(`找不到這個資源：${request.params.uri}。目前只提供 ${TICKETS_URI}。`);
  }
  return {
    contents: [
      { uri: TICKETS_URI, mimeType: "application/json", text: await getTicketsResource() },
    ],
  };
});

// ────────────────────────────────────────────────────────────
// Prompts：預先寫好的決策流程，人選擇套用
// ────────────────────────────────────────────────────────────
server.setRequestHandler(ListPromptsRequestSchema, async () => ({
  prompts: [
    {
      name: "triage_ticket",
      description: "工單分流：先查知識庫，查得到就回答、查不到才開票",
      arguments: [
        { name: "complaint", description: "使用者回報的問題", required: true },
        { name: "priority", description: "真的要開票時的優先級：low / medium / high", required: false },
      ],
    },
  ],
}));

server.setRequestHandler(GetPromptRequestSchema, async (request) => {
  if (request.params.name !== "triage_ticket") {
    throw new Error(`找不到這個 prompt：${request.params.name}。目前只提供 triage_ticket。`);
  }
  const complaint = request.params.arguments?.complaint ?? "（使用者尚未描述問題）";
  const priority = request.params.arguments?.priority ?? "medium";

  return {
    description: "工單分流決策流程",
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: [
            `你是公司 IT 支援的分流助理。使用者回報：「${complaint}」`,
            "",
            "請依序執行，不要跳步：",
            "1. 先呼叫 search_knowledge_base，query 用問題裡的關鍵字；必要時用 tag（security / infrastructure / process）縮小範圍。",
            "2. 若 articles 非空且內容真的能解答問題 → 用自然語言總結解法並附上文章 id，**不要開票**。",
            `3. 只有在 articles 為空、或內容明顯答非所問時 → 才呼叫 create_ticket，priority 用 "${priority}"，title 是問題摘要，description 要寫清楚你查過哪些關鍵字、為什麼知識庫解決不了。`,
            "4. 最後回報你實際呼叫了哪些工具、順序為何。",
            "",
            "鐵律：查得到答案就不要開票——開票是有副作用的動作。",
          ].join("\n"),
        },
      },
    ],
  };
});

// ────────────────────────────────────────────────────────────
// 啟動
// ────────────────────────────────────────────────────────────
async function main() {
  // 反面教材開關（鐵律 3）：MCP_DEMO_BREAK_STDOUT=1 時故意把文字寫進 stdout。
  // 下面這行做的事跟 console.log 一模一樣——把非 JSON-RPC 的文字丟進協定通道。
  // 課堂上只用來示範「協定會怎麼壞掉」，正式程式碼永遠不該有這種東西。
  if (process.env.MCP_DEMO_BREAK_STDOUT === "1") {
    process.stdout.write("[debug] server starting...\n");
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  // 除錯訊息一律走 stderr
  console.error("company-knowledge-mcp running on stdio");
}

main().catch((error) => {
  console.error("server 啟動失敗：", error);
  process.exit(1);
});
