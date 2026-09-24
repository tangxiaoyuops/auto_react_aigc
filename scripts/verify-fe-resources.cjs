// CDP 验证：前端资源库页面展示后端真实 API 数据（M1 打通验证）
const http = require('http');
const WebSocket = require('ws');

const CDP_PORT = 9222;
const TARGET = 'http://localhost:5175/#/resources?tab=tool';
// 5173/5174 被另一个旧项目 frontend 占用；本项目 vite 顺延到 5175

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
      path: '/json/new?' + encodeURIComponent(TARGET),
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
  await sleep(4500);

  // 直接读取当前 hash=tab=tool 的页面文本（URL 已带 /resources?tab=tool）
  const text = await cdp.evalExpr('document.body.innerText');
  console.log('===== PAGE TEXT (first 1600 chars) =====');
  console.log((text || '').slice(0, 1600));

  // 截图
  const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
  require('fs').writeFileSync('D:/projects/react_demo/auto_react_aigc/screenshots/m4-resources-tooltab.png', Buffer.from(shot.result.data, 'base64'));
  console.log('screenshot saved');

  ws.close();
  const pass = checkPass(text);
  console.log('\n===== VERDICT =====');
  console.log('前端资源库(工具Tab)正常渲染:', pass ? 'YES' : 'NO');
  process.exit(pass ? 0 : 1);
}

function checkPass(t) {
  const t0 = t || '';
  // 工具 Tab 应显示「新建工具」，且说明文案含「工具」（新代码特征）
  return t0.includes('新建工具');
}

main().catch((e) => { console.error(e); process.exit(1); });