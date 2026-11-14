"""Fetch locally and optionally publish the verified Google Scholar snapshot."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPOSITORY = 'https://github.com/ShuoLv-fp/ShuoLv-fp.github.io.git'
BRANCH = 'google-scholar-stats'
FILES = ('gs_data.json', 'gs_data_shieldsio.json')


def update_time(value):
    timestamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    return timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)


def publish_results(results, repository=REPOSITORY):
    results = Path(results)
    snapshot = json.loads((results / FILES[0]).read_text(encoding='utf-8'))
    if snapshot.get('scholar_id') != 'VAsm0T8AAAAJ':
        raise ValueError('Refusing to publish statistics for a different author')
    for field in ('citedby', 'hindex'):
        if type(snapshot.get(field)) is not int or snapshot[field] < 0:
            raise ValueError(f'Invalid {field}')
    fetched_at = update_time(snapshot['updated'])
    badge = json.loads((results / FILES[1]).read_text(encoding='utf-8'))
    if badge.get('message') != str(snapshot['citedby']):
        raise ValueError('Citation badge does not match the snapshot')

    environment = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    with tempfile.TemporaryDirectory(prefix='scholar-publish-') as directory:
        def git(*arguments):
            return subprocess.run(
                ['git', *arguments], cwd=directory, env=environment,
                check=True, timeout=90, text=True, capture_output=True,
            ).stdout.strip()

        git('clone', '--quiet', '--depth', '1', '--single-branch',
            '--branch', BRANCH, repository, '.')
        published = json.loads((Path(directory) / FILES[0]).read_text(encoding='utf-8'))
        if update_time(published['updated']) >= fetched_at:
            print('Published statistics are already at least as recent; skipped.')
            return False
        for filename in FILES:
            shutil.copyfile(results / filename, Path(directory) / filename)
        git('add', *FILES)
        git('commit', '-m', 'Update Google Scholar statistics')
        # A normal push rejects concurrent branch changes instead of overwriting them.
        git('push', 'origin', BRANCH)
        print(f"Published {snapshot['updated']}: citations={snapshot['citedby']}, h-index={snapshot['hindex']}")
        return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='Publish the fetched snapshot to GitHub')
    arguments = parser.parse_args()
    crawler = Path(__file__).resolve().with_name('main.py')
    with tempfile.TemporaryDirectory(prefix='scholar-fetch-') as directory:
        subprocess.run([sys.executable, '-u', str(crawler)], cwd=directory,
                       check=True, timeout=180)
        if arguments.publish:
            publish_results(Path(directory) / 'results')
        else:
            print('Fetch succeeded. Use --publish to update the website.')


if __name__ == '__main__':
    main()
