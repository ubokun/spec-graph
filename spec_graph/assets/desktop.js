'use strict';
const $=id=>document.getElementById(id);
const node=(tag,text,cls)=>{const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;return e;};
let data=null,tab='current',group=null,selected=null,busy=false;
const labels={current:'現在',past:'過去',future:'予想・計画'};
async function request(method,...args){
 if(busy)return;busy=true;for(const id of ['open','github','refresh'])$(id).disabled=true;
 try{const result=await window.pywebview.api[method](...args);if(result.cancelled)return;if(!result.ok)throw new Error(result.error);data=result;selected=null;group=null;render();$('error').hidden=true;}
 catch(error){$('error').textContent=error.message;$('error').hidden=false;}
 finally{busy=false;for(const id of ['open','github','refresh'])$(id).disabled=false;}
}
function render(){
 const g=data?.graph;$('repo').textContent=g?.repository||'未選択';$('source').textContent=g?(data.source?'ローカルファイル':'GitHub · default branch'):'ファイルまたはGitHubリポジトリを開いてください。';
 $('heading').textContent=tab==='current'?'現在の仕様':tab==='past'?'過去の仕様':'予想・計画';
 document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===tab)));
 $('groups').replaceChildren();if(g){for(const [id,label] of [[null,'すべての仕様'],...Object.entries(g.spec_groups).map(([id,v])=>[id,v.description])]){const b=node('button',label);b.setAttribute('aria-pressed',String(group===id));b.onclick=()=>{group=id;selected=null;render();};$('groups').append(b);}}
 const query=$('search').value.toLocaleLowerCase();
 const entries=g?Object.entries(tab==='future'?g.proposals:g.nodes).filter(([id,n])=>id!=='null'&&(tab==='future'||n.state===tab)&&(!group||n.groups.includes(group))&&(`${id} ${n.text}`).toLocaleLowerCase().includes(query)):[];
 $('count').textContent=entries.length+'件';$('list').replaceChildren();
 for(const [id,n] of entries){const b=node('button','',`spec ${tab}`);b.setAttribute('aria-pressed',String(id===selected));b.append(node('span',labels[tab],'badge'),node('span',id,'id'),node('span',n.text,'text'));for(const key of n.groups)b.append(node('span',key,'tag'));b.onclick=()=>{selected=id;render();};$('list').append(b);}
 if(!entries.length)$('list').append(node('p',g?'該当する仕様はありません。':'リポジトリを開くと、現在の仕様をここに表示します。','empty'));
 detail();
}
function go(id){const g=data.graph;if(id==='null')return;tab=g.proposals[id]?'future':g.nodes[id].state;group=null;selected=id;$('search').value='';render();}
function detail(){const root=$('detail');root.replaceChildren();const g=data?.graph,n=g&&selected!==null&&(g.nodes[selected]||g.proposals[selected]);if(!n){root.append(node('h2','仕様を選択'),node('p','本文と、その仕様を生んだ意図・後続の変更を確認できます。'));return;}
 root.append(node('h2',labels[tab]+'の仕様'),node('code',selected),node('p',n.text,'body'));
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
$('search').oninput=render;document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;selected=null;render();});
window.addEventListener('pywebviewready',()=>request('snapshot'));render();
