# AgentLens — Priority 1 Publishing Guide

**Owner:** Internal only — push this file to `Agentlens_internal` only, never to the public repo.
**Objective:** Get `pip install agentlens-sdk`, `pip install agentlens-server`, `pip install agentlens-mcp`, and `npm install @agentlens/sdk` working publicly so any developer can install in one line.

---

## Status Overview

| Package | PyPI name | npm name | Status |
|---------|-----------|----------|--------|
| Python SDK | `agentlens-sdk` | — | dist/ artifacts built, ready to upload |
| Server | `agentlens-server` | — | dist/ artifacts built, ready to upload |
| MCP Server | `agentlens-mcp` | — | not yet built, pyproject.toml now complete |
| TypeScript SDK | — | `@agentlens/sdk` | needs `npm run build` then publish |

**Name availability confirmed:**
- `agentlens-sdk` on PyPI — AVAILABLE
- `agentlens-server` on PyPI — AVAILABLE
- `agentlens-mcp` on PyPI — AVAILABLE
- `@agentlens/sdk` on npm — requires `@agentlens` org to be claimed first

---

## Pre-flight Checklist

Run through this before any publish command:

- [ ] All URLs in source files say `ArkFelix7/agentlens` (not `agentlens-oss`) — done 2026-03-06
- [ ] `mcp-server/pyproject.toml` has full metadata (readme, license, classifiers, URLs) — done 2026-03-06
- [ ] CI is green on `main` (server + dashboard + sdk-ts pass; sdk-python fix merged)
- [ ] You have a PyPI account and a PyPI API token (see section below)
- [ ] You have an npm account with `@agentlens` org claimed (see section below)
- [ ] `python3 -m pip install build twine` runs without error
- [ ] `node --version` >= 18, `npm --version` >= 9

---

## Step 1: PyPI Setup (one-time)

### 1.1 Create PyPI account
1. Go to https://pypi.org/account/register/
2. Use a permanent email (this is the package owner forever)
3. Enable 2FA immediately (required for publishing)

### 1.2 Create API token
1. https://pypi.org/manage/account/token/
2. Token scope: "Entire account" for first publish (you can scope per-project after first upload)
3. Copy the token — it starts with `pypi-` and is shown only once
4. Store it: `~/.pypirc`

```ini
[distutils]
index-servers = pypi

[pypi]
  username = __token__
  password = pypi-YOUR_TOKEN_HERE
```

chmod 600 `~/.pypirc`.

### 1.3 Install build tools
```bash
pip install --upgrade build twine
```

---

## Step 2: Build and Publish Python Packages

### 2.1 Python SDK (`agentlens-sdk`)

```bash
cd /Users/aarya/dev_all/Agentlens/sdk-python

# Clean any old artifacts
rm -rf dist/ build/ *.egg-info

# Build sdist + wheel
python3 -m build

# Verify the build locally
twine check dist/*
# Should output: PASSED for both .tar.gz and .whl

# Dry-run upload to TestPyPI first (strongly recommended)
twine upload --repository testpypi dist/*
# Username: __token__
# Password: <your testpypi token>

# Install from TestPyPI to verify
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentlens-sdk
python3 -c "from agentlens_sdk import init, trace, auto_instrument; print('OK')"

# If TestPyPI passes, upload to production PyPI
twine upload dist/*
```

**Expected dist/ contents after build:**
```
agentlens_sdk-0.1.0-py3-none-any.whl
agentlens_sdk-0.1.0.tar.gz
```

**Post-publish verification:**
```bash
pip install agentlens-sdk
python3 -c "from agentlens_sdk import init, trace, auto_instrument, get_tracer; print('agentlens-sdk install OK')"
```

### 2.2 Server (`agentlens-server`)

```bash
cd /Users/aarya/dev_all/Agentlens/server

# The server pyproject.toml uses packages = ["src"] — this packages the entire src/ tree.
# The CLI entrypoint references "src.main:run" which works when installed.
rm -rf dist/ build/ *.egg-info
python3 -m build
twine check dist/*
twine upload --repository testpypi dist/*

# Verify CLI entrypoint works from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentlens-server
agentlens-server &   # should start on :8766
curl http://localhost:8766/health
kill %1

# Production upload
twine upload dist/*
```

**Post-publish verification:**
```bash
pip install agentlens-server
agentlens-server &
curl http://localhost:8766/health  # {"status":"ok"}
kill %1
```

### 2.3 MCP Server (`agentlens-mcp`)

```bash
cd /Users/aarya/dev_all/Agentlens/mcp-server

rm -rf dist/ build/ *.egg-info
python3 -m build
twine check dist/*
twine upload --repository testpypi dist/*

# Verify CLI entrypoint (requires agentlens-server running first)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentlens-mcp
agentlens-mcp --help   # should print usage or start listening on stdio

# Production upload
twine upload dist/*
```

**Post-publish verification:**
```bash
pip install agentlens-mcp
# Configure in Claude Desktop and verify tool appears
```

### 2.4 Publish order

Publish in this order to avoid any circular install issues:

1. `agentlens-sdk` first
2. `agentlens-server` second
3. `agentlens-mcp` third

---

## Step 3: npm Setup and Publish (`@agentlens/sdk`)

### 3.1 Claim `@agentlens` npm organization (one-time, CRITICAL)

1. Log into npmjs.com
2. Go to https://www.npmjs.com/org/create
3. Organization name: `agentlens`
4. Choose **Free** plan (unlimited public packages, $0)
5. Once created, the `@agentlens` scope is yours and `npm publish` with `"publishConfig": {"access": "public"}` will work

**If `@agentlens` is already taken:** Check if the org is active. If it appears abandoned (no packages, no activity), you can contact npm support to request transfer. As a fallback, use `@agentlens-dev/sdk` or `agentlens-sdk` (unscoped).

### 3.2 Build and publish

```bash
cd /Users/aarya/dev_all/Agentlens/sdk-typescript

# Install deps
npm install

# Build (tsc → dist/)
npm run build

# Check dist contents
ls dist/
# Should see: index.js, index.d.ts, client.js, trace.js, types.js, config.js, interceptors/

# Dry-run to see what would be published
npm publish --dry-run

# Login to npm
npm login
# Username: your npm username
# Password: your npm password or OTP

# Publish
npm publish
```

**`package.json` fields already set (no changes needed):**
- `"publishConfig": {"access": "public"}` — required for scoped packages, prevents 402 error
- `"files": ["dist", "README.md", "LICENSE"]` — prevents leaking source/node_modules
- `"prepublishOnly": "npm run build"` — auto-builds before publish

**Post-publish verification:**
```bash
npm install @agentlens/sdk
node -e "const { init, trace, autoInstrument } = require('@agentlens/sdk'); console.log('OK')"
```

---

## Step 4: Post-Publish Checklist

After all packages are live, verify the full install flow from a clean environment:

```bash
# Create a fresh venv
python3 -m venv /tmp/agentlens-test && source /tmp/agentlens-test/bin/activate

# Install all packages
pip install agentlens-server agentlens-sdk agentlens-mcp

# Verify server
agentlens-server &
sleep 1
curl -s http://localhost:8766/health

# Verify SDK
python3 -c "
from agentlens_sdk import init, trace, auto_instrument, get_tracer
print('SDK imports OK')
"

# Stop server
kill %1

deactivate
rm -rf /tmp/agentlens-test
```

```bash
# npm verification
mkdir /tmp/agentlens-npm-test && cd /tmp/agentlens-npm-test
npm init -y
npm install @agentlens/sdk
node -e "const sdk = require('@agentlens/sdk'); console.log('TS SDK OK:', Object.keys(sdk))"
cd - && rm -rf /tmp/agentlens-npm-test
```

---

## Step 5: Update README Badges

After PyPI and npm are live, update `README.md` badges — they point to the right places already but will show "not found" until packages are published:

```markdown
[![PyPI SDK](https://img.shields.io/pypi/v/agentlens-sdk?label=agentlens-sdk)](https://pypi.org/project/agentlens-sdk/)
[![PyPI Server](https://img.shields.io/pypi/v/agentlens-server?label=agentlens-server)](https://pypi.org/project/agentlens-server/)
[![npm](https://img.shields.io/npm/v/@agentlens/sdk)](https://www.npmjs.com/package/@agentlens/sdk)
```

These are already in the README. They go live automatically within 5–10 minutes of publishing.

---

## Step 6: OG Image (agentlens-og.png)

Already generated programmatically at `dashboard/public/agentlens-og.png` (1200×630px, 40KB).

To regenerate (e.g., after UI updates):
```bash
cd /Users/aarya/dev_all/Agentlens
pip install pillow -q
python3 scripts/generate_og_image.py   # see script below
```

The image is referenced in `dashboard/index.html` OG meta tags (committed 2026-03-06) and in the README demo GIF placeholder comment.

**To create an improved version** (after you have a real screenshot):
1. Take a screenshot of the dashboard Traces tab with live data
2. Resize to 1200×630 with the terminal command: `sips -z 630 1200 screenshot.png --out agentlens-og.png`
3. Or use Figma/Canva template: dark card (#0a0a0f), indigo accent bar at top, screenshot in center, "AgentLens" in JetBrains Mono top-left, tagline below

---

## Step 7: CI/CD Integration for Automated Publishing

Once packages are manually published once, add automated publishing to CI on version tag push.

### 7.1 GitHub Secrets to add (Settings → Secrets → Actions)

| Secret name | Value |
|-------------|-------|
| `PYPI_TOKEN` | Your PyPI API token (`pypi-...`) |
| `NPM_TOKEN` | Your npm access token (create at npmjs.com → Access Tokens → Automation type) |

### 7.2 Add publish workflow (`.github/workflows/publish.yml`)

```yaml
name: Publish

on:
  push:
    tags:
      - 'v*'   # triggers on v0.1.0, v0.2.0, etc.

jobs:
  publish-sdk-python:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: sdk-python
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build twine
      - run: python3 -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}

  publish-server:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: server
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build twine
      - run: python3 -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}

  publish-mcp:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: mcp-server
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install build twine
      - run: python3 -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}

  publish-sdk-typescript:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: sdk-typescript
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          registry-url: "https://registry.npmjs.org"
      - run: npm ci
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 7.3 How to trigger a publish

```bash
# Bump versions in all pyproject.toml + package.json first, then:
git tag v0.1.0
git push origin v0.1.0
# GitHub Actions will build and publish all 4 packages automatically
```

---

## Troubleshooting

### "File already exists" on PyPI
You cannot re-upload the same version. Bump to `0.1.1` in `pyproject.toml`, rebuild, and re-upload.

### 402 on npm publish
The `@agentlens` org is not claimed or `publishConfig.access` is not `"public"`. Both are already fixed in `package.json`. Ensure org is created first.

### "Package name not available" on PyPI
Run `pip install <name>` — if it errors with "No matching distribution", the name is available. If it installs something, the name is taken.

### Wheel contains wrong files
Check `[tool.hatch.build.targets.wheel] packages = [...]` in `pyproject.toml`. Run `python3 -m build && unzip -l dist/*.whl` to inspect contents before uploading.

### CLI entrypoint `agentlens-server` not found after install
The `[project.scripts]` section maps `agentlens-server = "src.main:run"`. This only works when the package is installed (not `python3 src/main.py`). Verify with `which agentlens-server` after `pip install agentlens-server`.

### TestPyPI install fails with dependency errors
TestPyPI doesn't mirror all of production PyPI. Use `--extra-index-url https://pypi.org/simple/` when installing from TestPyPI so it falls back to production for dependencies.

---

## Key Contacts and Resources

| Resource | URL |
|----------|-----|
| PyPI project dashboard | https://pypi.org/manage/projects/ |
| TestPyPI | https://test.pypi.org/ |
| npm org management | https://www.npmjs.com/org/agentlens |
| GitHub Actions | https://github.com/ArkFelix7/agentlens/actions |
| Public repo | https://github.com/ArkFelix7/agentlens |
| Internal repo | https://github.com/ArkFelix7/Agentlens_internal |

---

## Version Bump Checklist (for each future release)

1. `sdk-python/pyproject.toml` → bump `version`
2. `server/pyproject.toml` → bump `version`
3. `mcp-server/pyproject.toml` → bump `version`
4. `sdk-typescript/package.json` → bump `version`
5. Git tag: `git tag v<version> && git push origin v<version>`
6. GitHub Actions publish workflow triggers automatically (after initial manual setup)
7. Update `CHANGELOG.md` (create one when shipping 0.2.0)
