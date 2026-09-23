const http = require('http');
const WebSocket = require('ws');
function cdpConnect(url) { return new Promise((res, rej) => { const ws = new WebSocket(url); ws.on('open', () => res(ws)); ws.on('error', rej); }); }
http.get('http://localhost:9222/json', (r) => {
  let d = ''; r.on('data', (c) => (d += c));
  r.on('end', async () => {
    const pages = JSON.parse(d).filter((p) => p.type === 'page' && (p.url.includes('/chat') || p.url.includes('/agents')));
    const ws = await cdpConnect(pages[0].webSocketDebuggerUrl);
    let id = 0; const pend = new Map();
    ws.on('message', (m) => { const x = JSON.parse(m.toString()); if (x.id && pend.has(x.id)) { pend.get(x.id)(x); pend.delete(x.id); } });
    const send = (method, params = {}) => new Promise((res) => { const i = ++id; pend.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
    const ev = async (e) => { const r = await send('Runtime.evaluate', { expression: e, returnByValue: true, awaitPromise: true }); return r.result && r.result.result ? r.result.result.value : null; };
    const keys = await ev("(()=>{const o={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);o[k]=localStorage.getItem(k)}return o})()");
    console.log('LOCALSTORAGE:', JSON.stringify(keys, null, 2));
    ws.close(); process.exit(0);
  });
}).on('error', (e) => { console.error('err', e); process.exit(1); });