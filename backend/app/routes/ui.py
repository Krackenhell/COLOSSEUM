from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Colosseum MVP</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;overflow-anchor:none}
h1{text-align:center;margin-bottom:20px;color:#38bdf8}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:1400px;margin:0 auto}
.card{background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155}
.card h2{color:#38bdf8;margin-bottom:12px;font-size:1.1rem}
label{display:block;font-size:.85rem;margin-top:8px;color:#94a3b8}
input,select{width:100%;padding:6px 8px;margin-top:2px;border-radius:6px;border:1px solid #475569;background:#0f172a;color:#e2e8f0}
button{margin-top:10px;padding:8px 16px;border:none;border-radius:6px;cursor:pointer;font-weight:600;background:#38bdf8;color:#0f172a}
button:hover{background:#7dd3fc}
button.demo{background:#22c55e;color:#fff;font-size:1rem;width:100%}
button.small{padding:4px 10px;font-size:.8rem;margin:2px}
button.ai{background:#a855f7;color:#fff}
button.ai:hover{background:#c084fc}
button.danger{background:#ef4444;color:#fff}
button.danger:hover{background:#f87171}
button.replay{background:#f59e0b;color:#000}
button.replay:hover{background:#fbbf24}
#log{background:#020617;border:1px solid #334155;border-radius:8px;padding:10px;margin-top:12px;height:200px;overflow-y:auto;font-family:monospace;font-size:.82rem;white-space:pre-wrap;overflow-anchor:none}
.ok{color:#4ade80}.err{color:#f87171}.info{color:#38bdf8}.warn{color:#fbbf24}
#leaderboard{margin-top:8px}
#leaderboard table{width:100%;border-collapse:collapse;font-size:.82rem}
#leaderboard th,#leaderboard td{padding:4px 6px;border-bottom:1px solid #334155;text-align:left}
#leaderboard th{color:#38bdf8}
#timer-box{background:#020617;border:1px solid #334155;border-radius:8px;padding:10px;margin-top:8px;font-family:monospace;font-size:.9rem}
.status-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.8rem;font-weight:600}
.status-scheduled{background:#eab308;color:#000}.status-running{background:#22c55e;color:#000}.status-finished{background:#ef4444;color:#fff}.status-archived{background:#64748b;color:#fff}
#existing-list{margin-top:8px;max-height:150px;overflow-y:auto}
#existing-list .item{padding:4px 8px;cursor:pointer;border-radius:4px;font-size:.85rem}
#existing-list .item:hover{background:#334155}
#existing-list .item.active{background:#38bdf8;color:#0f172a}
.sep{border-top:1px solid #334155;margin:14px 0}
.key-display{background:#020617;border:1px solid #a855f7;border-radius:8px;padding:8px 12px;font-family:monospace;font-size:.85rem;color:#c084fc;word-break:break-all;margin-top:6px}
.ai-panel{border:1px solid #a855f7;background:linear-gradient(135deg,#1e293b 0%,#1a1035 100%)}
#ai-agent-log{background:#020617;border:1px solid #a855f7;border-radius:8px;padding:10px;margin-top:8px;height:180px;overflow-y:auto;font-family:monospace;font-size:.8rem;white-space:pre-wrap;color:#c084fc;overflow-anchor:none}
.info-box{background:#0c1222;border:1px solid #334155;border-radius:8px;padding:12px;margin-top:8px;font-size:.82rem;line-height:1.5;color:#94a3b8}
.info-box code{background:#1e293b;padding:2px 6px;border-radius:4px;color:#e2e8f0;font-size:.8rem}
.studio-panel{border:1px solid #22c55e;background:linear-gradient(135deg,#1e293b 0%,#0f2918 100%)}
.agent-card{background:#0f172a;border:1px solid #334155;border-radius:10px;padding:14px;margin-top:10px}
.agent-card h3{font-size:1rem;margin-bottom:8px}
.conn-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}
.conn-on{background:#4ade80;box-shadow:0 0 6px #4ade80}.conn-off{background:#ef4444}
.signal-ok{color:#4ade80;font-size:.78rem}.signal-err{color:#f87171;font-size:.78rem}
.pos-row{font-size:.78rem;padding:2px 0;border-bottom:1px solid #1e293b}
.stat{display:inline-block;margin-right:16px;font-size:.82rem}
.stat b{color:#38bdf8}
.chart-box{background:#020617;border:1px solid #334155;border-radius:8px;padding:12px;margin:10px 0}
.key-row{font-size:.8rem;padding:4px 8px;border-bottom:1px solid #1e293b;display:flex;justify-content:space-between;align-items:center}
.key-active{color:#4ade80}.key-expired{color:#ef4444}.key-revoked{color:#94a3b8}
#replay-box{background:#020617;border:1px solid #f59e0b;border-radius:8px;padding:12px;margin-top:10px;max-height:400px;overflow-y:auto;font-family:monospace;font-size:.8rem;display:none}
#debug-box{background:#020617;border:1px solid #ef4444;border-radius:8px;padding:12px;margin-top:10px;max-height:400px;overflow-y:auto;font-size:.82rem;display:none}
</style></head><body>
<h1>&#x2694;&#xFE0F; Colosseum MVP</h1>
<div class="grid">

<!-- TOURNAMENT PANEL -->
<div class="card"><h2>&#x1F3DF;&#xFE0F; Tournament</h2>
<label>Name<input id="tName" value="Demo Tournament"></label>
<label>Start<input id="tStart" type="datetime-local"></label>
<label>End<input id="tEnd" type="datetime-local"></label>
<button onclick="createTournament()">Create</button>
<div class="sep"></div>
<h2>&#x1F4CB; Tournaments</h2>
<button class="small" onclick="loadTournaments()">Refresh</button>
<button class="small" onclick="loadAllTournaments()">All History</button>
<div id="existing-list"></div>
<div class="sep"></div>
<label>Tournament ID<input id="tId" readonly></label>
<div id="timer-box">Select a tournament...</div>
<button onclick="setStatus('running')">&#x25B6; Force Start</button>
<button onclick="setStatus('finished')">&#x23F9; End</button>
</div>

<!-- SIGNAL PANEL -->
<div class="card"><h2>&#x1F4E1; Signal</h2>
<label>Symbol<select id="sSym"><option>BTCUSDT</option><option>ETHUSDT</option><option>AVAXUSDT</option></select></label>
<label>Side<select id="sSide"><option value="buy">buy</option><option value="sell">sell</option></select></label>
<label>Qty<input id="sQty" type="number" value="0.1" step="0.01"></label>
<div class="sep"></div>
<label>Leverage<input id="tLeverage" type="number" value="10" min="1" max="125"></label>
<label>Risk Profile<select id="tRisk"><option value="normal">normal</option><option value="hft">hft</option></select></label>
<button onclick="submitSignal()">Submit Signal</button>
<div class="sep"></div>
<h2>&#x1F916; Agent</h2>
<label>Agent ID<input id="aId" value="agent-alpha"></label>
<label>Agent Name<input id="aName" value="Alpha Bot"></label>
<button onclick="registerAgent()">Register</button>
<button onclick="connectAgent()">Connect</button>
<button onclick="heartbeat()">&#x1F493; Heartbeat</button>
</div>

<!-- AI AGENT PANEL -->
<div class="card ai-panel" style="grid-column:1/-1"><h2>&#x1F9E0; AI Agent</h2>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
<div>
<label>API Key<input id="aiApiKey" placeholder="col_..."></label>
<div style="display:flex;gap:8px;margin-top:8px">
<button class="ai" onclick="registerAIAgent()">&#x1F511; Register AI</button>
<button class="ai" onclick="aiAgentStatus()">&#x1F4CA; Status</button>
</div>
<div id="ai-key-display" style="display:none"></div>
<div class="sep"></div>
<label>Agent ID<input id="aiAgentId" value="my-ai-bot"></label>
<label>Agent Name<input id="aiAgentName" value="My AI Bot"></label>
<div class="sep"></div>
<h2 style="color:#a855f7;font-size:1rem">&#x1F680; Test AI Agent</h2>
<div style="display:flex;gap:8px">
<button class="ai" onclick="startTestAI()">&#x25B6; Start</button>
<button class="danger" onclick="stopTestAI()">&#x23F9; Stop</button>
<button class="small" onclick="refreshTestAILog()">&#x1F504;</button>
</div>
<div id="test-ai-id" style="font-size:.8rem;color:#94a3b8;margin-top:4px"></div>
</div>
<div>
<div id="ai-agent-log">AI agent log...</div>
</div>
</div>
</div>

<!-- MARKET STATUS -->
<div class="card" style="grid-column:1/-1"><h2>&#x1F4B9; Market Status</h2>
<button class="small" onclick="fetchMarketStatus()">Refresh</button>
<div id="market-status" style="font-size:.82rem;margin-top:8px"></div>
</div>

<!-- LEADERBOARD -->
<div class="card" style="grid-column:1/-1"><h2>&#x1F4CA; Leaderboard</h2>
<button onclick="fetchLeaderboard()">Refresh</button>
<button onclick="fetchEvents()">Events</button>
<div id="leaderboard"></div>
</div>

<!-- AGENT STUDIO -->
<div class="card studio-panel" style="grid-column:1/-1"><h2>&#x1F3AC; Agent Studio</h2>
<button onclick="fetchStudio()">&#x1F504; Refresh</button>
<button onclick="fetchEquityChart()">&#x1F4C8; Load Chart</button>
<div class="chart-box"><canvas id="equityChart" height="200"></canvas></div>
<div id="studio-agents"></div>
</div>

<!-- REPLAY & DEBUG -->
<div class="card" style="grid-column:1/-1"><h2>&#x1F3AC; Replay & Debug</h2>
<button class="replay" onclick="fetchReplay()">&#x1F504; Load Replay Timeline</button>
<label>Debug Agent ID<input id="debugAgentId" placeholder="agent-alpha"></label>
<button class="danger" onclick="fetchDebug()">&#x1F50D; Debug: Why Agent Lost</button>
<div id="replay-box"></div>
<div id="debug-box"></div>
</div>

<!-- API KEYS -->
<div class="card" style="grid-column:1/-1"><h2>&#x1F511; API Keys</h2>
<button onclick="fetchKeys()">Refresh Keys</button>
<div id="keys-list"></div>
</div>

</div>

<div style="max-width:1400px;margin:16px auto">
<button class="demo" onclick="quickStart()">&#x1F680; Quick Start Demo</button>
<div id="log"></div>
</div>

<script>
const KEY='dev-gateway-key';
const H={'Content-Type':'application/json','x-api-key':KEY};
const log=document.getElementById('log');

// --- Scroll-safe logging: only auto-scroll if user is already at bottom ---
function isNearBottom(el){return el.scrollHeight-el.scrollTop-el.clientHeight<40}
function scrollToBottom(el){el.scrollTop=el.scrollHeight}

function L(msg,cls='info'){const d=document.createElement('div');d.className=cls;d.textContent=new Date().toLocaleTimeString()+' '+msg;log.prepend(d)}
function nonce(){return crypto.randomUUID()}
function ts(){return Date.now()/1000}
let equityChartInstance=null;

(function(){
  const pad=v=>String(v).padStart(2,'0');
  function localISO(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())+'T'+pad(d.getHours())+':'+pad(d.getMinutes())}
  const now=new Date();
  document.getElementById('tStart').value=localISO(new Date(now.getTime()+10*1000));
  document.getElementById('tEnd').value=localISO(new Date(now.getTime()+24*3600*1000));
})();

async function api(method,path,body){
  try{
    const r=await fetch(path,{method,headers:H,body:body?JSON.stringify(body):undefined});
    const j=await r.json();
    if(!r.ok){L('ERROR '+r.status+': '+(j.detail||JSON.stringify(j)),r.status===429?'warn':'err');return null}
    L(method+' '+path+' -> OK','ok');return j;
  }catch(e){L('FETCH ERROR: '+e,'err');return null}
}

async function loadTournaments(){
  const list=await api('GET','/tournaments');if(!list)return;
  renderTournamentList(list);
}
async function loadAllTournaments(){
  const list=await api('GET','/tournaments/all-history');if(!list)return;
  renderTournamentList(list);
}
function renderTournamentList(list){
  const el=document.getElementById('existing-list');el.innerHTML='';
  list.forEach(t=>{const d=document.createElement('div');d.className='item'+(t.id===tid()?' active':'');
    const eff=t.effectiveStatus||t.status;
    d.innerHTML='<span class="status-badge status-'+eff+'">'+eff+'</span> <b>'+t.name+'</b> ('+t.id+')';
    d.onclick=()=>{document.getElementById('tId').value=t.id;loadTournaments();refreshTimer()};el.appendChild(d)});
}

async function createTournament(){
  const sv=document.getElementById('tStart').value,ev=document.getElementById('tEnd').value;
  const se=sv?new Date(sv).getTime()/1000:(Date.now()/1000+10),ee=ev?new Date(ev).getTime()/1000:(se+86400);
  const r=await api('POST','/tournaments',{name:document.getElementById('tName').value,startAt:se,endAt:ee,
    riskProfile:document.getElementById('tRisk').value,leverage:parseFloat(document.getElementById('tLeverage').value)||10});
  if(r){document.getElementById('tId').value=r.id;L('Tournament: '+r.id+' (previous tournaments auto-archived)','ok');loadTournaments();refreshTimer()}
}
function tid(){return document.getElementById('tId').value}
function aid(){return document.getElementById('aId').value}

async function refreshTimer(){
  if(!tid()){document.getElementById('timer-box').textContent='Select a tournament...';return}
  try{const r=await fetch('/tournaments/'+tid()+'/timer');
  if(r.status===404){
    L('Tournament '+tid()+' no longer active, switching...','warn');
    document.getElementById('timer-box').innerHTML='Tournament ended/archived. Switching...';
    await autoSelectActiveTournament();return}
  if(!r.ok)return;const d=await r.json();
  const box=document.getElementById('timer-box');
  let h='<span class="status-badge status-'+d.effectiveStatus+'">'+d.effectiveStatus.toUpperCase()+'</span> ';
  if(d.effectiveStatus==='scheduled')h+='Starts in: '+fmtSec(d.startsInSec);
  else if(d.effectiveStatus==='running')h+='Remaining: '+fmtSec(d.remainingSec);
  else if(d.effectiveStatus==='finished'||d.effectiveStatus==='archived'){h+='Finished';await autoSelectActiveTournament()}
  else h+='Finished';box.innerHTML=h}catch(e){}
}
async function autoSelectActiveTournament(){
  try{const list=await api('GET','/tournaments');if(!list||list.length===0)return;
  document.getElementById('tId').value=list[0].id;renderTournamentList(list);L('Auto-switched to: '+list[0].name,'info')}catch(e){}
}
function fmtSec(s){return Math.floor(s/3600)+'h '+Math.floor((s%3600)/60)+'m '+Math.floor(s%60)+'s'}
setInterval(refreshTimer,2000);

async function registerAgent(){await api('POST','/tournaments/'+tid()+'/register-agent',{agentId:aid(),name:document.getElementById('aName').value})}
async function setStatus(s){const r=await api('POST','/tournaments/'+tid()+'/status',{status:s});if(r)refreshTimer()}
async function connectAgent(){await api('POST','/gateway/connect-agent',{agentId:aid(),tournamentId:tid(),timestamp:ts(),nonce:nonce()})}
async function heartbeat(){await api('POST','/gateway/heartbeat',{agentId:aid(),tournamentId:tid(),timestamp:ts(),nonce:nonce()})}
async function submitSignal(){
  const r=await api('POST','/gateway/submit-signal',{agentId:aid(),tournamentId:tid(),symbol:document.getElementById('sSym').value,
    side:document.getElementById('sSide').value,qty:parseFloat(document.getElementById('sQty').value),timestamp:ts(),nonce:nonce()});
  if(r){fetchLeaderboard();fetchStudio()}
}
async function fetchLeaderboard(){
  if(!tid())return;
  const r=await api('GET','/tournaments/'+tid()+'/leaderboard');if(!r)return;
  let h='<table><tr><th>#</th><th>Agent</th><th>Equity</th><th>PnL</th><th>Trades</th></tr>';
  r.forEach((a,i)=>{h+='<tr><td>'+(i+1)+'</td><td>'+a.name+'</td><td>'+a.equity.toFixed(2)+'</td><td style="color:'+(a.totalPnl>=0?'#4ade80':'#f87171')+'">'+a.totalPnl.toFixed(2)+'</td><td>'+a.trades_count+'</td></tr>'});
  document.getElementById('leaderboard').innerHTML=h+'</table>';
}
async function fetchEvents(){const r=await api('GET','/tournaments/'+tid()+'/events');if(r)r.slice(-10).reverse().forEach(e=>L(e.type+' | '+e.agentId+' | '+JSON.stringify(e.detail),'info'))}

async function quickStart(){
  L('=== Quick Start Demo ===','info');const now=Date.now()/1000;
  const t=await api('POST','/tournaments',{name:'Futures Demo',startAt:now+2,endAt:now+3600,leverage:10,riskProfile:'normal'});
  if(!t)return;document.getElementById('tId').value=t.id;loadTournaments();
  await api('POST','/tournaments/'+t.id+'/register-agent',{agentId:'agent-alpha',name:'Alpha Bot'});
  await api('POST','/gateway/connect-agent',{agentId:'agent-alpha',tournamentId:t.id,timestamp:ts(),nonce:nonce()});
  L('Waiting for start (2s)...','info');await new Promise(r=>setTimeout(r,2500));refreshTimer();
  await api('POST','/gateway/submit-signal',{agentId:'agent-alpha',tournamentId:t.id,symbol:'BTCUSDT',side:'buy',qty:0.5,timestamp:ts(),nonce:nonce()});
  L('Opened long 0.5 BTC','ok');fetchLeaderboard();fetchStudio();
}

// ======== AI AGENT ========
const aiLog=document.getElementById('ai-agent-log');
function aiL(msg){
  const wasBottom=isNearBottom(aiLog);
  aiLog.innerHTML+=new Date().toLocaleTimeString()+' '+msg+'\n';
  if(wasBottom)scrollToBottom(aiLog);
}
async function registerAIAgent(){
  const id=document.getElementById('aiAgentId').value||'my-ai-bot',nm=document.getElementById('aiAgentName').value||id;
  try{const r=await fetch('/agent-api/v1/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agentId:id,name:nm})});
  const j=await r.json();if(r.ok){document.getElementById('aiApiKey').value=j.api_key;
  document.getElementById('ai-key-display').style.display='block';
  document.getElementById('ai-key-display').innerHTML='<div class="key-display">Key: <b>'+j.api_key+'</b></div>';
  aiL('Registered: '+j.agentId);L('AI registered: '+j.agentId,'ok');fetchKeys()}else{aiL('Error: '+JSON.stringify(j))}}catch(e){aiL('Error: '+e)}
}
async function aiAgentStatus(){
  const key=document.getElementById('aiApiKey').value;if(!key){aiL('Enter key first');return}
  try{const r=await fetch('/agent-api/v1/my/balance',{headers:{'Authorization':'Bearer '+key}});const j=await r.json();
  if(r.ok){Object.entries(j).forEach(([t,b])=>aiL('T:'+t+' cash='+b.cash_balance+' eq='+b.equity+' pnl='+b.realized_pnl))}
  else{aiL('Error: '+JSON.stringify(j))}}catch(e){aiL('Error: '+e)}
}

let testAIAgentId=null,testAIInterval=null;
async function startTestAI(){
  const t=tid();if(!t){aiL('Select tournament first!');return}
  try{const r=await fetch('/test-agent/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tournamentId:t})});
  if(!r.ok){aiL('Error: '+r.status+' '+await r.text());return}const j=await r.json();
  if(j.agentId){testAIAgentId=j.agentId;document.getElementById('test-ai-id').textContent='AI: '+j.agentId;
  aiL('Started: '+j.agentId);L('Test AI started','ok');if(testAIInterval)clearInterval(testAIInterval);
  testAIInterval=setInterval(()=>{refreshTestAILog();fetchStudio()},3000)}else{aiL('Error: '+JSON.stringify(j))}}catch(e){aiL('Error: '+e)}
}
async function stopTestAI(){if(!testAIAgentId){aiL('No AI running');return}
  try{await fetch('/test-agent/stop/'+testAIAgentId,{method:'POST'});aiL('Stopped');if(testAIInterval)clearInterval(testAIInterval)}catch(e){aiL('Error: '+e)}}
async function refreshTestAILog(){if(!testAIAgentId)return;
  try{const r=await fetch('/test-agent/status/'+testAIAgentId);if(!r.ok)return;const j=await r.json();
  if(j.log){
    const wasBottom=isNearBottom(aiLog);
    aiLog.textContent=j.log.join('\n');
    if(wasBottom)scrollToBottom(aiLog);
  }
  if(j.running===false&&testAIInterval){clearInterval(testAIInterval);aiL('Finished')}}catch(e){}}

// ======== AGENT STUDIO (throttled, no page jump) ========
const COLORS=['#38bdf8','#a855f7','#22c55e','#f59e0b','#ef4444','#ec4899','#14b8a6','#f97316','#6366f1','#84cc16'];
let _studioFetching=false;
async function fetchStudio(){
  if(!tid()||_studioFetching)return;
  _studioFetching=true;
  try{const r=await fetch('/tournaments/'+tid()+'/agents-studio');if(!r.ok){_studioFetching=false;return}const agents=await r.json();
  const el=document.getElementById('studio-agents');
  // Preserve scroll position of parent
  const scrollY=window.scrollY;
  el.innerHTML='';
  agents.forEach(a=>{
    let posHtml='';Object.entries(a.positions).forEach(([sym,p])=>{
      const c=p.unrealized_pnl>=0?'#4ade80':'#f87171';
      posHtml+='<div class="pos-row">'+p.side.toUpperCase()+' '+p.size+' '+sym+' @ '+p.entry_price+' → '+p.current_price+' <span style="color:'+c+'">'+(p.unrealized_pnl>=0?'+':'')+p.unrealized_pnl.toFixed(2)+'</span></div>'});
    if(!posHtml)posHtml='<div style="font-size:.78rem;color:#94a3b8">No open positions</div>';
    let sigHtml='';a.recent_signals.slice(-5).reverse().forEach(s=>{
      const cls=s.status==='executed'?'signal-ok':'signal-err';const icon=s.status==='executed'?'✅':'❌';
      sigHtml+='<div class="'+cls+'">'+icon+' '+s.side+' '+s.qty+' '+s.symbol+(s.price?' @ '+s.price.toFixed(2):'')+(s.error?' — '+s.error:'')+'</div>'});
    if(!sigHtml)sigHtml='<div style="font-size:.78rem;color:#94a3b8">No signals yet</div>';
    let errHtml='';a.recent_errors.forEach(e=>{errHtml+='<div class="signal-err">⚠ '+e.symbol+' '+e.side+': '+e.error+'</div>'});
    const pnlColor=a.realized_pnl>=0?'#4ade80':'#f87171';
    const card=document.createElement('div');card.className='agent-card';
    card.innerHTML='<h3><span class="conn-dot '+(a.connected?'conn-on':'conn-off')+'"></span>'+a.name+' <span style="font-size:.75rem;color:#94a3b8">('+a.agentId+')</span></h3>'+
      '<div><span class="stat"><b>Equity:</b> $'+a.equity.toFixed(2)+'</span>'+
      '<span class="stat"><b>Cash:</b> $'+a.cash_balance.toFixed(2)+'</span>'+
      '<span class="stat"><b>PnL:</b> <span style="color:'+pnlColor+'">'+(a.realized_pnl>=0?'+':'')+a.realized_pnl.toFixed(2)+'</span></span>'+
      '<span class="stat"><b>Unrealized:</b> '+a.unrealized_pnl.toFixed(2)+'</span>'+
      '<span class="stat"><b>Trades:</b> '+a.trades_count+'</span>'+
      '<span class="stat"><b>Risk:</b> '+a.riskProfile+'</span>'+
      '<span class="stat"><b>Signals:</b> '+a.total_signals+' ('+a.rejected_count+' rejected)</span></div>'+
      '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px">'+
      '<div><b style="font-size:.82rem;color:#38bdf8">Positions</b>'+posHtml+'</div>'+
      '<div><b style="font-size:.82rem;color:#22c55e">Recent Signals</b>'+sigHtml+'</div>'+
      '<div><b style="font-size:.82rem;color:#f87171">Errors</b>'+(errHtml||'<div style="font-size:.78rem;color:#94a3b8">None</div>')+'</div></div>';
    el.appendChild(card)});
  // Restore scroll position to prevent jumping
  window.scrollTo(0,scrollY);
  }catch(e){console.error(e)}
  _studioFetching=false;
}

let _chartFetching=false;
async function fetchEquityChart(){
  if(!tid()||_chartFetching)return;
  _chartFetching=true;
  try{const r=await fetch('/tournaments/'+tid()+'/equity-chart');if(!r.ok){_chartFetching=false;return}const data=await r.json();
  const ctx=document.getElementById('equityChart').getContext('2d');
  const datasets=data.datasets.map((ds,i)=>({label:ds.name||ds.agentId,data:ds.data,
    borderColor:COLORS[i%COLORS.length],backgroundColor:COLORS[i%COLORS.length]+'33',
    borderWidth:2,pointRadius:1,tension:0.3,fill:false}));
  if(equityChartInstance){
    // Update data in-place instead of destroy/recreate to prevent reflow
    equityChartInstance.data.datasets=datasets;
    equityChartInstance.update('none'); // 'none' = no animation, minimal reflow
  }else{
    equityChartInstance=new Chart(ctx,{type:'line',data:{datasets},
      options:{responsive:true,animation:false,plugins:{legend:{labels:{color:'#e2e8f0'}},title:{display:true,text:'Equity Over Time',color:'#38bdf8'}},
      scales:{x:{type:'linear',ticks:{color:'#94a3b8',callback:v=>new Date(v).toLocaleTimeString()},grid:{color:'#1e293b'}},
      y:{ticks:{color:'#94a3b8'},grid:{color:'#1e293b'}}}}});
  }
  }catch(e){console.error(e)}
  _chartFetching=false;
}

// ======== REPLAY & DEBUG ========
async function fetchReplay(){
  if(!tid())return;
  const box=document.getElementById('replay-box');box.style.display='block';box.innerHTML='Loading...';
  try{const r=await fetch('/tournaments/'+tid()+'/replay');if(!r.ok){box.innerHTML='Error: '+r.status;return}
  const data=await r.json();
  let h='<div style="color:#f59e0b;margin-bottom:8px"><b>'+data.name+'</b> | Status: '+data.status+' | Events: '+data.totalEvents+'</div>';
  data.timeline.forEach(ev=>{
    const t=new Date(ev.ts*1000).toLocaleTimeString();
    const c=ev.subtype==='rejected'?'#f87171':ev.type==='signal'?'#4ade80':'#38bdf8';
    h+='<div style="color:'+c+'">'+t+' ['+ev.type+'/'+ev.subtype+'] '+ev.agentId+' '+JSON.stringify(ev.detail)+'</div>';
  });
  box.innerHTML=h;
  }catch(e){box.innerHTML='Error: '+e}
}

async function fetchDebug(){
  const agentId=document.getElementById('debugAgentId').value;
  if(!tid()||!agentId){L('Select tournament and enter agent ID','err');return}
  const box=document.getElementById('debug-box');box.style.display='block';box.innerHTML='Loading...';
  try{const r=await fetch('/tournaments/'+tid()+'/debug/'+agentId);if(!r.ok){box.innerHTML='Error: '+r.status+' '+(await r.json()).detail;return}
  const d=await r.json();
  let h='<h3 style="color:#ef4444">Debug: '+d.name+' ('+d.agentId+')</h3>';
  h+='<div><b>Rank:</b> #'+d.rank+'/'+d.totalAgents+' | <b>Final Equity:</b> $'+d.finalEquity+' | <b>PnL:</b> '+d.finalPnl+'</div>';
  h+='<div><b>Max Equity:</b> $'+d.maxEquity+' | <b>Min:</b> $'+d.minEquity+' | <b>Drawdown:</b> '+d.maxDrawdownPct+'%</div>';
  h+='<div><b>Trades:</b> '+d.totalTrades+' | <b>Signals:</b> '+d.executedSignals+' exec / '+d.rejectedSignals+' rejected</div>';
  h+='<div class="sep"></div><b style="color:#f59e0b">Diagnostics:</b><ul>';
  d.diagnostics.forEach(diag=>{h+='<li style="color:#fbbf24">'+diag+'</li>'});
  h+='</ul>';
  if(Object.keys(d.rejectionReasons).length>0){
    h+='<b style="color:#f87171">Rejection Reasons:</b><ul>';
    Object.entries(d.rejectionReasons).forEach(([k,v])=>{h+='<li>'+k+': '+v+'x</li>'});
    h+='</ul>';
  }
  if(d.worstEquityDrops.length>0){
    h+='<b>Worst Equity Drops:</b><ul>';
    d.worstEquityDrops.forEach(w=>{h+='<li>'+new Date(w.ts*1000).toLocaleTimeString()+': '+w.delta.toFixed(2)+'</li>'});
    h+='</ul>';
  }
  box.innerHTML=h;
  }catch(e){box.innerHTML='Error: '+e}
}

// ======== API KEYS ========
async function fetchKeys(){
  const key=document.getElementById('aiApiKey').value;if(!key)return;
  try{const r=await fetch('/agent-api/v1/keys',{headers:{'Authorization':'Bearer '+key}});
  if(!r.ok)return;const keys=await r.json();const el=document.getElementById('keys-list');el.innerHTML='';
  keys.forEach(k=>{const cls=!k.is_active?'key-revoked':k.expired?'key-expired':'key-active';
    const status=!k.is_active?'REVOKED':k.expired?'EXPIRED':'ACTIVE'+(k.remaining_hours!=null?' ('+k.remaining_hours+'h left)':'');
    const row=document.createElement('div');row.className='key-row';
    row.innerHTML='<span class="'+cls+'">'+k.api_key+' | '+k.agentId+' | '+status+'</span>'+
      (k.is_active&&!k.expired?'<button class="small danger" onclick="revokeKey(\''+k.api_key_full+'\')">Revoke</button>':'');
    el.appendChild(row)});
  }catch(e){}}
async function revokeKey(k){
  const key=document.getElementById('aiApiKey').value;
  try{await fetch('/agent-api/v1/keys/'+k+'/revoke',{method:'POST',headers:{'Authorization':'Bearer '+key}});fetchKeys()}catch(e){}}

// ======== MARKET STATUS (5s auto-refresh) ========
async function fetchMarketStatus(){
  try{const r=await fetch('/market-status');if(!r.ok)return;const d=await r.json();
  let h='<span class="status-badge '+(d.chainlinkConnected?'status-running':'status-finished')+'">'+d.marketSource.toUpperCase()+'</span> ';
  h+=d.chainlinkConnected?'Connected':'Not connected';
  if(d.chainlinkStrictOnly){h+=' <span style="background:#ef4444;color:#fff;padding:2px 8px;border-radius:4px;font-size:.8rem;font-weight:700;margin-left:8px">⛓ STRICT CHAINLINK ONLY ON</span>'}
  else{h+=' <span style="background:#334155;color:#94a3b8;padding:2px 8px;border-radius:4px;font-size:.75rem;margin-left:8px">STRICT CHAINLINK ONLY OFF</span>'}
  h+=' | TTL:'+d.cacheTtlSec+'s | <span style="color:#94a3b8;font-size:.75rem">Updated: '+new Date().toLocaleTimeString()+'</span><br>';
  // Strict mode: show blocked symbols alert
  if(d.chainlinkStrictOnly){
    let blocked=[];Object.entries(d.symbols).forEach(([sym,s])=>{if(s.strictBlocked)blocked.push(sym)});
    if(blocked.length>0){h+='<div style="background:#7f1d1d;border:2px solid #ef4444;border-radius:8px;padding:10px;margin:8px 0;color:#fca5a5;font-weight:700;font-size:.95rem">🚫 TRADING BLOCKED: ORACLE STALE/UNAVAILABLE — '+blocked.join(', ')+'</div>'}
  }

  // Section WS: LIVE WEBSOCKET PRICE (MVP)
  if(d.marketSource==='ws_mvp'){
    h+='<div style="margin-top:10px;padding:10px;border:2px solid #a855f7;border-radius:8px;background:#1a1035">';
    h+='<b style="color:#a855f7;font-size:.95rem">⚡ LIVE WEBSOCKET PRICE (MVP)</b>';
    const wsConn=d.wsConnected?'<span style="color:#4ade80"> ● CONNECTED</span>':'<span style="color:#f87171"> ● DISCONNECTED</span>';
    h+=wsConn;
    if(d.wsProviders){Object.entries(d.wsProviders).forEach(([name,p])=>{
      const dot=p.connected?'🟢':'🔴';
      const age=p.lastMsgAgeSec!=null?Math.round(p.lastMsgAgeSec)+'s ago':'—';
      const err=p.error?'<span style="color:#f87171"> '+p.error.substring(0,60)+'</span>':'';
      const rc=p.reconnects>0?' <span style="color:#94a3b8">(reconnects:'+p.reconnects+')</span>':'';
      h+='<div style="padding:2px 0;font-size:.82rem">'+dot+' <b>'+name.toUpperCase()+'</b> last:'+age+rc+err+'</div>';
    })}
    h+='<div style="margin-top:6px">';
    Object.entries(d.symbols).forEach(([sym,s])=>{
      const price=s.wsPrice!=null?s.wsPrice:'—';
      const age=s.wsAgeSec!=null?Math.round(s.wsAgeSec)+'s':'—';
      const src=s.wsSource||'—';
      const stale=s.wsStale?'<span style="color:#f59e0b"> ⚠ STALE</span>':'<span style="color:#4ade80"> FRESH</span>';
      h+='<div style="padding:2px 0"><b>'+sym+'</b>: <span style="color:#a855f7;font-size:1rem">$'+price+'</span> | age:'+age+' | source:'+src+stale+'</div>';
    });
    h+='</div></div>';
  }

  // Section A: CHAINLINK ORACLE PRICE
  h+='<div style="margin-top:10px;padding:10px;border:1px solid #334155;border-radius:8px;background:#0c1222">';
  h+='<b style="color:#f59e0b;font-size:.95rem">⛓ CHAINLINK ORACLE PRICE</b><br>';
  Object.entries(d.symbols).forEach(([sym,s])=>{
    const price=s.chainlinkPrice!=null?s.chainlinkPrice:'—';
    const round_id=s.chainlinkRoundId?s.chainlinkRoundId.slice(-8):'—';
    const oracleAge=s.chainlinkAgeSec!=null?Math.round(s.chainlinkAgeSec)+'s':'—';
    const pollAge=s.pollAgeSec!=null?Math.round(s.pollAgeSec)+'s':'—';
    const fb=s.fallbackActive?'<span style="color:#f59e0b"> ⚠ FALLBACK</span>':'';
    const err=s.lastError?'<span style="color:#f87171"> '+s.lastError+'</span>':'';
    h+='<div style="padding:2px 0"><b>'+sym+'</b>: <span style="color:#4ade80;font-size:1rem">$'+price+'</span> | round:'+round_id+' | oracle age:'+oracleAge+' | poll:'+pollAge+fb+err+'</div>';
  });
  h+='</div>';

  // Section B: LIVE EXCHANGE PRICE
  h+='<div style="margin-top:10px;padding:10px;border:1px solid #334155;border-radius:8px;background:#0c1222">';
  h+='<b style="color:#38bdf8;font-size:.95rem">📊 LIVE EXCHANGE PRICE</b><br>';
  Object.entries(d.symbols).forEach(([sym,s])=>{
    const price=s.liveExchangePrice!=null?s.liveExchangePrice:'—';
    const age=s.liveExchangeAgeSec!=null?Math.round(s.liveExchangeAgeSec)+'s':'—';
    const src=s.liveExchangeSource||'—';
    const stale=s.liveExchangeStale?'<span style="color:#f59e0b"> ⚠ STALE</span>':'';
    h+='<div style="padding:2px 0"><b>'+sym+'</b>: <span style="color:#38bdf8;font-size:1rem">$'+price+'</span> | age:'+age+' | source:'+src+stale+'</div>';
  });
  h+='</div>';

  // Section C: EFFECTIVE TRADING PRICE
  h+='<div style="margin-top:10px;padding:10px;border:1px solid #22c55e;border-radius:8px;background:#0c1222">';
  h+='<b style="color:#22c55e;font-size:.95rem">💰 EFFECTIVE TRADING PRICE</b>';
  h+=' <span style="color:#94a3b8;font-size:.75rem">(max oracle age: '+d.tradingMaxOracleAgeSec+'s)</span><br>';
  Object.entries(d.symbols).forEach(([sym,s])=>{
    const price=s.effectiveTradingPrice!=null?s.effectiveTradingPrice:'—';
    const src=s.tradingSource||'—';
    const srcColor=src==='chainlink'?'#4ade80':src==='live_exchange'?'#38bdf8':'#f59e0b';
    let badge='<span style="background:'+srcColor+';color:#000;padding:1px 6px;border-radius:4px;font-size:.75rem;font-weight:600">'+src.toUpperCase()+'</span>';
    let warn='';
    if(s.staleReason){warn=' <span style="color:#f87171;font-size:.75rem">⚠ '+s.staleReason+'</span>'}
    h+='<div style="padding:3px 0"><b>'+sym+'</b>: <span style="color:#22c55e;font-size:1.1rem;font-weight:700">$'+price+'</span> '+badge+warn+'</div>';
  });
  h+='</div>';

  document.getElementById('market-status').innerHTML=h}catch(e){}}
fetchMarketStatus();setInterval(()=>{if(!document.hidden)fetchMarketStatus()},5000);

// Auto-refresh: only when page visible, 15s interval
setInterval(()=>{if(tid()&&!document.hidden){fetchStudio();fetchEquityChart()}},15000);
loadTournaments();
</script></body></html>"""


@router.get("/", response_class=HTMLResponse)
def index():
    return HTML
