"""Conditional reads through local gh; persist graph/status metadata only."""
import base64
import json
import re
import subprocess
from .core import GraphError, require, validate


def conditional_api(endpoint, etag=None):
    command = ['gh', 'api', '--include', endpoint]
    if etag:
        command += ['-H', 'If-None-Match: ' + etag]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        headers, separator, body = result.stdout.partition('\n\n')
        require(bool(separator), 'invalid GitHub HTTP response')
        status = int(headers.splitlines()[0].split()[1])
        response_etag = next((line.split(':', 1)[1].strip() for line in headers.splitlines()
                              if line.lower().startswith('etag:')), etag)
        if status == 304:
            return None, response_etag
        require(result.returncode == 0 and status == 200, f'GitHub read failed ({status}): {endpoint}')
        return json.loads(body), response_etag
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as exc:
        raise GraphError(f'GitHub read failed for {endpoint}; check gh authentication and repository access') from exc


def sync(repository, cache):
    require(bool(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository)), 'invalid repository')
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (repository.replace('/', '__') + '.json')
    old = json.loads(path.read_text()) if path.exists() else {}
    etags = {}
    payload, etags['graph'] = conditional_api(f'repos/{repository}/contents/.spec-graph/graph.json', old.get('etags', {}).get('graph'))
    if payload is None:
        require('graph' in old, '304 response without cached graph')
        graph, sha = validate(old['graph']), old['sha']
    else:
        graph = validate(json.loads(base64.b64decode(payload['content'])))
        sha = payload['sha']
    require(graph['repository'] == repository, 'graph repository identity mismatch')
    statuses = {}
    for intent in graph['intents'].values():
        for kind, endpoint in (('issue', 'issues'), ('pr', 'pulls')):
            number = intent[kind]
            if number is not None:
                key = f'{kind}:{number}'
                item, etags[key] = conditional_api(f'repos/{repository}/{endpoint}/{number}', old.get('etags', {}).get(key))
                if item is None:
                    require(key in old.get('statuses', {}), '304 response without cached status')
                    statuses[key] = old['statuses'][key]
                else:
                    statuses[key] = ('merged' if item.get('merged_at') else 'draft' if item.get('draft') and item['state'] == 'open' else item['state'])
    result = {'sha': sha, 'graph': graph, 'statuses': statuses, 'etags': etags}
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    temp.replace(path)
    return result
