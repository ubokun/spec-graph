const test = require('node:test');
const assert = require('node:assert/strict');
const cy = require('../spec_graph/assets/cytoscape.min.js');
cy.use(require('../spec_graph/assets/cytoscape-dagre.min.js'));
const {project, specKey, intentKey} = require('../spec_graph/assets/graph-model.js');
const example = require('../examples/graph.json');
test('shared specs appear once, forecast targets stay proposals, input stays unchanged',()=>{
  const before=JSON.stringify(example), elements=project(example);
  assert.equal(elements.filter(e=>e.data.id===specKey('spec:login:v1')).length,1);
  assert.equal(elements.find(e=>e.data.id===specKey('spec:login:v2')).data.state,'proposal');
  assert.equal(elements.filter(e=>e.classes==='pending').length,2);
  assert.equal(JSON.stringify(example),before);
});
test('many-to-many intent is one junction with m+n edges; IDs cannot collide',()=>{
  const graph={nodes:{null:{text:'',groups:[],state:'current'},a:{text:'A',groups:[],state:'past'},b:{text:'B',groups:[],state:'past'},c:{text:'C',groups:[],state:'current'},d:{text:'D',groups:[],state:'current'}},proposals:{},intents:{a:{text:'merge/split',state:'applied',before:['a','b'],after:['c','d'],issue:1,pr:2}}};
  const elements=project(graph);
  assert.equal(elements.filter(e=>e.data.kind==='intent').length,1);
  assert.equal(elements.filter(e=>e.data.source).length,4);
  assert.equal(new Set(elements.map(e=>e.data.id)).size,elements.length);
  const ids=new Set(elements.map(e=>e.data.id));
  for(const e of elements.filter(e=>e.data.source)){assert.ok(ids.has(e.data.source));assert.ok(ids.has(e.data.target));}
});
test('filters keep endpoints and omit unrelated nodes',()=>{
  const elements=project(example,'planned');
  assert.ok(elements.find(e=>e.data.id===specKey('spec:login:v1')));
  assert.ok(!elements.find(e=>e.data.id===specKey('null')));
  assert.ok(!elements.find(e=>e.data.id===intentKey('intent:bootstrap')));
});
test('null-only graph is visible; empty filter is truly empty',()=>{
  const graph={nodes:{null:{text:'',groups:[],state:'current'}},proposals:{},intents:{}};
  assert.equal(project(graph).length,1);
  assert.equal(project(graph,'planned').length,0);
});
test('bundled Dagre lays out real graph from left to right',()=>{
  const graph=cy({headless:true,elements:project(example)});
  graph.layout({name:'dagre',rankDir:'LR'}).run();
  const chain=[specKey('null'),intentKey('intent:bootstrap'),specKey('spec:login:v1'),intentKey('intent:passkey'),specKey('spec:login:v2')];
  for(let i=1;i<chain.length;i++)assert.ok(graph.getElementById(chain[i]).position('x')>graph.getElementById(chain[i-1]).position('x'));
  graph.destroy();
});
