// CDP 验证：DebugPanel 清空后发送「总结一下」，确认走真实后端(非 mock)
const http = require('http');
const WebSocket = require('ws');
const CDP_PORT = 9222;
// 用真实 DB 中 LegalRegulatoryDashboard_1 的 id 进入其配置页(含 DebugPanel)
const AGENT_ID = 'ee5a8d9a-a525-4db8-8f65-46da5027ceac';
const TARGET = `http://localhost:5175/#/agents/${AGENT_ID}`;

function getWsUrl() {
  return new Promise((resolve, reject) => {
    http.get(`http://localhost:${CDP_PORT}/json/version`, (res) => {
      let d = ''; res.on('data', (c) => (d += c)); res.on('end', () => resolve(JSON.parse(d).webSocketDebuggerUrl));
    }).on('error', reject);
  });
}
function createPage() {
  return new Promise((resolve, reject) => {
    const req = http.request({ method: 'PUT', host: 'localhost', port: CDP_PORT, path: '/json/new?' + encodeURIComponent(TARGET) },
      (res) => { let d=''; res.on('data',(c)=>(d+=c)); res.on('end', () => resolve(JSON.parse(d))); });
    req.on('error', reject); req.end();
  });
}
function connect(url) { return new Promise((res, rej) => { const ws = new WebSocket(url); ws.on('open',()=>res(ws)); ws.on('error',rej); }); }
class CDP {
  constructor(ws){ this.ws=ws; this.id=0; this.pending=new Map(); ws.on('message',(d)=>{ const m=JSON.parse(d.toString()); if(m.id&&this.pending.has(m.id)){this.pending.get(m.id)(m);this.pending.delete(m.id);} }); }
  send(method,params={}){ const id=++this.id; return new Promise((resolve)=>{ this.pending.set(id,resolve); this.ws.send(JSON.stringify({id,method,params})); }); }
  async ev(expr){ const r=await this.send('Runtime.evaluate',{expression:expr, returnByValue:true}); return r.result?.result?.value; }
}
const sleep = (ms) => new Promise(r=>setTimeout(r,ms));

async function main() {
  const wsUrl=await getWsUrl(); const page=await createPage(); const ws=await connect(page.webSocketDebuggerUrl);
  const cdp=new CDP(ws);
  await cdp.send('Page.enable'); await cdp.send('Runtime.enable'); await sleep(3500);

  // 点击「清空」
  const clr=await cdp.ev(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText==='清空'); if(b){b.click();return true}return false})()`);
  console.log('清空:', clr?'YES':'NO'); await sleep(700);

  // 找到一个输入框 typing 并回车发送
  const sent=await cdp.ev(`(()=>{
    const inp=document.querySelector('input[placeholder*="输入消息"]');
    if(!inp) return false;
    const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    setter.call(inp,'总结一下'); inp.dispatchEvent(new Event('input',{bubbles:true}));
    setTimeout(()=>{ const btn=Array.from(document.querySelectorAll('button')).find(x=>x.innerText==='发送'); if(btn) btn.click(); },200);
    return true;
  })()`);
  console.log('发送「总结一下」:', sent?' 触发':' NO'); await sleep(9000);

  const text=await cdp.ev('document.body.innerText');
  console.log('\n===== PAGE TEXT (tail 700) =====');
  console.log((text||'').slice(-700));

  const shot=await cdp.send('Page.captureScreenshot',{format:'png'});
  require('fs').writeFileSync('D:/projects/react_demo/auto_react_aigc/screenshots/m4-debug-realtime.png',Buffer.from(shot.result.data,'base64'));
  ws.close();

  // 判断：真实后端会返回较长任务理解(非 mock 的 mockReply 摘要) 且带多步真实执行
  const t0=text||'';
  const isMock = t0.includes('我帮您完成了内容摘要') || t0.includes('我已完成了任务理解');
  console.log('\n===== VERDICT =====');
  console.log('含 mockReply 文案:', isMock?'YES(仍走mock)':'NO');
  ws.close();
  require('fs').writeFileSync('D:/projects/react_demo/auto_react_aigc/screenshots/m4-debug-realtime.png',Buffer.from(shot.result.data,'base64'));
  process.exit(isMock?1:0);
}
main().catch(e=>{console.error(e);process.exit(1);});