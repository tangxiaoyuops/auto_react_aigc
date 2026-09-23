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
    if (!pages.length) { console.log('no chat'); process.exit(1); }
    const ws = await cdpConnect(pages[0].webSocketDebuggerUrl);
    let id = 0; const pend = new Map();
    ws.on('message', (m) => { const x = JSON.parse(m.toString()); if (x.id && pend.has(x.id)) { pend.get(x.id)(x); pend.delete(x.id); } });
    const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async (e) => { const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true }); return r.result && r.result.result ? r.result.result.value : null; };

    // 简单请求（无自定义头）
    const simple = await ev("fetch('http://localhost:8080/api/v1/health').then(r=>'OK:'+r.status).catch(e=>'CORS:'+e.message)");
    console.log('1 简单GET /health:', simple);

    // 带 Authorization 的 POST（触发预检）
    const g = "fetch('http://localhost:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'test@example.com',password:'password123'})})";
    const login = await ev("(async()=>{const r=await fetch('http://localhost:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'test@example.com',password:'password123'})});return 'OK:'+r.status})()");
    console.log('2 带Content-Type POST /login:', login);

    // 带 Authorization header 的 GET（触发预检）
    const authedGet = await ev("(async()=>{try{const r=await fetch('http://localhost:8080/api/v1/sessions',{headers:{'Authorization':'Bearer x'}});return 'OK:'+r.status}catch(e){return 'CORS:'+e.message}})()");
    console.log('3 带Authorization GET /sessions:', authedGet);

    ws.close(); process.exit(0);
  });
}).on('error', (e) => { console.error('err', e); process.exit(1); });