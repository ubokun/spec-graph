import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from importlib.resources import files
from pathlib import Path
import sys
from .core import GraphError, apply_intent, check_pr, graph_diff, require, validate
from .github import sync

DEFAULT = '.spec-graph/graph.json'

def read(path):
    return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)

def initial(repository):
    return {'version': 1, 'repository': repository, 'spec_groups': {},
            'intent_groups': {'spec-graph:correctness@1': {
                'description': 'Observable behavioral correctness',
                'measurement': 'Run automated acceptance and regression checks; record commands and outcomes.',
                'evidence': 'Provide reproducible commands and results, with links or paths to supporting artifacts.',
                'issue_sections': ['Intent', 'Acceptance criteria', 'Measurement'],
                'pr_sections': ['Intent', 'Changes', 'Evidence']}},
            'nodes': {'null': {'text': '', 'groups': [], 'state': 'current'}},
            'proposals': {}, 'intents': {}}

def serve(args):
    assets = files('spec_graph').joinpath('assets')
    cache = Path(args.cache)
    def snapshot():
        return sync(args.repo, cache) if args.repo else {'graph': validate(read(args.graph)), 'statuses': {}}
    static_assets = {
        '/': ('viewer.html', 'text/html; charset=utf-8'),
        **{f'/assets/{name}': (name, mime) for name, mime in [
            ('viewer.css', 'text/css; charset=utf-8'),
            ('viewer.js', 'text/javascript; charset=utf-8'),
            ('graph-model.js', 'text/javascript; charset=utf-8'),
            ('cytoscape.min.js', 'text/javascript; charset=utf-8'),
            ('cytoscape-dagre.min.js', 'text/javascript; charset=utf-8'),
            ('THIRD_PARTY_LICENSES.txt', 'text/plain; charset=utf-8'),
        ]},
    }
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/api/graph' and self.path not in static_assets:
                self.send_error(404); return
            try:
                if self.path == '/api/graph':
                    content = json.dumps(snapshot(), ensure_ascii=False).encode()
                    mime = 'application/json; charset=utf-8'
                else:
                    filename, mime = static_assets[self.path]
                    content = assets.joinpath(filename).read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
                self.end_headers(); self.wfile.write(content)
            except (GraphError, OSError, ValueError, KeyError) as exc:
                self.send_error(502, str(exc))
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Spec-Graph: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

def main():
    parser = argparse.ArgumentParser(prog='spec-graph')
    parser.add_argument('--graph', default=DEFAULT)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--repo', required=True)
    sub.add_parser('validate')
    apply = sub.add_parser('apply'); apply.add_argument('intent')
    diff = sub.add_parser('diff'); diff.add_argument('--base', required=True)
    ci = sub.add_parser('ci'); ci.add_argument('--base', required=True)
    ci.add_argument('--pr', type=int, required=True); ci.add_argument('--pr-body', required=True); ci.add_argument('--issue-body', required=True)
    view = sub.add_parser('view'); view.add_argument('--repo'); view.add_argument('--port', type=int, default=8765)
    view.add_argument('--cache', default='.spec-graph/cache')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            require(not Path(args.graph).exists(), 'graph already exists')
            skill = Path('.agents/skills/spec-graph-atomizer/SKILL.md')
            require(not skill.exists(), 'Atomizer skill already exists; refusing to overwrite')
            graph = validate(initial(args.repo))
            skill.parent.mkdir(parents=True, exist_ok=True)
            skill.write_text(files('spec_graph').joinpath('assets/atomizer/SKILL.md').read_text())
            write(args.graph, graph)
            print('Initialized graph and Atomizer skill. Ignore .spec-graph/cache/ in Git.')
        elif args.command == 'view':
            serve(args)
        else:
            graph = validate(read(args.graph))
            if args.command == 'validate':
                print('Graph is valid.')
            elif args.command == 'apply':
                write(args.graph, apply_intent(graph, args.intent)); print('Intent applied.')
            elif args.command == 'diff':
                print(json.dumps(graph_diff(read(args.base), graph), indent=2))
            else:
                matches = [i for i in graph['intents'].values() if i['pr'] == args.pr]
                require(len(matches) == 1, 'PR must link exactly one intent')
                issue = matches[0]['issue']
                result = check_pr(read(args.base), graph, args.pr, Path(args.pr_body).read_text(), {issue: Path(args.issue_body).read_text()})
                print(json.dumps(result, indent=2))
    except (GraphError, OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr); raise SystemExit(1)
