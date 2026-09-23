// CDP 验证：前端 Agent 列表是否展示后端真实数据
const http = require('http');
const WebSocket = require('ws');

const CDP_PORT = 9222;

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
      path: '/json/new?' + encodeURIComponent('http://localhost:5173/#/agents'),
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
  await sleep(4500); // 等前端 ensureAuth + fetchAgents 完成

  // 读取页面文本
  const text = await cdp.evalExpr('document.body.innerText');
  console.log('===== PAGE TEXT =====');
  console.log(text);
  const hasBackendAgent = text.includes('LegalRegulatoryDashboard_1') || text.includes('客服助手');
  console.log('\n===== VERDICT =====');
  console.log('展示后端 Agent 数据:', hasBackendAgent ? 'YES' : 'NO');

  // 捕获截图
  const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
  require('fs').writeFileSync('D:/projects/react_demo/screenshots/p2-agentlist.png', Buffer.from(shot.result.data, 'base64'));
  console.log('screenshot saved');

  ws.close();
  process.exit(hasBackendAgent ? 0 : 1);
}

main().catch((e) => { console.error(e); process.exit(1); });