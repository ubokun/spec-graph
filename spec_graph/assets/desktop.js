'use strict';
const $=id=>document.getElementById(id);
const node=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e;};
let data=null,group=null,selected=null,busy=false;
const labels={current:'現在',past:'過去',future:'予想・計画'};
async function request(method,...args){
 if(busy)return;busy=true;for(const id of ['open','github','refresh'])$(id).disabled=true;
 try{const result=await window.pywebview.api[method](...args);if(result.cancelled)return;if(!result.ok)throw new Error(result.error);data=result;selected=null;group=null;render();$('error').hidden=true;}
 catch(error){$('error').textContent=error.message;$('error').hidden=false;}
 finally{busy=false;for(const id of ['open','github','refresh'])$(id).disabled=false;}
}
function render(){
 const g=data?.graph;$('repo').textContent=g?.repository||'未選択';$('source').textContent=g?(data.source?'ローカルファイル':'GitHub · default branch'):'ファイルまたはGitHubリポジトリを開いてください。';
 $('groups').replaceChildren();if(g){for(const [id,label] of [[null,'すべての仕様'],...Object.entries(g.spec_groups).map(([id,v])=>[id,v.description])]){const b=node('button',label);b.setAttribute('aria-pressed',String(group===id));b.onclick=()=>{group=id;selected=null;render();};$('groups').append(b);}}
 const query=$('search').value.toLocaleLowerCase();
 let total=0;$('list').replaceChildren();
 for(const state of ['current','future','past']){
  const entries=g?Object.entries(state==='future'?g.proposals:g.nodes).filter(([id,n])=>id!=='null'&&(state==='future'||n.state===state)&&(!group||n.groups.includes(group))&&(`${id} ${n.text}`).toLocaleLowerCase().includes(query)):[];
  total+=entries.length;
  const section=node('section','',`spec-section ${state}`),heading=node('div','','section-heading');
  const title=node('h2',labels[state]);title.id='section-'+state;section.setAttribute('aria-labelledby',title.id);
  heading.append(title,node('span',entries.length+'件','section-count'));
  const actions=node('div','','rail-actions'),rail=node('div','','card-rail');rail.id='rail-'+state;rail.tabIndex=0;rail.setAttribute('role','region');rail.setAttribute('aria-label',labels[state]+'の仕様カード');
  for(const [text,direction] of [['←',-1],['→',1]]){const button=node('button',text);button.setAttribute('aria-label',labels[state]+(direction<0?'を左へ':'を右へ'));button.disabled=!entries.length;button.onclick=()=>rail.scrollBy({left:direction*324,behavior:'smooth'});actions.append(button);}
  heading.append(actions);section.append(heading,rail);
  for(const [id,n] of entries){const button=node('button','',`spec ${state}`);button.dataset.specId=id;button.setAttribute('aria-pressed',String(id===selected));button.append(node('span',labels[state],'badge'),node('span',id,'id'),node('span',n.text,'text'));for(const key of n.groups)button.append(node('span',key,'tag'));
   button.onclick=()=>{selected=id;document.querySelectorAll('.spec').forEach(card=>card.setAttribute('aria-pressed',String(card.dataset.specId===id)));detail();};rail.append(button);}
  if(!entries.length)rail.append(node('p',g?'該当する仕様はありません。':'リポジトリを開いてください。','empty'));
  $('list').append(section);
 }
 $('count').textContent=total+'件';
 detail();
}
function go(id){const g=data.graph;if(id==='null')return;group=null;selected=id;$('search').value='';render();const card=Array.from(document.querySelectorAll('.spec')).find(e=>e.dataset.specId===id);if(card){card.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'});card.focus({preventScroll:true});}}
function detail(){const root=$('detail');root.replaceChildren();const g=data?.graph,n=g&&selected!==null&&(g.nodes[selected]||g.proposals[selected]);if(!n){root.append(node('h2','仕様を選択'),node('p','本文と、その仕様を生んだ意図・後続の変更を確認できます。'));return;}
 root.append(node('h2',labels[g.proposals[selected]?'future':n.state]+'の仕様'),node('code',selected),node('p',n.text,'body'));
 for(const key of n.groups)root.append(node('span',g.spec_groups[key].description,'tag'));
 for(const [heading,predicate] of [['この仕様を生んだ意図',i=>i.after.includes(selected)],['後続の変更・予想',i=>i.before.includes(selected)]]){
 root.append(node('h3',heading));const found=Object.entries(g.intents).filter(([,i])=>predicate(i));if(!found.length)root.append(node('p','まだありません。'));
 for(const [id,i] of found){const box=node('section','','intent');box.append(node('span',i.state==='applied'?'適用済み':i.issue===null?'予想':'計画','badge'),node('p',i.text),node('code',id),node('p',i.group));
 for(const kind of ['issue','pr'])if(i[kind]!==null)box.append(node('span',`${kind.toUpperCase()} #${i[kind]} · ${data.statuses[`${kind}:${i[kind]}`]||'未取得'}`,'tag'));
 if(i.state==='planned'&&i.before.some(ref=>g.nodes[ref].state==='past'))box.append(node('p','変更元が過去のため再検討が必要です。','note'));
 for(const [label,refs] of [['変更前',i.before],['変更後',i.after]])for(const ref of refs){const b=node('button',label+' · '+ref);b.disabled=ref==='null';b.onclick=()=>go(ref);box.append(b);}root.append(box);}
 }
}
$('open').onclick=()=>request('open_local');$('refresh').onclick=()=>request('snapshot');$('github').onclick=()=>$('github-dialog').showModal();$('cancel').onclick=()=>$('github-dialog').close();
$('github-form').onsubmit=event=>{event.preventDefault();$('github-dialog').close();request('open_github',$('repository').value.trim());};
$('search').oninput=()=>{selected=null;render();};
window.addEventListener('pywebviewready',()=>request('snapshot'));render();
