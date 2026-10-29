#!/usr/bin/env python3
"""Chat bridge: dispatch one reel, optionally wait and download its video artifact.

The chat passes a JSON request with the seven user inputs. The printed local MP4
path can be embedded by the chat. Nothing is committed, released or published.
Requires the caller's existing authenticated gh CLI, never an API key in inputs.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
import uuid

try:
    from .reel_show import validate_inputs
except ImportError:
    from reel_show import validate_inputs

REPOSITORY = 'ploeffler/PersonalNewsHost'
BRANCH = 'Full-featured-Newsoutlet'
# This existing workflow is registered on the default branch. Dispatch its reel
# mode at the development ref; it calls chat-reel.yml without changing main.
WORKFLOW = 'avatar-test.yml'


def gh(*args, body=None):
    result = subprocess.run(['gh', *args], input=json.dumps(body) if body is not None else None, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('GitHub operation failed; inspect authentication/run status; dispatch is not retried automatically')
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request', type=Path)
    parser.add_argument('--wait', action='store_true')
    parser.add_argument('--destination', type=Path, default=Path('out/chat-reel-download'))
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    validate_inputs(request)
    request_id = uuid.uuid4().hex
    request['request_id'] = request_id
    request.setdefault('test_mode', False)
    request = {k: request[k] for k in ['station_name', 'show_name', 'host_description', 'studio_description', 'rss_feed', 'news_count', 'output_name', 'request_id', 'test_mode']}
    gh('api', '--method', 'POST', 'repos/' + REPOSITORY + '/actions/workflows/' + WORKFLOW + '/dispatches',
       '--input', '-', body={'ref': BRANCH, 'inputs': {'mode': 'reel', 'request': json.dumps(request), 'request_id': request_id}})
    print('request_id=' + request_id, flush=True)
    if not args.wait:
        return
    deadline = time.monotonic() + 70 * 60
    run = None
    while time.monotonic() < deadline:
        runs = json.loads(gh('api', 'repos/' + REPOSITORY + '/actions/workflows/' + WORKFLOW + '/runs?event=workflow_dispatch&per_page=100'))['workflow_runs']
        matches = [r for r in runs if r['head_branch'] == BRANCH and r['display_title'].endswith(' · ' + request_id)]
        if matches:
            run = matches[0]
            if run['status'] == 'completed':
                break
        time.sleep(20)
    if not run or run['status'] != 'completed' or run['conclusion'] != 'success':
        raise RuntimeError('Reel did not complete successfully: ' + (run['html_url'] if run else request_id))
    destination = args.destination.resolve() / request_id
    destination.mkdir(parents=True, exist_ok=False)
    gh('run', 'download', str(run['id']), '--repo', REPOSITORY, '--name', 'chat-reel-' + str(run['id']), '--dir', str(destination))
    manifest = json.loads((destination / 'manifest.json').read_text())
    video = (destination / manifest['video']).resolve()
    if not video.is_relative_to(destination) or video.suffix != '.mp4' or not video.is_file():
        raise RuntimeError('Invalid video artifact')
    print('run=' + run['html_url'])
    print('video=' + str(video))


if __name__ == '__main__':main()
