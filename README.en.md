# writing-style-extractor

**Reverse-engineer an author's writing style from sample articles into an evidence-backed, executable rule pack — validated through controlled trials.**

[中文](./README.md) ｜ [SKILL.md](./SKILL.md) ｜ [Full methodology](./references/methodology.md)

---

## Why it exists

"Imitate my writing style" is a wish, not a constraint — an AI only obeys specific, testable rules. The two common approaches each fail in their own way:

- **Feed a few sample articles**: the model copies the author's identity elements — self-references, column tags, signature closing lines — and the results are unstable.
- **Run a one-shot "style analysis"**: the conclusions cannot be verified. "The author favors short sentences" — evidence from which article, which paragraph, at what frequency? All on the model's word, and never acceptance-tested.

This skill translates the *feeling* of "reads like that author" into an **executable instruction manual**, then validates it the way a clinical trial would: controlled experiments, blind evaluation, held-out samples, and acceptance gates.

## How it works: six stages × user gates

| Stage | What happens | Output | Gate |
|---|---|---|---|
| 1 Archive & sampling | Define scope; collect samples as "6 mining + 2 dev-check + 2 held-out" | Archive notes, sample list, numbered texts | User confirms grouping & boundaries |
| 2 Analysis & rule prototype | Statistical signature + six-dimension per-article analysis → cross-article comparison; rule pack V0.1 | Evidence table, rule pack | Evidence check passes + user review |
| 3 Development trials | 3 tasks × groups A/B/C/D = 12 essays; blind evaluation; iterate via failure-mode table | Trial records, blind-eval sheets | User confirms revision direction after scoring |
| 4 Independent retest | Freeze rules; 3 fresh tasks × rules vs exemplar-fed baseline × 2 runs = 12 essays; held-out ground truth unlocked for review | Retest records, gate checklist | All five acceptance gates pass |
| 5 Promotion | Ship a deployable rule pack (with conflict protocol & validity statement) | Promotion snapshot | **Explicit user confirmation required** |

The four-group design: **A** base input / **B** +exemplar essays / **C** +rules / **D** +rules+exemplars. C vs A answers "do the rules work at all"; D vs B answers "what do rules add over just feeding exemplars" — the reason a rule pack should exist, and the mandatory baseline in retesting.

### Four core mechanisms

1. **Traceable evidence.** Every observation carries a sample-paragraph citation (e.g. `S01-P05`); `evidence_check.py` verifies each one — any citation that cannot be located gets deleted. No "model impressions" allowed as evidence.
2. **Held-out isolation.** Two ground-truth articles stay untouched until rules are frozen — no analysis, no revision, no scoring — so the retest has uncontaminated judges.
3. **Blindness by mechanism.** `blind_eval.py shuffle` produces shuffled, anonymized texts plus a key file that stays sealed until scoring is done; `tally` then unblinds and checks the acceptance gates.
4. **Facts first.** Content truth > explicit task requirements > style rules. Style is never an excuse to fabricate facts, data, or experiences; rules transfer expression only, never the author's identity elements.

## Installation

For coding agents that support the SKILL.md convention (Claude Code, ZCode, etc.):

```bash
git clone https://github.com/<your-username>/writing-style-extractor.git
# Copy the whole directory into your agent's user-level skills directory, e.g.:
cp -r writing-style-extractor ~/.claude/skills/          # Claude Code
cp -r writing-style-extractor ~/.zcode/skills/           # ZCode
```

Works without an agent too: [references/methodology.md](./references/methodology.md) is the complete methodology, the six [templates/](./templates/) can be filled in by hand, and the three [scripts/](./scripts/) run standalone (Python 3 stdlib only).

## Quick start

1. Collect ~10 articles by the target author (clean body text, authorship confirmed) into a directory;
2. Tell your agent to "extract the writing style" / "create a style archive";
3. The skill scans the archive directory to infer the current stage, resumes from the breakpoint, and waits for your confirmation at each gate;
4. After six stages you get a rule pack with an explicit validity statement, deployable to any model.

## Scripts

| Script | Command | Purpose |
|---|---|---|
| style_stats.py | `python scripts/style_stats.py <analysis-dir>` | Statistical signature: single-sentence-paragraph ratio, average paragraph length, sentence-length distribution… |
| evidence_check.py | `python scripts/evidence_check.py <evidence.md> <analysis-dir>` | Citation verification; exits non-zero on any untraceable reference |
| blind_eval.py | `python scripts/blind_eval.py shuffle <output-dir>`<br>`python scripts/blind_eval.py tally <eval-dir>` | Build a shuffled blind-eval bundle with a sealed key; unblind, score, and check gates afterwards |

## Repository layout

```
├── SKILL.md                    # skill entry: state machine, hard rules, six-stage flow
├── references/
│   ├── methodology.md          # full methodology (sampling, analysis, rules, validation, revision)
│   └── archive-protocol.md     # archive directory conventions & stage inference for resuming
├── templates/                  # six templates: sample list / evidence / rule pack / task brief / trial log / blind-eval sheet
├── scripts/                    # three deterministic scripts (stdlib only, no dependencies)
└── VERSION / CHANGELOG.md / LICENSE (MIT)
```

## Boundaries & hard rules

- **This repository contains no sample articles by any real author.** Users bring their own samples and are responsible for their legality; produced rule packs must not redistribute the original texts either.
- Rules transfer **expression only**. The author's self-references, column tags, engagement phrases, and signature closing lines are identity elements — copying them is forbidden.
- "All five gates passed" yields a *release candidate* only; freezing it as an official baseline requires explicit user confirmation — the model never promotes on its own.
- Every rule pack ships with a validity statement (genre, length, verified/unverified scenarios). Extrapolate at your own risk.

## Validation status (as of v0.1.0)

- The full six-stage pipeline has been completed on one style through promotion: 10 samples, 66 evidence observations, 24 rules (10 core + 16 conditional), 24 trial essays, 6/6 paired wins in the independent retest, all five acceptance gates passed.
- The process and templates have been reused to set up a second, substantially different style archive.
- The three scripts were tested against a real archive: statistical metrics within ≤2 percentage points of manual analysis; all 85 evidence citations verified; blind evaluation exercised in both dev and retest modes.

## License

[MIT](./LICENSE)
