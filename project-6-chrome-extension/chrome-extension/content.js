/**
 * Content Script (實習生)：
 * 運行於不受信任的網頁環境。
 * 職責：監聽使用者選字、顯示浮動選單、將文字透過 sendMessage 傳給 Background。
 * 絕不儲存、存取或包含任何 API 金鑰。
 */

let activeToolbar = null;
let activeBubble = null;

document.addEventListener('mouseup', (e) => {
  // Ignore clicks inside our own popup/toolbar
  if (e.target.closest('.highlight-ai-toolbar') || e.target.closest('.highlight-ai-bubble')) {
    return;
  }

  const selection = window.getSelection();
  const text = selection ? selection.toString().trim() : '';

  if (text.length >= 3) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    showToolbar(rect, text);
  } else {
    removeToolbar();
  }
});

function showToolbar(rect, text) {
  removeToolbar();

  const toolbar = document.createElement('div');
  toolbar.className = 'highlight-ai-toolbar';
  toolbar.style.top = `${window.scrollY + rect.top - 42}px`;
  toolbar.style.left = `${window.scrollX + rect.left}px`;

  toolbar.innerHTML = `
    <button class="highlight-ai-btn" id="hl-btn-summary">✨ AI 摘要</button>
    <button class="highlight-ai-btn" id="hl-btn-translate">🌐 翻譯</button>
  `;

  document.body.appendChild(toolbar);
  activeToolbar = toolbar;

  toolbar.querySelector('#hl-btn-summary').addEventListener('click', () => {
    executeAction(text, 'summary', rect);
  });

  toolbar.querySelector('#hl-btn-translate').addEventListener('click', () => {
    executeAction(text, 'translate', rect);
  });
}

function executeAction(text, action, rect) {
  removeToolbar();
  showBubble(rect, '⏳ 總管正在安全處理中...');

  chrome.runtime.sendMessage(
    {
      type: 'ANALYZE_TEXT',
      payload: { text, action },
    },
    (res) => {
      if (res && res.success) {
        showBubble(rect, res.data, text);
      } else {
        showBubble(rect, `❌ 處理失敗: ${res ? res.error : '未知錯誤'}`);
      }
    }
  );
}

function showBubble(rect, content, originalText = null) {
  removeBubble();

  const bubble = document.createElement('div');
  bubble.className = 'highlight-ai-bubble';
  bubble.style.top = `${window.scrollY + rect.bottom + 8}px`;
  bubble.style.left = `${window.scrollX + rect.left}px`;

  bubble.innerHTML = `
    <div class="highlight-ai-bubble-header">
      <span>⚡ Highlight AI</span>
      <button class="highlight-ai-bubble-close" id="hl-bubble-close">×</button>
    </div>
    <div style="white-space: pre-wrap; margin-bottom: 10px;">${content}</div>
    ${originalText ? '<button class="highlight-ai-btn" id="hl-btn-save" style="width: 100%; justify-content: center;">💾 儲存筆記</button>' : ''}
  `;

  document.body.appendChild(bubble);
  activeBubble = bubble;

  bubble.querySelector('#hl-bubble-close').addEventListener('click', removeBubble);

  if (originalText) {
    bubble.querySelector('#hl-btn-save').addEventListener('click', () => {
      chrome.runtime.sendMessage({
        type: 'SAVE_HIGHLIGHT',
        payload: {
          text: originalText,
          summary: content,
          url: window.location.href,
          title: document.title,
        },
      }, () => {
        const btn = bubble.querySelector('#hl-btn-save');
        btn.textContent = '✓ 已儲存至擴充清單！';
        btn.style.backgroundColor = '#10b981';
      });
    });
  }
}

function removeToolbar() {
  if (activeToolbar) {
    activeToolbar.remove();
    activeToolbar = null;
  }
}

function removeBubble() {
  if (activeBubble) {
    activeBubble.remove();
    activeBubble = null;
  }
}
