const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.join(__dirname,'..'),src=fs.readFileSync(path.join(root,'src/main.cpp'),'utf8');
const block=src.split('    std::string EvolutionSessionWatchScript() const {')[1].split('    std::string PragmaticSessionWatchScript() const {')[0];
const script=block.split('R"JS(')[1]+'offline'+block.split('R"JS(')[2].split(')JS";')[0];
const executable=script.replace(')JS" + runTokenJs + ','');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const ctx=await browser.newContext({serviceWorkers:'block'});await ctx.route('**/*',r=>r.abort());
  const page=await ctx.newPage();await page.setContent('<div data-role="tablesList"></div>');
  await page.evaluate(()=>{
   window.time=100000;Date.now=()=>time;window.events=[];window.transport={_isDisposed:false};
   document.querySelector('[data-role="tablesList"]').__reactFiber$fixture={memoizedProps:{value:{multiplayApi:{props:{transport}}}}};
   console.log=s=>{if(s.startsWith('__BAC_EVOLUTION_SESSION_WATCH__'))events.push(JSON.parse(s.slice('__BAC_EVOLUTION_SESSION_WATCH__'.length)));};
  });
  const run=()=>page.evaluate(executable),disposedCount=()=>page.evaluate(()=>events.filter(e=>e.action==='FEED_DISPOSED').length);
  assert.equal(await run(),'evolution-session:ok');assert.equal(await disposedCount(),0);
  await page.evaluate(()=>transport._isDisposed=true);assert.equal(await run(),'evolution-session:transport-disposed');assert.equal(await disposedCount(),0);
  await page.evaluate(()=>time+=3999);await run();assert.equal(await disposedCount(),0);
  await page.evaluate(()=>time+=1);await run();assert.equal(await disposedCount(),1);
  await page.evaluate(()=>time+=9999);await run();assert.equal(await disposedCount(),1);
  await page.evaluate(()=>time+=1);await run();assert.equal(await disposedCount(),2);
  await page.evaluate(()=>transport._isDisposed=false);assert.equal(await run(),'evolution-session:ok');
  await page.evaluate(()=>{transport._isDisposed=true;time+=10000;});await run();assert.equal(await disposedCount(),2);
  await page.evaluate(()=>{time+=3999;__BCP_EVOLUTION_SESSION_WATCH__.runToken='previous';});await run();assert.equal(await disposedCount(),2);
  await page.evaluate(()=>time+=4000);await run();assert.equal(await disposedCount(),3);
  assert.equal(await page.evaluate(()=>events.some(e=>e.action==='ERROR')),false);
  await page.evaluate(()=>{document.body.insertAdjacentHTML('beforeend','<div>SITZUNG ABGELAUFEN Ihre Spielsitzung wurde wegen zu langer Inaktivität ausgesetzt. Bitte melden Sie sich erneut auf der Website an.</div>');time+=10001;});
  await run();assert.equal(await page.evaluate(()=>events.some(e=>e.action==='SESSION_TERMINATED'&&e.reason==='inactivity-login-required')),true);
  // A provider popup may outlive its list/React transport. It must still stop
  // recovery and must never fall through to a stale Continue button.
  await page.evaluate(()=>{document.querySelector('[data-role="tablesList"]').remove();window.clicks=0;document.body.insertAdjacentHTML('beforeend','<button onclick="window.clicks++">Weiterspielen</button>');events=[];time+=10000;});
  assert.equal(await run(),'evolution-session:login-required');
  assert.equal(await page.evaluate(()=>events.filter(e=>e.action==='SESSION_TERMINATED').length),1);
  await run();assert.equal(await page.evaluate(()=>events.filter(e=>e.action==='SESSION_TERMINATED').length),1);
  assert.equal(await page.evaluate(()=>clicks),0);
  // Also detect the main-table popup while a list still reports a healthy
  // transport; a cross-frame teardown does not happen atomically.
  await page.evaluate(()=>{document.body.insertAdjacentHTML('afterbegin','<div data-role="tablesList"></div>');transport._isDisposed=false;document.querySelector('[data-role="tablesList"]').__reactFiber$fixture={memoizedProps:{value:{multiplayApi:{props:{transport}}}}};events=[];time+=10000;});
  assert.equal(await run(),'evolution-session:login-required');
  assert.equal(await page.evaluate(()=>events.some(e=>e.action==='SESSION_TERMINATED')),true);
  assert.equal(await page.evaluate(()=>clicks),0);
  fs.writeFileSync(path.join(root,'.validation/evolution_disposed_feed_results.json'),JSON.stringify({ok:true,sourceSha256:require('node:crypto').createHash('sha256').update(src).digest('hex'),explicitGlobalExpiryDetected:true,expiryWithoutTransportDetected:true,expiryBeforeTransportTeardownDetected:true,expiryNotificationThrottled:true,expiredContinueNeverClicked:true},null,2));
  console.log('PASS production disposed-feed detection: healthy stream, four-second confirmation, ten-second log throttle, recovery and run reset');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
