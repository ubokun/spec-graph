/* Pure display projection. The persisted domain model is never modified. */
(function (root) {
  const specKey = id => `spec:${id}`;
  const intentKey = id => `intent:${id}`;
  const short = text => Array.from(text).length > 34 ? Array.from(text).slice(0, 34).join('') + '…' : text;
  function project(graph, filter = 'all') {
    const intents = Object.entries(graph.intents).filter(([, value]) => filter === 'all' || value.state === filter);
    const used = new Set(filter === 'all' ? [...Object.keys(graph.nodes), ...Object.keys(graph.proposals)] : []);
    for (const [, intent] of intents) for (const id of [...intent.before, ...intent.after]) used.add(id);
    const elements = [];
    for (const id of used) {
      const node = graph.nodes[id] || graph.proposals[id];
      const state = id === 'null' ? 'origin' : node.state || 'proposal';
      elements.push({data: {id: specKey(id), ref: id, kind: 'spec', state,
        label: id === 'null' ? '∅ 起点' : short(node.text), text: node.text, groups: node.groups}, classes: state});
    }
    for (const [id, intent] of intents) {
      const state = intent.state === 'applied' ? 'applied' : intent.issue === null ? 'forecast' : 'planned';
      elements.push({data: {id: intentKey(id), ref: id, kind: 'intent', state,
        label: state === 'forecast' ? '予想' : state === 'planned' ? '計画' : 'Intent', text: intent.text}, classes: `intent ${state}`});
      for (const [direction, refs] of [['before', intent.before], ['after', intent.after]]) {
        for (const ref of refs) elements.push({data: {
          id: `edge:${JSON.stringify([id, direction, ref])}`, intent: id,
          source: direction === 'before' ? specKey(ref) : intentKey(id),
          target: direction === 'before' ? intentKey(id) : specKey(ref)
        }, classes: intent.state === 'planned' ? 'pending' : 'applied'});
      }
    }
    return elements;
  }
  const api = {project, specKey, intentKey};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SpecGraphModel = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
