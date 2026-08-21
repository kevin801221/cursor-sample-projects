/**
 * Service Worker (總管)：
 * 唯一被信任的環境。持有 API Key，處理 LLM 請求與 Storage 讀寫。
 * Content Script 永遠無法直接讀取此處的金鑰。
 */

const DEFAULT_SETTINGS = {
  apiKey: '',
  provider: 'mock', // 'mock' | 'openai' | 'gemini'
  customPrompt: '請用繁體中文以三點總結以下選取文字的重點：',
};

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'ANALYZE_TEXT') {
    handleAnalyzeText(message.payload)
      .then((result) => sendResponse({ success: true, data: result }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // async response
  }

  if (message.type === 'SAVE_HIGHLIGHT') {
    handleSaveHighlight(message.payload)
      .then(() => sendResponse({ success: true }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (message.type === 'GET_HIGHLIGHTS') {
    chrome.storage.local.get(['highlights'], (res) => {
      sendResponse({ success: true, data: res.highlights || [] });
    });
    return true;
  }
});

async function handleAnalyzeText({ text, action }) {
  const settings = await getSettings();

  // Offline / Mock fallback for classroom demonstrations
  if (settings.provider === 'mock' || !settings.apiKey) {
    await new Promise((r) => setTimeout(r, 600)); // simulate latency
    if (action === 'translate') {
      return `【AI 繁體中文翻譯】\n"${text}"\n→ 譯文：「這是一段經過安全 Service Worker 代理所生成的翻譯內容。」`;
    }
    return `【AI 智慧重點摘要】\n1. 核心論點：${text.slice(0, 40)}...\n2. 安全架構：本請求完全由 Service Worker 代理，網頁 JS 無法攔截 API 金鑰。\n3. 建議行動：可點擊儲存按鈕將此段筆記記錄至本機擴充庫。`;
  }

  // Real LLM API call if key configured
  const prompt = `${settings.customPrompt}\n\n${text}`;
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${settings.apiKey}`,
    },
    body: JSON.stringify({
      model: 'gpt-4o-mini',
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.3,
    }),
  });

  if (!res.ok) {
    throw new Error(`API 請求失敗: ${res.statusText}`);
  }

  const data = await res.json();
  return data.choices[0].message.content;
}

async function handleSaveHighlight(highlight) {
  return new Promise((resolve) => {
    chrome.storage.local.get(['highlights'], (res) => {
      const list = res.highlights || [];
      const updated = [
        {
          id: 'hl_' + Date.now(),
          text: highlight.text,
          summary: highlight.summary,
          url: highlight.url,
          title: highlight.title,
          createdAt: new Date().toISOString(),
        },
        ...list,
      ];
      chrome.storage.local.set({ highlights: updated }, resolve);
    });
  });
}

function getSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(DEFAULT_SETTINGS, (items) => {
      resolve(items);
    });
  });
}
