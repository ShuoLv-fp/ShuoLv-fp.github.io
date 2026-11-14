"""Skip scheduled recovery attempts after a successful update this week."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys


def refresh_due(snapshot, now):
    if not isinstance(snapshot, dict) or snapshot.get('scholar_id') != 'VAsm0T8AAAAJ':
        return True
    for field in ('citedby', 'hindex'):
        if type(snapshot.get(field)) is not int or snapshot[field] < 0:
            return True
    try:
        updated = datetime.fromisoformat(snapshot['updated'].replace('Z', '+00:00'))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
    except (KeyError, AttributeError, ValueError):
        return True
    local = now.astimezone(timezone(timedelta(hours=8)))
    week_start = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return not week_start <= updated <= now


def main():
    try:
        snapshot = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        snapshot = None
    due = os.environ.get('GITHUB_EVENT_NAME') != 'schedule' or refresh_due(snapshot, datetime.now(timezone.utc))
    print(f'due={str(due).lower()}')
    if not due and os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as summary:
            summary.write('This week already has a verified Scholar snapshot; recovery fetch skipped.\n')


if __name__ == '__main__':
    main()
