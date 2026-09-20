// Real production DOM helpers + phase controller. Local HTML only, network blocked.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const src=fs.readFileSync(process.env.BACCARAT_SOURCE||path.join(__dirname,'../src/main.cpp'),'utf8');
const section=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i);assert(i>=0&&j>i,a);return src.slice(i,j)};
const production=section('const chipVisible=','const chipSourceByHit=')+
 section('const mainTarget=','const tableBetValue=')+
 section('const tableBetValue=','const clickRegistry=')+
 section('const pairControlState=','const emitReadiness=')+
 section('const nativeBetWindowReady=','const sought=isMainBaccarat');
const actualProbe=src.slice(src.lastIndexOf('probeAndMaybeArm=()=>{'),src.indexOf('if(AUTO_BET_REQUEST)ROOT_WINDOW.setTimeout(probeAndMaybeArm,180);')).replace('probeAndMaybeArm=()=>{','const runReadinessProbe=()=>{');
const results=[];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const ctx=await browser.newContext({viewport:{width:1200,height:800},serviceWorkers:'block'});
  await ctx.route('**/*',r=>r.abort());const page=await ctx.newPage();
  async function fixture(side='Banker',required=true){
   await page.setContent(`<style>body{margin:20px}.row{display:flex;gap:2px}.cell{width:52px;height:56px;background:#ccc}.cell span{pointer-events:none}.chip{position:absolute;top:250px;width:40px;height:40px}.closed{pointer-events:none}</style><section id="table"><header>Speed Baccarat 5 ID: 123</header><div class="row"><div class="cell" id="pp"><span>S PAAR</span></div><div class="cell" id="player"><span>9</span></div><div class="cell" id="tie"><span>REMIS</span></div><div class="cell" id="banker"><span>3</span></div><div class="cell" id="bp"><span>B PAAR</span></div></div><div id="bet">EINSATZ 0,00 €</div></section><button class="chip" id="one" style="left:20px">1</button><button class="chip" id="pair" style="left:70px">0,2</button>`);
   await page.evaluate(({production,actualProbe,side,required})=>{
    (0,eval)(`
const ROOT_WINDOW=window,NodeFilter=window.NodeFilter;
const norm=s=>String(s||'').replace(/\\s+/g,' ').trim(),lower=s=>norm(s).toLowerCase(),pairText=s=>lower(s).replace(/[-–—_]+/g,' ').replace(/\\s+/g,' ').trim();
const visible=el=>!!el&&el.isConnected&&getComputedStyle(el).display!=='none'&&getComputedStyle(el).visibility!=='hidden'&&el.getBoundingClientRect().width>0;
const RUN_TOKEN='run',TARGET_ID='table',TARGET_NAME='Speed Baccarat 5',SOURCE_GAME='123',REQUEST_TOKEN='1';
const AUTO_BET_REQUEST=true,MAIN_REQUIRED=${required},MAIN_SIDE=${JSON.stringify(side)},MAIN_STAKE_CENTS=100,MAIN_CHIP_CENTS=100,MAIN_CHIP_CLICKS=1,PAIR_CHIP_CENTS=20,PAIR_CHIP_DENOM_CENTS=20,PAIR_CHIP_CLICKS=1;
const isMulti=true,context='offline',href='offline',rootHref='offline',focusKey='test',chipSourceByHit=new WeakMap();
const toRootViewportPoint=(x,y)=>({x,y}),canonicalTable=()=>document.getElementById('table'),tableTextMatches=t=>t.startsWith(TARGET_NAME);
const pairTargets=()=>({player:document.getElementById('pp'),banker:document.getElementById('bp')});
let selected=100,accepted=1,nativeOpen=true,ackEnabled=true,clock=1000;
Date.now=()=>clock;const timers=[],events=[];window.setTimeout=(fn,ms)=>{timers.push({fn,at:clock+ms});};
const operation={startedAt:clock,uiWaitDeadline:clock+20000,hardDeadline:clock+30000,deadline:clock+30000,uiReadyAt:0,finished:false,pending:false,mainPrepared:!MAIN_REQUIRED,stakePrepared:false,confirmed:{player:false,banker:false},attempt:0};
const clickRegistry={},lastChipSelectorDiag={},lastChipSearchDiag={},lastChipRackDiag={};
const finishRetry=reason=>{operation.finished=true;events.push({kind:'finished',reason})};
const probeAndMaybeArm=()=>{},emitReadiness=()=>{};
const chipTarget=c=>document.getElementById(c===100?'one':'pair');
const multiplayChipSelector=()=>null,selectedMultiplayChip=c=>selected===c?chipTarget(c):null;
const chipTargetMeta=el=>({strong:true,denom:String((el?.id==='one'?100:20)/100),selectedToggle:!!el&&(el.id==='one'?100:20)===selected});
const chipActiveEvidence=()=>({active:true,evidence:'fixture-selected',signature:String(selected)}),chipSelectionSignature=()=>String(selected),chipRackSignature=()=>String(selected);
window.__BCP_STAKE_PREP_ACKS__={};window.__BCP_BET_WINDOW_ACKS__={};
window.console.log=message=>{const i=message.indexOf('{');if(i<0)return;const kind=message.slice(0,i),payload=JSON.parse(message.slice(i));events.push({kind,payload});
 if(kind==='__BAC_BET_WINDOW_PROBE__'&&ackEnabled)window.__BCP_BET_WINDOW_ACKS__['table|123|1']={allowed:nativeOpen,probeToken:payload.probeToken,ts:clock};
 if(kind==='__BAC_STAKE_PREP_COORDS__'){
  window.__BCP_STAKE_PREP_ACKS__[['table','123','1',payload.phase,payload.stakePrepAttempt].join('|')]={sendOk:true};
  selected=payload.phase==='pair'?20:100;
  if(payload.phase==='main')document.getElementById('bet').innerText='EINSATZ '+accepted.toFixed(2).replace('.',',')+' €';
 }
};
${production}
${actualProbe}
window.api={operation,events,probe:runReadinessProbe,prepare:()=>storePairClickCoords(pairTargets()),row:()=>mainBetRow(canonicalTable()),target:s=>mainTarget(canonicalTable(),s)?.id||null,ui:p=>bettingUiState(canonicalTable(),p),
 advance:ms=>{clock+=ms;const due=timers.filter(t=>t.at<=clock);for(const t of due){timers.splice(timers.indexOf(t),1);t.fn();}},
 ready:()=>{document.getElementById('player').innerHTML='<span>SPIELER</span>';document.getElementById('banker').innerHTML='<span>BANKIER</span>';},
 closed:()=>{nativeOpen=false;},noAck:()=>{ackEnabled=false;},accepted:x=>{accepted=x;}};
`);
   },{production,actualProbe,side,required});
  }
  async function test(name,fn){try{await fn();results.push({name,ok:true});console.log('PASS '+name)}catch(e){results.push({name,ok:false,error:String(e)});console.error('FAIL '+name,e)}}
  await test('Result-only Player/Banker fields resolve structurally but cannot place bets',async()=>{
   await fixture();assert.deepEqual(await page.evaluate(()=>['Player','Banker','Tie'].map(api.target)),['player','banker','tie']);
   assert.equal(await page.evaluate(()=>api.ui('main').reason),'previous-result-visible');
   await page.evaluate(()=>{api.prepare();api.prepare();api.advance(7000);api.prepare();api.prepare()});
   assert.equal(await page.evaluate(()=>api.events.some(e=>e.kind==='__BAC_STAKE_PREP_COORDS__')),false);
   assert.equal(await page.evaluate(()=>api.operation.uiReadyAt),0);
  });
  for(const side of ['Player','Banker','Tie'])await test(side+': UI opens after 7 s; main confirmation precedes Pair chip and Pair request',async()=>{
   await fixture(side);await page.evaluate(()=>{api.prepare();api.prepare();api.advance(7000);api.ready();api.prepare();api.prepare()});
   assert.equal(await page.evaluate(()=>api.operation.uiReadyAt),8000);
   assert(await page.evaluate(()=>api.operation.deadline>=14500));
   assert.deepEqual(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').map(e=>e.payload.phase)),['main-chip']);
   await page.evaluate(()=>{api.prepare();api.advance(500);api.prepare();api.prepare();api.advance(700);api.prepare();api.prepare();api.advance(500);api.prepare();api.prepare()});
   const events=await page.evaluate(()=>api.events);
   assert.deepEqual(events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').map(e=>e.payload.phase),['main-chip','main','pair']);
   const confirmation=events.findIndex(e=>e.kind==='__BAC_STAKE_PREP_CONFIRM__'&&e.payload.phase==='main');
   const pairs=events.findIndex(e=>e.kind==='__BAC_PAIR_CLICK_COORDS__');assert(confirmation>=0&&pairs>confirmation,JSON.stringify(events));
  });
  await test('Native betting closes while UI lags: no stake request',async()=>{
   await fixture();await page.evaluate(()=>{api.prepare();api.prepare();api.advance(7000);api.closed();api.prepare();api.ready();api.prepare()});
   assert.equal(await page.evaluate(()=>api.operation.finished),true);
   assert.equal(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').length),0);
  });
  await test('Missing/stale native acknowledgement blocks even an open UI',async()=>{
   await fixture();await page.evaluate(()=>{api.ready();api.noAck();api.prepare();api.prepare();api.advance(2000);api.prepare()});
   assert.equal(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').length),0);
  });
  await test('A still-young positive reply cannot stand in for the requested refresh',async()=>{
   await fixture();await page.evaluate(()=>{api.prepare();api.prepare();api.advance(300);api.noAck();api.ready();api.prepare();api.prepare()});
   assert.equal(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').length),0);
  });
  await test('Disabled/covered main control stays blocked',async()=>{
   await fixture();await page.evaluate(()=>{api.ready();document.getElementById('banker').setAttribute('aria-disabled','true')});
   assert.equal(await page.evaluate(()=>api.target('Banker')),null);
   await page.evaluate(()=>{document.getElementById('banker').removeAttribute('aria-disabled');const r=document.getElementById('banker').getBoundingClientRect();const el=document.createElement('div');el.style=`position:fixed;left:${r.left}px;top:${r.top}px;width:${r.width}px;height:${r.height}px;z-index:100;background:black`;document.body.append(el)});
   assert.equal(await page.evaluate(()=>api.target('Banker')),null);
  });
  await test('An ambiguous/reordered row is never inferred from positions',async()=>{
   await fixture();await page.evaluate(()=>{document.getElementById('tie').innerText='Bonus';});
   assert.equal(await page.evaluate(()=>api.row()),null);
   assert.equal(await page.evaluate(()=>api.target('Banker')),null);
  });
  await test('Unconfirmed main wager prevents Pair phase',async()=>{
   await fixture();await page.evaluate(()=>{api.ready();api.accepted(0);api.prepare();api.prepare();api.advance(500);api.prepare();api.prepare();api.advance(700);api.prepare()});
   assert.equal(await page.evaluate(()=>api.operation.finished),true);
   assert.deepEqual(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').map(e=>e.payload.phase)),['main-chip','main']);
  });
  await test('Pair-only signal also waits through old score overlay',async()=>{
   await fixture('Banker',false);await page.evaluate(()=>{api.prepare();api.prepare()});
   assert.equal(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').length),0);
   await page.evaluate(()=>{api.ready();api.prepare()});
   assert.deepEqual(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').map(e=>e.payload.phase)),['pair']);
  });
  await test('Native close after confirmed main prevents further Pair preparation',async()=>{
   await fixture();await page.evaluate(()=>{api.ready();api.prepare();api.prepare();api.advance(500);api.prepare();api.prepare();api.advance(700);api.closed();api.prepare();api.prepare()});
   assert.equal(await page.evaluate(()=>api.operation.finished),true);
   assert.deepEqual(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').map(e=>e.payload.phase)),['main-chip','main']);
  });
  await test('A never-ready UI times out without carrying the signal forward',async()=>{
   await fixture();await page.evaluate(()=>{api.probe();api.advance(21000);api.probe()});
   assert.equal(await page.evaluate(()=>api.events.find(e=>e.kind==='finished').reason),'table-betting-ui-timeout');
   assert.equal(await page.evaluate(()=>api.events.some(e=>e.kind==='__BAC_STAKE_PREP_COORDS__')),false);
  });
  await test('Re-rendered betting cells are resolved from the current DOM',async()=>{
   await fixture();await page.evaluate(()=>{api.prepare();const row=document.querySelector('.row');row.replaceWith(row.cloneNode(true));api.ready();api.prepare()});
   assert.equal(await page.evaluate(()=>api.target('Banker')),'banker');
   assert.deepEqual(await page.evaluate(()=>api.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').map(e=>e.payload.phase)),['main-chip']);
  });
  await ctx.close();
 }finally{await browser.close()}
 const out=process.env.TEST_REPORT||path.join(__dirname,'../.validation/betting_window_results.json');fs.writeFileSync(out,JSON.stringify(results,null,2));
 if(results.some(r=>!r.ok))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
