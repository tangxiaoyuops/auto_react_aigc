// CDP 验证：侧边栏「工具」管理入口存在且可点击进入工具管理 tab
const http = require('http');
const WebSocket = require('ws');

const CDP_PORT = 9222;
const START = 'http://localhost:5175/#/';

function getWsUrl() {
  return new Promise((resolve, reject) => {
    http.get(`http://localhost:${CDP_PORT}/json/version`, (res) => {
      let d = '';
      res.on('data', (c) => (d += c));
      res.on('end', () => resolve(JSON.parse(d).webSocketDebuggerUrl));
    }).on('error', reject);
  });
}

function createPage() {
  return new Promise((resolve, reject) => {
    const req = http.request({
      method: 'PUT',
      host: 'localhost',
      port: CDP_PORT,
      path: '/json/new?' + encodeURIComponent(START),
    }, (res) => {
      let d = '';
      res.on('data', (c) => (d += c));
      res.on('end', () => resolve(JSON.parse(d)));
    });
    req.on('error', reject);
    req.end();
  });
}

function connect(url) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(url);
    ws.on('open', () => resolve(ws));
    ws.on('error', reject);
  });
}

class CDP {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.on('message', (data) => {
      const msg = JSON.parse(data.toString());
      if (msg.id && this.pending.has(msg.id)) {
        this.pending.get(msg.id)(msg);
        this.pending.delete(msg.id);
      }
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve) => {
      this.pending.set(id, resolve);
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evalExpr(expr) {
    const r = await this.send('Runtime.evaluate', { expression: expr, returnByValue: true });
    return r.result?.result?.value;
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const wsUrl = await getWsUrl();
  const page = await createPage();
  const ws = await connect(page.webSocketDebuggerUrl);
  const cdp = new CDP(ws);

  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');
  await sleep(4000);

  // 1. 首页侧边栏应出现「工具」菜单项
  const hasMenu = await cdp.evalExpr(
    `[...document.querySelectorAll('nav a')].map(a => a.textContent.trim()).includes('工具')`
  );
  console.log('侧边栏有「工具」菜单项:', hasMenu ? 'YES' : 'NO');

  // 2. 点击「工具」菜单项（用 NavLink 文本匹配）
  const clicked = await cdp.evalExpr(
    `(() => { const a = [...document.querySelectorAll('nav a')].find(x => x.textContent.trim() === '工具'); if (!a) return false; a.click(); return true; })()`
  );
  console.log('点击「工具」:', clicked ? 'YES' : 'NO');
  await sleep(2500);

  // 3. 检查当前 hash 和页面渲染
  const hash = await cdp.evalExpr('location.hash');
  const text = await cdp.evalExpr('document.body.innerText');
  console.log('当前 URL hash:', hash);
  const hasToolTitle = (text || '').includes('新建工具');
  const hasCalculator = (text || '').includes('Calculator');
  const hasWebSearch = (text || '').includes('Web Search');
  console.log('渲染出「新建工具」按钮:', hasToolTitle ? 'YES' : 'NO');
  console.log('渲染出 Calculator:', hasCalculator ? 'YES' : 'NO');
  console.log('渲染出 Web Search:', hasWebSearch ? 'YES' : 'NO');

  // 截图
  const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
  require('fs').writeFileSync('D:/projects/react_demo/auto_react_aigc/screenshots/m4-tool-menu-entry.png', Buffer.from(shot.result.data, 'base64'));
  console.log('screenshot saved: screenshots/m4-tool-menu-entry.png');

  ws.close();
  const pass = hasMenu && clicked && hash.includes('resources') && hash.includes('tab=tool') && hasToolTitle && hasCalculator && hasWebSearch;
  console.log('\n===== VERDICT =====');
  console.log('工具管理入口完整可用:', pass ? 'YES' : 'NO');
  process.exit(pass ? 0 : 1);
}

main().catch((e) => { console.error(e); process.exit(1); });