"""Verify collected seasonal artwork before adding optional presentation metadata."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_season_art():
 path=ROOT/'research/season-posters/reference-art.json'
 if not path.exists():return {}
 data=json.loads(path.read_text(encoding='utf8'))
 if hashlib.sha256((ROOT/'public/data/catalog.json').read_bytes()).hexdigest()!=data['sourceCatalogSha256']:raise ValueError('Seasonal mapping source catalog changed; rerun collector')
 records=data['records']
 for r in records.values():
  p=ROOT/'public'/r['url'].lstrip('/')
  if not p.resolve().is_relative_to((ROOT/'public/season-art').resolve()):raise ValueError('Seasonal art outside destination')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Seasonal art hash mismatch')
 return records
