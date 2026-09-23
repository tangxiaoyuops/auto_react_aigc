// CDP 验证：对话页 SSE 链路（发送消息 → 后端 LangGraph → SSE 渲染 trace）
const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');

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

function createPage(url) {
  return new Promise((resolve, reject) => {
    const req = http.request({ method: 'PUT', host: 'localhost', port: CDP_PORT, path: '/json/new?' + encodeURIComponent(url) }, (res) => {
      let d = '';
      res.on('data', (c) => (d += c));
      res.on('end', () => resolve(JSON.parse(d)));
    });
    req.on('error', reject);
    req.end();
  });
}

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.pending = new Map();
    ws.on('message', (d) => { const m = JSON.parse(d.toString()); if (m.id && this.pending.has(m.id)) { this.pending.get(m.id)(m); this.pending.delete(m.id); } });
  }
  send(method, params = {}) { const id = ++this.id; return new Promise((res) => { this.pending.set(id, res); this.ws.send(JSON.stringify({ id, method, params })); }); }
  async evalExpr(expr) { const r = await this.send('Runtime.evaluate', { expression: expr, returnByValue: true }); return r.result?.result?.value; }
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function main() {
  const wsUrl = await getWsUrl();
  const page = await createPage('http://localhost:5173/#/chat');
  const ws = await new Promise((res, rej) => { const w = new WebSocket(page.webSocketDebuggerUrl); w.on('open', () => res(w)); w.on('error', rej); });
  const cdp = new CDP(ws);
  await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
  await sleep(4000);

  // 找 Agent 列表里第一个，点击它选择（若有）
  // 直接聚焦输入框并输入，触发发送
  const inputSet = await cdp.evalExpr(`
    (() => {
      const inp = document.querySelector('input[placeholder*="输入消息"]');
      if (!inp) return false;
      // 使用原生 setter 触发 React onChange
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(inp, '帮我分析一下最近的销售数据');
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    })()
  `);
  console.log('inputSet:', inputSet);

  await sleep(500);
  // 提交表单（回车）
  await cdp.evalExpr(`
    (() => {
      const inp = document.querySelector('input[placeholder*="输入消息"]');
      if (!inp) return;
      inp.form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
      return true;
    })()
  `);

  // 等待 SSE 流式回复
  await sleep(7000);
  const text = await cdp.evalExpr('document.body.innerText');
  console.log('===== CHAT TEXT (截取) =====');
  console.log(text.slice(0, 1200));

  const hasTrace = text.includes('正在思考') || text.includes('THOUGHT') || text.includes('调用') || text.includes('完成') || text.includes('销售数据');
  console.log('===== VERDICT =====');
  console.log('对话链路触发(含执行trace):', hasTrace ? 'YES' : 'CHECK');

  const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/projects/react_demo/screenshots/p2-chat.png', Buffer.from(shot.result.data, 'base64'));
  console.log('screenshot saved');
  ws.close();
  process.exit(0);
}
main().catch((e) => { console.error(e); process.exit(1); });