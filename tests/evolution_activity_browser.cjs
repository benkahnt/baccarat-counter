const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.join(__dirname,'..'),header=fs.readFileSync(path.join(root,'src/evolution_activity_script.h'),'utf8');
const raw=header.split('R"EVOACT(')[1].split(')EVOACT"')[0],results=[];
(async()=>{const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});try{
const context=await browser.newContext({viewport:{width:1000,height:800},serviceWorkers:'block'});
await context.route('**/*',r=>r.abort());const page=await context.newPage();
async function setup(){await page.goto('about:blank');await page.setContent('<a id="headerLogo" style="display:block;width:100px;height:40px">Logo</a><iframe id="main" style="width:400px;height:250px"></iframe><iframe id="multi" style="width:400px;height:250px"></iframe>');
await page.evaluate(()=>{window.events=[];window.clicks=0;console.log=x=>events.push(JSON.parse(x.slice('__BAC_EVOLUTION_ACTIVITY__'.length)));
 const main=document.querySelector('#main').contentDocument,multi=document.querySelector('#multi').contentDocument;
 main.body.innerHTML='<button data-role="menu-button" style="display:none">hidden</button><button data-role="help-button" style="width:60px;height:40px">Help</button>';
 multi.body.innerHTML='<button data-role="menu-button" style="width:60px;height:40px">Menu</button>';
 for(const d of [document,main,multi])d.addEventListener('click',()=>window.clicks++);
});}
async function run(){await page.evaluate(code=>(0,eval)(code),raw.replace('__EVO_ACTIVITY_REQUEST__',JSON.stringify({runToken:'test',sequence:1})));return page.evaluate(()=>events);}
async function test(name,fn){await setup();await fn();results.push({name,ok:true});console.log('PASS '+name);}
await test('parent, main table and MULTIPLAY each receive trusted movement without clicks',async()=>{const events=await run();assert.deepEqual(events.map(x=>x.control),['headerLogo','help-button','menu-button']);for(const e of events)await page.mouse.move(e.x,e.y);const r=await page.evaluate(()=>({clicks,proof:[document,document.querySelector('#main').contentDocument,document.querySelector('#multi').contentDocument].map(d=>d.__BCP_ACTIVITY_PROOF__.trustedMoveAt)}));assert.equal(r.clicks,0);assert(r.proof.every(n=>n>0));});
await test('hidden first control does not suppress visible main-table header',async()=>{const events=await run();assert(events.some(e=>e.control==='help-button'));});
await test('covered main-table header is never targeted',async()=>{await page.evaluate(()=>{const d=document.querySelector('#main').contentDocument;d.body.insertAdjacentHTML('beforeend','<div style="position:fixed;inset:0;background:white;z-index:999"></div>');});assert(!(await run()).some(e=>e.control==='help-button'));});
await test('expired session stops all activity before emitting coordinates',async()=>{await page.evaluate(()=>document.querySelector('#main').contentDocument.body.insertAdjacentHTML('beforeend','<div>SITZUNG ABGELAUFEN</div>'));assert.equal((await run()).length,0);});
await test('missing headers produce diagnostic only, never a betting-field fallback',async()=>{await page.evaluate(()=>{for(const d of [document,document.querySelector('#main').contentDocument,document.querySelector('#multi').contentDocument])for(const e of d.querySelectorAll('a,button'))e.remove();});const events=await run();assert.equal(events.length,1);assert.equal(events[0].slot,-1);assert.equal(events[0].x,undefined);});
fs.writeFileSync(path.join(root,'.validation/evolution_activity_browser_results.json'),JSON.stringify({sourceSha256:require('node:crypto').createHash('sha256').update(header).digest('hex'),results},null,2));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
