const http = require('http');
const WebSocket = require('ws');
const fs = require('fs');
function cdpConnect(url) { return new Promise((res, rej) => { const ws = new WebSocket(url); ws.on('open', () => res(ws)); ws.on('error', rej); }); }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

http.get('http://localhost:9222/json', (r) => {
  let d = ''; r.on('data', (c) => (d += c));
  r.on('end', async () => {
    const page = JSON.parse(d).find((p) => p.type === 'page' && p.url.includes('/chat'));
    if (!page) { console.log('no chat'); process.exit(1); }
    const ws = await cdpConnect(page.webSocketDebuggerUrl);
    let id = 0; const pend = new Map();
    ws.on('message', (m) => { const x = JSON.parse(m.toString()); if (x.id && pend.has(x.id)) { pend.get(x.id)(x); pend.delete(x.id); } });
    const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async (e) => { const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true }); return r.result && r.result.result ? r.result.result.value : null; };
    await send('Page.enable'); await send('Runtime.enable');

    // 1. 强制清空 token + session，模拟"后端恢复但前端无认证"的最坏场景
    await ev("localStorage.removeItem('agent_platform_token'); localStorage.removeItem('agent_demo_session_id'); true");

    // 2. 刷新页面加载修复后的代码（AppLayout 挂载 ensureAuth 会先拿到 token）
    await send('Page.reload', { ignoreCache: true });
    await sleep(6000);
    const hasToken = await ev("!!localStorage.getItem('agent_platform_token')");
    console.log('mount后自动获得token:', hasToken);

    // 3. 发送消息
    await ev(`(() => {
      const i = Array.from(document.querySelectorAll('input')).find(x => (x.placeholder||'').includes('消息'));
      if (!i) return; const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
      setter.call(i, '用短短几句话总结销售趋势分析方法'); i.dispatchEvent(new Event('input',{bubbles:true}));
    })()`);
    await sleep(300);
    await ev(`(() => { const i = Array.from(document.querySelectorAll('input')).find(x => (x.placeholder||'').includes('消息')); if(!i)return; const f=i.closest('form'); if(f)f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})); })()`);
    console.log('sent...'); await sleep(15000);

    const body = await ev('document.body.innerText');
    const hasMock = body.includes('共检索到 1,286') || body.includes('我已开始分析相关数据');
    console.log('===== 尾部 =====');
    console.log(body.slice(Math.max(0, body.length - 600)));
    console.log('===== 判断 =====');
    console.log('含前端mock:', hasMock);
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('D:/projects/react_demo/screenshots/auto-reauth-chat.png', Buffer.from(shot.result.data, 'base64'));
    ws.close(); process.exit(0);
  });
}).on('error', (e) => { console.error('err', e); process.exit(1); });