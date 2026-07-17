const API_BASE = 'http://localhost:8000';

const loadBtn = document.getElementById('loadBtn');
const output = document.getElementById('output');

loadBtn.addEventListener('click', async () => {
  loadBtn.disabled = true;
  output.textContent = '加载中...';

  try {
    const res = await fetch(`${API_BASE}/api/items`);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();
    output.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    output.textContent = [
      '加载失败，请检查：',
      '1. 后端是否已启动（uvicorn backend.main:app --port 8000）',
      '2. 浏览器控制台(F12)是否有 CORS 或网络错误',
      '',
      `错误: ${error.message}`,
    ].join('\n');
  } finally {
    loadBtn.disabled = false;
  }
});
