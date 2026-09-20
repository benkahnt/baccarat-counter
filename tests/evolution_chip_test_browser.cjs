const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.join(__dirname,'..'),header=fs.readFileSync(path.join(root,'src/evolution_chip_test_script.h'),'utf8');
const script=header.split('R"EVOTEST(')[1].split(')EVOTEST"')[0];
const results=[];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
 const context=await browser.newContext({viewport:{width:900,height:800},serviceWorkers:'block'});
 await context.route('**/*',r=>r.abort());const page=await context.newPage();
 async function fixture(options={}){
  await page.goto('about:blank');
  await page.setContent(`<style>body{margin:0}.list{width:390px;height:560px;overflow:auto}.table{height:180px;margin:8px;border:1px solid}header{height:20px}.row{display:flex}[data-role^="bet-spot"]{width:65px;height:62px;border:1px solid;cursor:pointer} [data-role="chip-stack"]{position:absolute;top:600px;left:80px;width:260px;height:60px} [data-role="revolver-item-list"]{display:none;position:absolute;bottom:65px;background:white;padding:0}li{display:inline-block;width:40px;height:40px} [data-role="chip-stack-toggle"]{width:44px;height:44px;background:orange} [data-role="chip"]{width:36px;height:36px;cursor:pointer}</style>
  <div class="list" data-role="tablesList"></div><div data-role="chip-stack"><ul data-role="revolver-item-list">${[1,5,25,50,100,500].map(n=>`<li data-role="revolver-chip-item"><div data-role="chip" data-value="${n}">${n}</div></li>`).join('')}</ul><div data-role="chip-stack-toggle"><div data-role="selected-chip"><div data-role="chip" data-value="1">1</div></div></div></div>`);
  await page.evaluate(options=>{
   window.testClock=100000;Date.now=()=>window.testClock;window.events=[];window.clicks=[];window.listeners=new Set();window.wagerCount=0;
   const log=console.log;console.log=(s)=>{if(typeof s==='string'&&s.startsWith('__BAC_EVOLUTION_CHIP_TEST__'))events.push(JSON.parse(s.slice('__BAC_EVOLUTION_CHIP_TEST__'.length)));else log(s);};
   window.store={agX:{tableId:'wanted',gameRoundId:'round-1',currency:{code:'EUR'},disposed:false},tableStatus:{isClosed:false},commissionMode:{isNoCommission:false},settings:{tiePays9to1:false},shoe:{stats:{playerWins:30,bankerWins:25,ties:5}},gamePhase:{isBetsOpen:true,isBurning:false,isLongBetting:false},timer:{timeRemaining:15},bets:{bets:{}},betSpot:{minBetSpotValues:{Player:1,Banker:1,Tie:1,PlayerPair:1,BankerPair:1},maxBetSpotValues:{Player:5000,Banker:5000,Tie:200,PlayerPair:200,BankerPair:200}}};
   const component=()=>({props:{value:store}});component.toString=()=>'( )=>jsx(Provider,{store:t})';
   window.api={props:{transport:{_isDisposed:false,_isPaused:false,incomingMessages:{onValue:f=>listeners.add(f),offValue:f=>listeners.delete(f)}}},tables:{getTableInstance:id=>id==='wanted'?{component}:null},chipstack:{chipStackValue:1}};
   const scroller=document.querySelector('[data-role="tablesList"]'),ids=Array.from({length:options.offscreen?14:2},(_,i)=>i===(options.offscreen?12:1)?'wanted':'other'+i);
   scroller.__reactFiber$fixture={memoizedProps:{data:ids,value:{multiplayApi:api}}};
   const spotNames=['PlayerPair','Player','Tie','Banker','BankerPair'];
   for(const id of ids){const el=document.createElement('section');el.className='table';el.dataset.role='table';el.dataset.tableid=id;el.innerHTML=`<header>${id}</header><div class="row">${spotNames.map(s=>`<div data-role="bet-spot-${s}">${s}</div>`).join('')}</div>`;scroller.appendChild(el);
    for(const field of el.querySelectorAll('[data-role^="bet-spot"]'))field.onclick=()=>{
     const spot=field.dataset.role.slice('bet-spot-'.length);window.clicks.push({id,spot,amount:api.chipstack.chipStackValue});window.wagerCount++;
     if(id!=='wanted')throw Error('Wrong table clicked');
     store.bets.bets[spot]=(store.bets.bets[spot]||0)+api.chipstack.chipStackValue;
     if(!options.noAck)window.sendAck(options.reject?'Rejected':'Betting',options.wrongAckGame?'old-round':store.agX.gameRoundId,options.wrongAckTable?'other':'wanted');
    };
   }
   window.sendAck=(status='Betting',gameId=store.agX.gameRoundId,tableId='wanted')=>{for(const f of [...listeners])f({type:'baccarat.playerBettingState',payload:{tableId,gameId,state:{status,currentChips:{...store.bets.bets},rejectedBets:status==='Rejected'?{Banker:{amount:5,error:1}}:{},acceptedBets:status==='Accepted'?Object.fromEntries(Object.entries(store.bets.bets).map(([k,v])=>[k,{amount:v}])):{}}}});};
   const list=document.querySelector('[data-role="revolver-item-list"]');
   document.querySelector('[data-role="chip-stack-toggle"]').onclick=()=>{list.style.display=list.style.display==='block'?'none':'block';};
   for(const chip of list.querySelectorAll('[data-role="chip"]'))chip.onclick=()=>{api.chipstack.chipStackValue=Number(chip.dataset.value);const selected=document.querySelector('[data-role="selected-chip"] [data-role="chip"]');selected.dataset.value=chip.dataset.value;selected.textContent=chip.dataset.value;list.style.display='none';};
   if(options.closed)store.gamePhase.isBetsOpen=false;
   if(options.disposed)api.props.transport._isDisposed=true;
   if(options.under60)store.shoe.stats.playerWins=29;
   if(options.existing)store.bets.bets.Player=1;
   if(options.currency)store.agX.currency.code='USD';
   if(options.limit)store.betSpot.minBetSpotValues.Banker=10;
   if(options.noTimer)store.timer.timeRemaining=undefined;
   if(options.shortTime)store.timer.timeRemaining=3;
  },options);
 }
 let requestOverrides={};
 async function tick(side='Banker'){
  const before=await page.evaluate(()=>events.length);
  const request={runToken:'offline',request:'test-1',tableId:'wanted',mainSide:side,...requestOverrides};
  await page.evaluate(code=>{testClock+=600;(0,eval)(code);},script.replace('__EVO_TEST_REQUEST__',JSON.stringify(request)));
  const newEvents=await page.evaluate(n=>events.slice(n),before);
  for(const event of newEvents.filter(e=>e.action==='CLICK'))await page.mouse.click(event.x,event.y);
  return newEvents;
 }
 async function finish(side='Banker',steps=40){for(let n=0;n<steps;n++){await tick(side);const state=await page.evaluate(()=>({done:window.__BCP_EVOLUTION_CHIP_TEST__?.done,index:window.__BCP_EVOLUTION_CHIP_TEST__?.index,total:window.__BCP_EVOLUTION_CHIP_TEST__?.stepCount}));if(state.done)break;if(state.index===state.total)await page.evaluate(()=>sendAck('Accepted'));}return page.evaluate(()=>({events,clicks,wagerCount,listeners:listeners.size}));}
 async function test(name,fn){requestOverrides={};await fn();results.push({name,ok:true});console.log('PASS '+name);}
 for(const side of ['Player','Banker','Tie'])await test(side+' main acknowledged before both pairs',async()=>{await fixture();const r=await finish(side);assert.deepEqual(r.clicks,[{id:'wanted',spot:side,amount:5},{id:'wanted',spot:'PlayerPair',amount:1},{id:'wanted',spot:'BankerPair',amount:1}]);assert.equal(r.events.at(-1).action,'SUCCESS');assert.equal(r.listeners,0);});
 await test('offscreen selected table is scrolled into view',async()=>{await fixture({offscreen:true});const r=await finish();assert.equal(r.events.at(-1).action,'SUCCESS');assert(r.clicks.every(c=>c.id==='wanted'));});
 for(const flag of ['disposed','existing','currency','limit'])await test(flag+' prevents all wagers',async()=>{await fixture({[flag]:true});const r=await finish();assert.equal(r.wagerCount,0);assert.equal(r.events.at(-1).action,'FAILED');});
 await test('selected Evolution table supports technical test below hand 60',async()=>{await fixture({under60:true});const r=await finish();assert.deepEqual(r.clicks,[{id:'wanted',spot:'Banker',amount:5},{id:'wanted',spot:'PlayerPair',amount:1},{id:'wanted',spot:'BankerPair',amount:1}]);assert.equal(r.events.at(-1).action,'SUCCESS');});
 for(const flag of ['closed','noTimer','shortTime'])await test(flag+' waits without wagering',async()=>{await fixture({[flag]:true});const r=await finish();assert.equal(r.wagerCount,0);assert.equal(r.events.at(-1).action,'WAIT');});
 await test('opening betting window releases the pending request',async()=>{await fixture({closed:true});await tick();await page.evaluate(()=>store.gamePhase.isBetsOpen=true);assert.equal((await finish()).events.at(-1).action,'SUCCESS');});
 for(const flag of ['noAck','wrongAckGame','wrongAckTable','reject'])await test(flag+' stops after one main wager without retry',async()=>{await fixture({[flag]:true});const r=await finish();assert.equal(r.wagerCount,1);assert.equal(r.events.at(-1).action,'FAILED');});
 await test('round change after main never wagers on next round',async()=>{await fixture();for(let n=0;n<12;n++){await tick();if(await page.evaluate(()=>wagerCount>0))break;}await page.evaluate(()=>store.agX.gameRoundId='round-2');const r=await finish();assert.equal(r.wagerCount,1);assert.equal(r.events.at(-1).action,'FAILED');});
 await test('closed window after main stops pair clicks',async()=>{await fixture();for(let n=0;n<12;n++){await tick();if(await page.evaluate(()=>wagerCount>0))break;}await page.evaluate(()=>store.gamePhase.isBetsOpen=false);const r=await finish();assert.equal(r.wagerCount,1);assert.equal(r.events.at(-1).action,'FAILED');});
 await test('configured 10/2/2 amounts use exact repeated denominations',async()=>{await fixture();requestOverrides={signal:true,targetGameId:'round-1',mainCents:1000,pairCents:200};const r=await finish();assert.equal(r.events.at(-1).action,'SUCCESS');assert.deepEqual(r.clicks.map(c=>[c.spot,c.amount]),[['Banker',5],['Banker',5],['PlayerPair',1],['PlayerPair',1],['BankerPair',1],['BankerPair',1]]);});
 await test('unsupported 0.20 stake is never rounded up',async()=>{await fixture();requestOverrides={signal:true,targetGameId:'round-1',mainCents:100,pairCents:20};const r=await finish();assert.equal(r.wagerCount,0);assert.equal(r.events.at(-1).action,'FAILED');});
 await test('signal cannot migrate to a later round',async()=>{await fixture();requestOverrides={signal:true,targetGameId:'previous',mainCents:500,pairCents:100};const r=await finish();assert.equal(r.wagerCount,0);assert.equal(r.events.at(-1).action,'FAILED');});
 await test('pair-only signal below hand 60',async()=>{await fixture({under60:true});requestOverrides={signal:true,targetGameId:'round-1',mainCents:0,pairCents:100};const r=await finish();assert.equal(r.events.at(-1).action,'SUCCESS');assert.deepEqual(r.clicks.map(c=>c.spot),['PlayerPair','BankerPair']);});
 await test('main requirement enforced at hand 60',async()=>{await fixture();requestOverrides={signal:true,targetGameId:'round-1',mainCents:0,pairCents:100};const r=await finish();assert.equal(r.wagerCount,0);assert.equal(r.events.at(-1).action,'FAILED');});
 await test('virtualized target is mounted after scrolling',async()=>{await fixture({offscreen:true});await page.evaluate(()=>{const list=document.querySelector('[data-role="tablesList"]'),tile=document.querySelector('[data-tableid="wanted"]');tile.remove();list.addEventListener('scroll',()=>{if(!tile.isConnected){list.appendChild(tile);tile.scrollIntoView({block:'center'});}});});const r=await finish();assert.equal(r.events.at(-1).action,'SUCCESS');assert(r.clicks.every(c=>c.id==='wanted'));});
 await test('overlay blocks wager without guessing coordinates',async()=>{await fixture();await page.evaluate(()=>{const el=document.createElement('div');el.style='position:fixed;inset:0;background:#eee;z-index:99999';document.body.appendChild(el);});const r=await finish();assert.equal(r.wagerCount,0);});
 fs.mkdirSync(path.join(root,'.validation'),{recursive:true});fs.writeFileSync(path.join(root,'.validation/evolution_chip_test_browser_results.json'),JSON.stringify({sourceSha256:require('node:crypto').createHash('sha256').update(header).digest('hex'),results},null,2));
 }finally{await browser.close();}
 console.log('TOTAL '+results.length+' passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
