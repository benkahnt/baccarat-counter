// Production focus helpers and selection sequence, offline only.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const src=fs.readFileSync(path.join(__dirname,'../src/main.cpp'),'utf8');
const section=(a,b)=>{const i=src.indexOf(a,src.indexOf('void PragmaticFocusSignalTable(')),j=src.indexOf(b,i);assert(i>=0&&j>i,a);return src.slice(i,j)};
const production=section('const visible=el=>{','const pairText=s=>')+
  section('const sought=isMainBaccarat','const immediateTargets=pairTargets(target);');
const results=[];
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{
  const ctx=await browser.newContext({viewport:{width:1000,height:700},serviceWorkers:'block'});
  await ctx.route('**/*',r=>r.abort());
  const page=await ctx.newPage();
  for(const variant of ['current-name-resolver','legacy-table-id','no-visible-game-id']){
   const tile=n=>`<section class="table-card" id="tile${n}" ${variant==='legacy-table-id'?`data-role="table" data-tableid="${n===17?'bcpirpmfpebc1908':'other'+n}"`:''}><header onclick="window.headerClicks.push(${n})">Speed Baccarat ${n}</header><div class="row"><button onclick="window.wagerClicks++">S PAAR</button><button onclick="window.wagerClicks++">SPIELER</button><button onclick="window.wagerClicks++">REMIS</button><button onclick="window.wagerClicks++">BANKIER</button><button onclick="window.wagerClicks++">B PAAR</button></div>${variant==='no-visible-game-id'?'':`<footer>ID: ${n===17?'18071460019':String(18071461000+n)}</footer>`}</section>`;
   await page.setContent(`<style>body{margin:0}.list{position:absolute;left:710px;top:35px;width:260px;height:580px;overflow:auto}.table-card{height:190px;margin:6px;background:#ccc}header{height:25px}.row{display:flex}button{width:45px;height:50px;padding:0}</style><div class="list" data-testid="virtuoso-scroller">${Array.from({length:20},(_,i)=>tile(i+1)).join('')}</div>`);
   const result=await page.evaluate(async({production,variant})=>{
    window.headerClicks=[];window.wagerClicks=0;window.events=[];
    return await (0,eval)(`(async()=>{
const ROOT_WINDOW=window,TARGET_ID='bcpirpmfpebc1908',TARGET_NAME='Speed Baccarat 17',SOURCE_GAME='18071460019',RUN_TOKEN='offline',REQUEST_TOKEN='1';
const isMulti=true,isMainBaccarat=false,ALL_TABLES_AUTO=false;
const norm=s=>String(s||'').replace(/\\s+/g,' ').trim();
const tableTextMatches=t=>t===TARGET_NAME||t.startsWith(TARGET_NAME+' ');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
const toRootViewportPoint=(x,y)=>({x,y});
const fail=reason=>{throw new Error(reason)};
const oldLog=console.log;console.log=msg=>events.push(msg);
${production}
console.log=oldLog;
return {target:target.id,selected,rectTop:target.getBoundingClientRect().top,scroll:document.querySelector('.list').scrollTop,headers:headerClicks,wagers:wagerClicks,events};
})()`);
   },{production,variant});
   assert.equal(result.target,'tile17');
   assert.equal(result.selected,true);
   assert.deepEqual(result.headers,[17]);
   assert.equal(result.wagers,0);
   assert(result.scroll>2000);
   assert(result.rectTop>=30&&result.rectTop<65);
   assert(result.events.some(e=>e.startsWith('__BAC_TILE_ACTIVATE_COORDS__')));
   results.push({name:variant,ok:true});console.log('PASS Speed Baccarat 17 focus: '+variant+', scroll into view, header only, zero wager clicks');
  }
  await ctx.close();
 }finally{await browser.close()}
 if(process.env.TEST_REPORT)fs.writeFileSync(process.env.TEST_REPORT,JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
