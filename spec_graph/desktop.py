"""Native window with a read-only bridge to existing graph operations."""
import argparse
import json
import os
from importlib.resources import files
from pathlib import Path
from threading import Lock
from .core import validate
from .github import sync

class DesktopAPI:
    def __init__(self, graph=None):
        self._graph = Path(graph).resolve() if graph else None
        self._repository = None
        self._window = None
        self._lock = Lock()
        self._cache = Path.home() / 'Library' / 'Caches' / 'Spec-Graph'

    def snapshot(self):
        with self._lock:
            try:
                if self._repository:
                    return {'ok': True, **sync(self._repository, self._cache)}
                if self._graph:
                    return {'ok': True, 'graph': validate(json.loads(self._graph.read_text())), 'statuses': {}, 'source': str(self._graph)}
                return {'ok': True, 'graph': None, 'statuses': {}}
            except (ValueError, OSError, KeyError) as exc:
                return {'ok': False, 'error': str(exc)}

    def open_local(self):
        import webview
        selected = self._window.create_file_dialog(webview.FileDialog.OPEN, allow_multiple=False, file_types=('Graph JSON (*.json)',))
        if not selected:
            return {'cancelled': True}
        try:
            path = Path(selected[0]).resolve()
            validate(json.loads(path.read_text()))
            with self._lock:
                self._graph, self._repository = path, None
            return self.snapshot()
        except (ValueError, OSError) as exc:
            return {'ok': False, 'error': str(exc)}

    def open_github(self, repository):
        # Do not replace the current selection until a new source loads successfully.
        try:
            with self._lock:
                result = sync(repository, self._cache)
                self._repository = repository
                return {'ok': True, **result}
        except (ValueError, OSError, KeyError, TypeError) as exc:
            return {'ok': False, 'error': str(exc)}

def main():
    parser = argparse.ArgumentParser(prog='spec-graph-desktop')
    parser.add_argument('--graph', help='Graph JSON to open at startup')
    args = parser.parse_args()
    try:
        import webview
    except ImportError:
        parser.exit(1, 'Install desktop support: pip install "spec-graph[desktop]"\n')
    # Finder-launched applications do not inherit a shell PATH.
    os.environ['PATH'] = os.environ.get('PATH', '') + os.pathsep + '/opt/homebrew/bin:/usr/local/bin'
    assets = files('spec_graph').joinpath('assets')
    html = assets.joinpath('desktop.html').read_text()
    html = html.replace('/* DESKTOP_CSS */', assets.joinpath('desktop.css').read_text())
    html = html.replace('/* DESKTOP_JS */', assets.joinpath('desktop.js').read_text())
    api = DesktopAPI(args.graph)
    window = webview.create_window('Spec-Graph', html=html, js_api=api, width=1280, height=820,
                                   min_size=(900, 600), background_color='#10151e', text_select=True)
    api._window = window
    webview.start(private_mode=True)

if __name__ == '__main__':
    main()
