document.addEventListener('DOMContentLoaded', () => {
  if (typeof chrome !== 'undefined' && chrome.runtime) {
    chrome.runtime.sendMessage({ type: 'GET_HIGHLIGHTS' }, (res) => {
      if (res && res.success) {
        renderList(res.data);
      }
    });

    document.getElementById('optionsBtn').addEventListener('click', () => {
      chrome.runtime.openOptionsPage();
    });
  }
});

function renderList(list) {
  const container = document.getElementById('listContainer');
  const countLabel = document.getElementById('countLabel');
  countLabel.textContent = `${list.length} 則標註`;

  if (list.length === 0) {
    container.innerHTML = '<div style="text-align: center; color: #64748b; font-size: 13px; padding: 20px 0;">尚無儲存的標註筆記</div>';
    return;
  }

  container.innerHTML = list.map((item) => `
    <div class="card">
      <div class="card-text">"${item.text.slice(0, 60)}..."</div>
      <div class="card-summary">${item.summary}</div>
      <div style="font-size: 10px; color: #64748b; margin-top: 6px;">${new Date(item.createdAt).toLocaleString('zh-TW')}</div>
    </div>
  `).join('');
}
