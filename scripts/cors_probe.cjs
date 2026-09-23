const http = require('http');
const WebSocket = require('ws');

function cdpConnect(url) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(url);
    ws.on('open', () => res(ws));
    ws.on('error', rej);
  });
}

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

    // 检查 token
    const token = await ev("localStorage.getItem('agent_platform_token')");
    console.log('HAS_TOKEN:', token ? 'yes' : 'no');

    // 测试跨域 POST -> register 所触发的 CORS preflight
    const corsTest = await ev("fetch('http://localhost:8080/api/v1/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'xx@xx.com',username:'uu',password:'pp'})}).then(r=>({ok:r.ok,status:r.status})).catch(e=>'NET:'+e.message)");
    console.log('CORS_REGISTER:', JSON.stringify(corsTest));

    // 测试登录
    const loginTest = await ev("fetch('http://localhost:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'test@example.com',password:'password123'})}).then(r=>({ok:r.ok,status:r.status})).catch(e=>'NET:'+e.message)");
    console.log('CORS_LOGIN:', JSON.stringify(loginTest));

    ws.close();
    process.exit(0);
  });
}).on('error', (e) => { console.error('http err', e); process.exit(1); });