"""Verify all copied raw/preview hashes and catalog references, without the game."""
import collections
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def main():
    manifest = read('assets/manifest.json')
    catalog = read('public/data/catalog.json')
    index = read('public/data/asset-index.json')
    resources = manifest['resources']
    assert len({r['requested'] for r in resources}) == len(resources)
    assert len(catalog['boxes']) == len({b['id'] for b in catalog['boxes']}) == 524
    assert len(catalog['rewards']) == 3117
    assert all(r['tableRecordFound'] for r in catalog['rewards'].values())
    assert all(e['key'] in catalog['rewards'] for b in catalog['boxes'] for entries in b['pools'].values() for e in entries)
    assert all(e['key'] in catalog['rewards'] for b in catalog['boxes'] for e in b['supplemental'])
    assert sum(r['emptyEntries'] for r in catalog['accumulate']) == 14
    assert all(e['key'] in catalog['rewards'] for row in catalog['accumulate'] for entries in row['pools'].values() for e in entries)
    mapping = read('research/rules/reward-table-mapping.json')
    lookup = {r['type']: r['table'] for r in mapping['mappings']}
    assert all(lookup[r['type']] == 'pydata/' + r['sourceTable'] + '.py' for r in catalog['rewards'].values())
    checked = {}
    preview_checked = {}
    files = {}
    for r in resources:
        if r['status'] == 'copied':
            files[r['file']] = r['sha256']
            if r.get('preview'):
                files['public' + r['preview']] = r['previewSha256']
    def inspect_copy(item):
        relative, expected = item
        path = ROOT / relative
        metadata = path.stat()
        actual = sha(path)
        assert actual == expected, relative
        return relative, dict(sha256=actual, bytes=metadata.st_size, links=metadata.st_nlink, symlink=path.is_symlink())
    file_checks = {}
    with ThreadPoolExecutor(max_workers=12) as executor:
        for relative, metadata in executor.map(inspect_copy, files.items()):
            file_checks[relative] = metadata
            if len(file_checks) % 5000 == 0:
                print('Verified file hashes:', len(file_checks), '/', len(files), flush=True)
    for r in resources:
        assert index[r['requested']]['status'] == r['status']
        if r['status'] != 'copied':
            assert r.get('error')
            continue
        file = (ROOT / r['file']).resolve()
        assert file.is_relative_to(ROOT / 'assets/raw') and not file_checks[r['file']]['symlink']
        assert file_checks[r['file']]['links'] == 1, 'Raw assets must be copies, not hardlinks'
        if r['file'] not in checked:
            checked[r['file']] = file_checks[r['file']]
        assert checked[r['file']]['sha256'] == r['sha256']
        assert checked[r['file']]['bytes'] == r['bytes']
        if r.get('preview'):
            image = ROOT / 'public' / r['preview'].lstrip('/')
            assert image.resolve().is_relative_to(ROOT / 'public/media')
            if r['preview'] not in preview_checked:
                preview_checked[r['preview']] = file_checks['public' + r['preview']]['sha256']
            assert preview_checked[r['preview']] == r['previewSha256']
    for item in [*catalog['boxes'], *catalog['rewards'].values()]:
        if item.get('image'):
            assert item['image'] in preview_checked
    for name, source in manifest['sourceFiles'].items():
        filename = source['module'].replace('/', '__') + '.json' if 'module' in source else name
        assert sha(ROOT / 'source-data' / filename) == source['json_sha256']
    assert manifest['summary'] == catalog['summary']
    assert manifest['summary']['pending'] == len(manifest['pending'])
    assert manifest['summary']['copied'] == sum(r['status']=='copied' for r in resources)
    assert manifest['summary']['decodedBytes'] == sum(r.get('bytes',0) for r in resources)
    assert manifest['toolSha256'] == sha(ROOT / 'tools/build_catalog.py')
    for helper, expected in manifest.get('helperHashes', {}).items():
        assert sha(ROOT / 'tools' / helper) == expected
    runs = [(p, json.loads(p.read_text(encoding='utf-8'))) for p in (ROOT / 'research').rglob('result.json')]
    assert all(r['status'] in ('passed','partial') for _,r in runs)
    report = dict(status='passed', summary=catalog['summary'],
        uniqueRawFiles=len(checked), uniqueRawBytes=sum(r['bytes'] for r in checked.values()),
        uniquePreviewFiles=len(preview_checked),
        boxesWithPreview=sum(bool(b.get('image')) for b in catalog['boxes']),
        rewardsWithPreview=sum(bool(r.get('image')) for r in catalog['rewards'].values()),
        resourceStatuses=dict(collections.Counter(r['status'] for r in resources)),
        formats=dict(collections.Counter(Path(r['file']).suffix for r in resources if r['status']=='copied')),
        stageRuns=[dict(path=p.relative_to(ROOT).as_posix(),status=r['status']) for p,r in runs],
        hashes={p:sha(ROOT/p) for p in ['assets/manifest.json','public/data/catalog.json','public/data/asset-index.json',
            'server.mjs','public/engine.js','public/app.js','public/index.html','public/styles.css','tools/build_catalog.py']},
        limits=['File/hash/reference checks only. Not native render or server RNG validation.',
                'Queue exhaustion is scoped to the bounded literal/candidate collector; full closure remains unproven.'])
    (ROOT / 'research/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
