"""Copy original data and bounded decoded assets into EssenceLab, without game execution.

Run with the installed NeoXtractor Python (BXML/Pillow dependencies). Runtime is
standalone; only this rebuild step requires the configured research checkout.
"""
import collections
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
from essence_localization import resolve_tid

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'config.local.json').read_text(encoding='utf-8'))
PROJECT = Path(CFG['research_project'])
sys.path.insert(0, str(PROJECT / 'tools'))
from character_table_data import load_table
from inspect_character_models import ResourceStore
from research_store import ScriptStore
from essence_resource_store import EssenceResourceStore, MAX_BYTES
from probe_opcode_mapping import reference, inspect
from recover_literal_tables import recover, encode
sys.path.insert(0, CFG['extractor'])
from core.formats.bxml import parse_bxml_bytes
from PIL import Image

EXTENSIONS = r'gim|mesh|skeleton|animconfig|mtg|mtl|dds|png|tga|plist|csb|pse|npse|anim|animation|ani|json|xml|ogg|wav|bnk|wem|ktx|pvr'
PATHS = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_./\\-]{1,300}\.(?:' + EXTENSIONS + r')(?![A-Za-z0-9_.])', re.I)
TABLES = {1: 'cloth', 2: 'specific_action', 3: 'wating_action', 4: 'poster', 5: 'decoration',
          6: 'appendage', 7: 'chase_music', 9: 'face', 10: 'face_frame', 14: 'furniture',
          97: 'token_data', 202: 'offerings'}
TYPE_NAMES = {1: 'Trang phục', 2: 'Biểu cảm', 3: 'Tư thế chờ', 4: 'Graffiti', 5: 'Phụ kiện',
              6: 'Thú cưng', 7: 'Nhạc truy đuổi', 9: 'Chân dung', 10: 'Khung chân dung',
              14: 'Nội thất', 97: 'Token', 202: 'Vật phẩm hỗ trợ'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')


def main():
    os.chdir(PROJECT)  # ScriptStore's selected-map path is relative to research checkout.
    source_dir = Path(CFG['analysis']) / 'tables'
    snapshot = Path(CFG['snapshot'])
    source_files = {}
    tables = {}
    scripts = ScriptStore(snapshot, Path(CFG['analysis']) / 'ScriptCache')
    mapping, caches, families = reference(PROJECT / 'research-output/repo-review-more/hax0r31337/denpk2/src/opcode/mapping.rs', PROJECT / 'research-output/repo-review-more/cpython-opcode-3.11.6.py')
    def table(name):
        if name in tables:
            return tables[name]
        filename = 'pydata/' + name + '.py'
        source = source_dir / (filename.replace('/', '__') + '.json')
        row = scripts.by_name[filename]
        code = scripts.load(row)
        values, _ = recover(code, inspect(code, mapping, caches, families))
        if encode(values) != json.loads(source.read_text(encoding='utf-8')):
            raise ValueError('Snapshot mismatch: ' + filename)
        data, meta = load_table(source_dir, filename)
        if meta['errors']:
            raise ValueError(meta['errors'])
        shutil.copy2(source, ROOT / 'source-data' / source.name)
        source_files[name] = dict(module=filename, decoded_sha256=row['decoded_sha256'],
            content_id=row['id'], layer=row['layer'], json_sha256=sha(source), snapshot_match=True)
        tables[name] = data
        return data
    boxes = table('t_box')
    accumulate = table('t_box_accumulate')
    table('box_guarantee_fix')
    table('article_type')
    for name in TABLES.values():
        table(name)
    scripts.close()
    texts = {}
    for path in [*sorted(source_dir.glob('pydata__tid_data__all_tid_en_*.py.json')), source_dir / 'pydata__all_tid_en_diff.py.json']:
        texts.update(json.loads(path.read_text(encoding='utf-8')).get('data', {}))
        shutil.copy2(path, ROOT / 'source-data' / path.name)
        source_files[path.name] = dict(json_sha256=sha(path), snapshot_match='cached locale, not re-recovered')
    save(ROOT / 'source-data/localization-en.json', texts)
    for name in ['essence-catalog-audit-2026-11-25.json', 'essence-presentation-audit-2026-11-25.json', 'essence-controller-ir-2026-11-25.json']:
        shutil.copy2(PROJECT / 'docs/evidence/character-catalog' / name, ROOT / 'research' / name)

    pkg_path = snapshot / 'files/pkgmapping.json'
    shutil.copy2(pkg_path, ROOT / 'source-data/pkgmapping.json')
    pkg_rules = sorted(json.loads(pkg_path.read_text(encoding='utf-8'))['mapping'], key=lambda x: -len(x[0]))
    def normalize(path):
        path = re.sub('/+', '/', path.replace('\\', '/')).strip('/')
        if '..' in path.split('/') or ':' in path or not path:
            raise ValueError('Unsafe logical URI')
        if path.startswith(('image/', 'common/', 'system/')):
            path = 'ui/dm65ui/res/' + path
        for prefix, group in pkg_rules:
            if path.startswith(prefix + '/'):
                return group + '/' + path[len(prefix) + 1:]
        return path
    store = EssenceResourceStore(Path(CFG['analysis']) / 'resources.sqlite', CFG['game'], ROOT / 'assets/raw')
    memory = sqlite3.connect(':memory:')
    store.db.backup(memory)
    store.db.close()
    store.db = memory
    memory.row_factory = sqlite3.Row
    memory.execute('PRAGMA query_only=ON')
    queue = collections.deque()
    queued = set()
    manifest = {}
    edges = []
    budget = 0

    def enqueue(path, parent=None, depth=0, basis='table literal'):
        try:
            normalized = normalize(path)
        except ValueError:
            return None
        if '/' not in normalized:
            return None
        if parent:
            edges.append(dict(source=parent, target=normalized, basis=basis, runtime_dependency_proven=False))
        if normalized not in queued and normalized not in manifest:
            queue.append((normalized, depth))
            queued.add(normalized)
        return normalized

    def root_refs(value):
        if isinstance(value, str):
            yield from PATHS.findall(value)
        elif isinstance(value, dict):
            for v in value.values():
                yield from root_refs(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                yield from root_refs(v)

    def display(tid):
        return resolve_tid(tid, texts)

    rewards = {}
    def reward(kind, ident):
        key = f'{kind}:{ident}'
        if key in rewards:
            return key
        source = TABLES.get(kind)
        row = tables.get(source, {}).get(ident, tables.get(source, {}).get(str(ident)))
        row = row if isinstance(row, dict) else {}
        for uri in root_refs(row):
            enqueue(uri)
        icon = row.get('icon_path') or row.get('icon') or row.get('small_icon') or row.get('big_icon')
        icon = enqueue(icon) if isinstance(icon, str) and '/' in icon else None
        name = display(row.get('name') or row.get('g_name') or row.get('token_name')) or f'{TYPE_NAMES.get(kind, kind)} #{ident}'
        rewards[key] = dict(key=key, type=kind, id=ident, typeName=TYPE_NAMES.get(kind, str(kind)),
            name=name, description=display(row.get('g_desc') or row.get('token_desc')), quality=row.get('quality'),
            iconUri=icon, sourceTable=source, tableRecordFound=bool(row),
            configuration=row)
        return key

    output_boxes = []
    for ident, row in boxes.items():
        pools = {}
        for g in range(1, 6):
            pools[str(g)] = [dict(key=reward(v[0], v[1]), tail=v[2:]) for v in row.get(f'grade_{g}', [])]
        supplemental = [dict(season=v[0], key=reward(v[1], v[2]), tail=v[3:]) for v in row.get('all_grade_with_season', [])]
        for uri in root_refs(row):
            enqueue(uri)
        category = 'classic' if row.get('classic') else 'rank' if row.get('rank') else 'season' if row.get('season') else 'other'
        name = display(row.get('name')) or str(ident)
        if name.startswith('TID_SEASON_T_COLLECTION_'):
            match = re.match(r'TID_SEASON_T_COLLECTION_(\d)', name)
            if match and row.get('season'):
                name = f"S{row['season']} Essence {match[1]}"
        output_boxes.append(dict(id=str(ident), name=name, nameTid=row.get('name'), season=row.get('season'), category=category,
            pools=pools, supplemental=supplemental, iconUri=enqueue(row['icon_path']) if row.get('icon_path') else None,
            modelUri=enqueue(row['model']) if row.get('model') else None,
            shareRateId=str(row.get('share_rate_id', ident)), configuration=row,
            ruleStatus='unverified-server', available=False))
    supplemental_records = []
    for ident, row in accumulate.items():
        supplemental_records.append(dict(id=ident, boxId=str(row.get('t_box_id')), season=row.get('season_id'),
            pools={str(g): [dict(key=reward(v[0], v[1]), tail=v[2:]) for v in row.get(f'grade_{g}_accumulate', []) if len(v) >= 2] for g in range(1, 6)},
            emptyEntries=sum(not v for g in range(1, 6) for v in row.get(f'grade_{g}_accumulate', []))))
    for path in ['ui/dm65ui/res/treasure_open_one_ani.csb', 'ui/dm65ui/res/treasure_open_ten_ani.csb', 'ui/dm65ui/res/treasure_open_item.csb', 'ui/dm65ui/res/treasure_list_new.csb']:
        enqueue(path)

    previous_path = ROOT / 'assets/manifest.json'
    if '--resume' in sys.argv and previous_path.exists():
        previous = json.loads(previous_path.read_text(encoding='utf-8'))
        if previous['sourceFiles'] != source_files or previous['pkgmappingSha256'] != sha(pkg_path):
            raise ValueError('Resume source identity changed; use a fresh subproject output.')
        manifest = {r['requested']: r for r in previous['resources']}
        retry = []
        if '--retry-decode-errors' in sys.argv:
            retry = [(p, r['depth']) for p, r in manifest.items()
                     if r['status'] != 'copied' and 'Logical key' not in r.get('error', '')]
            for p, _ in retry:
                del manifest[p]
        edges = previous['edges']
        budget = previous['summary']['decodedBytes']
        pending = [*previous['pending'], *retry, *queue]
        queue = collections.deque()
        queued = set(manifest)
        for path, depth in pending:
            if path not in queued:
                queue.append((path, depth))
                queued.add(path)
        print(f'Resuming {len(manifest)} processed URIs, {len(queue)} pending', flush=True)

    print(f'Catalog ready: {len(output_boxes)} boxes, {len(rewards)} reward IDs, {len(queue)} resource roots', flush=True)
    while queue and len(manifest) < CFG['max_resources'] and budget < CFG['max_decoded_bytes']:
        path, depth = queue.popleft()
        candidates = [(path, 'literal')]
        if path.lower().endswith(('.png', '.tga')):
            candidates.append((path.rsplit('.', 1)[0] + '.dds', 'same-basename DDS candidate'))
        if path.lower().endswith('.pse'):
            candidates.append((path[:-4] + '.npse', 'compiled particle candidate'))
        chosen = next(((p, basis) for p, basis in candidates if store.lookup(p)), None)
        entry = dict(requested=path, depth=depth, status='unresolved', candidates=[p for p, _ in candidates])
        try:
            if chosen is None:
                raise FileNotFoundError('Logical key not resolved under tested candidates')
            resolved, basis = chosen
            if budget + MAX_BYTES > CFG['max_decoded_bytes']:
                queue.appendleft((path, depth))
                break
            # Per-payload and total decoded limits are independent.
            store.bytes_read = 0
            raw, stamp = store.read(resolved)
            budget += len(raw)
            entry.update(status='copied', resolved=resolved, resolution=basis,
                native_alias_proven=basis == 'literal', sha256=stamp['sha256'], id=stamp['id'], layer=stamp['layer'],
                bytes=len(raw), file=Path(stamp['output']).relative_to(ROOT).as_posix(),
                sourceArchive=stamp['source_archive'], sourceOffset=stamp['source_offset'], layers=stamp['layers'])
            ext = Path(path).suffix.lower()
            if ext in ('.png', '.tga', '.dds'):
                try:
                    if raw[:8] == b'CompBlks':
                        w, h = int.from_bytes(raw[16:18], 'little'), int.from_bytes(raw[18:20], 'little')
                        size = ((w+3)//4)*((h+3)//4)*16
                        if raw[8:10] != b'\xf3\x83' or not 0 < w*h <= 4096*4096 or len(raw) < 28+size:
                            raise ValueError('Unsupported bounded CompBlks layout')
                        img = Image.frombytes('RGBA', (w, h), raw[28:28+size], 'bcn', (3,))
                    else:
                        img = Image.open(io.BytesIO(raw))
                        if img.width*img.height > 4096*4096:
                            raise ValueError('Image exceeds pixel budget')
                        img.load()
                    img = img.convert('RGBA')
                    img.thumbnail((512, 512))
                    preview = ROOT / 'public/media' / (stamp['sha256'] + '.png')
                    img.save(preview)
                    entry.update(preview='/media/' + preview.name, previewSha256=sha(preview))
                except (ValueError, OSError, NotImplementedError) as exc:
                    entry['previewError'] = str(exc)
            if depth < CFG['max_depth'] and ext in ('.gim', '.mtg', '.mtl', '.animconfig', '.plist', '.csb', '.json', '.xml', '.pse', '.npse'):
                text = raw.decode('ascii', errors='ignore')
                if raw[:4] == b'\xc1YA\r':
                    try:
                        text = parse_bxml_bytes(raw)
                    except Exception as exc:
                        entry['bxmlError'] = str(exc)
                for ref in sorted(set(PATHS.findall(text))):
                    if ref.startswith(('chr/', 'scene/', 'ui/', 'material/', 'effect/', 'effects/', 'camera_lens/', 'wwise/')):
                        target = ref
                    elif path.startswith('ui/'):
                        target = 'ui/dm65ui/res/' + ref
                    else:
                        target = path.rsplit('/', 1)[0] + '/' + ref
                    enqueue(target, path, depth+1, 'literal reference; relative resolution candidate')
                if ext == '.gim':
                    for suffix in ('.mesh', '.mtg'):
                        enqueue(path[:-4] + suffix, path, depth+1, 'same-basename assembly candidate; not literal')
        except (ValueError, OSError, KeyError) as exc:
            entry['error'] = str(exc)
        manifest[path] = entry
        if len(manifest) % 250 == 0:
            print(f'Assets {len(manifest)}; queued {len(queue)}; decoded {budget//(1024*1024)} MiB', flush=True)
            save(ROOT / 'assets/progress.json', dict(processed=len(manifest), queued=len(queue), decodedBytes=budget))

    store.close()
    for value in [*output_boxes, *rewards.values()]:
        icon = manifest.get(value.get('iconUri'), {})
        value['image'] = icon.get('preview')
        value['iconStatus'] = icon.get('status', 'no-reference')
    summary = dict(boxes=len(output_boxes), rewards=len(rewards), directRewards=3117,
        rewardTableJoins=sum(v['tableRecordFound'] for v in rewards.values()),
        copied=sum(v['status']=='copied' for v in manifest.values()),
        unresolved=sum(v['status']!='copied' for v in manifest.values()), decodedBytes=budget,
        previews=sum(bool(v.get('preview')) for v in manifest.values()), pending=len(queue),
        fullClosureProven=False, exactRngVerified=False)
    save(ROOT / 'public/data/catalog.json', dict(schemaVersion=1, snapshot=snapshot.name, summary=summary,
        boxes=output_boxes, rewards=rewards, accumulate=supplemental_records))
    save(ROOT / 'assets/manifest.json', dict(schemaVersion=1, snapshot=snapshot.name, summary=summary,
        sourceFiles=source_files, pkgmappingSha256=sha(pkg_path), toolSha256=sha(__file__),
        helperHashes={p:sha(ROOT/'tools'/p) for p in ['essence_resource_store.py','essence_localization.py']},
        resources=list(manifest.values()), edges=edges, pending=list(queue),
        limits=['Literal/candidate dependency graph, not proven full closure.', '64 MiB packed/decoded payload per resource; 16 GiB total and depth 8.',
                'DDS/NPSE and same-basename assembly candidates are recorded, not asserted native aliases.',
                'No executable game scripts, original archives, accounts or authentication state are copied.',
                'All raw data/model formats remain original decoded bytes; no browser 3D parity claim.']))
    save(ROOT / 'public/data/asset-index.json', {k: {f:v for f,v in r.items() if f in ('status','file','sha256','resolved','preview','resolution','error','bytes')} for k,r in manifest.items()})
    save(ROOT / 'public/data/status.json', dict(summary=summary, sourceFiles=source_files,
        limits=['Server RNG chưa được xác minh.', 'Pool theo season/tích lũy được tách riêng; chưa chứng minh thứ tự áp dụng.',
                'Model gốc đã sao chép không đồng nghĩa đã render đúng trong browser.']))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
