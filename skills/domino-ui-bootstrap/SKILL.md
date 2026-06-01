---
name: domino-ui-bootstrap
description: Bootstrap or retrofit a Vite + React 18 + TypeScript project so it uses the Domino design system (`@dominodatalab/extensions-tools`). Scoped to projects that are (or will be) a **fully standalone SPA frontend for a Domino application or extension** — not snippets, library additions, or work inside an existing Domino monorepo package. Use this skill whenever the user wants to create, build, scaffold, start, refactor, retrofit, or set up such an SPA — a React app, web app, frontend, UI, or extension that should "look like Domino", use Domino components, follow the Domino design system, or integrate with the Domino platform — even when they don't say the word "Domino" explicitly but mention Domino-flavored terms like DominoThemeProviderDecorator, extensions-tools, or base-components. Also use when the user points at an existing standalone React/Vite project and asks to make it "Domino-styled", wire it up to the Domino component library, add Domino theming, or migrate it. The skill handles version pinning (React 18, react-router 5), MCP registration for the Storybook component reference, theme provider wiring, and a verification step — all things that are easy to get wrong otherwise.
---

# Domino UI Bootstrap

This skill makes a project use the Domino design system correctly. It works in three contexts:

- **Empty or non-existent directory** — scaffold a Vite + React 18 + TS project from scratch, then apply the Domino setup.
- **Existing Vite + React project** — leave the project alone, retrofit just the Domino bits (deps, theme provider, MCP, `CLAUDE.md`).
- **Existing React project on a different bundler/setup** — flag the mismatch to the user, then proceed only with their direction.

In all three cases, the skill executes the work end-to-end (runs commands, edits files), but it adapts to what's already there instead of overwriting blindly.

## Why this exists

A handful of choices look arbitrary but aren't — they match the rest of the Domino ecosystem and are easy to get wrong:

- **React 18, not 19.** `@dominodatalab/extensions-tools` peer-depends on React 18. React 19 fails at install.
- **react-router 5, not 6.** The library uses v5 APIs (`HashRouter` from `react-router-dom@5`).
- **HashRouter, not BrowserRouter.** This is what the library expects internally. It also gives cleaner isolation between the app's frontend and backend — client-side routes live entirely after the `#`, so they never collide with backend paths or the Domino proxy prefix, and inner navigation/linking works without server-side rewrite rules.
- **The npm package name is `@dominodatalab/extensions-tools`.** Storybook code snippets show imports from `@domino/base-components` — that's a Storybook-internal alias. Rewrite every such import to `@dominodatalab/extensions-tools` before pasting into a Domino project. This is the single most common mistake.
- **`DominoThemeProviderDecorator` wraps the whole React tree.** Without it, Domino components render unstyled or crash.
- **URLs must survive the proxy path.** Domino serves the app under a prefix (e.g. `/preview/<appId>/`), so asset and API URLs must be document-relative — not root-absolute. Vite's default `base: '/'` emits `/assets/…` and bypasses the proxy; user-written `fetch('/api/…')` does the same. Set `base: './'` and build API URLs against `document.baseURI`. See Step 8. Invisible in local dev (`pathname` is `/`), surfaces only after deployment.

Treat these as invariants the project must satisfy by the end. How you get there depends on what's already in the target directory.

---

## Step 1 — Elicit project info

Ask the user, in a single turn, for:

1. **Target path** — the absolute or workspace-relative path where the Vite + React app will live ("the app folder"). Ask this as a plain chat question, not a multiple-choice picker, because paths are free-form.
2. **Project root path** — where shared project config (`CLAUDE.md`, `.mcp.json`, `.claude/settings.local.json`) should live. Default to the target path; set this to a parent directory when the target is a subfolder of a larger repo (monorepos, an existing project with apps under `apps/`, etc.) — those files belong at the repo root, not nested inside the app folder. Ask explicitly; don't assume. If the user doesn't volunteer one, propose the target path and confirm.
3. **Display name** — free-form, any string. Used in `CLAUDE.md`, UI titles, and the hand-off message. Example: `Domino Frontend`.
4. **Package name** — the value that goes in `package.json`'s `name` field. npm requires lowercase, no spaces, no leading dot or underscore, URL-safe. Default to the kebab-case-lowercase of the display name (e.g. `Domino Frontend` → `domino-frontend`) and confirm. If retrofitting, default to whatever the existing `package.json` says and confirm.
5. **What to do if the path has unexpected content** — present this with `ask_user_input_v0` once you've inspected the directory (Step 2). The options depend on what you find; see Step 2.

If the user has already given any of these in the conversation, skip the corresponding question. If they give only one name, treat it as the display name and derive the package name from it — don't ask twice for the same information, just confirm the normalized package name. Throughout the rest of this skill, "project root" means the path from question 2 (equal to the target path unless the user said otherwise) and "app folder" means the target path from question 1.

---

## Step 2 — Survey the target directory

Before changing anything, find out what's there. This determines which branch of the skill you take.

Look for:

- Does the path exist? Is it empty?
- Is there a `package.json`? If so:
  - Is `react` already a dependency? At what major version?
  - Is `vite` a devDependency? Some other bundler (`webpack`, `next`, `parcel`, `cra`)?
  - Does `@dominodatalab/extensions-tools` already appear (any version)?
- Is there a `src/` directory with `main.tsx` / `main.jsx` / `index.tsx` / `index.jsx`?
- At the **project root** (from Step 1 — may equal the app folder, may not): is there an existing `.mcp.json`, `.claude/`, or `CLAUDE.md`? These live at the project root, not the app folder, so check there even when the app folder is a fresh empty subdirectory.

Classify the directory into one of these states, then ask the user how to proceed if needed:

| State | What you found | What to do |
|---|---|---|
| **Empty / nonexistent** | No files, or directory doesn't exist | Go to Step 3 (scaffold from scratch). |
| **Vite + React already** | `package.json` lists `vite` and `react` | Skip scaffolding. Go to Step 4 (align deps), then continue. |
| **React but not Vite** | React present, bundler is webpack/CRA/Next/etc. | Stop and ask the user: do they want to migrate to Vite, or keep their bundler and just add the Domino library? The skill is Vite-shaped; if they keep their bundler, the version pinning and theme-provider wiring still apply, but the scaffolding steps don't. |
| **Unrelated content** | Files exist but no `package.json`, or a non-React `package.json` | Ask the user: overwrite (delete and scaffold fresh), bootstrap in place (let Vite prompt), or pick a different path. |
| **Already partially Domino-wired** | `@dominodatalab/extensions-tools` already in deps | Treat as a verification/repair job: check each invariant below and only touch what's actually wrong. |

Run `node -v` and `npm -v`. Stop if Node is older than 20.

---

## Step 3 — Scaffold (only if empty / nonexistent / overwrite chosen)

From the target directory:

```bash
npm create vite@latest . -- --template react-ts
```

Do not run `npm install` immediately afterward. The next step rewrites `package.json` so the install picks up the right versions in one pass.

If the directory had existing content and the user chose "overwrite", clear it first (`rm -rf` the contents, not the directory itself).

---

## Step 4 — Align `package.json` to the Domino invariants

You're enforcing constraints, not writing a fixed file. View the current `package.json` and make sure it satisfies these:

**Required `dependencies`** (add or pin to these exact versions):

- `@dominodatalab/extensions-tools` — `latest` is fine for fresh projects; use a specific version if the user gave one or if one is already pinned in the existing `package.json`. (See the post-install pin step at the end of this section.)
- `react` — `18.2.0`
- `react-dom` — `18.2.0`
- `react-router` — `5.3.4`
- `react-router-dom` — `5.3.4`

**Required `devDependencies`** (the React typings must match React 18):

- `@types/react` — `18.2.0`
- `@types/react-dom` — `18.2.0`
- `@types/react-router` — `5.1.20`
- `@types/react-router-dom` — `^5.3.3`

**Node-version branch — check this BEFORE leaving the scaffold's toolchain alone.**

Run `node -v`. The current `npm create vite@latest` scaffold writes Vite 9 / TypeScript 6 / ESLint 10 / `@types/node` 24, all of which require Node ≥ 20.19. The Domino default workspace image ships Node 20.18.3, so the scaffold's defaults will fail `npm run build` (rolldown native binding error) and TS will error on `erasableSyntaxOnly` (a 5.6+ flag) and on missing `composite: true` for `tsc -b`.

- **If Node ≥ 20.19:** the scaffold's defaults are fine. Skip to "Leave alone" below.
- **If Node < 20.19:** pin the toolchain to a Node-20.18-compatible set before installing:
  - `vite` — `^5.4.0`
  - `@vitejs/plugin-react` — `^4.3.4`
  - `typescript` — `~5.5.4` (or `~5.6` if you keep `erasableSyntaxOnly` — but the simpler path is to drop the flag)
  - `@types/node` — `^20.12.0`
  - Remove the `eslint`, `@eslint/js`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`, `typescript-eslint`, and `globals` entries from `devDependencies`. The Vite-9 scaffold's ESLint pins all require Node ≥ 20.19 — easier to drop them than to find a compatible set.
  - Strip the `erasableSyntaxOnly` line from `tsconfig.app.json` and `tsconfig.node.json` (TS 5.6+ only).
  - Add `"composite": true` to both `tsconfig.app.json` and `tsconfig.node.json` (required when `build` runs `tsc -b`).
  - Delete `eslint.config.js` since ESLint was removed.

**Leave alone:**

- Vite, ESLint, TypeScript, `@vitejs/plugin-react`, and any other tooling already in the file — assuming the Node-version branch above didn't tell you to touch them. Whatever versions are there are fine if they work on the user's Node.
- Any scripts, fields, or sections you don't have a specific reason to change. In particular, don't rewrite `scripts` if the existing ones work; only add `dev`/`build`/`preview` if they're missing.
- Any project-specific dependencies the user already has (state libraries, icon packs, data-fetching libs, etc.). The skill is additive.

**Remove or downgrade:**

- If `react` or `react-dom` is at 19+, downgrade to `18.2.0`. Same for the `@types/*`.
- If `react-router-dom` is at 6+, downgrade to `5.3.4`. Warn the user — their existing routes use v6 syntax (`<Routes>` / `element={}`) and will need to be rewritten to v5 (`<Switch>` / `component={}` or `render={}`). Don't silently rewrite their routes; tell them what needs to change.

**After install — pin the resolved `@dominodatalab/extensions-tools` version.**

Once Step 5 has run cleanly and `latest` was used, resolve the floating tag to a concrete version and rewrite `package.json`:

```bash
npm view @dominodatalab/extensions-tools version
```

Replace `"latest"` in `dependencies` with the exact version string this returns. Skip if a specific version was already pinned (the user explicitly chose one, or you retrofitted). This keeps future installs reproducible — `latest` drifts.

---

## Step 5 — Install

```bash
npm install
```

Likely failures:

- **Peer-dep error about React 19** → Step 4 didn't take. Re-check `package.json`. Don't use `--legacy-peer-deps`.
- **404 / E401 / EAUTH on `@dominodatalab/extensions-tools`** → the user needs to authenticate to a private npm registry. Stop and ask how they normally authenticate. Don't switch to a tarball or alternative source on your own.

---

## Step 6 — Register the Storybook MCP

The Storybook MCP is what lets future Claude sessions look up real component props instead of guessing. Two files need to exist at the **project root** (from Step 1 — not the app folder if those are different paths) with the right shape; their exact formatting doesn't matter, but the contents do. They must sit in the same directory: if `.mcp.json` and `.claude/settings.local.json` get split across folders, Claude Code won't apply the allow-list to the registered MCP and the server stays disabled.

**`.mcp.json`** must register a server named `storybook` that points at the Domino library's live Storybook:

- URL: `https://main--60c0de3f60dd96003bdcb1a1.chromatic.com/mcp`
- Transport: `http`

If a `.mcp.json` already exists at the project root (with other MCP servers, or from a prior bootstrap), merge — don't overwrite. Add the `storybook` entry alongside whatever's there. If a `storybook` server is already registered at a different URL, ask the user before changing it. If no `.mcp.json` exists at the project root, create one there — never create one inside the app folder.

**`.claude/settings.local.json`** must:

- Pre-allow tools under the `mcp__storybook` namespace.
- Enable project-level MCP servers (`enableAllProjectMcpServers: true`).
- List `storybook` in the enabled servers.

If the file already exists at the project root, merge the relevant fields rather than overwriting. Preserve any other permissions or settings already there. If it doesn't exist, create it at the project root (next to `.mcp.json`), not inside the app folder.

---

## Step 7 — Wire up the React entry point

The project's React entry (`src/main.tsx` for a fresh scaffold, but it might be `src/index.tsx` or similar in an existing project) needs to satisfy these invariants:

- `DominoThemeProviderDecorator` from `@dominodatalab/extensions-tools` wraps the entire app tree. It must be an ancestor of every Domino component that gets rendered.
- A `HashRouter` from `react-router-dom` (v5) wraps the app inside the theme provider. Not `BrowserRouter`, not v6.
- The app component is rendered via `createRoot` from `react-dom/client` (React 18 idiom).
- `StrictMode` is fine to keep if Vite added it; not required.

For a fresh scaffold, write a clean `main.tsx` from scratch. For an existing project:

- If the entry already wraps the app in some other provider (Redux store, React Query client, custom theme), keep those wrappers and insert `DominoThemeProviderDecorator` so it's an ancestor of any Domino components. The usual place is outermost or just inside `StrictMode`, but the user's existing structure may dictate otherwise — don't blindly reorder providers that have ordering requirements (e.g., Redux usually goes outermost; auth providers often need to be high up).
- If the project already has a router, check which one. If it's `BrowserRouter` from v5, swap to `HashRouter`. If it's any router from v6, you'll need to convert routes too (see Step 4's note) — flag this to the user before doing it.
- Don't remove existing CSS imports. The theme provider injects its own styles, so a separate Domino CSS import isn't needed, but the user's app CSS should stay.

A heads-up worth passing to the user: in a standalone (non-Domino-backend) environment, `DominoThemeProviderDecorator` will try to fetch user / white-label data and fail silently. The UI still renders with defaults. If they want to suppress those requests, point them at `node_modules/@dominodatalab/extensions-tools/README.md` for the static `useStoreHook` prop.

---

## Step 8 — Make URLs proxy-aware (assets AND API calls)

When this app runs inside Domino it's served under a proxy prefix (e.g. `https://<host>/preview/<appId>/`). Root-absolute URLs bypass the proxy and 404 — both asset tags emitted as `/assets/index-*.js` and user-written `fetch('/api/…')` calls. This is invisible in local dev (where `pathname` is `/` and root-absolute happens to work) and only surfaces after deployment.

Two things to get right:

### 8a. `base: './'` in `vite.config.ts` (the scaffold does NOT set this)

The `npm create vite` scaffold leaves `base` at its default `/`, which emits root-absolute asset URLs (`/assets/…`) that bypass the proxy. Set it explicitly so emitted assets are document-relative:

```ts
export default defineConfig({
  base: './',
  plugins: [react()],
})
```

### 8b. `apiBase` resolved against `document.baseURI`

Build API URLs off `document.baseURI` so they resolve against the proxied path:

```ts
const apiBase = new URL('api', document.baseURI).href
fetch(`${apiBase}/projects`)
```

Don't construct API URLs from `window.location.pathname` (`pathname.replace(/[^/]*$/, '') + 'api'` etc.) — those either bypass the proxy or break under deeper routes. Use `document.baseURI`.

**When to apply this:**

- **Fresh scaffolds / starter screens you're generating:** write 8a and 8b in from the start. If the starter screen calls a backend, route it through `apiBase`.
- **Retrofits:** add 8a if `base` is missing/`/`. For API calls, scan for `fetch('/`, `axios.get('/`, `new WebSocket('ws`, and any `pathname`-based URL construction. Surface root-absolute or pathname-based URLs and recommend the `document.baseURI` form — **don't silently rewrite their fetches** (some may intentionally target another host).

This overlaps with the `dominodatalab:app-deployment` skill, which covers the full deploy shape (launch script, port binding, build output location). Point the user there for an actual app publish.

---

## Step 9 — Starter screen (only for fresh scaffolds)

Skip this step for retrofits — don't overwrite the user's existing `App.tsx` and don't touch their existing CSS.

For a fresh scaffold, replace Vite's default `App.tsx` with something that exercises a few real Domino components, to prove the install works. The minimum it should demonstrate:

- An import from `@dominodatalab/extensions-tools` (so the install path is verified).
- At least one component that depends on the theme provider (e.g., `Button`, `Card`, `Typography`) — this proves Step 7 is wired correctly.
- Optionally, `IconResolver` to demonstrate the icon system.

### Replace `src/index.css` (fresh scaffolds only)

Vite's default `src/index.css` ships ~80 lines of template chrome: a fixed-width centered `#root`, custom color tokens, `h1`/`h2`/`p`/`code` overrides, dark-mode rules, and decorative styles for the Vite hero. All of it overrides or conflicts with `DominoThemeProviderDecorator`'s tokens. On a fresh scaffold this isn't "the user's app CSS" — it's template noise.

- Overwrite `src/index.css` with a minimal reset:

  ```css
  body { margin: 0; }
  #root { min-height: 100svh; }
  ```

- Delete `src/App.css` if `App.tsx` no longer imports it.

This overrides the "don't remove existing CSS imports" line in Step 7 for the fresh-scaffold case. Step 7's guidance is about preserving real user CSS in a real codebase; it doesn't apply to Vite-template chrome on an empty scaffold. On retrofits, the Step 7 rule stands — leave existing CSS alone.

### Components safe to use without an MCP query

These are the components and prop shapes confirmed to work against the published `@dominodatalab/extensions-tools`. Use them for the starter screen without needing to consult the MCP. For anything beyond this set, query the Storybook MCP first (see the `CLAUDE.md` workflow in Step 10) — don't guess.

| Component | Safe usage |
|---|---|
| `Button` | `type='primary' \| 'secondary' \| 'tertiary'`, `onClick`, children. |
| `Card` | `title`, `extra`, `helpMessage`, `noPadding`, children. **No `size` prop.** |
| `Row` / `Col` / `Space` | Ant-style. `Space` takes `direction`, `size`. |
| `Tag` | `type` (**not `color`**). Values: `user-generated`, `success`, `danger`, `warning`. |
| `Typography` | **Namespace, not a wrapper.** Render `Typography.H1` / `.H2` / `.H3` / `.Text`. Never `<Typography>…</Typography>` — it'll throw React error #130 at runtime. |
| `Typography.Text` | Optional `type='BodyDefault' \| 'BodyDefaultStrong' \| 'BodySmall' \| 'BodySmallStrong' \| 'BodyCode'`. |
| `SpinnerWrapper` | Loading wrapper. |

### Watch out: `node_modules` README uses the Storybook alias

`node_modules/@dominodatalab/extensions-tools/README.md` (and any code snippets it embeds) imports from `@domino/base-components` — that's the Storybook-internal alias, not the published package name. Even though `node_modules` reads as authoritative, **every import in this project must use `@dominodatalab/extensions-tools`**. The `CLAUDE.md` written in Step 10 reminds future sessions of this, but the starter screen is the first place it can go wrong.

---

## Step 10 — Write or update `CLAUDE.md`

The **project root** (from Step 1 — not the app folder if those are different paths) should have a `CLAUDE.md` that tells future Claude Code sessions four things:

1. The npm package is `@dominodatalab/extensions-tools`. All imports in this project use that name.
2. Storybook code snippets (and the `node_modules/@dominodatalab/extensions-tools/README.md`) import from `@domino/base-components` — that's a Storybook alias. Rewrite to `@dominodatalab/extensions-tools` before pasting.
3. Component APIs come from the Storybook MCP. Don't invent props.
4. **URLs must be proxy-aware (assets and API).** When deployed, this app is served under a proxy prefix (e.g. `/preview/<appId>/`). Two things keep URLs working (see Step 8): `base: './'` in `vite.config.ts`, and an `apiBase` resolved against `document.baseURI`. Root-absolute URLs (`fetch('/api/…')`) bypass the proxy and 404.
   ```ts
   const apiBase = new URL('api', document.baseURI).href
   fetch(`${apiBase}/projects`)
   ```

It should also describe the MCP lookup workflow (`list-all-documentation` → `get-documentation` → `get-documentation-for-story`), note that React 18 / react-router 5 versions are pinned for peer-dep reasons, and remind that all backend URLs route through `apiBase` (not root-absolute paths).

If a `CLAUDE.md` already exists at the project root, **merge** rather than overwrite — preserve whatever project-specific guidance is there, and add a Domino section. The user's existing `CLAUDE.md` may have important info about their codebase that you'd erase by replacing it. If no `CLAUDE.md` exists at the project root, create one there — never inside the app folder, even when the app folder is a subdirectory of the project root.

---

## Step 11 — Update `.gitignore`

The **app folder** (the target path from Step 1) needs a `.gitignore` that excludes the things this skill (and a normal Vite + Domino workflow) generates but that shouldn't be committed. Make sure the following entries are present:

- `node_modules/` — npm install output.
- `dist/` and `build/` — Vite production builds.
- `.vite/` — Vite's dev cache.
- `*.log`, `npm-debug.log*`, `yarn-debug.log*`, `yarn-error.log*` — package manager logs.
- `.DS_Store`, `Thumbs.db` — OS junk.
- `.env`, `.env.local`, `.env.*.local` — local environment files. Keep `.env.example` if the project has one.
- `.claude/settings.local.json` — this is the per-user MCP/permissions file. It can leak machine-specific paths and personal preferences. `.mcp.json` **should** be committed (it's shared project config); `.claude/settings.local.json` should not. Only add this entry when the project root equals the app folder — when they differ, `.claude/settings.local.json` lives at the project root (Step 6), so it belongs in *that* directory's `.gitignore`. Don't create or modify a project-root `.gitignore` for this; surface the missing entry to the user and let them decide.

**How to handle the file itself:**

- If `.gitignore` doesn't exist, create it with the entries above.
- If it already exists (Vite's scaffold writes one), read it first and **append only the entries that aren't already covered**. Don't duplicate lines and don't reorder what's there. A grep-and-append per missing entry is fine.
- Preserve any project-specific patterns the user already has (their own ignored directories, secrets paths, build artifacts from other tools, etc.).
- If the user has committed something this skill is now telling git to ignore (e.g., they checked in `node_modules` once by accident, or `.claude/settings.local.json` is already tracked), don't run `git rm` on their behalf — surface it and let them decide.

---

## Step 12 — Verify

The most reliable verification is a clean production build:

```bash
npm run build
```

**`npm install` is not a sufficient check.** It can succeed while the toolchain is broken in ways that only surface at build time — most commonly the rolldown native-binding error when Vite 9 runs on Node < 20.19, which `install` happily writes to disk and only fails when `build` tries to load. Always run `npm run build` before reporting success.

This catches version mismatches deterministically. If it passes, the pinning and the entry-point wiring are correct.

`npm run dev` is a softer check — it'll start even with some misconfigurations. Run it if the user wants to eyeball the result, but `npm run build` is the one that gates "done".

**`npm run build` does NOT catch the proxy-URL bug from Step 8** — that's a runtime/deploy failure, not a compile one. After a successful build, also confirm the URL wiring by inspecting the built `dist/index.html`:

- Asset tags are **relative** (`src="./assets/…"`, `href="./assets/…"`) — not `/assets/…`. If they're root-absolute, `base: './'` is missing (Step 8a).
- API calls use `new URL('api', document.baseURI)` (Step 8b). `grep -rn "pathname.replace" src/` should return nothing — any hit is a pathname-based URL builder to replace.

Expected, not a failure: Vite will emit a warning that some chunks are larger than 500 KB. The Domino library bundles a lot — this is normal for Domino apps and doesn't need chasing.

If `build` fails:

- **Rolldown native binding error** (`Cannot find module @rolldown/binding-*` or similar) → the Vite toolchain in `package.json` requires Node ≥ 20.19 but the workspace is on an older Node. Go back to Step 4's Node-version branch and apply the downgrade set.
- JSX runtime or React typing errors → React or `@types/react` versions don't match. Recheck Step 4.
- TypeScript errors about `erasableSyntaxOnly` or missing `composite` → leftover from a TS-6 scaffold on a downgraded TS. Recheck the Node-version branch in Step 4 (strip `erasableSyntaxOnly`, add `composite: true`).
- Missing modules from `@dominodatalab/extensions-tools` → install didn't complete. Check `node_modules/@dominodatalab/extensions-tools/dist`.
- TypeScript errors in the user's existing code (only relevant on retrofits) → don't try to fix them as part of this skill. Surface them to the user and let them decide.

If the build is green but **assets or API calls 404 after deploy**:

- **Cause:** root-absolute URLs (asset tags pointing to `/assets/…`, or `fetch('/api/…')`) bypass the proxy.
- **Fix:** apply both parts of Step 8 — `base: './'` (8a) and `apiBase` via `document.baseURI` (8b).
- Verify the running app is on the latest commit and was re-published — a stale publish serves the old build regardless of code changes.

---

## Step 13 — Hand off

Tell the user:

- Where the project lives.
- How to start the dev server.
- That future component additions should go through the Storybook MCP (which the `CLAUDE.md` you wrote will remind the next Claude session about).
- Anything that changed in their existing code (downgraded versions, swapped router, edited entry point) so they're not surprised.
- **Bundle-size warning is expected.** Vite emits a `>500 KB chunk` warning on build because the Domino component library bundles a lot. It's not a failure — don't chase it.
- **Port 8888 is reserved inside Domino workspaces.** If the user runs both a Vite dev server and a backend dev server inside a Domino workspace, port 8888 is occupied by code-server. Pick a different port for one of them.

---

## Guiding principles when in doubt

- **Describe the goal, change the minimum.** The invariants in this skill are about Domino integration. Everything else in the user's project is their business — don't touch what isn't broken.
- **Read before you write.** On any retrofit, view a file before modifying it. The user's structure matters; preserve it where the Domino constraints don't override it.
- **Surface, don't silently fix.** If the user's existing code conflicts with a Domino invariant (router v6 routes, React 19 hooks), tell them what needs to change. Don't rewrite their app under the hood.
- **Test cases over conviction.** When unsure whether a component or prop exists, query the Storybook MCP. Don't ship invented props.

---

## What this skill is not for

- Editing `@dominodatalab/extensions-tools` source. Only the published npm package is consumed; upstream changes need a release from the library repo.
- Setting up test runners, CI, Tailwind, or other tooling on top. If the user wants those, finish the Domino bootstrap first (Step 12 green), then handle them separately — too many things can fail at once otherwise.
- Authenticating to private npm registries. If install fails on auth, ask the user; don't guess at credentials or workarounds.
- Building anything beyond a minimal app *before* the Storybook MCP is running. If the user asks for more than a minimal application while the MCP is not yet available, only scaffold the boilerplate plus a minimal app, then instruct the user to restart Claude after finishing the app configuration so the MCP loads and the rest can be built against real component APIs.
