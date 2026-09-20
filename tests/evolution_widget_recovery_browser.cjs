const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.join(__dirname,'..'),header=fs.readFileSync(path.join(root,'src/evolution_widget_recovery_script.h'),'utf8');
const raw=header.split('R"EVOREC(')[1].split(')EVOREC"')[0],results=[];
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});try{
const ctx=await browser.newContext({serviceWorkers:'block'});await ctx.route('**/*',r=>r.abort());const page=await ctx.newPage();
async function setup(mode='normal'){await page.goto('about:blank');await page.setContent('<section id="widget"><button data-role="close-button">close</button><div data-role="tablesList"></div></section><button data-role="multiplay-button">Multiplay</button>');await page.evaluate(mode=>{
 window.clock=100000;Date.now=()=>clock;window.events=[];window.closeCount=0;window.opened=0;window.transport={_isDisposed:mode!=='healthy',_isPaused:false};
 window.shoe={shoeTracked:true,shoeTrusted:true,remainingRanks:{A:29},gameId:'g1',lastCompletedGameId:'g1',lastCompletedHandCardCount:4,lastOfficialCardsOut:100,lastTransportTs:mode==='healthy'?clock:clock-30000};
 window.__BCP_LIVE_TRANSPORT_RUNS={offline:{tables:{a:shoe}}};
 const mount=()=>document.querySelector('[data-role="tablesList"]').__reactFiber$fixture={memoizedProps:{value:{multiplayApi:{props:{transport}}}}};mount();
 console.log=s=>{if(s.startsWith('__BAC_EVOLUTION_WIDGET_RECOVERY__'))events.push(JSON.parse(s.slice('__BAC_EVOLUTION_WIDGET_RECOVERY__'.length)));};
 document.querySelector('[data-role="close-button"]').onclick=()=>{closeCount++;document.querySelector('#widget').style.display='none';document.querySelector('[data-role="tablesList"]').remove();};
 document.querySelector('[data-role="multiplay-button"]').onclick=()=>{opened++;if(mode==='noFeed')return;document.querySelector('#widget').style.display='block';const list=document.createElement('div');list.dataset.role='tablesList';document.querySelector('#widget').appendChild(list);transport._isDisposed=false;shoe.lastTransportTs=clock;mount();};
 if(mode==='ambiguous')document.querySelector('#widget').insertAdjacentHTML('beforeend','<button data-role="close-button">other</button>');
 if(mode==='expired')document.body.insertAdjacentHTML('beforeend','<div>SITZUNG ABGELAUFEN: Bitte wegen InaktivitÃ¤t erneut anmelden</div>');
},mode);}
const run=async()=>{await page.evaluate(code=>{clock+=700;(0,eval)(code);},raw.replace('__EVO_RECOVERY_REQUEST__',JSON.stringify({runToken:'offline',request:'r1',stale:false})));const clicks=await page.evaluate(()=>events.filter(e=>['CLOSE','OPEN'].includes(e.action)&&!e.dispatched).map(e=>{e.dispatched=true;return e;}));for(const e of clicks)await page.mouse.click(e.x,e.y);return page.evaluate(()=>({closeCount,opened,events,ranks:shoe.remainingRanks,pending:shoe.continuityPending}));};
async function test(name,fn){await fn();results.push({name,ok:true});console.log('PASS '+name);}
await test('only widget closes and opens once; ranks retained; new feed required',async()=>{await setup();await run();await run();await run();const r=await run();assert.equal(r.closeCount,1);assert.equal(r.opened,1);assert.equal(r.events.at(-1).action,'RECOVERED');assert.deepEqual(r.ranks,{A:29});assert.equal(r.pending.gameId,'g1');assert.equal(page.url(),'about:blank');});
await test('healthy feed never closes without fresh post-start evidence',async()=>{await setup('healthy');const r=await run();assert.equal(r.closeCount,0);assert.equal(r.events.at(-1).action,'FAILED');});
await test('ambiguous close buttons never clicked',async()=>{await setup('ambiguous');const r=await run();assert.equal(r.closeCount,0);assert.equal(r.events.at(-1).action,'FAILED');});
await test('explicit inactivity expiry requires login without reopening',async()=>{await setup('expired');const r=await run();assert.equal(r.closeCount,0);assert.equal(r.opened,0);assert.equal(r.events.at(-1).action,'AUTH_REQUIRED');});
await test('missing new feed times out without repeated UI clicks',async()=>{await setup('noFeed');await run();await run();await page.evaluate(()=>clock+=31000);const r=await run();assert.equal(r.closeCount,1);assert.equal(r.opened,1);assert.equal(r.events.at(-1).action,'FAILED');});
fs.writeFileSync(path.join(root,'.validation/evolution_widget_recovery_results.json'),JSON.stringify({sourceSha256:require('node:crypto').createHash('sha256').update(header).digest('hex'),results},null,2));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});

