// CDP：打开真实 agent 配置页，抓 console，发送消息，定位 DebugPanel 走 mock 的真实异常
const http = require('http');
const WebSocket = require('ws');
const CDP_PORT = 9222;
const AGENT_ID = 'ee5a8d9a-a525-4db8-8f65-46da5027ceac'; // test 用户 LegalRegulatoryDashboard_1
const TARGET = `http://localhost:5175/#/agents/${AGENT_ID}`;

function getWsUrl(){return new Promise((res,rej)=>{http.get(`http://localhost:${CDP_PORT}/json/version`,(r)=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>res(JSON.parse(d).webSocketDebuggerUrl))}).on('error',rej);});}
function createPage(){return new Promise((res,rej)=>{const q=http.request({method:'PUT',host:'localhost',port:CDP_PORT,path:'/json/new?'+encodeURIComponent(TARGET)},(r)=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>res(JSON.parse(d)))});q.on('error',rej);q.end();});}
function connect(u){return new Promise((res,rej)=>{const w=new WebSocket(u);w.on('open',()=>res(w));w.on('error',rej);});}
class CDP{constructor(ws){this.ws=ws;this.id=0;this.p=new Map();ws.on('message',d=>{const m=JSON.parse(d.toString());if(m.id&&this.p.has(m.id)){this.p.get(m.id)(m);this.p.delete(m.id);}});}send(method,params={}){const id=++this.id;return new Promise(res=>{this.p.set(id,res);this.ws.send(JSON.stringify({id,method,params}));});}async ev(expr){const r=await this.send('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true});if(r.result?.exceptionDetails)return 'EXC:'+(r.result.exceptionDetails.exception?.description||'').slice(0,300);return r.result?.result?.value;}}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function main(){
  const wsUrl=await getWsUrl(); const page=await createPage(); const ws=await connect(page.webSocketDebuggerUrl);
  const cdp=new CDP(ws);
  await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
  const logs=[];
  ws.on('message',d=>{const m=JSON.parse(d.toString());if(m.method==='Runtime.consoleAPICalled'){const t=m.params.args.map(a=>a.value||a.description||'').join(' ');logs.push('[console] '+t);}if(m.method==='Runtime.exceptionThrown'){logs.push('[EXC] '+(m.params.exceptionDetails.exception?.description||'').slice(0,300));}});
  await sleep(1500);

  // 先通过 fetch 在该页面上下文拿到 token 并注入 localStorage，使 store 能加载真实 agents
  const loginOut=await cdp.ev(`(async()=>{
    const resp=await fetch('http://localhost:8080/api/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'test@example.com',password:'password123'})});
    if(!resp.ok) return 'login-fail:'+resp.status;
    const d=await resp.json();
    localStorage.setItem('agent_platform_token', d.access_token);
    return 'token-set';
  })()`);
  console.log('注入 token:', loginOut);
  // 跳转到目标配置页
  await cdp.ev(`location.hash='#/agents/${AGENT_ID}'; 'nav'`);
  await sleep(5000);

  const hasPanel=await cdp.ev(`document.body.innerText.includes('对话调试')`);
  console.log('进入 DebugPanel 配置页:', hasPanel?'YES':'NO');
  const bodyText=await cdp.ev(`document.body.innerText`);
  console.log('页面含 "Agent 不存在":', (bodyText||'').includes('Agent 不存在')?'YES':'NO');

  // 输入并发送一条非模板消息
  await cdp.ev(`(()=>{
    const inp=document.querySelector('input[placeholder*="输入消息"]'); if(!inp) return 'no-inp';
    const setter=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
    setter.call(inp,'你好，介绍一下你自己'); inp.dispatchEvent(new Event('input',{bubbles:true}));
    return 'typed';
  })()`);
  await sleep(300);
  const sent=await cdp.ev(`(()=>{const b=Array.from(document.querySelectorAll('button')).find(x=>x.innerText==='发送');if(b){b.click();return true}return false})()`);
  console.log('发送:', sent?'YES':'NO');
  await sleep(10000);

  const text=await cdp.ev('document.body.innerText');
  const isMock=(text||'').includes('真实环境下将由后端 LangGraph Agent');
  console.log('\n=== 页面含 mock 文案:', isMock?'是(走mock)':'否');
  console.log('\n=== CONSOLE (last 20) ===');
  (logs||[]).slice(-20).forEach(l=>console.log(l));
  ws.close(); process.exit(0);
}
main().catch(e=>{console.error('SCRIPT ERR',e);process.exit(1);});