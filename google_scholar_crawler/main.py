from scholarly import scholarly
import json
from datetime import datetime, timezone
import os
from pathlib import Path


def main():
    scholar_id = os.environ.get('GOOGLE_SCHOLAR_ID', 'VAsm0T8AAAAJ')
    scholarly.set_timeout(20)
    scholarly.set_retries(3)
    author = scholarly.search_author_id(scholar_id)
    scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])

    if author.get('scholar_id') != scholar_id:
        raise ValueError('Google Scholar returned a different author')
    for field in ('citedby', 'hindex'):
        value = author.get(field)
        if type(value) is not int or value < 0:
            raise ValueError(f'Google Scholar returned an invalid {field}')

    author['publications'] = {v['author_pub_id']: v for v in author['publications']}
    author['updated'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    shieldio_data = {
        'schemaVersion': 1,
        'label': 'citations',
        'message': str(author['citedby']),
    }
    # Validate and serialize everything before replacing any last-good output.
    files = {
        'gs_data.json': json.dumps(author, ensure_ascii=False, allow_nan=False, indent=2),
        'gs_data_shieldsio.json': json.dumps(shieldio_data, allow_nan=False, indent=2),
    }
    output = Path('results')
    output.mkdir(exist_ok=True)
    for filename, content in files.items():
        temporary = output / (filename + '.tmp')
        temporary.write_text(content + '\n', encoding='utf-8')
        temporary.replace(output / filename)

    print(f"Updated {author['updated']}: citations={author['citedby']}, h-index={author['hindex']}")


if __name__ == '__main__':
    main()
