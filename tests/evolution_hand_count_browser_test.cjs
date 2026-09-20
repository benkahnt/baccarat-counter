const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const src=fs.readFileSync(path.join(__dirname,'../src/main.cpp'),'utf8');
const a=src.indexOf('const evolutionOutcomeCounts='),b=src.indexOf('const emitLiveTableStatus=',a);
const helpers=src.slice(a,b);
const captured=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/evolution_outcome_capture.json'),'utf8'));
const results=[];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const ctx=await browser.newContext({viewport:{width:900,height:800},serviceWorkers:'block'});
  await ctx.route('**/*',r=>r.abort());const page=await ctx.newPage();
  const fixtures=[
   ['screenshot Speed Baccarat 2','<footer>P 13 B 8 T 7</footer>',28],
   ['screenshot Speed Baccarat E','<footer><span>P</span><span>16</span><span>B</span><span>16</span><span>T</span><span>2</span></footer>',34],
   ['SVG letter icons','<footer><svg aria-label="P"></svg>13<svg aria-label="B"></svg>8<svg aria-label="T"></svg>7</footer>',28],
   ['SVG symbol refs','<footer><svg><use href="#baccarat-player"/></svg>13<svg><use href="#baccarat-banker"/></svg>8<svg><use href="#baccarat-tie"/></svg>7</footer>',28],
   ['new shoe zero','<footer>P 0 B 0 T 0</footer>',0],
   ['missing Tie','<footer>P 13 B 8</footer>',null],
   ['card values and timer','<div>PLAYER 8 BANKER 3 TIE 8:1</div><div>P PAIR B PAIR</div><span>9</span>',null],
   ['negative counter','<footer>P -1 B 8 T 7</footer>',null],
   ['fractional counter','<footer>P 1.5 B 8 T 7</footer>',null],
   ['impossible deck total','<footer>P 100 B 80 T 7</footer>',null],
   ['conflicting visible groups','<footer>P 13 B 8 T 7</footer><footer>P 14 B 8 T 7</footer>',null],
   ['hidden old group','<footer style="display:none">P 14 B 8 T 7</footer><footer>P 13 B 8 T 7</footer>',28],
   ['unlabelled values','<footer>13 8 7</footer>',null],
  ];
  for(const [i,c] of captured.dom.entries())fixtures.push(['capture DOM '+(i+1),c.text,c.total]);
  for(const [name,body,expected] of fixtures){
   await page.setContent(`<style>section{width:350px}svg{width:15px;height:15px}</style><section data-role="table" data-tableid="one" id="one">${body}</section><section data-role="table" data-tableid="two"><footer>P 25 B 25 T 5</footer></section>`);
   const actual=await page.evaluate(code=>(0,eval)(code+';evolutionOutcomeCounts(document.getElementById("one"))'),helpers);
   assert.equal(actual?.total??null,expected,name);results.push({name,ok:true});console.log('PASS '+name);
  }
  const state=await page.evaluate(code=>(0,eval)(code+`;(()=>{
   const original=Date.now;Date.now=()=>6001;
   const stale=evolutionDisplayCounts({providerOutcomeCounts:{total:28,seenAt:1000}});
   const fresh=evolutionDisplayCounts({providerOutcomeCounts:{total:28,seenAt:1001}});
   Date.now=original;return {stale,fresh};})()`),helpers);
  assert.equal(state.stale.total,28);assert.equal(state.fresh.total,28);
  assert.equal(state.stale.ageMs,5001);
  results.push({name:'confirmed counts survive quiet periods beyond five seconds',ok:true});
  for(const sample of captured.transport){
   const got=await page.evaluate(({helpers,msg})=>(0,eval)(helpers+`;(()=>{
     const st={shoeHands:null,shoeTracked:false,shoeTrusted:false,lastTransportTs:Date.now()};
     const ok=evolutionApplyShoeCounts(st,${JSON.stringify(msg)});
     return {ok,counts:evolutionDisplayCounts(st),shoeHands:st.shoeHands,shoeTracked:st.shoeTracked};
   })()`),{helpers,msg:sample.message});
   assert(got.ok);assert.equal(got.counts.total,sample.message.payload.stats.gameCount);
   assert.equal(got.counts.source,'evolution-encodedShoeState-gameCount');
   assert.equal(got.shoeHands,null);assert.equal(got.shoeTracked,false);
   results.push({name:'capture internal '+sample.tableName,ok:true});
   console.log('PASS internal gameCount '+sample.tableName+' = '+got.counts.total);
  }
  const rules=await page.evaluate(({helpers,msg})=>(0,eval)(helpers+`;(()=>{
    const msg=${JSON.stringify(msg)}, now=Date.now();
    const st={lastTransportTs:now,providerOutcomeCounts:{player:1,banker:1,tie:1,total:3,seenAt:now}};
    evolutionApplyShoeCounts(st,msg);
    const preferred=evolutionDisplayCounts(st).total;
    const bad=JSON.parse(JSON.stringify(msg));bad.payload.stats.gameCount++;
    const mismatch=evolutionApplyShoeCounts(st,bad);
    bad.payload.stats.gameCount--;bad.payload.history_v2.pop();
    const historyMismatch=evolutionApplyShoeCounts(st,bad);
    const old=JSON.parse(JSON.stringify(msg));old.timestamp--;
    const older=evolutionApplyShoeCounts(st,old);
    const nextShoe={lastTransportTs:now,providerCountsMinTimestamp:msg.timestamp+1};
    const afterReset=evolutionApplyShoeCounts(nextShoe,msg);
    st.lastTransportTs=now-5001;
    const fallback=evolutionDisplayCounts(st).total;
    const zero={timestamp:msg.timestamp+1,payload:{stats:{gameCount:0,playerWins:0,bankerWins:0,ties:0},history_v2:[]}};
    const fresh={lastTransportTs:now};evolutionApplyShoeCounts(fresh,zero);
    return {preferred,mismatch,historyMismatch,older,afterReset,fallback,zero:evolutionDisplayCounts(fresh).total};
  })()`),{helpers,msg:captured.transport[0].message});
  assert.deepEqual(rules,{preferred:56,mismatch:false,historyMismatch:false,older:false,afterReset:false,fallback:56,zero:0});
  results.push({name:'internal priority survives idle transport; validation, reset boundary and zero',ok:true});
  const routeStart=src.indexOf('const applyLiveTransportMessage=');
  const router=src.slice(src.indexOf('const evolutionCheckContinuity='),src.indexOf('const getLiveRun='))+
    src.slice(routeStart,src.indexOf('const updateLiveTransportCountdowns=',routeStart));
  const routed=await page.evaluate(({helpers,router,msg})=>{
   return (0,eval)(helpers+`;(()=>{
    const state={shoeHands:null,shoeTracked:false,shoeTrusted:false}, emissions=[];
    const getLiveRun=()=>({}),getLiveTable=()=>state;
    const emitLiveTableStatus=st=>emissions.push(evolutionDisplayCounts(st));
    ${router}
    const msg=${JSON.stringify(msg)},tid=msg.payload.tableId;
    applyLiveTransportMessage(msg,[tid],new Map([[tid,'Captured table']]));
    const ignored=JSON.parse(JSON.stringify(msg));ignored.payload.tableId='other';
    applyLiveTransportMessage(ignored,[tid],new Map());
    return {emissions,tracked:state.shoeTracked,hands:state.shoeHands};
   })()`);
  },{helpers,router,msg:captured.transport[0].message});
  assert.equal(routed.emissions.length,1);assert.equal(routed.emissions[0].total,56);
  assert.equal(routed.tracked,false);assert.equal(routed.hands,null);
  results.push({name:'production transport router handles subscribed offscreen table only',ok:true});
  const progression=await page.evaluate(({helpers,msg})=>(0,eval)(helpers+`;(()=>{
   const st={lastTransportTs:Date.now()},msg=${JSON.stringify(msg)};
   evolutionApplyShoeCounts(st,msg);
   const next=JSON.parse(JSON.stringify(msg));next.timestamp+=1000;
   next.payload.stats.gameCount++;next.payload.stats.playerWins++;
   next.payload.history_v2.push({winner:'Player'});
   evolutionApplyShoeCounts(st,next);
   const advanced=evolutionDisplayCounts(st).total;
   evolutionApplyShoeCounts(st,next);
   const duplicate=evolutionDisplayCounts(st).total;
   evolutionApplyShoeCounts(st,msg);
   return {advanced,duplicate,oldReplay:evolutionDisplayCounts(st).total};
  })()`),{helpers,msg:captured.transport[0].message});
  assert.deepEqual(progression,{advanced:57,duplicate:57,oldReplay:57});
  results.push({name:'next hand advances once, duplicate and older snapshots do not increment',ok:true});
  const retained=await page.evaluate(({helpers,msg})=>(0,eval)(helpers+`;(()=>{
   const st={lastTransportTs:Date.now()},msg=${JSON.stringify(msg)};
   evolutionApplyShoeCounts(st,msg);
   st.providerShoeCounts.seenAt-=180000;st.lastTransportTs-=180000;
   const idle=evolutionDisplayCounts(st);
   const neverObserved=evolutionDisplayCounts({});
   return {total:idle.total,age:idle.ageMs,neverObserved};
  })()`),{helpers,msg:captured.transport[0].message});
  assert.equal(retained.total,56);assert(retained.age>=180000);assert.equal(retained.neverObserved,null);
  results.push({name:'three-minute idle retains last confirmed count and true observation age; new run starts unknown',ok:true});
  const resetStart=src.indexOf('const initTrackedShoe=');
  const reset=src.slice(resetStart,src.indexOf('const currentPhysicalCardsOut=',resetStart));
  const resetResult=await page.evaluate(({helpers,reset,msg})=>(0,eval)(helpers+`;(()=>{
   const RUN_TOKEN='offline',freshRankComposition=()=>({A:32});
   ${reset}
   const msg=${JSON.stringify(msg)},st={lastMessageTimestamp:msg.timestamp+1};
   evolutionApplyShoeCounts(st,msg);
   st.providerOutcomeCounts={player:10,banker:10,tie:2,total:22,seenAt:Date.now()};
   initTrackedShoe(st,'offline-new-shoe',0);
   return {display:evolutionDisplayCounts(st),hands:st.shoeHands,oldReplay:evolutionApplyShoeCounts(st,msg)};
  })()`),{helpers,reset,msg:captured.transport[0].message});
  assert.deepEqual(resetResult,{display:null,hands:0,oldReplay:false});
  results.push({name:'production shoe reset clears both cached sources and rejects prior shoe replay',ok:true});
  const scanStart=src.indexOf('const scanTable=');
  const scanPrefix=src.slice(scanStart,src.indexOf('  const cardMap=new Map();',scanStart))+'};';
  await page.setContent('<section data-role="table" data-tableid="one" id="one"><footer>P 13 B 8 T 7</footer></section>');
  const domRetained=await page.evaluate(({helpers,scanPrefix})=>(0,eval)(helpers+`;(()=>{
   let tables=0;const st={},getLiveRun=()=>({}),getLiveTable=()=>st,emitLiveTableStatus=()=>{};
   ${scanPrefix}
   const tile=document.getElementById('one');scanTable(tile,'offline');
   const first=evolutionDisplayCounts(st).total;
   tile.innerHTML='<p>Betting closed</p>';scanTable(tile,'offline');
   return {first,after:evolutionDisplayCounts(st).total};
  })()`),{helpers,scanPrefix});
  assert.deepEqual(domRetained,{first:28,after:28});
  results.push({name:'production DOM scan retains confirmed counters while summary is absent',ok:true});
  await ctx.close();
 }finally{await browser.close()}
 if(process.env.TEST_REPORT)fs.writeFileSync(process.env.TEST_REPORT,JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
