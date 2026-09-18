from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from spec_graph.cli import initial
from spec_graph.core import GraphError, apply_intent, check_pr, graph_diff, validate
from spec_graph import github

ROOT = Path(__file__).resolve().parents[1]

def plan():
    graph = initial('example/demo')
    graph['spec_groups']['screen'] = {'description': 'Screen'}
    graph['proposals']['a'] = {'text': 'A user can sign in.', 'groups': ['screen']}
    graph['intents']['first'] = {'text': 'Enable account access.', 'group': 'spec-graph:correctness@1',
                                'state': 'planned', 'before': ['null'], 'after': ['a'], 'issue': 1, 'pr': 2}
    return graph

class GraphTests(unittest.TestCase):
    def test_null_initialization(self):
        validate(initial('example/demo'))
    def test_forecast_does_not_change_truth(self):
        g = plan(); g['intents']['first'].update(issue=None, pr=None)
        validate(g)
        self.assertEqual(list(g['nodes']), ['null'])
        with self.assertRaises(GraphError): apply_intent(g, 'first')
    def test_apply_does_not_mutate_input(self):
        g = plan(); before = deepcopy(g); head = apply_intent(g, 'first')
        self.assertEqual(g, before); self.assertEqual(head['nodes']['a']['state'], 'current')
        self.assertEqual(head['proposals'], {})
    def test_many_to_many_and_stale_prediction(self):
        g = plan(); g['proposals']['b'] = {'text': 'Second spec.', 'groups': ['screen']}
        g['intents']['first']['after'].append('b'); g = apply_intent(g, 'first')
        for name, issue in [('second', 3), ('competing', None)]:
            g['proposals'][name+'1'] = {'text': 'A replacement.', 'groups': ['screen']}
            g['proposals'][name+'2'] = {'text': 'Another replacement.', 'groups': ['screen']}
            g['intents'][name] = {'text': 'Improve workflow.', 'group': 'spec-graph:correctness@1', 'state': 'planned',
                                  'before': ['a', 'b'], 'after': [name+'1', name+'2'], 'issue': issue, 'pr': None}
        h = apply_intent(g, 'second'); validate(h)
        self.assertEqual(h['nodes']['a']['state'], 'past')
        self.assertEqual(graph_diff(g,h)['retired_nodes'], ['a','b'])
        h['intents']['competing']['issue'] = 4
        with self.assertRaisesRegex(GraphError, 'stale'): apply_intent(h, 'competing')
    def test_invalid_structures(self):
        for change in [lambda g:g['proposals']['a'].update(groups=['missing']),
                       lambda g:g['intents']['first'].update(before=['absent']),
                       lambda g:g['intents']['first'].update(issue=True),
                       lambda g:g['intents']['first'].update(after=['a','a']),
                       lambda g:g['nodes']['null'].update(state='past')]:
            with self.subTest(change=change):
                g=plan(); change(g)
                with self.assertRaises(GraphError): validate(g)
    def test_duplicate_links(self):
        g=plan(); g['proposals']['b']=deepcopy(g['proposals']['a'])
        g['intents']['second']={**g['intents']['first'],'after':['b']}
        with self.assertRaisesRegex(GraphError,'already linked'): validate(g)
    def test_cycle_rejected(self):
        g=apply_intent(plan(),'first')
        g['intents']['first']['before']=['b']; g['nodes']['a']['state']='past'
        g['nodes']['b']={'text':'B','groups':['screen'],'state':'past'}
        g['intents']['second']={**g['intents']['first'],'before':['a'],'after':['b'],'issue':3,'pr':4}
        with self.assertRaisesRegex(GraphError,'cycle'): validate(g)
    def test_history_mutation_rejected(self):
        g=apply_intent(plan(),'first'); h=deepcopy(g); h['nodes']['a']['text']='Rewritten'
        with self.assertRaisesRegex(GraphError,'mutated'): graph_diff(g,h)
    def test_applied_intent_cannot_be_rewritten(self):
        g=apply_intent(plan(),'first'); h=deepcopy(g); h['intents']['first']['text']='Different reason'
        with self.assertRaisesRegex(GraphError,'mutated'): graph_diff(g,h)
    def test_ci_formats_and_mapping(self):
        g=apply_intent(plan(),'first'); base=initial('example/demo')
        pr=(ROOT/'examples/pr.md').read_text(); issue=(ROOT/'examples/issue.md').read_text()
        self.assertEqual(check_pr(base,g,2,pr,{1:issue})['applied_intents'],['first'])
        for body in ['', '```\n'+pr+'\n```', '## Intent\n## Changes\n## Evidence\n']:
            with self.assertRaises(GraphError): check_pr(base,g,2,body,{1:issue})
        with self.assertRaises(GraphError): check_pr(base,g,99,pr,{1:issue})
    def test_group_redefinition_rejected(self):
        g=plan(); h=deepcopy(g); h['intent_groups']['spec-graph:correctness@1']['measurement']='Skip'
        with self.assertRaisesRegex(GraphError,'immutable'): graph_diff(g,h)

if __name__ == '__main__': unittest.main()
