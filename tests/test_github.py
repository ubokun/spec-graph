import base64
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from spec_graph.core import GraphError
from spec_graph.github import conditional_api, sync
from test_graph import plan

class GitHubTests(unittest.TestCase):
    def test_conditional_http(self):
        response = subprocess.CompletedProcess([], 0, 'HTTP/2.0 200 OK\nEtag: "abc"\n\n{"state":"open"}', '')
        with patch('spec_graph.github.subprocess.run', return_value=response) as run:
            self.assertEqual(conditional_api('repos/example/demo', '"old"'), ({'state':'open'}, '"abc"'))
            self.assertIn('If-None-Match: "old"', run.call_args.args[0])
        response.stdout='HTTP/2.0 304 Not Modified\nEtag: "abc"\n\n'
        with patch('spec_graph.github.subprocess.run', return_value=response):
            self.assertEqual(conditional_api('repos/example/demo'), (None, '"abc"'))
    def test_status_refresh_without_graph_change(self):
        graph=plan()
        payload={'sha':'abc','content':base64.b64encode(json.dumps(graph).encode()).decode()}
        with tempfile.TemporaryDirectory() as tmp:
            cache=Path(tmp)
            with patch('spec_graph.github.conditional_api', side_effect=[(payload,'g'),({'state':'open','body':'PRIVATE'},'i'),({'state':'open','draft':True},'p')]):
                first=sync('example/demo',cache)
            self.assertEqual(first['statuses']['pr:2'],'draft')
            with patch('spec_graph.github.conditional_api', side_effect=[(None,'g'),(None,'i'),({'state':'closed','merged_at':'today'},'p2')]) as request:
                second=sync('example/demo',cache)
            self.assertEqual(second['graph'],graph)
            self.assertEqual(second['statuses']['pr:2'],'merged')
            self.assertEqual(request.call_count,3)
            self.assertNotIn('PRIVATE',next(cache.glob('*.json')).read_text())
            before=next(cache.glob('*.json')).read_bytes()
            with patch('spec_graph.github.conditional_api', side_effect=GraphError('offline')):
                with self.assertRaises(GraphError): sync('example/demo',cache)
            self.assertEqual(next(cache.glob('*.json')).read_bytes(),before)
