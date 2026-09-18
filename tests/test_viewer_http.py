import json
from pathlib import Path
import subprocess
import sys
import unittest
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

class ViewerHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.process = subprocess.Popen([sys.executable, '-m', 'spec_graph', '--graph', str(ROOT/'examples/graph.json'), 'view', '--port', '0'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        cls.url = cls.process.stdout.readline().strip().split()[-1]

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)
        cls.process.stdout.close()

    def test_offline_assets_and_graph(self):
        for path, mime in [('/', 'text/html'), ('/assets/viewer.js', 'text/javascript'),
                           ('/assets/viewer.css', 'text/css'), ('/assets/graph-model.js', 'text/javascript'),
                           ('/assets/cytoscape.min.js', 'text/javascript'), ('/assets/cytoscape-dagre.min.js', 'text/javascript'),
                           ('/assets/THIRD_PARTY_LICENSES.txt', 'text/plain')]:
            with self.subTest(path=path), urllib.request.urlopen(self.url+path) as response:
                self.assertEqual(response.headers.get_content_type(), mime)
                self.assertTrue(response.read())
                self.assertIn("script-src 'self';", response.headers['Content-Security-Policy'])
        with urllib.request.urlopen(self.url+'/api/graph') as response:
            self.assertEqual(json.load(response)['graph']['repository'], 'example/spec-graph-demo')

    def test_arbitrary_local_files_are_not_served(self):
        for path in ['/assets/../cli.py', '/assets/%2e%2e/cli.py', '/.spec-graph/graph.json']:
            with self.subTest(path=path), self.assertRaises(urllib.error.HTTPError) as raised:
                urllib.request.urlopen(self.url+path)
            self.assertEqual(raised.exception.code,404)
            raised.exception.close()
