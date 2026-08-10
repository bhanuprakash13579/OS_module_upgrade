# MSc Math Sem-1 Booklet — Fix Plan (resumable across sessions)

Goal: produce an exam-grade study booklet PDF at
`/home/bhanu/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf`
with **zero** math/Unicode/spacing defects. End user: Bhanu, preparing for
MSc Mathematics + CSIR NET.

## Build pipeline (do not break)

Entry point: `python3 build_book.py` (in this directory).
Order: `*.md` → `mathify.preprocess_markdown` → `strip_decorations` →
`md2tex.md_to_latex` → concat with `preamble_v2.tex` → 3× xelatex →
copy `build/book.pdf` to `~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf`.
Per-chapter debug artifacts land in `build/<stem>.pre.md` and `build/<stem>.tex`.

## Defect catalog (from PDF dump `/tmp/booklet_dump.txt`)

### D1 — Prose eaten by math run (CRITICAL)
**Symptom**: Phrases like `(different inputs → different outputs)` get pulled
inside `$...$`, spaces collapse, output renders as `(𝑑𝑖𝑓𝑓𝑒𝑟𝑒𝑛𝑡𝑖𝑛𝑝𝑢𝑡𝑠 → 𝑑𝑖𝑓𝑓𝑒𝑟𝑒𝑛𝑡𝑜𝑢𝑡𝑝𝑢𝑡𝑠)`.
**Root cause**: `mathify.expand_run` accepts ANY word (including 9-letter prose)
when inside an unbalanced `(`/`[`/`{` scope. Original purpose was to handle
`\int f dx)` differentials; it's too aggressive.
**Fix**: limit "accept any word inside paren scope" to words of length ≤ 2.
**Examples**: lines 480, 499, 518, 565, 568, 594, 1287, 1288, 1293, 1299, 1321, 1324, 1473.

### D2 — Bare `^X`, `_X` not wrapped in `$...$`
**Symptom**: `Q^T Q = I`, `I_z = I_x + I_y`, `f_x(0,0)`, `proj_W(v)` render
as literal text — no superscript / subscript.
**Root cause**: `mathify._wrap_literal_subsuper` only matches `_{...}` /
`^{...}` (with braces) — not bare `^T` / `_x`.
**Fix**: extend the regex to match `[A-Za-z0-9)\]][_^][A-Za-z0-9]` (single-char
sub/sup) in addition to braced form.
**Examples**: lines 1417, 1436, 1473, 1676, 2405, 4686-4709, 4892, 5135, 5199, 5228.

### D3 — `Q⁻¹` superscript-minus-1 sometimes rendered loose
**Symptom**: `MR²/4` becomes `MR2 /4` (superscript 2 detached). Need verify.
**Likely fix**: ensure `²`/`⁻¹` near alphabetic base attaches via fold_supersub
inside the wrapped run.

### D4 — Set-difference `X\A` not in math mode
**Symptom**: `Int(X\A)` shows literal backslash-A.
**Likely fix**: same wrapping fix as D2 — once `X\A` is inside `$...$`,
`normalise_inside_math` already converts `\` to `\setminus`.

### D5 — Quick Refresher matrix art rendering (per user checklist)
**Status**: not yet investigated. Need to find the matrix in
`07_CSIR_NET_Quick_Revision.md` and check `build/07*.tex` output.

### D6 — Integral expansion (per user checklist)
**Resolved by**: the D1 fix. Differentials `dx`, `ds`, `dn` (≤2 letters) are
still admitted; English words are not.

## Workflow

For each fix:
1. Edit `mathify.py` (or source `.md` if defect is content-level, not pipeline-level).
2. `python3 build_book.py` — rebuild end-to-end.
3. `pdftotext -layout ~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf /tmp/booklet_dump.txt`.
4. `grep` for the defect class — confirm it's gone, no regressions.

## Progress log

- [x] Investigate pipeline, identify entry point (`build_book.py`).
- [x] Catalog defects from PDF dump.
- [x] D1 — prose-eaten math expansion: word-length cap (≤2) inside paren scope.
- [x] D2 — bare `^X`/`_X` wrapping: extend `_wrap_literal_subsuper` regex with `[_^][A-Za-z0-9]+`; multi-char alpha tail wrapped in `\mathrm{...}` for upright.
- [x] D3 — `²/⁻¹` already worked via `fold_supersub`; D2 was the visible part.
- [x] D4 — `X\A` set-difference: extended regex with Unicode capitals (ℝ ℂ ℚ …) and `(`,`[` after-class.
- [x] D5 — Quick Refresher rendering: was actually D1+D2 problems; resolved.
- [x] Set-builder auto-wrap (`{f ∈ V* : ...}`) via new `_wrap_set_builder` pass; prose like "for all" wrapped in `\text{ ... }` with surrounding spaces.
- [x] Filename guard: don't wrap `01_Advanced_LA.md` patterns.
- [x] Operator rewrites: `rank/diag/span/iff/proj/...` → `\rank/\diag/\Span/\iff/\proj` via `MATH_OP_REWRITES` and preamble `\DeclareMathOperator`.
- [x] Critical fix in `expand_run`: stop crossing `(`,`[`,`{` going LEFT and RIGHT; parens stay as body-text glyphs, math runs only cover the math content. Stops `(α is differentiable)` and similar from getting balance_parens-killed.
- [x] Validate: rebuilt PDF dump has zero of every defect signature.
- [x] Final build at `/home/bhanu/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf` (124 pages, 553 KB).

## Final metrics

```
Pages:                         124
Italic prose runs:             0
Missing-glyph (replacement) :  0
Raw \name leaks:               0
Set-difference leaks:          0
Orphan _X (non-filename):      0
```

## Files changed in this pass

- `mathify.py` — biggest changes: D1 word cap, `_wrap_literal_subsuper`
  rewrite (multi-letter base, bare sub/sup, filename guard, mathrm
  wrapping), new `_wrap_set_builder` and `_wrap_set_difference`
  preprocessors, `MATH_OP_REWRITES` table, paren-crossing block in
  `expand_run`.
- `preamble_v2.tex` — added `\proj`, `\Var`, `\Cov` math operators.
- `07_CSIR_NET_Quick_Revision.md` — fixed `fᵧᵧ` (Unicode subscript
  gamma — author meant `y`) → `f_yy`.

## How to resume

1. Read this file. Read `mathify.py`.
2. Run `pdftotext -layout ~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf /tmp/dump.txt`.
3. Run the QC greps from "Final metrics" — all should be zero.
4. If a new defect appears: catalog it, decide whether it's a pipeline
   bug (fix in `mathify.py`) or content (fix in the source `.md`),
   rebuild with `python3 build_book.py`, re-grep.

## Known stylistic minor (non-defect) items

- `√2` may show on a separate line from `2` in pdftotext layout
  output; this is a pdftotext quirk, the visual PDF is correct.
- Markdown body-text occurrences of `→`, `∈`, etc. (outside any math
  span) render via XeLaTeX's body font fallback. They look fine in
  the PDF. If a future font change drops these glyphs, wrap the
  surrounding text in `$...$` in the source.

## How to resume in a fresh session

1. Read this file.
2. Read `mathify.py` (the heart of the conversion).
3. Run `pdftotext -layout ~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf /tmp/booklet_dump.txt`.
4. Re-run the defect greps from the catalog above; the ones that still hit are the open work.
5. Continue from the first unchecked item in "Progress log".
