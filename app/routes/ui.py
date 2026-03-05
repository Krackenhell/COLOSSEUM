from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Colosseum MVP</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}
h1{text-align:center;margin-bottom:20px;color:#38bdf8}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:1200px;margin:0 auto}
.card{background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155}
.card h2{color:#38bdf8;margin-bottom:12px;font-size:1.1rem}
label{display:block;font-size:.85rem;margin-top:8px;color:#94a3b8}
input,select{width:100%;padding:6px 8px;margin-top:2px;border-radius:6px;border:1px solid #475569;background:#0f172a;color:#e2e8f0}
button{margin-top:10px;padding:8px 16px;border:none;border-radius:6px;cursor:pointer;font-weight:600;background:#38bdf8;color:#0f172a}
button:hover{background:#7dd3fc}
button.demo{background:#22c55e;color:#fff;font-size:1rem;width:100%}
button.small{padding:4px 10px;font-size:.8rem;margin:2px}
#log{background:#020617;border:1px solid #334155;border-radius:8px;padding:10px;margin-top:12px;height:260px;overflow-y:auto;font-family:monospace;font-size:.82rem;white-space:pre-wrap}
.ok{color:#4ade80}.err{color:#f87171}.info{color:#38bdf8}.warn{color:#fbbf24}
#leaderboard{margin-top:8px}
#leaderboard table{width:100%;border-collapse:collapse;font-size:.82rem}
#leaderboard th,#leaderboard td{padding:4px 6px;border-bottom:1px solid #334155;text-align:left}
#leaderboard th{color:#38bdf8}
#timer-box{background:#020617;border:1px solid #334155;border-radius:8px;padding:10px;margin-top:8px;font-family:monospace;font-size:.9rem}
.status-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.8rem;font-weight:600}
.status-scheduled{background:#eab308;color:#000}.status-running{background:#22c55e;color:#000}.status-finished{background:#ef4444;color:#fff}
#existing-list{margin-top:8px;max-height:150px;overflow-y:auto}
#existing-list .item{padding:4px 8px;cursor:pointer;border-radius:4px;font-size:.85rem}
#existing-list .item:hover{background:#334155}
#existing-list .item.active{background:#38bdf8;color:#0f172a}
.sep{border-top:1px solid #334155;margin:14px 0}
</style></head><body>
<h1>⚔️ Colosseum MVP</h1>
<div class="grid">

<!-- ===== TOURNAMENT PANEL (left) ===== -->
<div class="card"><h2>🏟️ Турнир (Tournament)</h2>

<label>Название турнира<input id="tName" value="Demo Tournament"></label>
<label>Начало турнира<input id="tStart" type="datetime-local"></label>
<label>Конец турнира<input id="tEnd" type="datetime-local"></label>
<button onclick="createTournament()">Создать турнир</button>

<div class="sep"></div>
<h2>📋 Существующие турниры</h2>
<button class="small" onclick="loadTournaments()">Обновить</button>
<div id="existing-list"></div>

<div class="sep"></div>
<label>ID турнира<input id="tId" readonly></label>
<div id="timer-box">Выберите турнир...</div>
<button onclick="setStatus('running')">▶ Форсировать старт</button>
<button onclick="setStatus('finished')">⏹ Завершить</button>
</div>

<!-- ===== SIGNAL PANEL (right top) ===== -->
<div class="card"><h2>📡 Сигнал (Signal)</h2>

<label>Символ (Symbol)<select id="sSym"><option>BTCUSDT</option><option>ETHUSDT</option><option>SOLUSDT</option></select></label>
<label>Сторона (Side)<select id="sSide"><option value="buy">buy</option><option value="sell">sell</option></select></label>
<label>Количество (Qty)<input id="sQty" type="number" value="0.1" step="0.01"></label>

<div class="sep"></div>
<label>Плечо (Leverage)<input id="tLeverage" type="number" value="10" min="1" max="125"></label>
<label>Риск-профиль агента<select id="tRisk"><option value="normal">normal</option><option value="hft">hft</option></select></label>

<button onclick="submitSignal()">Отправить сигнал</button>

<div class="sep"></div>
<h2>🤖 Агент (Agent)</h2>
<label>ID агента<input id="aId" value="agent-alpha"></label>
<label>Имя агента<input id="aName" value="Alpha Bot"></label>
<button onclick="registerAgent()">Зарегистрировать</button>
<button onclick="connectAgent()">Подключить</button>
<button onclick="heartbeat()">💓 Heartbeat</button>
</div>

<!-- ===== LEADERBOARD (full width) ===== -->
<div class="card" style="grid-column:1/-1"><h2>📊 Лидерборд (Leaderboard)</h2>
<button onclick="fetchLeaderboard()">Обновить</button>
<button onclick="fetchEvents()">События</button>
<div id="leaderboard"></div>
</div>

</div>

<div style="max-width:1200px;margin:16px auto">
<button class="demo" onclick="quickStart()">🚀 Quick Start Demo (futures)</button>
<div id="log"></div>
</div>

<script>
const KEY='dev-gateway-key';
const H={'Content-Type':'application/json','x-api-key':KEY};
const log=document.getElementById('log');
function L(msg,cls='info'){const d=document.createElement('div');d.className=cls;d.textContent=new Date().toLocaleTimeString()+' '+msg;log.prepend(d)}
function nonce(){return crypto.randomUUID()}
function ts(){return Date.now()/1000}

// Set default datetime-local values (now+10s start, +24h end)
(function(){
  const pad=v=>String(v).padStart(2,'0');
  function localISO(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())+'T'+pad(d.getHours())+':'+pad(d.getMinutes())}
  const now=new Date();
  const start=new Date(now.getTime()+10*1000);
  const end=new Date(now.getTime()+24*3600*1000);
  document.getElementById('tStart').value=localISO(start);
  document.getElementById('tEnd').value=localISO(end);
})();

async function api(method,path,body){
  try{
    const r=await fetch(path,{method,headers:H,body:body?JSON.stringify(body):undefined});
    const j=await r.json();
    if(!r.ok){
      const det=j.detail||JSON.stringify(j);
      const cls=r.status===429?'warn':'err';
      L('ERROR '+r.status+': '+det,cls);
      return null;
    }
    L(method+' '+path+' → OK','ok');
    return j;
  }catch(e){L('FETCH ERROR: '+e,'err');return null}
}

// --- Tournament list ---
async function loadTournaments(){
  const list=await api('GET','/tournaments');
  if(!list)return;
  const el=document.getElementById('existing-list');
  el.innerHTML='';
  list.forEach(t=>{
    const d=document.createElement('div');
    d.className='item'+(t.id===tid()?' active':'');
    const eff=t.effectiveStatus||t.status;
    d.innerHTML=`<span class="status-badge status-${eff}">${eff}</span> <b>${t.name}</b> (${t.id})`;
    d.onclick=()=>{document.getElementById('tId').value=t.id;loadTournaments();refreshTimer()};
    el.appendChild(d);
  });
}

async function createTournament(){
  const startVal=document.getElementById('tStart').value;
  const endVal=document.getElementById('tEnd').value;
  const startEpoch=startVal?new Date(startVal).getTime()/1000:(Date.now()/1000+10);
  const endEpoch=endVal?new Date(endVal).getTime()/1000:(startEpoch+86400);
  const r=await api('POST','/tournaments',{
    name:document.getElementById('tName').value,
    startAt:startEpoch,
    endAt:endEpoch,
    riskProfile:document.getElementById('tRisk').value,
    leverage:parseFloat(document.getElementById('tLeverage').value)||10,
  });
  if(r){
    document.getElementById('tId').value=r.id;
    L('Турнир создан: '+r.id,'ok');
    loadTournaments();
    refreshTimer();
  }
}

function tid(){return document.getElementById('tId').value}
function aid(){return document.getElementById('aId').value}

// --- Timer ---
async function refreshTimer(){
  if(!tid()){document.getElementById('timer-box').textContent='Выберите турнир...';return}
  const r=await fetch('/tournaments/'+tid()+'/timer');
  if(!r.ok)return;
  const d=await r.json();
  const box=document.getElementById('timer-box');
  let html=`<span class="status-badge status-${d.effectiveStatus}">${d.effectiveStatus.toUpperCase()}</span>\n`;
  if(d.effectiveStatus==='scheduled') html+=`До начала: ${fmtSec(d.startsInSec)}`;
  else if(d.effectiveStatus==='running') html+=`Осталось: ${fmtSec(d.remainingSec)}`;
  else html+=`Турнир завершён`;
  box.innerHTML=html;
}
function fmtSec(s){const h=Math.floor(s/3600);const m=Math.floor((s%3600)/60);const sec=Math.floor(s%60);return `${h}ч ${m}м ${sec}с`}
setInterval(refreshTimer,2000);

async function registerAgent(){
  await api('POST','/tournaments/'+tid()+'/register-agent',{agentId:aid(),name:document.getElementById('aName').value});
}
async function setStatus(s){
  const r=await api('POST','/tournaments/'+tid()+'/status',{status:s});
  if(r)refreshTimer();
}
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
  let h='<table><tr><th>#</th><th>Агент</th><th>Equity</th><th>PnL</th><th>Unrealized</th><th>Сделки</th><th>Позиции</th></tr>';
  r.forEach((a,i)=>{
    const posStr=Object.entries(a.positions||{}).map(([s,p])=>`${p.side} ${p.size} ${s}`).join(', ')||'-';
    h+=`<tr><td>${i+1}</td><td>${a.name}</td><td>${a.equity.toFixed(2)}</td><td>${a.totalPnl.toFixed(2)}</td><td>${a.unrealized_pnl.toFixed(2)}</td><td>${a.trades_count}</td><td style="font-size:.75rem">${posStr}</td></tr>`;
  });
  h+='</table>';
  document.getElementById('leaderboard').innerHTML=h;
}
async function fetchEvents(){
  const r=await api('GET','/tournaments/'+tid()+'/events');
  if(r)r.slice(-10).reverse().forEach(e=>L(e.type+' | '+e.agentId+' | '+JSON.stringify(e.detail),'info'));
}
async function quickStart(){
  L('=== Quick Start Demo (Futures) ===','info');
  const now=Date.now()/1000;
  const t=await api('POST','/tournaments',{name:'Futures Demo',startAt:now+2,endAt:now+3600,leverage:10,riskProfile:'normal'});
  if(!t)return;
  document.getElementById('tId').value=t.id;
  loadTournaments();
  await api('POST','/tournaments/'+t.id+'/register-agent',{agentId:'agent-alpha',name:'Alpha Bot'});
  await api('POST','/gateway/connect-agent',{agentId:'agent-alpha',tournamentId:t.id,timestamp:ts(),nonce:nonce()});
  L('Ожидание старта турнира (2с)...','info');
  await new Promise(r=>setTimeout(r,2500));
  refreshTimer();
  await api('POST','/gateway/submit-signal',{agentId:'agent-alpha',tournamentId:t.id,symbol:'BTCUSDT',side:'buy',qty:0.5,timestamp:ts(),nonce:nonce()});
  L('Открыт лонг 0.5 BTC. Попробуйте sell для закрытия!','ok');
  fetchLeaderboard();
}

loadTournaments();
</script></body></html>"""


@router.get("/", response_class=HTMLResponse)
def index():
    return HTML
