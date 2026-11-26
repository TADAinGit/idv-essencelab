"""Emit small static, on-demand web records from the preserved research catalog.

Run after build_catalog.py. The monolithic inputs stay available to research tools;
the web client should boot from v2/index.json and fetch detail records on selection.
"""
import hashlib
import io
import json
import re
from essence_localization import resolve_tid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'public/data'
OUT = DATA / 'v2'
PAGE_SIZE = 1000


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_model(path):
    if not isinstance(path, str):
        return None
    path = path.replace('\\', '/')
    for prefix, group in [('chr/boss/', 'chr_boss/'), ('chr/player/', 'chr_player/'),
                          ('chr/creature/', 'chr_creature/'), ('chr/prop/', 'chr_prop/')]:
        if path.startswith(prefix):
            return group + path[len(prefix):]
    return path


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from strings(child)


def light_card(reward):
    fields = ('key', 'type', 'id', 'typeName', 'name', 'quality', 'image', 'iconStatus', 'tableRecordFound')
    return {field: reward.get(field) for field in fields}


def banner(box, assets):
    from PIL import Image
    for uri in strings(box['configuration'].get('show_kv_path')):
        asset = assets.get(uri)
        if not asset:
            asset = assets.get(uri.rsplit('.', 1)[0] + '.dds')
        if not asset or asset.get('status') != 'copied':
            continue
        record = dict(requested=uri, resolved=asset.get('resolved'), sha256=asset.get('sha256'),
                      resolution=asset.get('resolution'), nativeAliasProven=asset.get('resolution') == 'literal')
        try:
            raw = (ROOT / asset['file']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != asset['sha256']:
                raise ValueError('Banner source hash mismatch')
            if raw[:8] == b'CompBlks':
                w, h = int.from_bytes(raw[16:18], 'little'), int.from_bytes(raw[18:20], 'little')
                size = ((w+3)//4)*((h+3)//4)*16
                if raw[8:10] != b'\xf3\x83' or not 0 < w*h <= 4096*4096 or len(raw) < 28+size:
                    raise ValueError('Unsupported bounded CompBlks layout')
                image = Image.frombytes('RGBA', (w, h), raw[28:28+size], 'bcn', (3,))
            else:
                image = Image.open(io.BytesIO(raw))
                if image.width*image.height > 4096*4096:
                    raise ValueError('Image exceeds pixel budget')
                image.load()
            record['sourceSize'] = [image.width, image.height]
            image = image.convert('RGBA')
            image.thumbnail((1600, 1600))
            modern = re.search(r'(?:Season|S)\s*(4[0-9]|[5-9][0-9])\b',box.get('name','')) and 'Rank' not in box.get('name','')
            target = ROOT / 'public/media' / ('banner-' + asset['sha256'] + ('-lossless.webp' if modern else '.webp'))
            image.save(target, format='WEBP', lossless=True, method=4) if modern else image.save(target, format='WEBP', quality=90, method=4)
            if modern:record['presentationEnhancement']='lossless source export; mild browser edge sharpening'
            record.update(previewSha256=sha(target), previewSize=[image.width, image.height])
            return '/media/' + target.name, record
        except (ValueError, OSError, NotImplementedError) as exc:
            record['error'] = str(exc)
            if asset.get('preview'):
                record['fallback'] = 'Existing bounded preview; full banner decode failed'
                return asset['preview'], record
    return None, None


def main():
    from crossover_reference_art import load_reference_art,reference_art,public_source
    from season_reference_art import load_season_art
    references = load_reference_art()
    seasonal_art = load_season_art()
    catalog = read(DATA / 'catalog.json')
    assets = read(DATA / 'asset-index.json')
    locale = read(ROOT / 'source-data/localization-en.json')
    lightweight = {key: light_card(reward) for key, reward in catalog['rewards'].items()}
    summaries = []
    detail_sizes = []
    recovered_path = ROOT / 'research/image-audit/recovered.json'
    recovered = read(recovered_path) if recovered_path.exists() else {}
    user_crossover_path = ROOT / 'research/crossover-audit/user-art/manifest.json'
    user_crossover = read(user_crossover_path)['records'] if user_crossover_path.exists() else {}
    coa_path = ROOT / 'research/coa-art/manifest.json'
    coa_art = read(coa_path)['records'] if coa_path.exists() else {}
    for box in catalog['boxes']:
        reference_icon,reference_poster = reference_art(box,references)
        summary = {field: box.get(field) for field in
                   ('id', 'name', 'nameTid', 'season', 'category', 'image', 'iconStatus')}
        # Display grouping only: retain the raw season field/configuration.
        source_season = (box['configuration'].get('show_img_num') or [None])[0]
        name_season = re.match(r'^(?:S|Season\s+)(\d+)\b', box['name'])
        display_season = box.get('season') or (source_season if box['category'] == 'rank' else None) or (int(name_season[1]) if name_season else None)
        summary['displaySeason'] = display_season
        if box['category']=='season':
            named = re.match(r'^(?:S|Season\s+)(\d+)\b.*?Essence\s*(\d+)\b',box['name'])
            pair = list(map(int,named.groups())) if named else box['configuration'].get('show_img_num')
            if pair and len(pair)==2:
                summary['displaySeason'],summary['displayEssence'] = pair
        if not summary['image'] and reference_icon:
            summary.update(image=reference_icon['url'],iconStatus='external-reference',iconSource=public_source(reference_icon))
        if box['id'] in coa_art:
            for art in coa_art[box['id']].values():
                target = ROOT / 'public' / art['url'].lstrip('/')
                if not target.resolve().is_relative_to((ROOT/'public/coa-art').resolve()) or sha(target) != art['sha256']:
                    raise ValueError('COA artwork path/hash mismatch')
            icon = coa_art[box['id']]['icon']
            summary.update(image=icon['url'],iconStatus='external-reference',iconSource=public_source(icon))
        summaries.append(summary)
        full = dict(box)
        if box['id'] in coa_art:
            full.update(image=summary['image'],iconStatus=summary['iconStatus'],iconSource=summary['iconSource'])
        if not full.get('image') and reference_icon:
            full.update(image=summary['image'],iconStatus=summary['iconStatus'],iconSource=summary['iconSource'])
        full['description'] = resolve_tid(box['configuration'].get('g_desc') or '', locale)
        full['displaySeason'] = display_season
        if 'displayEssence' in summary:
            full['displaySeason'],full['displayEssence'] = summary['displaySeason'],summary['displayEssence']
        full['banner'], full['bannerSource'] = banner(box, assets)
        if not full['banner'] and box['id'] in recovered:
            art = recovered[box['id']]
            target = ROOT / 'public' / art['url'].lstrip('/')
            if sha(target) != art['previewSha256']:
                raise ValueError('Recovered image SHA mismatch')
            full.update(banner=art['url'], bannerSource={k: v for k, v in art.items() if k != 'provenance'}, bannerKind=art['kind'])
        if not full['banner'] and reference_poster:
            full.update(banner=reference_poster['url'],bannerSource=public_source(reference_poster),bannerKind='reference-poster')
        if not full['banner'] and box['id'] in seasonal_art:
            art = seasonal_art[box['id']]
            full.update(banner=art['url'],bannerSource={k:art[k] for k in ['origin','nativeAliasProven','url','sha256','width','height','filePage','context','key']},bannerKind='reference-strip' if art.get('presentation')=='strip' else 'reference-poster')
            if art.get('viewport'):
                full['bannerViewport'] = art['viewport']
            if art.get('edit'):
                full['bannerSource']['edited'] = True
        if box['id'] in user_crossover:
            art = user_crossover[box['id']]
            target = ROOT / 'public' / art['url'].lstrip('/')
            if not target.resolve().is_relative_to((ROOT/'public/crossover-art').resolve()) or sha(target) != art['sha256']:
                raise ValueError('User crossover artwork path/hash mismatch')
            full.update(banner=art['url'],bannerSource={k:art[k] for k in ['origin','nativeAliasProven','url','sha256','width','height']},bannerKind='reference-poster',bannerViewport=[0,0,1,1],bannerFit='contain')
        needed = {entry['key'] for entries in box['pools'].values() for entry in entries}
        if box['id'] in coa_art:
            art = coa_art[box['id']]['banner']
            full.update(banner=art['url'],bannerSource={k:art[k] for k in ['origin','nativeAliasProven','url','sha256','width','height']},bannerKind='reference-poster',bannerViewport=[0,0,1,1],bannerFit='contain')
        needed.update(entry['key'] for entry in box['supplemental'])
        accumulate = [row for row in catalog['accumulate'] if row['boxId'] == box['id']]
        needed.update(entry['key'] for row in accumulate for entries in row['pools'].values() for entry in entries)
        path = OUT / 'boxes' / (box['id'] + '.json')
        save(path, dict(box=full, rewards={key: lightweight[key] for key in sorted(needed)}, accumulate=accumulate))
        detail_sizes.append(path.stat().st_size)
    save(OUT / 'index.json', dict(schemaVersion=2, snapshot=catalog['snapshot'], summary=catalog['summary'], boxes=summaries))
    save(OUT / 'reward-index.json', dict(rewards=lightweight))
    save(OUT / 'pool-index.json', dict(boxes=[dict(id=box['id'], shareRateId=box['shareRateId'], pools=box['pools']) for box in catalog['boxes']]))
    for key, reward in catalog['rewards'].items():
        full = dict(reward)
        original = reward['configuration'].get('model_path') or reward['configuration'].get('path')
        full['modelUri'] = original
        full['modelAsset'] = assets.get(normalize_model(original)) if original else None
        save(OUT / 'rewards' / (key.replace(':', '-') + '.json'), full)
    pages = []
    entries = list(assets.items())
    page_count = (len(entries) + PAGE_SIZE - 1) // PAGE_SIZE
    for page in range(page_count):
        batch = [dict(uri=uri, **asset) for uri, asset in entries[page*PAGE_SIZE:(page+1)*PAGE_SIZE]]
        name = f'page-{page}.json'
        save(OUT / 'assets' / name, dict(page=page, totalPages=page_count, entries=batch))
        pages.append(dict(page=page, file='/data/v2/assets/' + name, count=len(batch),
                          copied=sum(entry['status'] == 'copied' for entry in batch),
                          unresolved=sum(entry['status'] != 'copied' for entry in batch)))
    save(OUT / 'assets/index.json', dict(total=len(entries), pageSize=PAGE_SIZE, pages=pages))
    save(OUT / 'asset-page-index.json', dict(total=len(entries), pageSize=PAGE_SIZE, pages=pages))
    report = dict(schemaVersion=2, inputCatalogBytes=(DATA/'catalog.json').stat().st_size,
                  inputAssetIndexBytes=(DATA/'asset-index.json').stat().st_size,
                  bootstrapBytes=(OUT/'index.json').stat().st_size,
                  rewardIndexBytes=(OUT/'reward-index.json').stat().st_size,
                  poolIndexBytes=(OUT/'pool-index.json').stat().st_size,
                  boxes=len(summaries), rewardDetails=len(lightweight), assetPages=page_count,
                  detailBytes=dict(min=min(detail_sizes), max=max(detail_sizes), total=sum(detail_sizes)),
                  banners=sum(bool(read(OUT/'boxes'/(box['id']+'.json'))['box']['banner']) for box in catalog['boxes']),
                  sourceHashes={str(path.relative_to(ROOT)): sha(path) for path in [DATA/'catalog.json', DATA/'asset-index.json']},
                  toolSha256=sha(Path(__file__)))
    save(OUT / 'size-report.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
