/* global cytoscape, cytoscapeDagre, SpecGraphModel */
'use strict';
const $ = id => document.getElementById(id);
const el = (tag, text, className) => {
  const element = document.createElement(tag);
  element.textContent = text;
  if (className) element.className = className;
  return element;
};
const names = {origin:'起点',current:'現在',past:'過去',proposal:'候補',applied:'適用済み',forecast:'予想',planned:'計画'};
let snapshot, cy, selectedId;
cytoscape.use(cytoscapeDagre);
function layoutOptions() {
  const narrow=$('graph').clientWidth<650;
  return {name:'dagre',rankDir:narrow?'TB':'LR',rankSep:narrow?25:70,nodeSep:65,edgeSep:20,nodeDimensionsIncludeLabels:true,padding:30,animate:false};
}
function overview() {
  selectedId = null;
  $('details').replaceChildren(el('div','INSPECTOR','eyebrow'),el('h2','つながりから仕様を読む'),
    el('p','丸い点がSpec、菱形がIntentです。矢印をたどると、どの意図で仕様が変わったかを確認できます。'),
    el('p','点または線をクリックしてください。ノード一覧からも選択できます。'));
  if (cy) cy.elements().removeClass('dimmed focused');
}
function select(id, center=false) {
  const node = cy.getElementById(id);
  if (!node.length) return;
  selectedId=id;
  const data=node.data(), graph=snapshot.graph, details=$('details');
  details.replaceChildren(el('div',data.kind==='intent'?'INTENT / 変更の意図':'SPEC / 仕様','eyebrow'),
    el('span',names[data.state],'tag'),el('h2',data.text || '∅ nullnode'),el('code',data.ref));
  let neighborhood = node.closedNeighborhood();
  if(data.kind==='spec') neighborhood=neighborhood.union(node.neighborhood('node').closedNeighborhood());
  cy.elements().addClass('dimmed').removeClass('focused');
  neighborhood.removeClass('dimmed'); node.addClass('focused');
  if(data.kind==='spec') {
    for(const group of data.groups) details.append(el('span',group,'tag'));
    details.append(el('p',data.state==='proposal'?'まだ適用されていない仕様候補です。':data.state==='past'?'後続のIntentにより置き換えられた仕様です。':data.state==='origin'?'仕様のない起点です。':'このスナップショットで現在の仕様です。'));
  } else {
    const intent=graph.intents[data.ref];
    details.append(el('p',intent.group));
    for(const kind of ['issue','pr']) if(intent[kind]!==null) {
      details.append(el('span',`${kind.toUpperCase()} #${intent[kind]} · ${snapshot.statuses[`${kind}:${intent[kind]}`] || '未取得'}`,'tag'));
    }
    if(intent.issue===null) details.append(el('p','Issue未対応の予想Intentです。現在の仕様は変更しません。'));
    if(intent.state==='planned' && intent.before.some(ref=>graph.nodes[ref].state==='past')) details.append(el('p','要更新：変更元が過去の仕様になっています。'));
    for(const [label, refs] of [['変更前',intent.before],['変更後',intent.after]]) {
      details.append(el('p',label));
      for(const ref of refs) {const button=el('button',ref,'relation');button.onclick=()=>select(SpecGraphModel.specKey(ref),true);details.append(button);}
    }
  }
  if(center) cy.animate({center:{eles:node},duration:200});
  renderList();
}
function renderList() {
  if(!cy)return;
  const query=$('search').value.trim().toLocaleLowerCase();
  const nodes=cy.nodes().filter(node=>[node.data('ref'),node.data('text')].some(text=>text.toLocaleLowerCase().includes(query)));
  $('result-count').textContent=String(nodes.length);$('node-list').replaceChildren();
  nodes.forEach(node=>{
    const data=node.data(), button=el('button','','node-option');
    button.setAttribute('aria-pressed',String(selectedId===data.id));
    button.append(el('span',data.kind==='intent'?'◆':'●',data.kind==='intent'?'intent-dot':'dot '+data.state));
    const label=el('span','');label.append(el('small',`${names[data.state]} · ${data.ref}`),el('span',data.label));button.append(label);
    button.onclick=()=>select(data.id,true);$('node-list').append(button);
  });
  if(!nodes.length) $('node-list').append(el('p','一致するノードはありません。'));
}
function render() {
  const graph=snapshot.graph;
  $('repo').textContent=graph.repository;
  const nodes=Object.values(graph.nodes);
  $('counts').textContent=`${nodes.filter(n=>n.state==='current').length-1} 現在  /  ${nodes.filter(n=>n.state==='past').length} 過去  /  ${Object.keys(graph.proposals).length} 候補  /  ${Object.keys(graph.intents).length} Intent`;
  const elements=SpecGraphModel.project(graph,$('filter').value);
  if(cy)cy.destroy();
  cy=cytoscape({container:$('graph'),elements,minZoom:.15,maxZoom:3,wheelSensitivity:.22,layout:layoutOptions(),style:[
    {selector:'node',style:{'background-color':'#173c37','border-color':'#64d9bb','border-width':2,width:54,height:54,label:'data(label)',color:'#c3d3e5','font-size':12,'font-family':'system-ui','text-valign':'bottom','text-margin-y':12,'text-wrap':'wrap','text-overflow-wrap':'anywhere','text-max-width':155,'text-background-color':'#0e1521','text-background-opacity':.9,'text-background-padding':3}},
    ...($('graph').clientWidth<650 ? [{selector:'node',style:{'text-halign':'right','text-valign':'center','text-margin-x':15,'text-margin-y':0,'font-size':14}}] : []),
    {selector:'.past',style:{'background-color':'#1c2838','border-color':'#657990',color:'#93a6be'}},
    {selector:'.origin',style:{width:30,height:30,'background-color':'#192334','border-color':'#526680'}},
    {selector:'.proposal',style:{'background-color':'#3b3020','border-color':'#efbd65','border-style':'dashed',color:'#e7c58e'}},
    {selector:'node.intent',style:{shape:'diamond',width:32,height:32,'background-color':'#2c4067','border-color':'#8cabef','font-size':10,color:'#93ade0'}},
    {selector:'node.forecast, node.planned',style:{'border-style':'dashed','border-color':'#dbb677','background-color':'#433721',color:'#dbb677'}},
    {selector:'edge',style:{width:1.7,'line-color':'#55728c','target-arrow-color':'#7596b4','target-arrow-shape':'triangle','arrow-scale':.85,'curve-style':'bezier'}},
    {selector:'edge.pending',style:{'line-style':'dashed','line-color':'#aa8955','target-arrow-color':'#cfaa6e'}},
    {selector:'.dimmed',style:{opacity:.18}},
    {selector:'node.focused',style:{'border-width':4,'border-color':'#f2f7ff','overlay-color':'#84bfff','overlay-opacity':.12,'overlay-padding':10}}
  ]});
  cy.on('tap','node',event=>select(event.target.id()));
  cy.on('tap','edge',event=>select(SpecGraphModel.intentKey(event.target.data('intent'))));
  cy.on('tap',event=>{if(event.target===cy){overview();renderList();}});
  const zoomLabel=()=>$('zoom').textContent=Math.round(cy.zoom()*100)+'%';cy.on('zoom',zoomLabel);zoomLabel();
  $('empty').hidden=elements.length!==0;
  overview();renderList();
}
async function load() {
  $('refresh').disabled=true;
  try {
    const response=await fetch('/api/graph');
    if(!response.ok)throw new Error(`HTTP ${response.status}`);
    snapshot=await response.json();render();$('error').hidden=true;
  } catch(error) {$('error').textContent='更新に失敗しました。表示中のデータは前回取得分です。 '+error.message;$('error').hidden=false;}
  finally {$('refresh').disabled=false;}
}
$('refresh').onclick=load;$('filter').onchange=()=>{if(snapshot)render();};$('search').oninput=renderList;
$('fit').onclick=()=>{if(cy)cy.fit(undefined,45);};
$('layout').onclick=()=>{if(cy)cy.layout(layoutOptions()).run();};
for(const [id,factor] of [['zoom-in',1.25],['zoom-out',.8]])$(id).onclick=()=>{if(cy)cy.zoom({level:cy.zoom()*factor,renderedPosition:{x:cy.width()/2,y:cy.height()/2}});};
new ResizeObserver(()=>{if(cy)cy.resize();}).observe($('graph'));
load();
