# idv-essencelab

Browser-based Identity V Essence collection and gacha simulation.

Live website: [idv-essencelab.pages.dev](https://idv-essencelab.pages.dev).

Cloudflare Pages project: `idv-essencelab`.

- Seasonal, crossover, COA, Memory Sphere and Rank collections with lazy loading.
- Original game-derived UI, reward frames, audio and selected reference/user-supplied artwork.
- Anonymous 300-draw wallet, six-hour refill and 24-hour inactivity expiration in browser storage.
- Separate default/custom simulation counters, local collection/history and JSON export/import.
- Season 1 Essence 1–5 show their top three skins over the Rank red curtain.

Rates are a local reconstruction; exact server RNG and complete native rendering parity are not established.

## Local development

Requires Node 22+ and the matching research-generated runtime assets/data. These binary assets and private source tables are not included in this source repository. The original research kit remains an external rebuild dependency, not a browser runtime dependency.

```powershell
npm ci
npm test
npm start
```

Open 127.0.0.1:4173. The complete suite requires local runtime resources and research verification receipts; a source-only clone is not a standalone copy of the game-derived asset set.

## Cloudflare Pages

See [DEPLOY.md](DEPLOY.md). The upload workflow creates a separate, validated static package; it never uploads the repository root or research/source-data directories.

```powershell
npm run build:pages
npm run deploy:preview
npm run deploy:production
```

Use preview first, verify the returned URL, then publish production. No R2, backend account database or paid service is required by this static setup. Session data is local to each browser/origin.
