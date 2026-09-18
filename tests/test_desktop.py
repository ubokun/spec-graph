from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from spec_graph.desktop import DesktopAPI
from spec_graph.core import GraphError

ROOT = Path(__file__).resolve().parents[1]
class DesktopTests(unittest.TestCase):
    def test_empty_start_and_local_file(self):
        self.assertIsNone(DesktopAPI().snapshot()['graph'])
        result = DesktopAPI(ROOT/'examples/graph.json').snapshot()
        self.assertTrue(result['ok'])
        self.assertEqual(result['graph']['repository'], 'example/spec-graph-demo')

    def test_invalid_local_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'graph.json';path.write_text('{}')
            self.assertFalse(DesktopAPI(path).snapshot()['ok'])
        self.assertFalse(DesktopAPI(path).snapshot()['ok'])

    def test_failed_github_switch_preserves_current_source(self):
        api=DesktopAPI(ROOT/'examples/graph.json')
        with patch('spec_graph.desktop.sync',side_effect=GraphError('offline')):
            self.assertFalse(api.open_github('example/missing')['ok'])
        self.assertEqual(api.snapshot()['graph']['repository'],'example/spec-graph-demo')

    def test_github_switch_and_refresh(self):
        api=DesktopAPI()
        response={'graph':{'repository':'example/demo'},'statuses':{}}
        with patch('spec_graph.desktop.sync',return_value=response) as sync:
            self.assertTrue(api.open_github('example/demo')['ok'])
            self.assertEqual(api.snapshot()['graph']['repository'],'example/demo')
            self.assertEqual(sync.call_count,2)
