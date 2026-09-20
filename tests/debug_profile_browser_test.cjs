const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const localData=fs.mkdtempSync(path.join(root,'.validation','cleanup-browser-'));
const profile=path.join(localData,'BaccaratCounterChrome');
const launch=async()=>{
 const ctx=await chromium.launchPersistentContext(profile,{headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',serviceWorkers:'block'});
 await ctx.route('**/*',route=>route.fulfill({status:200,contentType:'text/html',body:'<!doctype html><title>Offline cleanup fixture</title>'}));
 return ctx;
};
(async()=>{
 let ctx=await launch();
 try{
  await ctx.addCookies([{name:'session_fixture',value:'test-only',url:'https://cleanup.test'},{name:'other_fixture',value:'test-only',url:'https://other.test'}]);
  const p=ctx.pages()[0];await p.goto('https://cleanup.test');
  await p.evaluate(async()=>{
   localStorage.setItem('session_fixture','test-only');
   const c=await caches.open('old-cache');await c.put('/old',new Response('test-only'));
   await new Promise((resolve,reject)=>{const r=indexedDB.open('old-db',1);r.onupgradeneeded=()=>r.result.createObjectStore('data');r.onsuccess=()=>{r.result.close();resolve()};r.onerror=()=>reject(r.error)});
  });
  assert.equal((await ctx.cookies()).length,2);
 }finally{await ctx.close()}
 const quote=s=>"'"+s.replace(/'/g,"''")+"'";
 const cmd='. '+quote(path.join(root,'reset_chrome_debug_data.ps1'))+'; Reset-DebugSiteData '+quote(localData);
 cp.execFileSync('powershell.exe',['-NoProfile','-ExecutionPolicy','Bypass','-Command',cmd],{encoding:'utf8',timeout:30000,windowsHide:true});
 ctx=await launch();let state;
 try{
  assert.equal((await ctx.cookies()).length,0);
  const p=ctx.pages()[0];await p.goto('https://cleanup.test');
  state=await p.evaluate(async()=>({localStorage:localStorage.length,caches:(await caches.keys()).length,indexedDB:(await indexedDB.databases()).length}));
  assert.deepEqual(state,{localStorage:0,caches:0,indexedDB:0});
 }finally{await ctx.close()}
 const result={ok:true,cookiesAcrossTwoOriginsCleared:true,...state,liveUserProfileTouched:false};
 fs.writeFileSync(path.join(root,'.validation/debug_profile_browser_results.json'),JSON.stringify(result,null,2));
 console.log('PASS real isolated Chrome restart: both cookies, Local Storage, CacheStorage and IndexedDB absent');
})().catch(e=>{console.error(e);process.exitCode=1});
