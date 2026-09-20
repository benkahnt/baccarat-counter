// Combined DOM/controller regression. All browser requests are blocked except
// a fixture fulfilled in memory; this never connects to a casino or user browser.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const source=process.env.BACCARAT_SOURCE||path.join(__dirname,path.basename(__dirname)==='tests'?'../src/main.cpp':'../project/src/main.cpp');
const src=fs.readFileSync(source,'utf8');
const section=(a,b)=>{const i=src.indexOf(a),j=src.indexOf(b,i);assert(i>=0&&j>i,a);return src.slice(i,j)};
const production=section('const toRootViewportPoint=','const clickRegistry=')+
 section('const pairControlState=','const emitReadiness=')+
 section('const nativeBetWindowReady=','const sought=isMainBaccarat');
const values=['0.2','1','2','5','25','100','250','1000'];
const svg=v=>`<span data-testid="chip"><svg viewBox="0 0 40 40"><g data-testid="chip-inner-text"><text x="4" y="24">${v.replace('.',',')}</text></g></svg></span>`;
const fixture=`<style>*{box-sizing:border-box}body{margin:0}#table{position:absolute;left:8px;top:80px;width:237px;height:180px}.row{display:flex;gap:2px}.cell{width:45px;height:56px;background:#ccc}.cell span{pointer-events:none}#component{position:fixed;left:0;top:0;width:253px;height:693px;pointer-events:none}button{border:0;padding:0;background:#f90;cursor:pointer}#toggle{position:fixed;left:110px;top:650px;width:40px;height:40px;pointer-events:auto;z-index:102}[data-testid="chip"]{display:block;width:40px;height:40px}svg{width:100%;height:100%;pointer-events:none}#drawer{position:fixed;z-index:101;left:0;top:500px;width:253px;height:150px;pointer-events:none}#drawer button{display:none;position:fixed;width:40px;height:40px;pointer-events:none;z-index:102}#modal{position:fixed;inset:0;z-index:100;display:none;pointer-events:auto;background:#0001}.open #modal{display:block}.open #drawer{pointer-events:auto}.open #drawer button{display:block;pointer-events:auto}</style>
<section id="table"><header>Speed Baccarat 18 ID: 123</header><div class="row"><div class="cell" id="pp"><span>S PAAR</span></div><div class="cell" id="player"><span>SPIELER</span></div><div class="cell" id="tie"><span>REMIS</span></div><div class="cell" id="banker"><span>BANKIER</span></div><div class="cell" id="bp"><span>B PAAR</span></div></div><div id="bet">EINSATZ 0,00 €</div></section>
<div data-testid="chip-stack-revolver" id="component"><div id="modal"></div><div data-testid="revolver-chip-stack-drawer" id="drawer">${values.map((v,i)=>`<button data-testid="chip-stack-value-${v}" style="left:${10+i%4*60}px;top:${530+Math.floor(i/4)*60}px" onclick="selectChip('${v}')">${svg(v)}</button>`).join('')}</div><button data-testid="chip-stack-revolver-button" id="toggle" onclick="document.getElementById('component').classList.toggle('open')">${svg('0.2')}</button></div>
<script>window.state={selected:20,total:0,clicks:[],badSelection:false,refuseCollapse:false,rejectMain:false,mainRequired:true};
function money(){document.getElementById('bet').innerText='EINSATZ '+(state.total/100).toFixed(2).replace('.',',')+' €'}
function selectChip(v){const cents=Math.round(Number(v)*100);state.clicks.push({kind:'chip',cents});if(state.badSelection&&cents===100)return;state.selected=cents;document.querySelector('#toggle text').textContent=v.replace('.',',');if(!state.refuseCollapse)document.getElementById('component').classList.remove('open');if(cents===100){const t=document.getElementById('table');t.style.top='150px';t.querySelector('.row').replaceWith(t.querySelector('.row').cloneNode(true));bind()}}
function bind(){for(const id of ['pp','player','tie','banker','bp'])document.getElementById(id).onclick=function(){state.clicks.push({kind:id,cents:state.selected});if(id==='pp'||id==='bp'){if(state.mainRequired&&state.total<100)return;this.dataset.bet=String(Number(this.dataset.bet||0)+state.selected);state.total+=state.selected}else if(!state.rejectMain)state.total+=state.selected;money()}}bind();</script>`;
const results=[];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const ctx=await browser.newContext({viewport:{width:253,height:693},serviceWorkers:'block'});
  await ctx.route('**/*',r=>r.request().url()==='https://fixture.invalid/desktop/multibaccarat/'?r.fulfill({contentType:'text/html',body:fixture}):r.abort());
  const page=await ctx.newPage();
  async function setup(side='Player',required=true,options={}){
   await page.goto('https://fixture.invalid/desktop/multibaccarat/');
   await page.evaluate(({production,side,required,options})=>{
    Object.assign(state,options,{mainRequired:required});
    (0,eval)(`
const ROOT_WINDOW=window,ROOT_DOCUMENT=document,NodeFilter=window.NodeFilter;
const norm=s=>String(s||'').replace(/\\s+/g,' ').trim(),lower=s=>norm(s).toLowerCase(),pairText=s=>lower(s).replace(/[-–—_]+/g,' ').replace(/\\s+/g,' ').trim();
const visible=el=>!!el&&el.isConnected&&getComputedStyle(el).display!=='none'&&getComputedStyle(el).visibility!=='hidden'&&el.getBoundingClientRect().width>0;
const RUN_TOKEN='run',TARGET_ID='table',TARGET_NAME='Speed Baccarat 18',SOURCE_GAME='123',REQUEST_TOKEN='1';
const AUTO_BET_REQUEST=true,MAIN_REQUIRED=${required},MAIN_SIDE=${JSON.stringify(side)},MAIN_STAKE_CENTS=100,MAIN_CHIP_CENTS=100,MAIN_CHIP_CLICKS=1,PAIR_CHIP_CENTS=20,PAIR_CHIP_DENOM_CENTS=20,PAIR_CHIP_CLICKS=1;
const isMulti=true,isMainBaccarat=false,context='offline',href=location.href,rootHref=location.href,focusKey='test';
const canonicalTable=()=>document.getElementById('table'),tableTextMatches=t=>t.startsWith(TARGET_NAME);
const pairTargets=()=>({player:document.getElementById('pp'),banker:document.getElementById('bp')});
let clock=1000,nativeOpen=true;Date.now=()=>clock;const timers=[],events=[],dispatch=[];window.setTimeout=(fn,ms)=>{timers.push({fn,at:clock+ms})};
const operation={startedAt:clock,uiWaitDeadline:clock+20000,hardDeadline:clock+30000,deadline:clock+30000,uiReadyAt:0,finished:false,pending:false,mainPrepared:!MAIN_REQUIRED,mainChipPrepared:!MAIN_REQUIRED,stakePrepared:false,confirmed:{player:false,banker:false},attempt:0};
const clickRegistry={},finishRetry=reason=>{operation.finished=true;events.push({kind:'finished',reason})},probeAndMaybeArm=()=>{},emitReadiness=()=>{};
window.__BCP_STAKE_PREP_ACKS__={};window.__BCP_BET_WINDOW_ACKS__={};
window.console.log=message=>{const i=message.indexOf('{');if(i<0)return;const kind=message.slice(0,i),payload=JSON.parse(message.slice(i));events.push({kind,payload});
 if(kind==='__BAC_BET_WINDOW_PROBE__')window.__BCP_BET_WINDOW_ACKS__['table|123|1']={allowed:nativeOpen,probeToken:payload.probeToken,ts:clock};
 if(['__BAC_CHIP_SELECTOR_OPEN_COORDS__','__BAC_STAKE_PREP_COORDS__','__BAC_PAIR_CLICK_COORDS__'].includes(kind))dispatch.push({kind,payload});
};
${production}
window.api={operation,events,dispatch,prepare:()=>storePairClickCoords(pairTargets()),close:()=>{nativeOpen=false},advance:ms=>{clock+=ms;const due=timers.filter(t=>t.at<=clock);for(const t of due){timers.splice(timers.indexOf(t),1);t.fn()}},
ack:p=>{window.__BCP_STAKE_PREP_ACKS__[['table','123','1',p.phase,p.stakePrepAttempt].join('|')]={sendOk:true}},
diagnose:()=>({main:mainTarget(canonicalTable(),MAIN_SIDE)?.id,mainChip:!!chipTarget(100,canonicalTable()),selector:(()=>{const s=multiplayChipSelector(canonicalTable());return s&&{open:s.open,denom:s.denom}})()})};
`);
   },{production,side,required,options});
  }
  async function drive(options={}){
   for(let turn=0;turn<80;turn++){
    await page.evaluate(()=>{api.prepare();api.advance(150)});
    const requests=await page.evaluate(()=>api.dispatch.splice(0));
    for(const request of requests){const p=request.payload;
     if(request.kind==='__BAC_CHIP_SELECTOR_OPEN_COORDS__'){await page.mouse.click(p.x,p.y);continue}
     if(request.kind==='__BAC_STAKE_PREP_COORDS__'){
      if(p.phase==='main-chip'){
       assert(p.mainChipX>=0&&p.mainChipY>=0,'main-chip only has chip point');assert(p.mainX<0,'main-chip must not carry a stale stake point');
       await page.mouse.click(p.mainChipX,p.mainChipY);
       if(options.closeAfterMainChip)await page.evaluate(()=>api.close());
       if(options.disableAfterMainChip)await page.evaluate(()=>document.getElementById('player').setAttribute('aria-disabled','true'));
      }else if(p.phase==='main'){
       assert.equal(await page.evaluate(()=>state.selected),100,'main wager only with exact selected 1 EUR');
       assert.equal(await page.evaluate(()=>document.getElementById('component').classList.contains('open')),false,'main wager cannot use covered field');
       assert(p.mainY>150,'main field was remeasured after changed row position');assert(p.mainChipX<0,'no duplicate chip selection in stake phase');
       await page.mouse.click(p.mainX,p.mainY);
       if(options.closeAfterMain)await page.evaluate(()=>api.close());
      }else if(p.phase==='pair')await page.mouse.click(p.pairChipX,p.pairChipY);
      else throw Error('unexpected phase '+p.phase);
      await page.evaluate(p=>api.ack(p),p);
     }else{
      if(p.playerRequested)await page.mouse.click(p.playerX,p.playerY);
      if(p.bankerRequested)await page.mouse.click(p.bankerX,p.bankerY);
     }
    }
    if(await page.evaluate(()=>api.operation.finished))break;
   }
   return await page.evaluate(()=>({events:api.events,operation:api.operation,state,diag:api.diagnose()}));
  }
  async function test(name,fn){if(process.env.TEST_FILTER&&!name.includes(process.env.TEST_FILTER))return;try{await fn();results.push({name,ok:true});console.log('PASS '+name)}catch(e){results.push({name,ok:false,error:String(e)});console.error('FAIL '+name,String(e).slice(0,300))}}
  for(const side of ['Player','Banker','Tie'])await test(side+': modal chip selection, fresh main coordinates, confirmed main before both Pairs',async()=>{
   await setup(side);const r=await drive();
   assert.deepEqual(r.events.filter(e=>e.kind==='__BAC_STAKE_PREP_COORDS__').map(e=>e.payload.phase),['main-chip','main','pair'],JSON.stringify(r));
   assert.equal(r.state.total,140,JSON.stringify(r));assert.equal(r.operation.confirmed.player,true);assert.equal(r.operation.confirmed.banker,true);
   assert.deepEqual(r.state.clicks.map(c=>c.kind),['chip',side.toLowerCase(),'chip','pp','bp']);
  });
  await test('Already open radial menu may select the chip while field is covered',async()=>{await setup();await page.evaluate(()=>document.getElementById('component').classList.add('open'));const r=await drive();assert.equal(r.state.total,140,JSON.stringify(r))});
  await test('Initially selected 1 EUR in collapsed menu opens the real drawer and then closes it before main wager',async()=>{await setup();await page.evaluate(()=>{state.selected=100;document.querySelector('#toggle text').textContent='1'});const r=await drive();assert.equal(r.state.total,140,JSON.stringify(r));assert.deepEqual(r.state.clicks.map(c=>c.kind),['chip','player','chip','pp','bp']);assert.equal(r.state.clicks[0].cents,100)});
  await test('Wrong selected denomination blocks main and Pairs',async()=>{await setup('Player',true,{badSelection:true});const r=await drive();assert.equal(r.state.total,0);assert(!r.state.clicks.some(c=>['player','banker','tie','pp','bp'].includes(c.kind)))});
  await test('Menu remaining open after selection blocks actual stake',async()=>{await setup('Player',true,{refuseCollapse:true});const r=await drive();assert.equal(r.state.total,0);assert(!r.state.clicks.some(c=>c.kind==='player'))});
  await test('Unconfirmed main prevents Pair clicks',async()=>{await setup('Player',true,{rejectMain:true});const r=await drive();assert.equal(r.state.total,0);assert(!r.state.clicks.some(c=>c.kind==='pp'||c.kind==='bp'))});
  await test('Native close after chip selection prevents main wager',async()=>{await setup();const r=await drive({closeAfterMainChip:true});assert.equal(r.state.total,0);assert(!r.state.clicks.some(c=>c.kind==='player'))});
  await test('Native close after main prevents Pair phase',async()=>{await setup();const r=await drive({closeAfterMain:true});assert.equal(r.state.total,100);assert(!r.state.clicks.some(c=>c.kind==='pp'||c.kind==='bp'))});
  await test('A main control disabled after chip selection prevents main wager',async()=>{await setup();const r=await drive({disableAfterMainChip:true});assert.equal(r.state.total,0);assert(!r.state.clicks.some(c=>c.kind==='player'))});
  await test('Unrelated covering dialog never bypasses betting readiness',async()=>{await setup();await page.evaluate(()=>{const el=document.createElement('div');el.style='position:fixed;inset:0;z-index:999;background:#0001';document.body.append(el)});const r=await drive();assert.equal(r.state.clicks.length,0);assert.equal(r.state.total,0)});
  await test('Pair-only signal also handles an already open modal chip selector',async()=>{await setup('Player',false);await page.evaluate(()=>document.getElementById('component').classList.add('open'));const r=await drive();assert.equal(r.state.total,40,JSON.stringify(r));assert(!r.state.clicks.some(c=>['player','banker','tie'].includes(c.kind)))});
  await test('Pair-only with selected 0.20 EUR and collapsed menu uses drawer then closes it before Pair wagers',async()=>{await setup('Player',false);const r=await drive();assert.equal(r.state.total,40,JSON.stringify(r));assert.deepEqual(r.state.clicks.map(c=>c.kind),['chip','pp','bp']);assert.equal(r.state.clicks[0].cents,20);assert.equal(r.events.filter(e=>e.kind==='__BAC_CHIP_SELECTOR_OPEN_COORDS__').length,1)});
  await ctx.close();
 }finally{await browser.close()}
 const out=process.env.TEST_REPORT||path.join(__dirname,'modal_chip_browser_results.json');fs.writeFileSync(out,JSON.stringify({source,sourceSha256:require('node:crypto').createHash('sha256').update(src).digest('hex'),results},null,2));if(results.some(r=>!r.ok))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});
