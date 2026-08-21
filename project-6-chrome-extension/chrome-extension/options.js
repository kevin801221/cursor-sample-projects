document.addEventListener('DOMContentLoaded', () => {
  if (typeof chrome !== 'undefined' && chrome.storage) {
    chrome.storage.sync.get(['apiKey', 'provider', 'customPrompt'], (res) => {
      if (res.apiKey) document.getElementById('apiKey').value = res.apiKey;
      if (res.provider) document.getElementById('provider').value = res.provider;
      if (res.customPrompt) document.getElementById('customPrompt').value = res.customPrompt;
    });

    document.getElementById('settingsForm').addEventListener('submit', (e) => {
      e.preventDefault();
      const apiKey = document.getElementById('apiKey').value;
      const provider = document.getElementById('provider').value;
      const customPrompt = document.getElementById('customPrompt').value;

      chrome.storage.sync.set({ apiKey, provider, customPrompt }, () => {
        const alertBox = document.getElementById('saveAlert');
        alertBox.style.display = 'block';
        setTimeout(() => (alertBox.style.display = 'none'), 3000);
      });
    });
  }
});
