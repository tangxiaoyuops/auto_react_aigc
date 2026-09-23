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

    // 1. 登录拿 token
    const token = await ev("(async()=>{const r=await fetch('http://localhost:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'test@example.com',password:'password123'})});const j=await r.json();return j.access_token||null})()");
    console.log('TOKEN got:', token ? 'yes' : 'NO');
    if (!token) { ws.close(); process.exit(1); }

    // 2. 写入 token + 清掉旧的 session cache（强制重建会话）
    await ev(`localStorage.setItem('agent_platform_token', '${token}'); localStorage.removeItem('agent_demo_session_id'); true`);

    // 3. 刷新页面，重新 mount -> ensureAuth 读到 token
    await send('Page.reload', { ignoreCache: true });
    await sleep(5000);

    // 4. 输入并发送
    const inp = await ev(`(() => {
      const i = Array.from(document.querySelectorAll('input')).find(x => (x.placeholder||'').includes('消息'));
      if (!i) return 'NO_INPUT';
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(i, '请用简短两句话介绍如何分析销售趋势');
      i.dispatchEvent(new Event('input', { bubbles: true }));
      return 'ok';
    })()`);
    console.log('input:', inp);
    await sleep(400);
    await ev(`(() => { const i = Array.from(document.querySelectorAll('input')).find(x => (x.placeholder||'').includes('消息')); if(!i)return; const f=i.closest('form'); if(f)f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})); })()`);
    console.log('sent, waiting...');
    await sleep(15000);

    const text = await ev('document.body.lastElementChild.textContent');
    const body = await ev('document.body.innerText');
    const hasMock = body.includes('共检索到 1,286') || body.includes('我已开始分析相关数据');
    console.log('===== 尾部文本 =====');
    console.log(body.slice(Math.max(0, body.length - 700)));
    console.log('===== 判断 =====');
    console.log('含前端mock:', hasMock);
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('D:/projects/react_demo/screenshots/realtoken-chat.png', Buffer.from(shot.result.data, 'base64'));
    ws.close(); process.exit(0);
  });
}).on('error', (e) => { console.error('err', e); process.exit(1); });