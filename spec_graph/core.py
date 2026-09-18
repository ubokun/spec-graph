"""Graph invariants and append-only transitions; no network or filesystem access."""
from copy import deepcopy
import re

class GraphError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise GraphError(message)

def fields(value, keys, label):
    require(isinstance(value, dict) and set(value) == set(keys.split()), f"{label}: expected fields {keys}")

def nonempty(value):
    return isinstance(value, str) and bool(value.strip())

def ids(value, label, allow_empty=False):
    require(isinstance(value, list) and (allow_empty or value), f"{label}: expected list")
    require(all(nonempty(x) for x in value), f"{label}: expected string IDs")
    require(len(value) == len(set(value)), f"{label}: duplicate IDs")

def validate(graph):
    fields(graph, "version repository spec_groups intent_groups nodes proposals intents", "graph")
    require(type(graph['version']) is int and graph['version'] == 1, 'unsupported graph version')
    require(isinstance(graph['repository'], str) and re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', graph['repository']), 'repository must be OWNER/REPO')
    for key in ('spec_groups', 'intent_groups', 'nodes', 'proposals', 'intents'):
        require(isinstance(graph[key], dict), f'{key}: expected object')
        require(all(nonempty(k) for k in graph[key]), f'{key}: empty ID')
    for name, group in graph['spec_groups'].items():
        fields(group, 'description', name)
        require(nonempty(group['description']), f'{name}: description required')
    for name, group in graph['intent_groups'].items():
        fields(group, 'description measurement evidence issue_sections pr_sections', name)
        require('@' in name and ':' in name, f'{name}: use globally namespaced versioned ID')
        for key in ('description', 'measurement', 'evidence'):
            require(nonempty(group[key]), f'{name}: {key} required')
        for key in ('issue_sections', 'pr_sections'):
            ids(group[key], f'{name}.{key}')
    nodes, proposals = graph['nodes'], graph['proposals']
    require(nodes.get('null') == {'text': '', 'groups': [], 'state': 'current'}, 'null node must be canonical')
    require(not set(nodes) & set(proposals), 'node and proposal IDs overlap')
    for collection, is_node in ((nodes, True), (proposals, False)):
        for name, node in collection.items():
            if name == 'null' and is_node:
                continue
            fields(node, 'text groups state' if is_node else 'text groups', name)
            require(nonempty(node['text']), f'{name}: natural-language spec required')
            ids(node['groups'], name + '.groups')
            require(set(node['groups']) <= set(graph['spec_groups']), f'{name}: unknown spec-group')
            if is_node:
                require(node['state'] in ('past', 'current'), f'{name}: invalid state')
    produced, consumed, proposed = {}, {}, {}
    references = {'issue': set(), 'pr': set()}
    for name, intent in graph['intents'].items():
        fields(intent, 'text group state before after issue pr', name)
        require(nonempty(intent['text']), f'{name}: intent rationale required')
        require(isinstance(intent['group'], str) and intent['group'] in graph['intent_groups'], f'{name}: unknown intent-group')
        require(intent['state'] in ('planned', 'applied'), f'{name}: invalid intent state')
        for ref in ('issue', 'pr'):
            value = intent[ref]
            require(value is None or (type(value) is int and value > 0), f'{name}: invalid {ref}')
            if value is not None:
                require(value not in references[ref], f'{name}: {ref} already linked')
                references[ref].add(value)
        require(intent['pr'] is None or intent['issue'] is not None, f'{name}: PR requires issue')
        ids(intent['before'], name + '.before'); ids(intent['after'], name + '.after')
        require(set(intent['before']) <= set(nodes), f'{name}: missing source node')
        require('null' not in intent['after'], f'{name}: cannot produce null')
        require('null' not in intent['before'] or intent['before'] == ['null'], f'{name}: null must be sole source')
        require(not set(intent['before']) & set(intent['after']), f'{name}: self edge')
        applied = intent['state'] == 'applied'
        targets = nodes if applied else proposals
        require(set(intent['after']) <= set(targets), f'{name}: missing target')
        for target in intent['after']:
            owners = produced if applied else proposed
            require(target not in owners, f'{target}: multiple producers')
            owners[target] = name
        if applied:
            require(intent['issue'] is not None, f'{name}: applied intent requires issue')
            for source in intent['before']:
                if source != 'null':
                    require(source not in consumed, f'{source}: multiple applied successors')
                    consumed[source] = name
    require(set(produced) == set(nodes) - {'null'}, 'every node requires an applied producer')
    require(set(proposed) == set(proposals), 'every proposal requires one planned producer')
    for name, node in nodes.items():
        if name != 'null':
            require(node['state'] == ('past' if name in consumed else 'current'), f'{name}: incorrect temporal state')
    # Reachability from null also rejects cycles and disconnected components.
    reachable = {'null'}
    pending = [i for i in graph['intents'].values() if i['state'] == 'applied']
    while pending:
        ready = [i for i in pending if set(i['before']) <= reachable]
        require(ready, 'applied graph contains a cycle or unreachable component')
        for intent in ready:
            reachable.update(intent['after']); pending.remove(intent)
    return graph

def apply_intent(graph, intent_id):
    validate(graph)
    result = deepcopy(graph)
    require(intent_id in result['intents'], 'unknown intent')
    intent = result['intents'][intent_id]
    require(intent['state'] == 'planned', 'intent already applied')
    require(intent['issue'] is not None, 'link an issue before applying')
    for source in intent['before']:
        require(result['nodes'][source]['state'] == 'current', f'{source}: stale intent; rebase it')
        if source != 'null':
            result['nodes'][source]['state'] = 'past'
    for target in intent['after']:
        result['nodes'][target] = {**result['proposals'].pop(target), 'state': 'current'}
    intent['state'] = 'applied'
    return validate(result)

def graph_diff(base, head):
    validate(base); validate(head)
    require(base['repository'] == head['repository'], 'repository identity changed')
    for key in ('spec_groups', 'intent_groups'):
        for name, value in base[key].items():
            require(head[key].get(name) == value, f'{key}/{name}: immutable; add a new ID/version')
    for name, node in base['nodes'].items():
        require(name in head['nodes'], f'{name}: historical node deleted')
        new = head['nodes'][name]
        require(node['text'] == new['text'] and node['groups'] == new['groups'], f'{name}: historical spec mutated')
        require(node['state'] != 'past' or new['state'] == 'past', f'{name}: past node revived')
    for name, intent in base['intents'].items():
        if intent['state'] == 'applied':
            require(head['intents'].get(name) == intent, f'{name}: applied intent mutated')
    applied = [name for name, i in head['intents'].items() if i['state'] == 'applied' and base['intents'].get(name, {}).get('state') != 'applied']
    for name in applied:
        for source in head['intents'][name]['before']:
            if source in base['nodes']:
                require(base['nodes'][source]['state'] == 'current', f'{name}: source was already past')
    return {'version': 1, 'applied_intents': sorted(applied),
            'added_nodes': sorted(set(head['nodes']) - set(base['nodes'])),
            'retired_nodes': sorted(n for n in base['nodes'] if base['nodes'][n]['state'] != head['nodes'][n]['state']),
            'planned_intents': sorted(n for n, i in head['intents'].items() if i['state'] == 'planned' and base['intents'].get(n) != i)}

def check_sections(body, sections, label):
    # Only top-level H2 sections outside fenced code blocks count.
    found, active, lines, fence = {}, None, [], None
    for line in (body or '').splitlines() + ['## __end__']:
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            char = marker[1][0]
            fence = None if fence == char else (char if fence is None else fence)
            continue
        if fence:
            continue
        if line.startswith('## '):
            if active is not None:
                require(active not in found, f'{label}: duplicate section {active}')
                found[active] = '\n'.join(lines).strip()
            active, lines = line[3:].strip(), []
        else:
            lines.append(line)
    for section in sections:
        require(bool(found.get(section)), f'{label}: missing/empty ## {section}')

def check_pr(base, head, pr_number, pr_body, issue_bodies):
    diff = graph_diff(base, head)
    matches = [(n, i) for n, i in head['intents'].items() if i['pr'] == pr_number]
    require(len(matches) == 1, 'PR must link exactly one intent')
    name, intent = matches[0]
    require(all(n == name for n in diff['applied_intents']), 'PR applies an unrelated intent')
    group = head['intent_groups'][intent['group']]
    check_sections(pr_body, group['pr_sections'], 'PR')
    require(intent['issue'] in issue_bodies, 'linked issue body missing')
    check_sections(issue_bodies[intent['issue']], group['issue_sections'], 'Issue')
    return diff
