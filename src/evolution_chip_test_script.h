#pragma once

// UI selectors and read-only store/ack schema verified on Evolution MULTIPLAY.
// The script only proposes clicks. The native monitor authorizes each request
// and dispatches CDP input; there are no private betting API calls.
inline constexpr const char* kEvolutionChipTestScript = R"EVOTEST(
(()=>{
const req=__EVO_TEST_REQUEST__,root=window,now=Date.now();
const emit=(action,detail,extra={})=>root.console.log('__BAC_EVOLUTION_CHIP_TEST__'+JSON.stringify({runToken:req.runToken,request:req.request,tableId:req.tableId,action,detail,...extra,ts:Date.now()}));
const compact=s=>String(s||'').replace(/\s+/g,' ').trim();
const spots=['Player','Banker','Tie','PlayerPair','BankerPair'];
const cents=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0&&Math.abs(v*100-Math.round(v*100))<.001?Math.round(v*100):null;
const amounts=o=>{const r={};if(!o||typeof o!=='object')return null;for(const [k,v] of Object.entries(o)){if(v==null)continue;const n=cents(v);if(n===null)return null;if(n)r[k]=n;}return r;};
const equal=(a,b)=>a&&b&&[...new Set([...Object.keys(a),...Object.keys(b)])].every(k=>(a[k]||0)===(b[k]||0));
const findContext=()=>{const seen=new Set();let found=null;function walk(w){if(found||seen.has(w))return;seen.add(w);try{const d=w.document,scroller=d.querySelector('[data-role="tablesList"],[data-testid="virtuoso-scroller"]');if(scroller){let f=scroller[Object.keys(scroller).find(k=>k.startsWith('__reactFiber$'))],api,ids=[];for(let n=0;f&&n<30;n++,f=f.return){const p=f.memoizedProps,a=p&&(Array.isArray(p.data)?p.data:Array.isArray(p.tables)?p.tables:null);if(a&&a.length>ids.length)ids=a.map(String);if(p?.value?.multiplayApi)api=p.value.multiplayApi;}if(api&&ids.includes(req.tableId))found={w,d,scroller,api,ids};}for(const frame of d.querySelectorAll('iframe'))try{walk(frame.contentWindow)}catch(_){}}catch(_){}}walk(root);return found;};
const storeFor=(api,id)=>{try{const inst=api.tables.getTableInstance(id),fn=inst?.component,source=String(fn||'');if(!/store:\w+/.test(source)||!/jsx\(/.test(source))return null;const el=fn(),s=el?.props?.value||el?.props?.children?.props?.store;return s?.agX?.tableId===id?s:null;}catch(_){return null;}};
const point=el=>{try{
 if(!el||el.closest('[aria-disabled="true"],:disabled'))return null;
 let w=el.ownerDocument.defaultView,d=w.document,r=el.getBoundingClientRect();
 const cs=w.getComputedStyle(el);if(r.width<5||r.height<5||cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0||cs.pointerEvents==='none')return null;
 let x=r.left+r.width/2,y=r.top+r.height/2;
 if(x<0||y<0||x>=w.innerWidth||y>=w.innerHeight)return null;
 let hit=d.elementFromPoint(x,y);if(!hit||!(hit===el||el.contains(hit)))return null;
 for(let n=0;w!==root&&n<8;n++){
  const frame=w.frameElement;if(!frame)return null;const fr=frame.getBoundingClientRect();
  x=fr.left+x*fr.width/Math.max(1,w.innerWidth);y=fr.top+y*fr.height/Math.max(1,w.innerHeight);
  w=frame.ownerDocument.defaultView;hit=w.document.elementFromPoint(x,y);if(!hit||!(hit===frame||frame.contains(hit)))return null;
 }
 return w===root&&x>=0&&y>=0&&x<root.innerWidth&&y<root.innerHeight?{x,y}:null;
 }catch(_){return null;}};
let st=root.__BCP_EVOLUTION_CHIP_TEST__;
if(st&&st.request!==req.request){st.dispose?.();st=null;}
if(!st){st={request:req.request,started:now,seq:0,index:0,expected:{},pending:null,gameId:'',lastClick:0,done:false,focusAt:0,lastWait:'',ack:null};root.__BCP_EVOLUTION_CHIP_TEST__=st;}
const finish=(action,detail)=>{if(st.done)return;st.done=true;st.dispose?.();emit(action,detail,{gameId:st.gameId,expected:st.expected});};
const wait=detail=>{if(st.lastWait!==detail){st.lastWait=detail;emit('WAIT',detail);}};
const click=(el,kind,detail)=>{const p=point(el);if(!p){wait('Warte auf freies Klickziel: '+detail);return false;}st.lastClick=now;emit('CLICK',detail,{...p,seq:++st.seq,kind,gameId:st.gameId});return true;};
try{
 if(st.done)return;
 if(req.cancel){finish('CANCELLED','Auftrag abgebrochen');return;}
 if(now-st.started>90000){finish('FAILED','90 Sekunden abgelaufen; kein weiterer Klick');return;}
 const ctx=findContext();if(!ctx){wait('Ausgewaehlter Tisch noch nicht im MULTIPLAY verfuegbar');return;}
 const {d,w,api,ids,scroller}=ctx,s=storeFor(api,req.tableId);
 if(api.props?.transport?._isDisposed===true||api.props?.transport?._isPaused===true){finish('FAILED','MULTIPLAY-Verbindung beendet oder pausiert');return;}
 if(!s){finish('FAILED','Tischzuordnung im Anbieterzustand nicht eindeutig');return;}
 if(st.store&&st.store!==s){finish('FAILED','Tischsitzung wurde ersetzt');return;}st.store=s;
 if(s.agX.currency?.code!=='EUR'){finish('FAILED','Test erfordert EUR');return;}
 if(s.tableStatus.isClosed||s.agX.disposed){finish('FAILED','Tisch geschlossen');return;}
 if(s.commissionMode?.isNoCommission===true||s.settings.tiePays9to1===true){finish('FAILED','Abweichende Hauptwetten-Auszahlung');return;}
 const stats=s.shoe.stats,counts=[stats.playerWins,stats.bankerWins,stats.ties];
 const hands=counts.every(n=>Number.isInteger(n)&&n>=0)?counts.reduce((a,b)=>a+b,0):-1;
 if(hands<0||hands>104){finish('FAILED','Anbieter-Handzahl nicht eindeutig');return;}
 if(st.hands!==undefined&&hands<st.hands){finish('FAILED','Schuhwechsel waehrend des Tests');return;}st.hands=hands;
 const gameId=String(s.agX.gameRoundId||'');
 const mainCents=req.mainCents??500,pairCents=req.pairCents??100;
 if(!Number.isInteger(mainCents)||mainCents<0||!Number.isInteger(pairCents)||pairCents<=0){finish('FAILED','Ungueltiger Einsatz');return;}
 if(req.signal&&gameId!==req.targetGameId){finish('FAILED','Signalrunde nicht mehr aktuell');return;}
 if(hands>=60&&mainCents<5*pairCents){finish('FAILED','Hauptwette erfuellt die 20-Prozent-Regel nicht');return;}
 const totals=[...(mainCents?[{spot:req.mainSide,cents:mainCents}]:[]),{spot:'PlayerPair',cents:pairCents},{spot:'BankerPair',cents:pairCents}];
 const stack=d.querySelector('[data-role="chip-stack"]');
 if(!stack){wait('Chip-Stack noch nicht sichtbar');return;}
 const denoms=[...new Set([...stack.querySelectorAll('[data-role="revolver-chip-item"] [data-role="chip"][data-value]')].map(e=>cents(Number(e.getAttribute('data-value')))).filter(n=>n>0))].sort((a,b)=>b-a);
 const steps=[];
 for(const total of totals){const denom=denoms.find(n=>total.cents%n===0&&total.cents/n<=20);if(!denom){finish('FAILED','Einsatz mit vorhandenen Evolution-Chips nicht exakt darstellbar: '+total.spot);return;}for(let i=0;i<total.cents/denom;i++)steps.push({spot:total.spot,cents:denom});}
 st.stepCount=steps.length;
 if(!['Player','Banker','Tie'].includes(req.mainSide)){finish('FAILED','Ungueltige Hauptwette');return;}
 for(const step of totals){const min=cents(s.betSpot.minBetSpotValues[step.spot]),max=cents(s.betSpot.maxBetSpotValues[step.spot]);if(min===null||max===null||step.cents<min||step.cents>max){finish('FAILED','Testbetrag ausserhalb Tischlimit: '+step.spot);return;}}
 if(!st.listener){
  const stream=api.props?.transport?.incomingMessages;if(!stream?.onValue||!stream?.offValue){finish('FAILED','Anbieterbestaetigung nicht lesbar');return;}
  st.listener=msg=>{try{const p=msg?.payload;if(msg?.type!=='baccarat.playerBettingState'||String(p?.tableId||'')!==req.tableId||!st.gameId||String(p.gameId||'')!==st.gameId||p.restore)return;
   const b=p.state;if(!b)return;const rejected=Object.keys(b.rejectedBets||{}).length>0;
   const accepted=b.acceptedBets&&Object.fromEntries(Object.entries(b.acceptedBets).map(([k,v])=>[k,v?.amount]));
   st.ack={at:Date.now(),status:b.status,chips:amounts(b.currentChips),accepted:amounts(accepted),rejected};
  }catch(_){}};
  stream.onValue(st.listener);st.dispose=()=>{stream.offValue(st.listener);st.listener=null;};
 }
 if(st.gameId&&gameId!==st.gameId){finish('FAILED','Runde gewechselt; keine Wiederholung von Wettklicks');return;}
 const ack=st.ack;
 if(ack&&(ack.rejected||['Rejected','Cancelled'].includes(ack.status))){finish('FAILED','Anbieter hat Wette abgelehnt oder Runde storniert');return;}
 if(st.pending){
  if(ack&&ack.at>=st.pending.at&&equal(ack.chips,st.expected)){
   emit('STORED','Anbieter bestaetigt '+st.pending.spot,{gameId:st.gameId,spot:st.pending.spot,cents:st.pending.cents});st.index++;st.pending=null;
  }else{if(now-st.pending.at>6000)finish('FAILED','Keine eindeutige Anbieterbestaetigung; Wettklick wird nicht wiederholt');return;}
 }
 if(st.index===steps.length){
  if(ack&&ack.status==='Accepted'&&equal(ack.accepted,st.expected)){finish('SUCCESS','Alle vorgesehenen Wetten vom Anbieter angenommen');return;}
  wait('Alle Chips serverseitig gespeichert; warte auf finale Annahme');return;
 }
 if(s.gamePhase.isBetsOpen!==true||s.gamePhase.isBurning||s.gamePhase.isLongBetting){
  if(st.index||st.gameId){finish('FAILED','Wettfenster geschlossen; restliche Klicks gestoppt');return;}
  wait('Warte bis der Tisch zum Wetten freigegeben wird');return;
 }
 if(!gameId){wait('Warte auf aktuelle Runden-ID');return;}
 // The live timer getter is in seconds (verified against the visible countdown).
 if(!Number.isFinite(s.timer.timeRemaining)||s.timer.timeRemaining<(st.index===0?Math.max(8,steps.length*.65+3):1.5)){if(st.gameId){finish('FAILED','Zu wenig Wettzeit fuer weitere sichere Klicks');return;}wait('Warte auf naechstes vollstaendiges Wettfenster');return;}
 const local=amounts(s.bets.bets);if(!equal(local,st.expected)){finish('FAILED','Bereits vorhandene oder fremd geaenderte Chips; kein Zusatzklick');return;}
 let tile=[...d.querySelectorAll('[data-role="table"][data-tableid]')].find(e=>e.getAttribute('data-tableid')===req.tableId);
 if(!tile){
  if(now-st.focusAt<500)return;st.focusAt=now;
  const rendered=[...d.querySelectorAll('[data-role="table"][data-tableid]')],first=rendered[0],idx=ids.indexOf(req.tableId),firstIdx=first?ids.indexOf(first.getAttribute('data-tableid')):-1;
  const h=first?first.getBoundingClientRect().height+8:Math.max(100,scroller.scrollHeight/ids.length);
  scroller.scrollTop=Math.max(0,firstIdx>=0?scroller.scrollTop+(idx-firstIdx)*h:idx*h);
  wait('Fokussiere ausgewaehlten Tisch im MULTIPLAY');return;
 }
 const step=steps[st.index],field=tile.querySelector('[data-role="bet-spot-'+step.spot+'"]');
 if(!point(field)){if(now-st.focusAt>=500){tile.scrollIntoView({block:'center',inline:'nearest',behavior:'auto'});st.focusAt=now;}wait('Warte auf sichtbares Wettfeld des ausgewaehlten Tisches');return;}
 const selected=stack?.querySelector('[data-role="selected-chip"] [data-role="chip"][data-value]');
 if(!stack||!selected){wait('Chip-Stack noch nicht sichtbar');return;}
 if(now-st.lastClick<450)return;
 const selectedCents=cents(Number(selected.getAttribute('data-value'))),storeCents=cents(api.chipstack?.chipStackValue);
 if(selectedCents!==step.cents||storeCents!==step.cents){
  const chip=[...stack.querySelectorAll('[data-role="revolver-chip-item"] [data-role="chip"][data-value]')].find(e=>cents(Number(e.getAttribute('data-value')))===step.cents&&point(e));
  if(chip)click(chip,'chip','Chip '+(step.cents/100)+' EUR auswaehlen');
  else click(stack.querySelector('[data-role="chip-stack-toggle"]'),'toggle','Chip-Auswahl oeffnen');
  return;
 }
 if(st.lastFocusGame&&st.lastFocusGame!==gameId){finish('FAILED','Runde waehrend Chip-Auswahl gewechselt');return;}st.lastFocusGame=gameId;
 // A wager click is proposed once. Only an exact server state advances it.
 st.gameId=gameId;
 if(click(field,'wager',step.spot+' '+(step.cents/100)+' EUR')){
  st.expected[step.spot]=(st.expected[step.spot]||0)+step.cents;st.pending={...step,at:now};
 }
}catch(e){finish('FAILED','Testfehler: '+String(e).slice(0,150));}
})()
)EVOTEST";
