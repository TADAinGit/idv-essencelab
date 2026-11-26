"""Own 64 MiB bounded reader using the audited project's lookup and WPK codec."""
import hashlib
from pathlib import Path
from inspect_character_models import ResourceStore
import probe_payload

MAX_BYTES = 64 * 1024 * 1024


class EssenceResourceStore(ResourceStore):
    def read(self, path):
        row = self.lookup(path)
        if row is None:
            raise FileNotFoundError('Logical key absent from catalog')
        if row['length'] < 0 or row['length'] > MAX_BYTES:
            raise ValueError('64 MiB packed payload limit')
        folder = self.game if row['layer'] == 'base' else self.game / 'Documents'
        group, package = row['group_name'], row['package']
        archive = folder / 'res' / (f'{group}{package:x}.wpk' if package != 255 else f"{group}/{row['id']}")
        before = archive.stat()
        if row['header_size'] != 48 or row['offset'] < 0 or row['offset'] + 48 + row['length'] > before.st_size:
            raise ValueError('Archive header/bounds mismatch')
        if archive not in self.handles:
            self.handles[archive] = archive.open('rb')
        stream = self.handles[archive]
        stream.seek(row['offset'])
        header, payload = stream.read(48), stream.read(row['length'])
        after = archive.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError('Archive changed during read')
        if len(header) != 48 or header[:4] != b'1DPW' or header[8:24].hex() != row['id'] or len(payload) != row['length']:
            raise ValueError('Archive content identity mismatch')
        # The source codecs reference this module-local bound. No source files
        # or game binaries change; every output layer remains bounded at 64 MiB.
        previous_limit = probe_payload.LIMIT
        try:
            probe_payload.LIMIT = MAX_BYTES
            raw, layers = probe_payload.unwrap(payload, nxs3_limit=MAX_BYTES)
        finally:
            probe_payload.LIMIT = previous_limit
        if len(raw) > MAX_BYTES:
            raise ValueError('64 MiB decoded payload limit')
        destination = self.output / (row['id'] + Path(path).suffix)
        destination.write_bytes(raw)
        self.bytes_read += len(payload)
        return raw, dict(path=path, id=row['id'], layer=row['layer'], decoded_bytes=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(), output=str(destination), source_archive=str(archive),
            source_offset=row['offset'], layers=[r['layer'] for r in layers])
