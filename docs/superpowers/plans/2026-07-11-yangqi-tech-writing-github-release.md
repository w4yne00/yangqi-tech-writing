# yangqi-tech-writing GitHub Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the verified `yangqi-tech-writing` v1 skill as the public repository `w4yne00/yangqi-tech-writing` with complete open-source documentation, CI, semantic versioning, tag, Release, and installable `.skill` asset.

**Architecture:** Copy the already verified skill source into the current empty Git repository, then add release metadata and repository-level quality checks without changing runtime behavior. Validate locally before the only initial release commit; create the remote, push `main`, tag `v1.0.0`, publish the package, and read back all external state.

**Tech Stack:** Markdown, JSON, Python 3.9 standard library, `unittest`, Git, GitHub CLI, GitHub Actions, ZIP-based `.skill` package.

---

## Working paths

Repository root:

```text
/Users/wayne/Documents/guoqi-write-style
```

Verified source:

```text
/Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing
```

Existing installable package:

```text
/Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing.skill
```

The current repository has no commits and is on `main`. `docs/codex-handoff.md` is absent. Preserve the approved runtime files; repository work must not change their behavior unless a release test exposes a defect.

## Target file map

```text
.
├── .github/workflows/test.yml
├── docs/superpowers/specs/2026-07-11-yangqi-tech-writing-github-release-design.md
├── docs/superpowers/plans/2026-07-11-yangqi-tech-writing-github-release.md
├── evals/evals.json
├── references/**
├── scripts/**
├── tests/**
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
├── ROADMAP.md
├── SKILL.md
├── TESTING.md
└── VERSION
```

The `.skill` archive is a Release asset, not a tracked source file.

### Task 1: Import the verified v1 source

**Files:**

- Create: `SKILL.md`
- Create: `TESTING.md`
- Create: `evals/evals.json`
- Create: `references/**/*.md`
- Create: `scripts/*.py`
- Create: `tests/**/*.py`
- Create: `tests/fixtures/*`

- [ ] **Step 1: Confirm source and destination state**

Run:

```bash
git status --short --branch
python3 /Users/wayne/.agents/skills/skill-creator/scripts/quick_validate.py /Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing
```

Expected: `No commits yet on main`; validator prints `Skill is valid!`.

- [ ] **Step 2: Copy only the verified source tree**

Copy `SKILL.md`, `TESTING.md`, `evals/`, `references/`, `scripts/`, and `tests/` from the verified source to the repository root. Do not copy its short README because Task 2 replaces it with the public-project README. Do not copy `.skill`, `__pycache__`, `.DS_Store`, or `.pyc` files.

- [ ] **Step 3: Verify imported content identity**

Run:

```bash
diff -rq /Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing/references references
diff -rq /Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing/scripts scripts
diff -rq /Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing/tests tests
cmp /Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing/SKILL.md SKILL.md
cmp /Users/wayne/Documents/Codex/2026-07-10/skill-https-github-com-oubigfa-de/outputs/yangqi-tech-writing/evals/evals.json evals/evals.json
```

Expected: all commands exit `0` without output.

### Task 2: Add public project metadata and documentation

**Files:**

- Create: `.gitignore`
- Create: `LICENSE`
- Create: `VERSION`
- Create: `CHANGELOG.md`
- Create: `ROADMAP.md`
- Create: `README.md`

- [ ] **Step 1: Add the release metadata contract test**

Create `tests/test_release_metadata.py` with tests that assert:

```python
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ReleaseMetadataTests(unittest.TestCase):
    def test_version_is_1_0_0(self):
        self.assertEqual("1.0.0", (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_readme_names_release_and_boundaries(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in ["yangqi-tech-writing", "v1.0.0", "七类场景", "H1—H6", "不判断作者身份", "MIT"]:
            self.assertIn(phrase, text)

    def test_release_documents_exist(self):
        for name in ["LICENSE", "CHANGELOG.md", "ROADMAP.md", ".gitignore"]:
            self.assertTrue((ROOT / name).is_file(), name)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the metadata test and confirm failure**

Run:

```bash
python3 -m unittest tests/test_release_metadata.py -v
```

Expected: failure because release metadata files do not yet exist.

- [ ] **Step 3: Create release files**

Use these exact contracts:

- `VERSION` contains one line: `1.0.0`.
- `.gitignore` excludes `__pycache__/`, `*.py[cod]`, `.DS_Store`, `.idea/`, `.vscode/`, `.venv/`, `dist/`, `build/`, and `*.skill`.
- `LICENSE` is the standard MIT License with `Copyright (c) 2026 Wayne`.
- `CHANGELOG.md` uses Keep a Changelog headings and records `1.0.0 - 2026-07-11`, including seven scenes, three scripts, 24 evals, 22 existing unit tests, quality gates, and limitations.
- `ROADMAP.md` lists v1.1 compatibility/eval improvements, v1.2 Style Profile support, and v2.0 `yangqi-style-distiller` integration without release dates.
- `README.md` follows the approved design order: positioning, seven scenes, execution flow, install, usage, layout, scripts and exit codes, testing, version roadmap, contribution, MIT, and limitations. It must not claim guaranteed compliance, technical correctness, or authorship detection.

- [ ] **Step 4: Run the metadata test**

Run:

```bash
python3 -m unittest tests/test_release_metadata.py -v
```

Expected: 3 tests pass.

### Task 3: Add GitHub Actions and validate repository contracts

**Files:**

- Create: `.github/workflows/test.yml`
- Modify: `tests/test_release_metadata.py`

- [ ] **Step 1: Extend the failing test for CI versions and commands**

Add assertions that `.github/workflows/test.yml` contains:

```python
def test_ci_matrix_and_commands(self):
    text = (ROOT / ".github/workflows/test.yml").read_text(encoding="utf-8")
    for token in ["3.9", "3.11", "3.12", "unittest discover -s tests -v", "style_audit.py tests/fixtures/sample.md"]:
        self.assertIn(token, text)
```

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
python3 -m unittest tests/test_release_metadata.py -v
```

Expected: error or failure because `.github/workflows/test.yml` is absent.

- [ ] **Step 3: Create the workflow**

Create `.github/workflows/test.yml` with `push` and `pull_request` triggers, `actions/checkout@v4`, `actions/setup-python@v5`, matrix versions `3.9`, `3.11`, `3.12`, and these steps:

```yaml
- name: Run unit tests
  run: python -m unittest discover -s tests -v
- name: Run style audit smoke test
  run: python scripts/style_audit.py tests/fixtures/sample.md
```

- [ ] **Step 4: Run metadata and full unit tests**

Run:

```bash
python3 -m unittest tests/test_release_metadata.py -v
python3 -m unittest discover -s tests -v
```

Expected: metadata tests pass; full suite reports 26 tests after adding four release tests.

### Task 4: Validate and package the release candidate

**Files:**

- Generate outside Git tracking: `/tmp/yangqi-tech-writing-release/yangqi-tech-writing.skill`

- [ ] **Step 1: Validate Skill and JSON**

Run:

```bash
python3 /Users/wayne/.agents/skills/skill-creator/scripts/quick_validate.py .
jq empty evals/evals.json
jq '.evals | length' evals/evals.json
```

Expected: `Skill is valid!`, JSON validation exits `0`, count is `24`.

- [ ] **Step 2: Package from the repository root**

Run from `/Users/wayne/.agents/skills/skill-creator`:

```bash
python3 -m scripts.package_skill /Users/wayne/Documents/guoqi-write-style /tmp/yangqi-tech-writing-release
```

Because the working directory is currently named `guoqi-write-style`, stage a copy at `/tmp/yangqi-tech-writing-release/yangqi-tech-writing/` before packaging so the archive top-level directory and filename are both `yangqi-tech-writing`.

- [ ] **Step 3: Verify package contents**

Run:

```bash
unzip -t /tmp/yangqi-tech-writing-release/yangqi-tech-writing.skill
unzip -Z1 /tmp/yangqi-tech-writing-release/yangqi-tech-writing.skill
```

Expected: no compressed-data errors; one `yangqi-tech-writing/` root; no `evals/`, `__pycache__`, `.DS_Store`, `.pyc`, or `.skill` entry.

### Task 5: Create the initial local release commit

**Files:**

- Stage: all approved repository source and documentation files

- [ ] **Step 1: Review scope before staging**

Run:

```bash
git status --short
git diff --check
```

Expected: only target repository files are untracked or modified; no whitespace errors.

- [ ] **Step 2: Stage explicit release paths**

Stage `.github`, `.gitignore`, `CHANGELOG.md`, `LICENSE`, `README.md`, `ROADMAP.md`, `SKILL.md`, `TESTING.md`, `VERSION`, `docs`, `evals`, `references`, `scripts`, and `tests`.

- [ ] **Step 3: Commit the release candidate**

Run:

```bash
git commit -m "release: publish yangqi-tech-writing v1.0.0"
```

Expected: the repository has one root commit on `main` and `git status --short` is empty.

### Task 6: Authenticate and create the public GitHub repository

**External state:**

- Create: `https://github.com/w4yne00/yangqi-tech-writing`

- [ ] **Step 1: Verify GitHub authentication**

Run:

```bash
gh auth status
```

Expected: authenticated as `w4yne00`. If the token is still invalid, stop and ask the user to run `gh auth login -h github.com`; do not create an alternative account or repository.

- [ ] **Step 2: Confirm repository name is available**

Run:

```bash
gh repo view w4yne00/yangqi-tech-writing --json nameWithOwner,visibility
```

Expected before creation: repository not found. If it exists, stop and inspect it before any push.

- [ ] **Step 3: Create and push the public repository**

Run:

```bash
gh repo create w4yne00/yangqi-tech-writing --public --source=. --remote=origin --push --description "G 企网络安全与信息化技术材料的起草、审阅与保真改写 Skill"
```

Expected: public repository created; `origin` points to the new repository; `main` is pushed with upstream tracking.

### Task 7: Tag and publish v1.0.0

**External state:**

- Create: annotated tag `v1.0.0`
- Create: GitHub Release `v1.0.0`
- Upload: `yangqi-tech-writing.skill`

- [ ] **Step 1: Create and push the annotated tag**

Run:

```bash
git tag -a v1.0.0 -m "yangqi-tech-writing v1.0.0"
git push origin v1.0.0
```

Expected: local and remote tag `v1.0.0` point to the initial release commit.

- [ ] **Step 2: Create the GitHub Release**

Create a temporary Release note containing: first public release, seven scenes, four hard principles, H1—H6, three scripts, 24 evals, test matrix, and the three capability limitations. Run:

```bash
gh release create v1.0.0 /tmp/yangqi-tech-writing-release/yangqi-tech-writing.skill --repo w4yne00/yangqi-tech-writing --title "yangqi-tech-writing v1.0.0" --notes-file /tmp/yangqi-tech-writing-release-notes.md
```

Expected: published Release with one `.skill` asset.

- [ ] **Step 3: Read back all external state**

Run:

```bash
gh repo view w4yne00/yangqi-tech-writing --json nameWithOwner,url,visibility,defaultBranchRef
gh run list --repo w4yne00/yangqi-tech-writing --limit 5
gh release view v1.0.0 --repo w4yne00/yangqi-tech-writing --json url,tagName,isDraft,isPrerelease,assets
git status --short --branch
```

Expected: repository is PUBLIC, default branch `main`, Release is published and not prerelease, asset is present, and local tree is clean. If Actions is still queued, report the exact status rather than claiming success.

## Plan self-review

- Spec coverage: repository structure, README, MIT, CI, semantic versions, v1.0.0 tag, Release asset, external verification, and capability boundaries are all mapped.
- Placeholder scan: no TODO/TBD or undefined implementation step remains.
- Type consistency: `VERSION` uses `1.0.0`; Git tag and Release use `v1.0.0`; repository name is consistently `w4yne00/yangqi-tech-writing`.
- Safety: repository creation, push, tag, and Release are explicit user-authorized external writes; invalid authentication blocks only external steps.
