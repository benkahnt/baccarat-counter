#pragma once
inline constexpr const char* kEvolutionActivityScript=R"EVOACT(
(()=>{const req=__EVO_ACTIVITY_REQUEST__,root=window;
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

const docs=[],seen=new Set();function walk(w){if(seen.has(w))return;seen.add(w);try{docs.push(w.document);for(const f of w.document.querySelectorAll('iframe'))walk(f.contentWindow)}catch(_){}}walk(root);
if(docs.some(d=>/Sitzung abgelaufen|session expired/i.test(d.body?.innerText||'')))return;
let slot=0;for(const d of docs){
 if(!d.__BCP_ACTIVITY_PROOF__){const proof=d.__BCP_ACTIVITY_PROOF__={trustedMoveAt:0};d.addEventListener('mousemove',e=>{if(e.isTrusted)proof.trustedMoveAt=Date.now();},{passive:true});}
 // Main-table documents have help/settings buttons instead of the lobby logo
 // or MULTIPLAY menu. Try each verified visible control; a hidden first match
 // must not prevent activity in an otherwise reachable document.
 const candidates=d.querySelectorAll('a#headerLogo,button[data-role="casino-logo-button"],button[data-role="menu-button"],button[data-role="help-button"],button[data-role="settings-button"]');
 let header=null,p=null;for(const candidate of candidates){p=point(candidate);if(p){header=candidate;break;}}
 if(!p)continue;
 // Alternate the point inside this verified header control. Never click it.
 p.x+=(req.sequence%2?1:-1);
 console.log('__BAC_EVOLUTION_ACTIVITY__'+JSON.stringify({runToken:req.runToken,sequence:req.sequence,slot:slot++,x:p.x,y:p.y,control:header.getAttribute('data-role')||header.id,documentStartedAt:d.defaultView.performance.timeOrigin,trustedMoveAt:d.__BCP_ACTIVITY_PROOF__.trustedMoveAt,ts:Date.now()}));
 if(slot===4)break;
}
if(!slot)console.log('__BAC_EVOLUTION_ACTIVITY__'+JSON.stringify({runToken:req.runToken,sequence:req.sequence,slot:-1,ts:Date.now()}));
})()
)EVOACT";
