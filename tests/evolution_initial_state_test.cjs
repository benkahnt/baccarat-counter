const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..'),src=fs.readFileSync(path.join(root,'src/main.cpp'),'utf8');
const extract=(a,b)=>src.slice(src.indexOf(a),src.indexOf(b,src.indexOf(a)));
const fixture=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/evolution_initial_state_capture.json'),'utf8'));
const results=[];
const test=(name,fn)=>{fn();results.push({name,ok:true});console.log('PASS '+name)};
const componentSource='()=>ve.jU(D,()=>i.jsx(CX.Kq,{store:t,children:i.jsx(E,{})}))';
let now=20000,calls=0;
function apiFor(sample,transform=x=>x){
 const stats={}; for(const [k,v] of Object.entries(sample.stats))Object.defineProperty(stats,k,{get:()=>v});
 const store=transform({agX:{tableId:sample.id},shoe:{stats,history:{length:sample.historyLength}},gamePhase:{phase:sample.phase}});
 const component=()=>{calls++;return {props:{value:store}}};component.toString=()=>componentSource;
 return {tables:{getTableInstance:id=>id===sample.id?{component}:null}};
}
const consoleEvents=[];
const context={Date:{now:()=>now},console:{log:s=>consoleEvents.push(String(s))},root:{},RUN_TOKEN:'test'};
vm.createContext(context);
vm.runInContext(extract('const evolutionDisplayCounts=','const emitLiveTableStatus=')+
 extract('const liveStatusText=','// Read only a complete, table-local')+
 `;globalThis.read=evolutionReadInitialState;globalThis.apply=evolutionApplyInitialState;
 globalThis.display=evolutionDisplayCounts;globalThis.status=liveStatusText;globalThis.bootstrap=evolutionBootstrapTables;`,context);
const sample=fixture.find(s=>s.id==='qsf65xtoyvbqoaop'),snapshot=context.read(apiFor(sample),sample.id);
const fresh=()=>({tableid:sample.id,discoveredTs:now,lastTransportTs:0,shoeTracked:false,shoeTrusted:false,shoeHands:null,playerCards:[],bankerCards:[]});
test('all 39 captured stores including non-enumerable MobX counters',()=>{
 for(const s of fixture){const got=context.read(apiFor(s),s.id);assert.equal(got.total,s.stats.gameCount);assert.equal(got.tableid,s.id)}
});
test('offscreen initial state is display-only and never a live receipt',()=>{
 const st=fresh();assert(context.apply(st,snapshot));assert.equal(context.display(st).total,30);
 assert.equal(st.lastTransportTs,0);assert.equal(st.shoeHands,null);assert.equal(st.shoeTracked,false);assert.equal(st.shoeTrusted,false);
 assert.equal(st.remainingRanks,undefined);assert.equal(st.gameId,undefined);assert.deepEqual(st.playerCards,[]);
 assert.match(context.status(st),/Anfangsstand/);now+=16000;assert.match(context.status(st),/noch keine Live-Daten/);
});
test('unknown component is never invoked',()=>{
 let invoked=false;const api={tables:{getTableInstance:()=>({component:()=>{invoked=true;return{}}})}};
 assert.equal(context.read(api,sample.id),null);assert.equal(invoked,false);
});
test('wrong table store cannot leak another table count',()=>{
 assert.equal(context.read(apiFor(sample,s=>({...s,agX:{tableId:'wrong'}})),sample.id),null);
 assert.equal(context.apply(fresh(),{...snapshot,tableid:'wrong'}),false);
});
test('missing or throwing store falls back safely',()=>{
 assert.equal(context.read({},sample.id),null);assert.equal(context.read({tables:{getTableInstance:()=>{throw Error('missing')}}},sample.id),null);
 assert.equal(context.read(apiFor(sample,()=>null),sample.id),null);
});
test('negative, fractional, incomplete and inconsistent counts rejected',()=>{
 for(const change of [{player:-1},{tie:0.1},{total:31},{historyLength:29},{banker:undefined},{player:105,total:116,historyLength:116}]){
  const st=fresh();assert.equal(context.apply(st,{...snapshot,...change}),false);assert.equal(st.providerInitialCounts,undefined);
 }
});
test('empty fresh shoe may display zero without trusting card composition',()=>{
 const st=fresh();assert(context.apply(st,{...snapshot,player:0,banker:0,tie:0,total:0,historyLength:0}));assert.equal(context.display(st).total,0);assert.equal(st.shoeTrusted,false);
});
test('real live receipt and actual shoe reset prevent cached overwrite',()=>{
 for(const fields of [{lastTransportTs:now},{providerCountsMinTimestamp:1},{transportUnavailableReason:'PlayerConnected'}]){
  const st={...fresh(),...fields};assert.equal(context.apply(st,snapshot),false);assert.equal(st.providerInitialCounts,undefined);
 }
 const start=src.indexOf('const initTrackedShoe=');const body=src.slice(start,src.indexOf('\n};',start));
 assert(body.includes('st.providerInitialCounts=null'));assert(body.includes("st.providerInitialPhase=''"));
});
test('live/DOM counts outrank bootstrap and age remains explicit',()=>{
 const st=fresh();context.apply(st,snapshot);now+=3000;assert.equal(context.display(st).ageMs,3000);
 st.providerOutcomeCounts={total:31,seenAt:now};assert.equal(context.display(st).total,31);
 st.providerShoeCounts={total:32,seenAt:now};assert.equal(context.display(st).total,32);
 st.lastTransportTs=now;st.betting='BetsClosed';assert.equal(context.status(st),'Bets geschlossen / warte auf Karten');
});
let tables={},emitted=[],discoveryIds=[sample.id],labels=new Map([[sample.id,sample.name]]),api=apiFor(sample);
context.getLiveRun=()=>({tables});
context.getLiveTable=(_,id,name)=>{const st=tables[id]||(tables[id]={...fresh(),tableid:id});st.tableName=name;return st};
context.emitLiveTableStatus=st=>emitted.push({id:st.tableid,status:context.status(st)});
test('bootstrap retry is bounded and stops as soon as transport arrives',()=>{
 calls=0;context.bootstrap(api,discoveryIds,labels);assert.equal(calls,1);
 context.bootstrap(api,discoveryIds,labels);assert.equal(calls,1);
 now+=2000;context.bootstrap(api,discoveryIds,labels);assert.equal(calls,2);
 tables[sample.id].lastTransportTs=now;now+=2000;context.bootstrap(api,discoveryIds,labels);assert.equal(calls,2);
});
const stream=()=>({listeners:new Set(),onValue(fn){this.listeners.add(fn)},offValue(fn){this.listeners.delete(fn)},send(msg){for(const fn of this.listeners)fn(msg)}});
let currentStream=stream();api.props={transport:{incomingMessages:currentStream}};
context.findContextAndIds=()=>({ctx:{multiplayApi:api},tableIds:discoveryIds});
context.transportTableNames=()=>[...labels].map(([id,label])=>({id,label}));
context.inspectTransportMessage=msg=>({type:msg.type,tableRefs:[],interesting:[]});
context.safeTransportClone=x=>x;
vm.runInContext(extract('const evolutionFreezeCounts=','const getLiveRun=')+
 extract('const applyLiveTransportMessage=','const updateLiveTransportCountdowns=')+
 extract('const maybeParsedTransportTap=','const maybeStoreProbe=')+
 ';globalThis.tap=maybeParsedTransportTap;globalThis.route=applyLiveTransportMessage;',context);
const msg=(id,total=2)=>({type:'baccarat.encodedShoeState',timestamp:now,payload:{tableId:id,stats:{gameCount:total,playerWins:total,bankerWins:0,ties:0},history_v2:Array(total).fill({})}});
test('real listener bootstrap installation is idempotent',()=>{
 tables={};context.tap({},'offline');assert.equal(currentStream.listeners.size,1);assert.equal(context.display(tables[sample.id]).total,30);
 context.tap({},'offline');assert.equal(currentStream.listeners.size,1);
});
test('existing listener accepts newly discovered offscreen table and label',()=>{
 discoveryIds=[sample.id,'added'];labels.set('added','New table');context.tap({},'offline');
 currentStream.send(msg('added'));assert.equal(tables.added.providerShoeCounts.total,2);assert.equal(tables.added.tableName,'New table');assert.equal(currentStream.listeners.size,1);
 labels.set('added','Renamed');context.tap({},'offline');currentStream.send(msg('added',3));assert.equal(tables.added.tableName,'Renamed');
});
test('unrelated table and balance noise do not create live card activity',()=>{
 currentStream.send(msg('not-subscribed'));assert.equal(tables['not-subscribed'],undefined);
 const st=tables[sample.id];assert.equal(st.lastTransportTs,0);
 currentStream.send({type:'balanceUpdated',payload:{tableId:sample.id}});assert.equal(st.lastTransportTs,0);
});
test('main-table removal is explicit even after virtual-list removal',()=>{
 tables.added.shoeTrusted=true;discoveryIds=[sample.id];context.tap({},'offline');
 currentStream.send({type:'widget.removeTable',payload:{tableId:'added',reason:'PlayerConnected'}});
 assert.equal(tables.added.shoeTrusted,false);assert.match(context.status(tables.added),/Haupttisch/);assert.equal(tables.added.countdownDeadline,0);
});
test('stream replacement detaches old listener and run change clears old tap',()=>{
 const old=currentStream;currentStream=stream();api.props.transport.incomingMessages=currentStream;context.tap({},'offline');
 assert.equal(old.listeners.size,0);assert.equal(currentStream.listeners.size,1);
 context.RUN_TOKEN='next-run';context.tap({},'offline');assert.equal(currentStream.listeners.size,1);assert.equal(context.root.__BCP_TRANSPORT_TAPS.test,undefined);
});
test('transport count takes over bootstrap without inventing shoe history',()=>{
 currentStream.send(msg(sample.id,31));const st=tables[sample.id];assert.equal(context.display(st).total,31);assert.equal(st.lastTransportTs,now);assert.equal(st.shoeTrusted,false);assert.equal(st.shoeHands,null);
});
test('final accepted amounts remain observable after a click job ended',()=>{
 const count=()=>consoleEvents.filter(s=>s.startsWith('__BAC_EVOLUTION_ACCEPTED__')).length;
 const send=state=>currentStream.send({type:'baccarat.playerBettingState',payload:{tableId:sample.id,gameId:'partial',state}});
 let before=count();send({status:'Accepted',acceptedBets:{Banker:{amount:5}}});assert.equal(count(),before+1);
 const event=JSON.parse(consoleEvents.findLast(s=>s.startsWith('__BAC_EVOLUTION_ACCEPTED__')).slice('__BAC_EVOLUTION_ACCEPTED__'.length));
 assert.equal(event.Banker,500);assert.equal(event.PlayerPair,0);assert.equal(event.BankerPair,0);
 send({status:'Accepted'});send({status:'Accepted',acceptedBets:{Banker:{amount:-5}}});
 assert.equal(count(),before+1);
 send({status:'Cancelled'});assert.equal(count(),before+2);
 const cancelled=JSON.parse(consoleEvents.findLast(s=>s.startsWith('__BAC_EVOLUTION_ACCEPTED__')).slice('__BAC_EVOLUTION_ACCEPTED__'.length));assert.equal(cancelled.Banker,0);
});
fs.writeFileSync(process.env.TEST_REPORT||path.join(root,'.validation/evolution_initial_results.json'),JSON.stringify(results,null,2));
