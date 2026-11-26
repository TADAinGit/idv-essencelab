"""Export authored Cocos gacha tracks and decoded sprite assets, never execute game code."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config.local.json').read_text(encoding='utf-8'))
PARSER = Path(CONFIG['extractor']) / 'gui/widgets/viewers/cocos_viewer/cocos_parser.py'
OUT = ROOT / 'public/game-fx'
EVIDENCE = ROOT / 'research/game-gacha-fx'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')


def main():
    sys.path.insert(0, CONFIG['extractor'])
    from PIL import Image
    spec = importlib.util.spec_from_file_location('essence_cocos_parser', PARSER)
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)  # Installed tool source, not a production game module.
    manifest = json.loads((ROOT / 'assets/manifest.json').read_text(encoding='utf-8'))
    records = {r['requested']: r for r in manifest['resources']}
    OUT.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    assets = {}
    unresolved = []

    def texture(path):
        uri = path if path.startswith('ui/') else 'ui/dm65ui/res/' + path
        if uri in assets:
            return assets[uri]['url']
        row = records.get(uri)
        if not row or row['status'] != 'copied':
            unresolved.append(uri)
            return None
        file = ROOT / row['file']
        if sha(file) != row['sha256']:
            raise ValueError('Copied source hash mismatch: ' + uri)
        raw = file.read_bytes()
        if len(raw) > 64*1024*1024:
            raise ValueError('Texture payload budget')
        if raw[:8] == b'CompBlks':
            w, h = int.from_bytes(raw[16:18], 'little'), int.from_bytes(raw[18:20], 'little')
            size = ((w+3)//4)*((h+3)//4)*16
            if raw[8:10] != b'\xf3\x83' or not 0 < w*h <= 4096*4096 or len(raw) < 28+size:
                raise ValueError('Unsupported CompBlks')
            img = Image.frombytes('RGBA', (w,h), raw[28:28+size], 'bcn', (3,))
        else:
            img = Image.open(io.BytesIO(raw))
            if img.width*img.height > 4096*4096:
                raise ValueError('Image pixel budget')
            img.load()
        target = OUT / (row['sha256'] + '.png')
        img.convert('RGBA').save(target)
        assets[uri] = dict(url='/game-fx/'+target.name, source=uri,
            sourceSha256=row['sha256'], sha256=sha(target), width=img.width, height=img.height,
            contentId=row['id'], resolution=row.get('resolution'), nativeAliasProven=row.get('native_alias_proven',False))
        return assets[uri]['url']

    documents = {}
    for name in ['treasure_open_one_ani', 'treasure_open_ten_ani']:
        uri = 'ui/dm65ui/res/' + name + '.csb'
        row = records[uri]
        source = ROOT / row['file']
        raw = source.read_bytes()
        if len(raw) > 8*1024*1024 or sha(source) != row['sha256']:
            raise ValueError('CSB bounds/hash')
        document = parser.CocosBinaryParser(types.SimpleNamespace(data=raw)).parse()
        save(EVIDENCE/(name+'.json'), document)
        root = document['root']
        main_nodes = [n for n in root['children'] if n['name'] in ('p_mc', 'p_avatar')]
        count = 0
        tags = set()
        def strip(node, depth=0):
            nonlocal count
            count += 1
            if depth > 32 or count > 500:
                raise ValueError('Node tree budget')
            tags.add(node['actionTag'])
            fields = ['name','classname','actionTag','position','scale','rotationSkew','anchorPoint','size','visible','alpha','color','zOrder','flipX','flipY']
            result = {k:node[k] for k in fields if k in node}
            resource = node.get('details',{}).get('resource',{})
            if resource.get('path'):
                result['texture'] = texture(resource['path'])
                result['resource'] = resource['path']
            result['children'] = [strip(c,depth+1) for c in node.get('children',[])]
            return result
        tree = dict(name='opening',position=dict(x=0,y=0),scale=dict(x=1,y=1),children=[strip(n) for n in main_nodes])
        tracks = [t for t in document['animation']['timelines'] if t['actionTag'] in tags]
        if sum(len(t['frames']) for t in tracks) > 20000:
            raise ValueError('Timeline frame budget')
        for track in tracks:
            for frame in track['frames']:
                if track['property'] == 'FileData' and isinstance(frame.get('value'),dict):
                    path=frame['value'].get('path')
                    if path:
                        frame['value']['texture']=texture(path)
        documents['ten' if 'ten' in name else 'one'] = dict(source=uri,
            sourceSha256=row['sha256'], width=root['size']['width'], height=root['size']['height'],
            root=tree, animation=dict(document['animation'], timelines=tracks),
            limitations=['p_mc and p_avatar authored 2D subtrees are rendered; current avatar_1 is selected.',
                         'Dynamic n_treasure ProjectNode is represented by selected Essence icon; not original assembled 3D model.',
                         'Original named-node gold/blue colors are bound separately; native particles, audio and server RNG are not ported.',
                         'Canvas supports linear Cocos property interpolation; custom easing/scale9/layout constraints are not yet verified.'])
    report = dict(schemaVersion=1, documents=documents, assets=assets,
        playback=dict(fps=60, speedFromCSB=True, interClipDelaySeconds=0.1,
                      sequence=dict(one=['open_one_1','open_one_2'],ten=['open_ten_1','open_ten_2'])),
        capabilities=dict(authored2DSpriteTimelines=True, exactNativeParity=False, original3DModel=False,
                          originalAudio=False, gradeColorMutation=True, horizontalShockLine=True, currentAvatar=True, gradeColorBindingCoverage=['p_mc/p_glow','p_avatar/light']),
        unresolved=sorted(set(unresolved)), provenance=dict(parser=str(PARSER), parserSha256=sha(PARSER),
            toolSha256=sha(__file__), manifestSha256=sha(ROOT/'assets/manifest.json')))
    save(OUT/'opening.json',report)
    save(EVIDENCE/'export-report.json',dict(assets=len(assets),unresolved=report['unresolved'],
        timelines={k:len(d['animation']['timelines']) for k,d in documents.items()},
        openingSha256=sha(OUT/'opening.json'),provenance=report['provenance'],capabilities=report['capabilities']))
    print(json.dumps(dict(assets=len(assets),unresolved=len(report['unresolved']),
        documents=list(documents),output=str(OUT/'opening.json')),indent=2))


if __name__ == '__main__':
    main()
