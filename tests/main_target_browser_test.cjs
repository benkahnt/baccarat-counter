// Production mainTarget/chipVisible/controlHitTarget against local DOM fixtures.
// The browser has every network request blocked.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const src=fs.readFileSync(path.join(__dirname,'../src/main.cpp'),'utf8');
const section=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b,src.indexOf(a)));
const production=section('const chipVisible=','const chipSourceByHit=')+section('const mainTarget=','const tableBetValue=');
const prelude=`const ROOT_WINDOW=window,norm=s=>String(s||'').replace(/\\s+/g,' ').trim(),lower=s=>norm(s).toLowerCase(),pairText=s=>lower(s).replace(/[-–—_]+/g,' ').replace(/\\s+/g,' ').trim();const visible=el=>!!el&&getComputedStyle(el).display!=='none'&&getComputedStyle(el).visibility!=='hidden'&&Number(getComputedStyle(el).opacity||1)>0&&el.getBoundingClientRect().width>0;`;
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const context=await browser.newContext({viewport:{width:1200,height:800},serviceWorkers:'block'});
  await context.route('**/*',r=>r.abort());
  const page=await context.newPage();
  for(const mode of ['main','multiplay'])for(const labels of [['PLAYER','BANKER','TIE'],['SPIELER','BANKIER','REMIS'],['SPIELER','BANKIER','UNENTSCHIEDEN']]){
   const [p,b,t]=labels;
   const button=(id,text)=>`<button id="${id}" class="bet-area"><span>${text}</span><small>8:1</small></button>`;
   await page.setContent(`<style>body{margin:15px}.table{display:flex;gap:3px;width:${mode==='main'?750:250}px}.bet-area{display:flex;flex-direction:column;align-items:center;justify-content:center;width:${mode==='main'?130:40}px;height:${mode==='main'?140:55}px;position:relative;flex-shrink:0;padding:0;font:12px Arial}.bet-area span,.bet-area small{pointer-events:none}#hidden{display:none}</style><div class="table" id="table">${button('pp',p+' PAIR')}${button('player',p)}${button('tie',t)}${button('banker',b)}${button('bp',b+' PAIR')}${button('hidden',t)}</div><div>${button('outside',t)}</div>`);
   await page.evaluate(code=>(0,eval)(code+';window.resolveMain=(side)=>mainTarget(document.getElementById("table"),side)?.closest("button")?.id||null;'),prelude+production);
   assert.deepEqual(await page.evaluate(()=>['Player','Banker','Tie','unknown'].map(resolveMain)),['player','banker','tie',null]);
   // Pair/bonus labels containing a separate exact Tie text node are excluded.
   await page.evaluate(()=>{const t=document.getElementById('tie');t.innerHTML='<span>REMIS</span><small>Bonus</small>';});
   assert.equal(await page.evaluate(()=>resolveMain('Tie')),null);
   // An overlaid/blocked main field cannot produce a trusted click target.
   await page.evaluate(t=>{const el=document.getElementById('tie');el.innerHTML=`<span>${t}</span>`;const r=el.getBoundingClientRect(),overlay=document.createElement('div');overlay.style=`position:fixed;left:${r.left}px;top:${r.top}px;width:${r.width}px;height:${r.height}px;background:black;z-index:10`;document.body.append(overlay);},t);
   assert.equal(await page.evaluate(()=>resolveMain('Tie')),null);
   console.log(`PASS ${mode} ${labels.join('/')} selection, bonus rejection and overlay rejection`);
  }
  await context.close();
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
