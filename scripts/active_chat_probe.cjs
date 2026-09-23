const http = require('http');
const WebSocket = require('ws');

function cdpConnect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url);
    ws.on('open', () => res(ws));
    ws.on('error', rej);
  });
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

http.get('http://localhost:9222/json', (r) => {
  let d = '';
  r.on('data', (c) => (d += c));
  r.on('end', async () => {
    const pages = JSON.parse(d).filter((p) => p.type === 'page' && p.url.includes('/chat'));
    if (!pages.length) { console.log('no chat page'); process.exit(1); }
    const ws = await cdpConnect(pages[0].webSocketDebuggerUrl);
    let id = 0; const pend = new Map();
    ws.on('message', (m) => { const x = JSON.parse(m.toString()); if (x.id && pend.has(x.id)) { pend.get(x.id)(x); pend.delete(x.id); } });
    const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async (e) => { const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true }); return r.result && r.result.result ? r.result.result.value : null; };

    await send('Page.enable'); await send('Runtime.enable');

    // 找到输入框并输入（React 需原生 setter）
    const inp = await ev(`(() => {
      const i = Array.from(document.querySelectorAll('input')).find(x => (x.placeholder||'').includes('消息') || (x.placeholder||'').includes('输入'));
      if (!i) return 'NO_INPUT';
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(i, '请用一两句话介绍销售趋势分析方法');
      i.dispatchEvent(new Event('input', { bubbles: true }));
      return i.placeholder;
    })()`);
    console.log('INPUT:', inp);
    await sleep(400);

    // 按回车 或 提交表单
    await ev(`(() => {
      const i = Array.from(document.querySelectorAll('input')).find(x => (x.placeholder||'').includes('消息') || (x.placeholder||'').includes('输入'));
      if (!i) return false;
      const f = i.closest('form');
      if (f) { f.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); return 'form_submitted'; }
      return i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', bubbles: true })) || 'key';
    })()`);
    console.log('sent');

    // 等待 SSE 真实回复（真实 LLM 可能较慢）
    await sleep(12000);
    const text = await ev('document.body.innerText');
    const hasMock = text.includes('我已开始分析相关数据') || text.includes('共检索到 1,286');
    const hasReal = text.includes('销售') || text.includes('时序') || text.includes('环比');
    console.log('===== 结果文本(尾部900字) =====');
    const idx = text.lastIndexOf('销售趋势');
    console.log(text.slice(Math.max(0, text.length - 900)));
    console.log('===== 判断 =====');
    console.log('含前端mock特征(共检索到1,286):', hasMock);
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    require('fs').writeFileSync('D:/projects/react_demo/screenshots/cors-probe.png', Buffer.from(shot.result.data, 'base64'));
    ws.close();
    process.exit(0);
  });
}).on('error', (e) => { console.error(err); process.exit(1); });