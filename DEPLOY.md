# Deploy idv-essencelab to Cloudflare Pages

Target project: `idv-essencelab`, production branch `main`, preview branch `review`.

This is a static Pages Direct Upload project. No R2, Functions, billing activation or server-side user database is required. The guest wallet/session remains browser-local. The exact pages.dev name is assigned by Cloudflare when creating the project.

## First setup

Use Node22+ and run `npm ci`. Authenticate with `npx wrangler login` only if `npx wrangler whoami` is not already authenticated. Create the project once:

```powershell
npx wrangler pages project create idv-essencelab --production-branch main --force
```

The source repository contains application code, tests and rebuild tooling. Runtime game data and binary images/audio/fonts are deliberately excluded from Git. A fresh source checkout needs the matching local research-generated `public/data/v2` and runtime resources described in the research continuation before the complete test suite/build can pass. Existing production assets are not silently substituted for a research rebuild.

## Publish

```powershell
npm run deploy:preview
# Review the returned preview URL, including /collection and /history.
npm run deploy:production
```

Each deployment checks Cloudflare authentication, runs the Node suite, builds `.deploy/pages`, then uploads that exact directory. `npm run build:pages` creates a local bundle without uploading. `npm run preview:pages` serves it at127.0.0.1:4174 using Cloudflare's local Pages emulator.

The packager includes only web assets reachable from the application and selected box/reward JSON. It omits unused media, old monolithic indexes, hidden asset-browser indexes, raw engine formats, source-data, research artifacts and local configuration. Every uploaded file is hashed in `.deploy/manifest.json`; this report stays local. It enforces Pages Free's20000-file and25MiB/file ceilings. Generated404.html disables implicit SPA fallback; physical collection.html/history.html entry points handle collection/history using Pages extensionless URLs, leaving unknown/private routes 404. Security headers and immutable hashed media caching are supplied through _headers.

Keep project tokens out of repository files and command arguments. Wrangler uses its existing user login or environment-based CI credentials. This workflow performs no paid-plan upgrade. Direct Upload projects cannot be converted to Git integration in place; this source repository still provides version history independently of the upload method.

## Roll back

Use Cloudflare Pages deployment history to roll back production to a prior known-good deployment. Do not reset browser collection or wallet during verification.

Wrangler 4.168.0 may delegate creation of a new Pages project to Workers when run by an agent. The initial create command uses --force to select Pages itself, retaining the requested pages.dev URL. Existing Pages projects do not need this option for subsequent deployments.

## Verified initial release — 2026-11-26

Production: https://idv-essencelab.pages.dev (deployment37da372a). Preview: https://review.idv-essencelab.pages.dev (deployment0299f7c3). Initial bundle6637files,237369702bytes.62Node tests passed; hosted ten-pull and session persistence verified on preview. Physical extensionless collection/history pages support direct refresh; private paths and legacy indexes return404. Source Git history is maintained separately from Pages Direct Upload.
