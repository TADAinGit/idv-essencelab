"""Validated optional presentation overlays, separate from source game tables."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ICON_MAP={
 'p5_s.png':'Persona 5 Crossover Essence',
 'danwan.png':'Danganronpa Crossover Essence Part 1',
 'danwan_02.png':'Danganronpa Crossover Essence Part 2',
 'danwan_03.png':'Danganronpa Crossover Essence Part 3',
 'death_note.png':'Death Note Crossover Essence',
 'conan_s.png':'Detective Conan Crossover Essence Part 1',
 'conan_02_s.png':'Detective Conan Crossover Essence Part 1',
 'kid_s.png':'Detective Conan Crossover Essence Part 2',
 'bsd_2023_s.png':'Bungo Stray Dogs Crossover Essence Part 2',
 'angels_of_death_s.png':'Angels of Death Crossover Essence',
 'xxxholic_2023_s.png':'xxxHOLiC Crossover Essence'
}
POSTER_MAP={
 'danwan.png':'DanganronpaCrossoverInGamePoster.png',
 'danwan_02.png':'DanganronpaPart2InGamePoster.png',
 'danwan_03.png':'DanganronpaPart3CrossoverEssenceInGamePoster.png',
 'death_note.png':'DNCrossoverPoster2.jpg',
 'conan_s.png':'Case_Closed_Poster_P1.png',
 'conan_02_s.png':'Case_Closed_Poster_P1.png',
 'kid_s.png':'ConanPart2Poster.jpg',
 'bsd_2023_s.png':'BSD2EssencePoster.jpg',
 'angels_of_death_s.png':'AngelsOfDeathCrossoverEventPoster.jpeg',
 'xxxholic_2023_s.png':'XxxHOLiCEssencePoster.jpg'
}
def load_reference_art():
 path=ROOT/'research/crossover-audit/reference-art.json'
 if not path.exists():return {}
 records=json.loads(path.read_text(encoding='utf8'))['assets']
 for r in records:
  p=ROOT/'public'/r['url'].lstrip('/')
  if not p.resolve().is_relative_to((ROOT/'public/crossover-art').resolve()):raise ValueError('Reference art outside destination')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Reference art hash mismatch')
 return {r['label']:r for r in records}
def public_source(r):
 return {k:r[k] for k in ['origin','nativeAliasProven','url','sha256','width','height','filePage','context']}
def reference_art(box,records):
 basename=Path(box.get('iconUri') or '').name
 icon=records.get(ICON_MAP.get(basename))
 poster_key=POSTER_MAP.get(basename)
 if basename=='p5_s.png':poster_key='Persona5Crossover2Poster.jpg' if 'Essence 2' in box['name'] else 'P5AwakenedPoster.jpg'
 return icon,records.get(poster_key)
