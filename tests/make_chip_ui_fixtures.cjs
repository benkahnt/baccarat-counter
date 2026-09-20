const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const target=path.resolve(__dirname,'../.validation/chip-ui');fs.mkdirSync(target,{recursive:true});
const browserTest=fs.readFileSync(path.join(__dirname,'chip_selector_browser_test.cjs'),'utf8');
const fixtureSource=browserTest.slice(browserTest.indexOf("const values="),browserTest.indexOf("const base="));
const fixtures=vm.runInNewContext(fixtureSource+';({main:mainHTML(),multi:multiHTML()})');
for(const [name,html] of Object.entries(fixtures)){
 const dir=path.join(target,'desktop',name==='multi'?'multibaccarat':'baccarat');fs.mkdirSync(dir,{recursive:true});fs.writeFileSync(path.join(dir,'index.html'),html);
}
const file=process.argv[2]||path.join(__dirname,'../src/main.cpp');
const src=fs.readFileSync(file,'utf8');
const section=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b,src.indexOf(a)));
const production=section('const toRootViewportPoint=','const mainTarget=')+section('const controlPoint=','const stablePairSignature=')+(src.includes('const requestChipSelectorOpen=')?section('const requestChipSelectorOpen=','const storePairClickCoords='):'');
const setup=(mode)=>`const ROOT_WINDOW=globalThis,ROOT_DOCUMENT=globalThis.document,window=ROOT_DOCUMENT.getElementById('${mode}').contentWindow,document=window.document,NodeFilter=window.NodeFilter,isMulti=${mode==='multi'};const SOURCE_GAME='123',TARGET_NAME='${mode==='multi'?'Baccarat 9':'Baccarat 1'}';const norm=s=>String(s||'').replace(/\\s+/g,' ').trim(),lower=s=>norm(s).toLowerCase(),visible=el=>!!el;const tableTextMatches=t=>norm(t).startsWith(TARGET_NAME);const AUTO_BET_REQUEST=true,RUN_TOKEN='run',TARGET_ID='table',REQUEST_TOKEN='7',context='test',href=window.location.href;const operation={finished:false};`;
const code=`const production=${JSON.stringify(production)};const setups=${JSON.stringify({main:setup('main'),multi:setup('multi')})};
function install(mode){(0,eval)(setups[mode]+production+';globalThis.api={chipTarget,chipRackRoot,controlPoint,chipSourceByHit,chipActiveEvidence,table:document.getElementById("table"),operation,'+(production.includes('const multiplayChipSelector=')?'multiplayChipSelector,selectedMultiplayChip,requestChipSelectorOpen,':'')+'diag:()=>lastChipSearchDiag};')}
function assert(ok,message){if(!ok)throw Error(message||'Assertion failed')}
const results=[];function test(name,fn){try{fn();results.push({name,ok:true})}catch(e){results.push({name,ok:false,error:String(e)})}}
function clickPoint(p){const frame=document.elementFromPoint(p.x,p.y);assert(frame?.tagName==='IFRAME','point must land in iframe');const r=frame.getBoundingClientRect();const hit=frame.contentDocument.elementFromPoint(p.x-r.left,p.y-r.top);assert(hit,'no target');hit.click()}
function run(){
test('Vertical main rack 42 x 430',()=>{install('main');const r=api.chipRackRoot(api.table)?.getBoundingClientRect();assert(r?.width===42&&r?.height===430,JSON.stringify(r))});
test('Main 0.20 and 1K resolved correctly',()=>{for(const [c,v]of[[20,'0,2'],[100000,'1K']]){const el=api.chipTarget(c,api.table),p=api.controlPoint(el);assert(el?.textContent===v,'wrong target '+el?.textContent);assert(p?.x>880&&p.x<960,'wrong frame')}});
test('Closed MULTIPLAY excludes main rack',()=>{install('multi');assert(api.chipTarget(20,api.table)===null,'selected foreign or decorative chip')});
test('Opener is center chip in footer',()=>{const s=api.multiplayChipSelector(api.table),p=s&&api.controlPoint(s.el);assert(s?.denom==='1'&&!s.open,JSON.stringify({denom:s?.denom,open:s?.open}));assert(p?.x>1080&&p.x<1120&&p.y>650,JSON.stringify(p))});
test('One open request per phase',()=>{const logs=[],old=console.log;console.log=x=>logs.push(x);try{assert(api.requestChipSelectorOpen(api.table,'pair'));assert(!api.requestChipSelectorOpen(api.table,'pair'))}finally{console.log=old}assert(logs.length===1);const p=JSON.parse(logs[0].split('__BAC_CHIP_SELECTOR_OPEN_COORDS__')[1]);clickPoint(p)});
test('Expanded radial menu resolves 0.20',()=>{const el=api.chipTarget(20,api.table),p=api.controlPoint(el);assert(el?.textContent==='0,2',JSON.stringify(api.diag()));assert(p?.x>970,JSON.stringify(p));clickPoint(p)});
test('Collapsed display confirms 0.20, rejects 1',()=>{const el=api.selectedMultiplayChip(20,api.table);assert(el,'no selected 0.20');assert(!api.selectedMultiplayChip(100,api.table),'wrong denomination accepted');assert(api.chipActiveEvidence(el).active)});
test('Next phase reopens independently',()=>{assert(api.requestChipSelectorOpen(api.table,'main'))});
test('Bare footer number rejected',()=>{const d=document.getElementById('multi').contentDocument;d.querySelector('.options').remove();d.querySelectorAll('.decor').forEach(e=>e.remove());assert(!api.multiplayChipSelector(api.table))});
test('Point uses source, not large hit ancestor',()=>{install('main');const d=api.table.ownerDocument,b=d.createElement('button');b.style='position:absolute;left:100px;top:600px;width:180px;height:60px';b.innerHTML='<span style="position:absolute;left:10px;top:15px;width:30px;height:30px;pointer-events:none">1</span>';d.body.append(b);api.chipSourceByHit.set(b,b.firstChild);const p=api.controlPoint(b);assert(p?.x===145&&p.y===660,JSON.stringify(p))});
document.getElementById('results').textContent=JSON.stringify(results,null,2);document.title=results.filter(x=>x.ok).length+'/'+results.length+' chip tests';window.testResults=results;
}
window.addEventListener('load',run);
`;
const html=`<!doctype html><meta charset="utf-8"><title>Chip tests</title><style>body{margin:0}iframe{position:absolute;top:30px;border:0;height:690px}#main{left:20px;width:940px}#multi{left:970px;width:255px}#results{position:absolute;top:730px;white-space:pre-wrap}</style><iframe id="main" src="desktop/baccarat/index.html"></iframe><iframe id="multi" src="desktop/multibaccarat/index.html"></iframe><pre id="results">Running local tests</pre><script>${code.replace(/<\/script/gi,'<\\/script')}</script>`;
fs.writeFileSync(path.join(target,process.argv[3]||'index.html'),html);
console.log('Local browser harness generated.');
