const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.join(__dirname,'..'),s=fs.readFileSync(path.join(root,'src/main.cpp'),'utf8');
const fragment=s.slice(s.indexOf('const evolutionFreezeCounts='),s.indexOf('const getLiveRun=()=>'));
const sandbox={root:{},RUN_TOKEN:'fixture',console:{log:()=>{}},Date};vm.createContext(sandbox);vm.runInContext(fragment+';globalThis.freeze=evolutionFreezeCounts;globalThis.check=evolutionCheckContinuity;',sandbox);
const shoe=()=>({shoeTracked:true,shoeTrusted:true,remainingRanks:{A:29},gameId:'g1',lastOfficialCardsOut:100,lastCompletedGameId:'g1',lastCompletedHandCardCount:4});
function reset(){const a=shoe(),b=shoe();sandbox.root.__BCP_LIVE_TRANSPORT_RUNS={fixture:{tables:{a,b}}};sandbox.freeze();return {a,b};}
let {a,b}=reset();assert.deepEqual(a.remainingRanks,{A:29});assert.equal(sandbox.check(a,'baccarat.cardDealt',{gameId:'g1'}),false);
assert.equal(sandbox.check(a,'baccarat.tableState',{shoeCardsOut:100,currentGame:{gameId:'g1'}}),true);assert(a.shoeTrusted&&!a.continuityPending);assert(b.continuityPending);
({a}=reset());assert(sandbox.check(a,'baccarat.newGame',{shoeCardsOut:104,gameId:'g2'}));assert(a.shoeTrusted);
({a,b}=reset());assert(sandbox.check(a,'baccarat.newGame',{shoeCardsOut:110,gameId:'g3'}));assert(!a.shoeTrusted);assert(b.shoeTrusted);assert.deepEqual(a.remainingRanks,{A:29});
({a}=reset());a.continuityPending.completed='previous';assert(sandbox.check(a,'baccarat.newGame',{shoeCardsOut:104,gameId:'g2'}));assert(!a.shoeTrusted);
({a}=reset());assert(sandbox.check(a,'baccarat.newGame',{shoeCardsOut:0,gameId:'new-shoe'}));assert(a.shoeTrusted);
({a}=reset());assert(!sandbox.check(a,'baccarat.gameState',{gameId:'g1'}));assert(a.continuityPending);
console.log('PASS preserved composition, same round, exact next round, missing rounds, unfinished hand, new shoe and absent evidence');
