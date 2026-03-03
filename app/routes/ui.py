from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Colosseum MVP</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}
h1{text-align:center;margin-bottom:20px;color:#38bdf8}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:1100px;margin:0 auto}
.card{background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155}
.card h2{color:#38bdf8;margin-bottom:12px;font-size:1.1rem}
label{display:block;font-size:.85rem;margin-top:8px;color:#94a3b8}
input,select{width:100%;padding:6px 8px;margin-top:2px;border-radius:6px;border:1px solid #475569;background:#0f172a;color:#e2e8f0}
button{margin-top:10px;padding:8px 16px;border:none;border-radius:6px;cursor:pointer;font-weight:600;background:#38bdf8;color:#0f172a}
button:hover{background:#7dd3fc}
button.demo{background:#22c55e;color:#fff;font-size:1rem;width:100%}
#log{background:#020617;border:1px solid #334155;border-radius:8px;padding:10px;margin-top:12px;height:260px;overflow-y:auto;font-family:monospace;font-size:.82rem;white-space:pre-wrap}
.ok{color:#4ade80}.err{color:#f87171}.info{color:#38bdf8}
#leaderboard{margin-top:8px}
#leaderboard table{width:100%;border-collapse:collapse;font-size:.85rem}
#leaderboard th,#leaderboard td{padding:4px 6px;border-bottom:1px solid #334155;text-align:left}
#leaderboard th{color:#38bdf8}
</style></head><body>
<h1>⚔️ Colosseum MVP</h1>
<div class="grid">

<div class="card"><h2>🏟️ Tournament</h2>
<label>Name<input id="tName" value="Demo Tournament"></label>
<button onclick="createTournament()">Create Tournament</button>
<label>Tournament ID<input id="tId" readonly></label>
<button onclick="setStatus('running')">▶ Set Running</button>
<button onclick="setStatus('finished')">⏹ Set Finished</button>
</div>

<div class="card"><h2>🤖 Agent</h2>
<label>Agent ID<input id="aId" value="agent-alpha"></label>
<label>Name<input id="aName" value="Alpha Bot"></label>
<button onclick="registerAgent()">Register Agent</button>
<button onclick="connectAgent()">Connect Agent</button>
<button onclick="heartbeat()">💓 Heartbeat</button>
</div>

<div class="card"><h2>📡 Signal</h2>
<label>Symbol<select id="sSym"><option>BTCUSDT</option><option>ETHUSDT</option><option>SOLUSDT</option></select></label>
<label>Side<select id="sSide"><option>buy</option><option>sell</option></select></label>
<label>Qty<input id="sQty" type="number" value="0.1" step="0.01"></label>
<button onclick="submitSignal()">Submit Signal</button>
</div>

<div class="card"><h2>📊 Monitoring</h2>
<button onclick="fetchLeaderboard()">Refresh Leaderboard</button>
<button onclick="fetchEvents()">Refresh Events</button>
<div id="leaderboard"></div>
</div>

</div>

<div style="max-width:1100px;margin:16px auto">
<button class="demo" onclick="quickStart()">🚀 Quick Start Demo</button>
<div id="log"></div>
</div>

<script>
const KEY='dev-gateway-key';
const H={'Content-Type':'application/json','x-api-key':KEY};
const log=document.getElementById('log');
function L(msg,cls='info'){const d=document.createElement('div');d.className=cls;d.textContent=new Date().toLocaleTimeString()+' '+msg;log.prepend(d)}
function nonce(){return crypto.randomUUID()}
function ts(){return Date.now()/1000}

async function api(method,path,body){
  try{
    const r=await fetch(path,{method,headers:H,body:body?JSON.stringify(body):undefined});
    const j=await r.json();
    if(!r.ok){L('ERROR '+r.status+': '+(j.detail||JSON.stringify(j)),'err');return null}
    L(method+' '+path+' → OK','ok');
    return j;
  }catch(e){L('FETCH ERROR: '+e,'err');return null}
}

async function createTournament(){
  const r=await api('POST','/tournaments',{name:document.getElementById('tName').value});
  if(r)document.getElementById('tId').value=r.id;
}
function tid(){return document.getElementById('tId').value}
function aid(){return document.getElementById('aId').value}

async function registerAgent(){
  await api('POST','/tournaments/'+tid()+'/register-agent',{agentId:aid(),name:document.getElementById('aName').value});
}
async function setStatus(s){await api('POST','/tournaments/'+tid()+'/status',{status:s})}
async function connectAgent(){
  await api('POST','/gateway/connect-agent',{agentId:aid(),tournamentId:tid(),timestamp:ts(),nonce:nonce()});
}
async function heartbeat(){
  await api('POST','/gateway/heartbeat',{agentId:aid(),tournamentId:tid(),timestamp:ts(),nonce:nonce()});
}
async function submitSignal(){
  const r=await api('POST','/gateway/submit-signal',{
    agentId:aid(),tournamentId:tid(),
    symbol:document.getElementById('sSym').value,
    side:document.getElementById('sSide').value,
    qty:parseFloat(document.getElementById('sQty').value),
    timestamp:ts(),nonce:nonce()
  });
  if(r)fetchLeaderboard();
}
async function fetchLeaderboard(){
  const r=await api('GET','/tournaments/'+tid()+'/leaderboard');
  if(!r)return;
  let h='<table><tr><th>#</th><th>Agent</th><th>Balance</th><th>PnL</th><th>Trades</th></tr>';
  r.forEach((a,i)=>{h+='<tr><td>'+(i+1)+'</td><td>'+a.name+'</td><td>'+a.cash_balance.toFixed(2)+'</td><td>'+a.totalPnl.toFixed(2)+'</td><td>'+a.trades_count+'</td></tr>'});
  h+='</table>';
  document.getElementById('leaderboard').innerHTML=h;
}
async function fetchEvents(){
  const r=await api('GET','/tournaments/'+tid()+'/events');
  if(r)r.slice(-10).reverse().forEach(e=>L(e.type+' | '+e.agentId+' | '+JSON.stringify(e.detail),'info'));
}
async function quickStart(){
  L('=== Quick Start Demo ===','info');
  const t=await api('POST','/tournaments',{name:'Demo Tournament'});
  if(!t)return;
  document.getElementById('tId').value=t.id;
  await api('POST','/tournaments/'+t.id+'/register-agent',{agentId:'agent-alpha',name:'Alpha Bot'});
  await api('POST','/tournaments/'+t.id+'/status',{status:'running'});
  await api('POST','/gateway/connect-agent',{agentId:'agent-alpha',tournamentId:t.id,timestamp:ts(),nonce:nonce()});
  await api('POST','/gateway/heartbeat',{agentId:'agent-alpha',tournamentId:t.id,timestamp:ts(),nonce:nonce()});
  L('Demo ready! Submit signals now.','ok');
}
</script></body></html>"""


@router.get("/", response_class=HTMLResponse)
def index():
    return HTML
