"""Recheck missing image identities without guessing replacement artwork."""
import collections
import hashlib
import json
from pathlib import Path
from extract_gacha_ui import ROOT, CFG, EssenceResourceStore, image_decode, sha, write_json


def main():
    out = ROOT / 'research/image-audit'
    out.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((ROOT / 'public/data/catalog.json').read_text(encoding='utf8'))
    locale_path = Path(CFG['analysis']) / 'offline-ui-bootstrap-ir.json'
    ir = json.loads(locale_path.read_text(encoding='utf8'))
    pack = next(m for m in ir if m['filename'] == 'etc/pack_config.py')
    fn = next(c for c in pack['code_objects'] if c['qualname'] == 'get_oversea_res_mapping_info')
    locales = set()
    def scan(value):
        if isinstance(value, (list, tuple)):
            if len(value) == 2 and all(isinstance(v, str) for v in value) and value[0] == '/res/':
                locales.add(value[1].strip('/'))
            for child in value:
                scan(child)
        elif isinstance(value, dict):
            for child in value.values():
                scan(child)
    scan(fn)
    if len(locales) != 10:
        raise ValueError('Unexpected locale mappings: ' + repr(locales))
    store = EssenceResourceStore(Path(CFG['analysis']) / 'resources.sqlite', CFG['game'], out / 'payloads')
    missing = collections.defaultdict(list)
    no_banner_field, unavailable_banners = [], []
    for b in catalog['boxes']:
        if not b.get('image'):
            missing[b['iconUri']].append(dict(id=b['id'], name=b['name']))
        detail = json.loads((ROOT / 'public/data/v2/boxes' / (b['id'] + '.json')).read_text(encoding='utf8'))['box']
        if not b['configuration'].get('show_kv_path'):
            no_banner_field.append(b['id'])
        elif not detail.get('banner') or detail.get('bannerKind'):
            unavailable_banners.append(dict(id=b['id'], name=b['name'], requested=b['configuration']['show_kv_path']))
    targets = dict(missing)
    for box in unavailable_banners:
        if isinstance(box['requested'], str):
            uri = box['requested']
            if not uri.startswith('ui/'):
                uri = 'ui/dm65ui/res/' + uri
            targets.setdefault(uri, []).append(dict(id=box['id'], name=box['name'], role='banner'))
    results = []
    recovered_art = {}
    for uri, boxes in targets.items():
        candidates = []
        for path in [uri] + [uri.replace('/res/', '/' + loc + '/', 1) for loc in sorted(locales)]:
            candidates.extend([path, path.rsplit('.', 1)[0] + '.dds', path.rsplit('.', 1)[0] + '.plist'])
        attempts, recovered = [], []
        for candidate in dict.fromkeys(candidates):
            hit = store.lookup(candidate)
            attempts.append(dict(uri=candidate, indexed=bool(hit)))
            if hit:
                try:
                    raw, stamp = store.read(candidate)
                    im = image_decode(raw)
                    target = ROOT / 'public/media' / (sha(raw) + '.png')
                    im.save(target)
                    recovered.append(dict(candidate=candidate, preview='/media/' + target.name, width=im.width, height=im.height,
                                          previewSha256=sha(target.read_bytes()), provenance=stamp))
                except (OSError, ValueError) as exc:
                    attempts[-1]['decodeError'] = str(exc)
        stem = Path(uri).stem
        if recovered:
            # English matches the existing catalog's display language. Select
            # explicitly, never let the last locale tested overwrite the first.
            chosen = next((r for r in recovered if '/res_en/' in r['candidate']), recovered[0])
            for box in boxes:
                if box.get('role') == 'banner':
                    recovered_art[box['id']] = dict(url=chosen['preview'],
                        kind='label' if '/img_text_' in uri else 'poster', requested=uri,
                        resolved=chosen['candidate'], width=chosen['width'], height=chosen['height'],
                        sha256=chosen['provenance']['sha256'], previewSha256=chosen['previewSha256'],
                        selection='English label when indexed, matching catalog display language; otherwise source res',
                        provenance=chosen['provenance'])
        named = [r[0] for r in store.db.execute('SELECT path FROM resources WHERE path LIKE ? LIMIT 30', ('%/' + stem + '.%',))]
        results.append(dict(requested=uri, boxes=boxes, attempts=attempts, recovered=recovered,
                            namedCandidates=named, reason='No indexed identity for literal, DDS or paired plist across base and 10 source-declared locale paths' if not any(a['indexed'] for a in attempts) else 'See per-candidate decode results'))
    icon_results = [r for r in results if r['requested'] in missing]
    banner_results = [r for r in results if any(b.get('role') == 'banner' for b in r['boxes'])]
    report = dict(snapshot=catalog['snapshot'], sourceCatalogSha256=sha((ROOT / 'public/data/catalog.json').read_bytes()),
                  localeIRSha256=sha(locale_path.read_bytes()), locales=sorted(locales), missingIcons=icon_results,
                  bannerChecks=banner_results,
                  noBannerField=no_banner_field, unavailableBanners=unavailable_banners,
                  limits=['Absence applies to tested logical keys in this index, not every historical game build.',
                          'Unnamed atlas entries, dynamic aliases and removed historical payloads remain possible.',
                          'No licensing/region/removal cause is established by this audit; no unrelated image substituted.'])
    write_json(out / 'report.json', report)
    write_json(out / 'recovered.json', recovered_art)
    lines = ['# Rà ảnh Essence — 25/11/2026', '',
             f"{len(missing)} URI icon / {sum(map(len, missing.values()))} record chưa có ảnh trước khi rà. Đã kiểm logical hash của PNG, DDS và plist cùng basename ở res và 10 locale nguồn.", '',
             '| Icon | Record | Tên | Kết quả |', '|---|---|---|---|']
    for r in icon_results:
        lines.append('| ' + Path(r['requested']).name + ' | ' + ', '.join(b['id'] for b in r['boxes']) + ' | ' + ' / '.join(dict.fromkeys(b['name'] for b in r['boxes'])) + ' | ' + ('Tìm được candidate; xem JSON' if r['recovered'] else 'Không có logical key trong index cho các đường dẫn đã kiểm') + ' |')
    lines.extend(['', f"{len(no_banner_field)} record không khai báo show_kv_path: không có poster tĩnh được chỉ định; một số dùng show_img_num/model/scene cũ. Web dùng icon gốc nếu có, không phóng thành poster toàn khung.", '',
                  f"Rà lại {len(unavailable_banners)} record có show_kv_path nhưng web chưa hiện: khôi phục được nhãn cho {len(recovered_art)} record Memory Sphere từ 2 URI DDS; đường dẫn tương đối trước đó chưa được gắn tiền tố ui/dm65ui/res. Đây là nhãn chữ, không phải poster toàn khung.", '',
                  'Poster còn thiếu: #514 Season 45 Essence 2 (img_s46_2.png), #515 Season 45 Essence 3 (img_s46_3.png). Không có logical key cho PNG/DDS/plist ở res và 10 locale đã kiểm. Không lấy số mùa trong filename để đổi sang poster khác.', '',
                  'Không đủ bằng chứng để kết luận do bản quyền, xóa asset hay khác khu vực. Có thể cần snapshot lịch sử hoặc chứng minh alias/atlas động. Không dùng ảnh cầu khác thay thế.'])
    (out / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    store.close()
    print(json.dumps(dict(missingIconURIs=len(icon_results), missingIconRecords=sum(map(len, missing.values())), recoveredIcons=sum(bool(r['recovered']) for r in icon_results), recoveredLabels=len(recovered_art), noBannerField=len(no_banner_field), bannerChecks=len(banner_results))))


if __name__ == '__main__':
    main()
