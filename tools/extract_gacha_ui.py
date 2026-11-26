"""Decode original gacha UI sprites, retaining CSB node/resource provenance.

Run with the installed NeoXtractor Python. This reads decoded CSB as data and
uses upstream parser code, never importing or executing production game scripts.
"""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shutil
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'config.local.json').read_text(encoding='utf-8'))
EXTRACTOR = Path(CFG['extractor'])
sys.path.insert(0, str(EXTRACTOR))
sys.path.insert(0, str(Path(CFG['research_project']) / 'tools'))
from essence_resource_store import EssenceResourceStore


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def image_decode(raw):
    if raw[:8] == b'CompBlks':
        width, height = int.from_bytes(raw[16:18], 'little'), int.from_bytes(raw[18:20], 'little')
        size = ((width + 3)//4) * ((height + 3)//4) * 16
        if raw[8:10] != b'\xf3\x83' or not 0 < width * height <= 4096*4096 or len(raw) < 28 + size:
            raise ValueError('Unsupported bounded CompBlks layout')
        return Image.frombytes('RGBA', (width, height), raw[28:28+size], 'bcn', (3,))
    image = Image.open(io.BytesIO(raw))
    if image.width * image.height > 4096 * 4096:
        raise ValueError('Pixel limit')
    image.load()
    return image.convert('RGBA')


def walk(node, path=''):
    path += '/' + node.get('name', '?')
    yield path, node
    for child in node.get('children', []):
        yield from walk(child, path)


def main():
    out = ROOT / 'public/game-ui'
    evidence_dir = ROOT / 'research/game-ui'
    out.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'assets/manifest.json').read_text(encoding='utf-8'))
    records = {r['requested']: r for r in manifest['resources']}
    parser_path = EXTRACTOR / 'gui/widgets/viewers/cocos_viewer/cocos_parser.py'
    spec = importlib.util.spec_from_file_location('essencelab_cocos_data_parser', parser_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    store = EssenceResourceStore(Path(CFG['analysis']) / 'resources.sqlite', CFG['game'], evidence_dir / 'payloads')
    source_csb = {}

    def payload(uri):
        record = records.get(uri)
        if record and record['status'] == 'copied':
            raw = (ROOT / record['file']).read_bytes()
            if sha(raw) != record['sha256']:
                raise ValueError('Copied source SHA mismatch: ' + uri)
            return raw, record
        candidates = [uri]
        if uri.lower().endswith('.png'):
            candidates.append(uri[:-4] + '.dds')
        for candidate in candidates:
            if store.lookup(candidate):
                raw, stamp = store.read(candidate)
                return raw, dict(requested=uri, resolved=candidate, sha256=stamp['sha256'],
                                 file=Path(stamp['output']).relative_to(ROOT).as_posix(), stamp=stamp)
        raise FileNotFoundError(uri)

    def parse(name):
        uri = 'ui/dm65ui/res/' + name
        raw, record = payload(uri)
        class Source:
            data = raw
            def __str__(self):
                return uri
        parser = module.CocosBinaryParser(Source())
        node = parser.parse_node(parser.reader.table(parser.reader.root(), 10))
        source_csb[name] = dict(uri=uri, sha256=sha(raw), nodeTreeOnly=True)
        write_json(evidence_dir / (name + '.nodes.json'), node)
        return node

    tree = parse('treasure_list_new.csb')
    nodes = dict(walk(tree))
    button_tree = parse('treasure_list_new_btn.csb')
    button_nodes = dict(walk(button_tree))
    assets = {}

    def export(key, path, field='resource', filename=None, csb='treasure_list_new.csb', node_map=None):
        node = (node_map or nodes)[path]
        details = node.get('details', {})
        resource = details[field]
        literal = resource['path']
        if resource.get('plist') or resource.get('resourceType', 0) != 0:
            raise ValueError('Atlas resources require explicit crop metadata')
        uri = literal if literal.startswith('ui/') else 'ui/dm65ui/res/' + literal
        raw, record = payload(uri)
        image = image_decode(raw)
        target = out / ((filename or key) + '.png')
        image.save(target)
        assets[key] = dict(url='/game-ui/' + target.name, source=uri, resolved=record.get('resolved', uri),
            decodedSha256=sha(raw), imageSha256=sha(target.read_bytes()), width=image.width, height=image.height,
            csb=csb, csbSha256=source_csb[csb]['sha256'], csbNode=path,
            actionTag=node.get('actionTag'), nodeSize=node.get('size'),
            capInsets=details.get('capInsets'), scale9Enabled=details.get('scale9Enabled', False),
            sourceFile=record['file'], resource=resource)

    export('openOne', '/treasure/p_avatar/btn_open_one', 'normalResource', 'open-one')
    export('openTen', '/treasure/p_avatar/btn_open_ten', 'normalResource', 'open-ten')
    export('openTenDisabled', '/treasure/p_avatar/btn_open_ten', 'disabledResource', 'open-ten-disabled')
    export('back', '/treasure/p_back/btn_back', 'normalResource')
    export('contents', '/treasure/p_operate/btn_content', 'normalResource')
    export('contentsPressed', '/treasure/p_operate/btn_content', 'pressedResource', 'contents-pressed')
    export('history', '/treasure/p_operate/btn_record', 'normalResource')
    export('historyPressed', '/treasure/p_operate/btn_record', 'pressedResource', 'history-pressed')
    export('background', '/treasure/bg/img_bg')
    export('backgroundSide', '/treasure/bg/img_bg_1', filename='background-side')
    export('listBackground', '/treasure/p_treasure_list/img_bg_tab', filename='list-background')
    export('treeLeft', '/treasure/bg/img_tree_l', filename='tree-left')
    export('treeRight', '/treasure/bg/img_tree_r', filename='tree-right')
    export('maskLeft', '/treasure/p_left/img_mask_left_nml', filename='mask-left')
    export('maskRight', '/treasure/p_right/img_mask_right_nml', filename='mask-right')
    export('bottomMask', '/treasure/p_avatar/img_bottom_mask', filename='bottom-mask')
    export('tabNormal', '/Node/btn_tab', 'normalResource', filename='tab-normal',
           csb='treasure_list_new_btn.csb', node_map=button_nodes)
    export('selected', '/Node/btn_tab', 'disabledResource', filename='tab-selected',
           csb='treasure_list_new_btn.csb', node_map=button_nodes)
    # Selection has its own ProjectNode; match its exact resource-bearing node.
    selection_candidates = [(path, node) for path, node in button_nodes.items()
                            if node.get('details', {}).get('resource', {}).get('path')]
    for index, (path, node) in enumerate(selection_candidates):
        export('selectionPart' + str(index), path, filename='selection-part-' + str(index),
               csb='treasure_list_new_btn.csb', node_map=button_nodes)
    # Authored font reference from text nodes, preserved as the original collection.
    font_refs = []
    for path, node in nodes.items():
        font = node.get('details', {}).get('fontResource', {}).get('path')
        if font:
            font_refs.append((path, font))
    fonts = []
    for literal in sorted({font for _, font in font_refs}):
        uri = literal if literal.startswith('ui/') else 'ui/dm65ui/res/' + literal
        try:
            # Exact lowercase entry is present in the verified resource index;
            # the authored TTC suffix differs in case from that indexed URI.
            resolved_uri = uri[:-4] + '.ttc' if uri.endswith('.TTC') else uri
            raw, record = payload(resolved_uri)
            if raw[:4] not in (b'ttcf', b'OTTO', b'\x00\x01\x00\x00'):
                raise ValueError('Not a known SFNT/collection header')
            # The game's .TTC extension is not the format: this sample is an
            # ordinary SFNT TrueType face (0x00010000), not a TTC collection.
            actual_suffix = '.ttf' if raw[:4] == b'\x00\x01\x00\x00' else '.otf' if raw[:4] == b'OTTO' else '.ttc'
            target = out / (Path(literal).stem + actual_suffix)
            target.write_bytes(raw)
            fonts.append(dict(url='/game-ui/' + target.name, source=uri, resolved=resolved_uri, sha256=sha(raw),
                csbNodes=[path for path, font in font_refs if font == literal],
                actualFormat='sfnt-truetype' if actual_suffix == '.ttf' else 'opentype' if actual_suffix == '.otf' else 'truetype-collection',
                browserCompatibilityVerified=False, sourceFile=record['file']))
        except (OSError, ValueError) as exc:
            fonts.append(dict(source=uri, status='unresolved', error=str(exc)))
    skin = dict(schemaVersion=1, assets=assets, fonts=fonts, sources=source_csb,
        parser=dict(path=str(parser_path), sha256=sha(parser_path.read_bytes())),
        limits=['Original UI pixels decoded without recoloring or invented texture replacement.',
                'Resource-node bindings use parsed NodeTree; list action parsing is excluded because upstream parser reaches an out-of-bounds frame.',
                'Selection ProjectNode images are exported separately; browser composition must retain authored sizes/placement.',
                'No native rendering or full CSS/layout parity acceptance claimed.'])
    write_json(out / 'skin.json', skin)
    write_json(evidence_dir / 'skin-provenance.json', skin)
    store.close()
    print(json.dumps(dict(assets=len(assets), fonts=fonts), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
