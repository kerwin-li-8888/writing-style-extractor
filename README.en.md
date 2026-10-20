# writing-style-extractor

**Turn one article — or a batch — into an evidence-backed, executable writing-style pack, validated by a real trial write.**

[中文](./README.md) ｜ [SKILL.md](./SKILL.md) ｜ [Full methodology](./references/methodology.md)

---

## Why it exists

"Imitate my writing style" is a wish, not a constraint — an AI only obeys specific, testable rules. The two common approaches each fail in their own way:

- **Feed a few sample articles**: the model copies the author's identity elements — self-references, column tags, signature closing lines — and the results are unstable.
- **Run a one-shot "style analysis"**: the conclusions cannot be verified. "The author favors short sentences" — evidence from which article, which paragraph, at what frequency? All on the model's word, and never acceptance-tested.

This skill translates the *feeling* of "reads like that author" into an **executable instruction manual**: every move traces back to a paragraph citation, and every produced style pack has to survive a real trial write. With enough samples, it adds controlled trials, blind evaluation, held-out retesting, and acceptance gates.

## Start small: three tiers

| Samples | Route | Output | What it can do | What it cannot claim |
|---|---|---|---|---|
| **1** | Single-article candidate | Paired style pack | Extract observable moves from that article; trial-write a new material of the same type | The author's overall style, cross-genre transfer, frequency statistics, full validation |
| **2-3** | Few-sample candidate | Paired style pack | Compare recurring moves; separate core and conditional rules | A stable author profile, a settled minimum sample size |
| **8-10** | Full validation | Rule pack | Four-arm trials + blind evaluation + held-out retest + five gates | Applicability to every genre |

All three tiers share the same evidence bar: every `S{nn}-P{nn}` citation must be traceable, and `evidence_check.py` removes anything it cannot find. Smaller samples lower the scope of the claim, never the evidence standard.

### The single-article path

Good for: you found one article whose style you want to reuse, and want a pack you can trial-write with first.

1. **Build a numbered analysis text**: `P01` is the title; number the body paragraphs as `S01-P01…`.
2. **Extract executable moves**: cite only this article's `S01-Pxx`; mark each move core / conditional / optional; separate style evidence from topic facts.
3. **Reverse-engineer the preparation rules**: for each move, work out what material it needs, how to select it, and what to do when it is missing.
4. **Generate the candidate pack**: `SKILL.md` plus `references/style-contract.json`, `preparation.md`, `rewriting.md`; `sample_count` is 1.
5. **Trial-write**: use a new material of the same type, record the observed usable range and open issues, and let the user evaluate before calling it "candidate-usable".

Hard boundaries for a single-article candidate:

- No frequency, share, or stability claims. "Appears in this article" does not mean "the author often does this".
- Accidental moves must not be promoted to universal rules; prefer core moves plus conditional rules.
- Scope is limited to new materials of the same type; cross-topic, cross-genre, and cross-platform are unverified.
- A single-article candidate cannot be promoted to an official baseline. To promote, add samples and run full validation.

## Full validation: five gates + observation period

| Stage | What happens | Output | Gate |
|---|---|---|---|
| 1 Archive & sampling | Define scope; collect samples as "6 mining + 2 dev-check + 2 held-out" | Archive notes, sample list, numbered texts | User confirms grouping & boundaries |
| 2 Analysis & rule prototype | Statistical signature + six-dimension per-article analysis → cross-article comparison; rule pack V0.1 | Evidence table, rule pack | Evidence check passes + user review |
| 3 Development trials | 3 tasks × groups A/B/C/D = 12 essays; blind evaluation; iterate via failure-mode table | Trial records, blind-eval sheets | User confirms revision direction after scoring |
| 4 Independent retest | Freeze rules; 3 fresh tasks × rules vs exemplar-fed baseline × 2 runs = 12 essays; held-out ground truth unlocked for review | Retest records, gate checklist | All five acceptance gates pass |
| 5 Promotion | Ship a deployable rule pack (with conflict protocol & validity statement) | Promotion snapshot | **Explicit user confirmation required** |

After promotion the archive enters an observation period: real-use issues are logged and accumulated for the next revision.

The four-group design: **A** base input / **B** +exemplar essays / **C** +rules / **D** +rules+exemplars. C vs A answers "do the rules work at all"; D vs B answers "what do rules add over just feeding exemplars" — the reason a rule pack should exist, and the mandatory baseline in retesting.

### Four core mechanisms

1. **Traceable evidence.** Every observation carries a sample-paragraph citation (e.g. `S01-P05`); `evidence_check.py` verifies each one — any citation that cannot be located gets deleted. No "model impressions" allowed as evidence.
2. **Held-out isolation.** Two ground-truth articles stay untouched until rules are frozen — no analysis, no revision, no scoring — so the retest has uncontaminated judges.
3. **Blindness by mechanism.** `blind_eval.py shuffle` produces shuffled, anonymized texts plus a key file that stays sealed until scoring is done; `tally` then unblinds and checks the acceptance gates.
4. **Facts first.** Content truth > explicit task requirements > style rules. Style is never an excuse to fabricate facts, data, or experiences; rules transfer expression only, never the author's identity elements.

## Installation

For coding agents that support the SKILL.md convention (Claude Code, ZCode, etc.):

```bash
git clone https://github.com/kerwin-li-8888/writing-style-extractor.git
# Copy the whole directory into your agent's user-level skills directory, e.g.:
cp -r writing-style-extractor ~/.claude/skills/          # Claude Code
cp -r writing-style-extractor ~/.zcode/skills/           # ZCode
```

Works without an agent too: [references/methodology.md](./references/methodology.md) is the complete methodology, the ten [templates/](./templates/) can be filled in by hand, and the four [scripts/](./scripts/) run standalone (Python 3 stdlib only).

## Quick start

**One article**

1. Put the article in a directory (clean body text, source confirmed);
2. Tell your agent: "**I only have one article — extract the style and build a paired pack**";
3. The skill follows the single-article candidate route: extract evidence, generate the pack, and ask you to trial-write a same-type material;
4. You evaluate the trial write, then decide whether to add samples and run full validation.

**8-10 articles**

1. Collect the target author's articles (clean body text, authorship confirmed);
2. Tell your agent to "extract the writing style" / "create a style archive";
3. The skill scans the archive directory, infers the current stage, resumes from the breakpoint, and waits for your confirmation at each gate;
4. After five gates you get a rule pack with an explicit validity statement, deployable to any model.

## Scripts

| Script | Command | Purpose |
|---|---|---|
| style_stats.py | `python scripts/style_stats.py <analysis-dir>` | Statistical signature: single-sentence-paragraph ratio, average paragraph length, sentence-length distribution… |
| evidence_check.py | `python scripts/evidence_check.py <evidence.md> <analysis-dir>` | Citation verification; exits non-zero on any untraceable reference |
| blind_eval.py | `python scripts/blind_eval.py shuffle <output-dir>`<br>`python scripts/blind_eval.py tally <eval-dir>` | Build a shuffled blind-eval bundle with a sealed key; unblind, score, and check gates afterwards |
| package_check.py | `python scripts/package_check.py <pack-dir>` | Paired-pack structure check: components, JSON, rule IDs, mapping, evidence, dependencies; exits 0 for a valid pack |

All four scripts use only the Python 3 standard library. `package_check.py` checks structure and fields only — it does not prove style quality or factual accuracy. Do not record "pack check passed" unless the checker was actually run.

## Repository layout

```
├── SKILL.md                    # skill entry: state machine, hard rules, dual routes, sample tiers
├── references/
│   ├── methodology.md          # full methodology (sampling, analysis, rules, validation, revision, single-article path)
│   ├── archive-protocol.md     # archive directory conventions & stage inference for resuming
│   └── paired-package-spec.md  # paired-pack spec: layout, style-contract.json, check criteria
├── templates/                  # ten templates: six full-validation + four paired-pack
├── scripts/                    # four deterministic scripts (stdlib only, no dependencies)
└── VERSION / CHANGELOG.md / LICENSE (MIT)
```

## Boundaries & hard rules

- **This repository contains no sample articles by any real author.** Users bring their own samples and are responsible for their legality; produced rule packs must not redistribute the original texts either.
- Rules transfer **expression only**. The author's self-references, column tags, engagement phrases, and signature closing lines are identity elements — copying them is forbidden.
- "All five gates passed" yields a *release candidate* only; freezing it as an official baseline requires explicit user confirmation — the model never promotes on its own. A single-article candidate cannot be promoted to an official baseline.
- Every rule pack ships with a validity statement (genre, length, verified/unverified scenarios). Extrapolate at your own risk.

## Validation status (as of v0.4.0)

- **Single-article candidate**: one article produced a V0.5 candidate pack (12 rules, 1 sample). `package_check.py` returned 0, `evidence_check.py` verified all 68 citations, `style_stats.py` produced a single-article signature; a real trial write on a same-type material was then confirmed by the user.
- **Few-sample candidate**: two same-topic samples independently produced another V0.5 candidate pack, with the same structural checks and a real trial write.
- **Full validation**: 10 samples, 66 evidence observations, 24 rules (10 core + 16 conditional), 24 trial essays, 6/6 paired wins in the independent retest, all five acceptance gates passed, promoted to an official baseline.
- **Scripts**: all four tested on real archives and packs; `package_check.py` returns 0 for valid packs and non-zero for missing preparation components, core rules without material handling, out-of-pack dependencies, sample observations without evidence, generic methods citing samples, invalid JSON, and duplicate rule IDs.

These are the maintainer's own validation records, not third-party replication. A candidate pack is not an official baseline; the applicable scope is defined by each pack's `style-contract.json`.

## License

[MIT](./LICENSE)
