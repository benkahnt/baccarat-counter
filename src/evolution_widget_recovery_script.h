#pragma once
inline constexpr const char* kEvolutionWidgetRecoveryScript = R"EVOREC(
(()=>{const req=__EVO_RECOVERY_REQUEST__,root=window,now=Date.now();
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

const emit=(action,detail,extra={})=>console.log('__BAC_EVOLUTION_WIDGET_RECOVERY__'+JSON.stringify({runToken:req.runToken,request:req.request,action,detail,...extra,ts:Date.now()}));
let state=root.__BCP_EVOLUTION_WIDGET_RECOVERY__;
if(!state||state.request!==req.request)state=root.__BCP_EVOLUTION_WIDGET_RECOVERY__={request:req.request,started:now,closed:false,opened:false,done:false};
if(state.done)return;
const finish=(action,detail)=>{state.done=true;emit(action,detail);};
if(now-state.started>30000){finish('FAILED','MULTIPLAY innerhalb von 30 Sekunden nicht wiederhergestellt');return;}
const docs=[],seen=new Set();function walk(w){if(seen.has(w))return;seen.add(w);try{docs.push(w.document);for(const f of w.document.querySelectorAll('iframe'))walk(f.contentWindow)}catch(_){}}walk(root);
const text=docs.map(d=>d.body?.innerText||'').join(' ');
if(root.__BCP_EVOLUTION_SESSION_TERMINATED__===req.runToken||(/Sitzung abgelaufen|session expired/i.test(text)&&/Inaktivit|inactiv|erneut.*anmelden|sign in/i.test(text))){finish('AUTH_REQUIRED','Anbieter verlangt nach Inaktivitaet eine erneute Anmeldung');return;}
const visible=el=>{try{const w=el.ownerDocument.defaultView,r=el.getBoundingClientRect(),cs=w.getComputedStyle(el);return el.isConnected&&!el.disabled&&r.width>2&&r.height>2&&r.right>0&&r.bottom>0&&r.left<w.innerWidth&&r.top<w.innerHeight&&cs.display!=='none'&&cs.visibility!=='hidden'&&cs.pointerEvents!=='none'&&Number(cs.opacity)>0&&el.getAttribute('aria-disabled')!=='true';}catch(_){return false;}};
const lists=docs.map(d=>({d,list:d.querySelector('[data-role="tablesList"],[data-testid="virtuoso-scroller"]')})).filter(x=>x.list);
let current=lists[0],transport;
if(lists.length>1){finish('FAILED','Mehrere MULTIPLAY-Oberflaechen; keine eindeutige Zuordnung');return;}
if(current){let f=current.list[Object.keys(current.list).find(k=>k.startsWith('__reactFiber$'))];for(let n=0;f&&n<30;n++,f=f.return){if(f.memoizedProps?.value?.multiplayApi)transport=f.memoizedProps.value.multiplayApi.props?.transport;}}
const live=root.__BCP_LIVE_TRANSPORT_RUNS?.[req.runToken];
const fresh=Object.values(live?.tables||{}).some(s=>s.lastTransportTs>=state.started&&now-s.lastTransportTs<5000);
if(current&&transport?._isDisposed===false&&transport?._isPaused!==true&&fresh){finish('RECOVERED','MULTIPLAY liefert wieder frische Tischdaten');return;}
if(!state.closed){
 if(!current){state.closed=true;return;}
 if(transport?._isDisposed!==true&&!req.stale){finish('FAILED','Verbindungsende nicht bestaetigt; MULTIPLAY bleibt offen');return;}
 const close=[...current.d.querySelectorAll('button[data-role="close-button"]')].filter(visible);
 if(close.length!==1){finish('FAILED','MULTIPLAY-Schliessen-Button nicht eindeutig sichtbar');return;}
 // Freeze only our own counting state. Never overwrite the provider store.
 for(const s of Object.values(live?.tables||{}))if(s.shoeTracked&&!s.continuityPending){s.continuityPending={gameId:s.gameId,official:s.lastOfficialCardsOut,completed:s.lastCompletedGameId,cardCount:s.lastCompletedHandCardCount};}
 const p=point(close[0]);if(!p){finish('FAILED','MULTIPLAY-Schliessen-Button verdeckt');return;}
 state.closed=true;state.closedAt=now;emit('CLOSE','Nur MULTIPLAY im bestehenden Tab schliessen',p);return;
}
if(!state.opened){
 if(current||now-(state.closedAt||state.started)<500)return;
 const open=docs.flatMap(d=>[...d.querySelectorAll('button[data-role="multiplay-button"]')]).filter(visible);
 if(open.length!==1){return;}
 const p=point(open[0]);if(!p)return;
 state.opened=true;emit('OPEN','MULTIPLAY im selben Tab erneut oeffnen',p);return;
}
})()
)EVOREC";
