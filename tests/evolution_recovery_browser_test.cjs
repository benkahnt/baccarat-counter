// Execute the production recovery functions against offline DOM fixtures.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.join(__dirname,'..'),src=fs.readFileSync(path.join(root,'src/main.cpp'),'utf8');
const start=src.indexOf('const recoveryVisible=',src.indexOf('std::string PragmaticProbeScript'));
const end=src.indexOf('const attrObj=',start);
assert(start>0&&end>start);const helpers=src.slice(start,end),results=[];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const ctx=await browser.newContext({serviceWorkers:'block'});
  await ctx.route('**/*',r=>r.fulfill({status:200,contentType:'text/html',body:'<html><body></body></html>'}));
  const page=await ctx.newPage(),target='https://betify2.so/de/play/149977-speed-baccarat-2';
  async function test(name,{html='',stage=4,paused=false,evolution=true,url='https://betify2.so/de/',aged=false}={},expected){
   await page.goto(url);await page.setContent(html);
   const got=await page.evaluate(({helpers,stage,paused,evolution,target,aged})=>{
    const code=`(()=>{const RUN_TOKEN='offline',root=window,RECOVERY_STAGE=${stage},EVOLUTION_LAUNCH=${evolution},EVOLUTION_PAUSED=${paused},AUTH_BALANCE_RECENT=false,TARGET_GAME_URL=${JSON.stringify(target)};
     const compact=s=>String(s||'').replace(/\\s+/g,' ').trim();const events=[];const recoveryEmit=(action)=>events.push(action);
     ${helpers}
     if(${aged})root.__BCP_PRAGMATIC_LOGIN_GUARD={offline:{playFrameSeenAt:Date.now()-4000}};
     runRecoveryStep(window,document,location.href);return events;})()`;
    return (0,eval)(code);
   },{helpers,stage,paused,evolution,target,aged});
   assert.deepEqual(got,expected,name);
   if(evolution)assert.equal(page.url(),url,name+' must not navigate directly');
   results.push({name,ok:true});console.log('PASS '+name);
  }
  await test('Evolution requests native navigation once',{},['EVOLUTION_PLAY_NAVIGATE_REQUEST']);
  await test('stage 3 requests native navigation',{stage:3},['EVOLUTION_PLAY_NAVIGATE_REQUEST']);
  for(const stage of [0,1,2,3,4]){
   await test('visible redirect stops stage '+stage,{stage,html:'<div role="alert">Redirect error,EvoSW: no url or ssid received</div><button>Login</button>'},['EVOLUTION_LAUNCH_ERROR']);
   await test('paused launch blocks stage '+stage,{stage,paused:true,html:'<button>Login</button>'},[]);
  }
  await test('hidden stale error is ignored',{html:'<div role="alert" style="display:none">Redirect error,EvoSW: no url or ssid received</div>'},['EVOLUTION_PLAY_NAVIGATE_REQUEST']);
  await test('unrelated alert is ignored',{html:'<div role="alert">Connection restored</div>'},['EVOLUTION_PLAY_NAVIGATE_REQUEST']);
  await test('target page waits without duplicate navigation',{url:target},['WAIT_PLAY_PAGE']);
  await test('new iframe waits for runtime',{url:target,html:'<iframe id="gameFrame"></iframe>'},['WAIT_PLAY_RUNTIME']);
  await test('stable iframe releases provider bootstrap',{url:target,html:'<iframe id="gameFrame"></iframe>',aged:true},['PLAY_PAGE_READY']);
  await test('Pragmatic retains existing navigation',{evolution:false},['PLAY_NAVIGATE']);
  fs.mkdirSync(path.join(root,'.validation'),{recursive:true});
  fs.writeFileSync(path.join(root,'.validation/evolution_recovery_browser_results.json'),JSON.stringify({sourceSha256:require('node:crypto').createHash('sha256').update(src).digest('hex'),results},null,2));
 }finally{await browser.close();}
 console.log('TOTAL '+results.length+' passed');
})().catch(e=>{console.error(e);process.exitCode=1;});
