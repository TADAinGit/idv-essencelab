"""Run with uv run --with fonttools python tools/verify_vi_font.py."""
import json
import unicodedata
from pathlib import Path
from fontTools.ttLib import TTFont
from hashlib import sha256

ROOT=Path(__file__).resolve().parents[1]
FONT=ROOT/'public/game-ui/font-vi.ttf'
chars=set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ăâđêôơưĂÂĐÊÔƠƯ')
chars.update(chr(c) for c in range(0x1ea0,0x1efa))
for char in list(chars):chars.update(unicodedata.normalize('NFD',char))
font=TTFont(FONT)
cmap=font.getBestCmap()
missing=sorted(c for c in chars if ord(c) not in cmap)
report=dict(fontSha256=sha256(FONT.read_bytes()).hexdigest(),family=font['name'].getDebugName(1),
            checkedCharacters=len(chars),missing=missing,source='ui/dm65ui/res/font/font_vi.ttc',
            controller='etc/pack_config.py::update_language_cocos_engine_config, offsets 2198-2266')
(ROOT/'research/reward-widgets/vietnamese-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=True))
if missing:raise SystemExit(1)
