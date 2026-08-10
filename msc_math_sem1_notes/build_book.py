#!/usr/bin/env python3
"""build_book.py — orchestrator: preprocess markdown, custom convert to
LaTeX, combine with preamble, run xelatex, and copy the PDF to Desktop.
"""
from __future__ import annotations
import re
import shutil
import subprocess
import sys
from pathlib import Path

import mathify
import md2tex

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / 'build'
BUILD.mkdir(exist_ok=True)

DESKTOP_PDF = Path.home() / 'Desktop' / 'MSc_Mathematics_Sem1_Complete_Booklet.pdf'
PREAMBLE = ROOT / 'preamble_v2.tex'
TEX_OUT = BUILD / 'book.tex'

CHAPTERS = [
    ('00A_Prerequisites.md',
     'Prerequisites — Class~12 \\& Foundations Refresher'),
    ('00_MASTER_INDEX.md',
     'Study Roadmap \\& CSIR NET Guide'),
    ('09_Hit_Rate_Analysis.md',
     'Topic Hit-Rate Priority Analysis'),
    ('01_Advanced_Linear_Algebra.md',
     'Advanced Linear Algebra'),
    ('01B_Linear_Algebra_Deep_Proofs.md',
     'Linear Algebra — Proofs \\& Worked Problems'),
    ('02_Mathematical_Analysis.md',
     'Mathematical Analysis'),
    ('02B_Analysis_Deep_Proofs.md',
     'Mathematical Analysis — Proofs \\& Worked Problems'),
    ('03_Topology.md',
     'Topology'),
    ('03B_Topology_Deep_Proofs.md',
     'Topology — Proofs \\& Counter-examples'),
    ('04_Advanced_Complex_Analysis.md',
     'Advanced Complex Analysis'),
    ('04B_Complex_Analysis_Deep_Proofs.md',
     'Complex Analysis — Proofs \\& Worked Problems'),
    ('05_Advanced_Differential_Equations.md',
     'Advanced Differential Equations'),
    ('05B_ODE_Deep_Proofs.md',
     'Differential Equations — Proofs \\& Worked Problems'),
    ('06_Dynamics_of_Rigid_Body.md',
     'Dynamics of a Rigid Body'),
    ('06B_Dynamics_Deep_Proofs.md',
     'Dynamics — Proofs \\& Worked Problems'),
    ('07_CSIR_NET_Quick_Revision.md',
     'CSIR NET Quick Revision'),
    ('08_PYQ_Compilation.md',
     'Previous-Year Questions — Solved'),
    ('11_Gap_Filler_All_Missing_Proofs.md',
     'Additional Proofs \\& Gap Filler'),
]


# ---------------------------------------------------------------------
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001FA70-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U0001F900-\U0001F9FF"
    "⭐✨⬆⬇➤➡✓✗"
    "]+", flags=re.UNICODE)
BOX_RE = re.compile('[─-╿]')


RATING_REPLACE = {
    # Plain-text replacements — safe through escaping.
    '★': '*', '☆': 'o',
    '⚡': '!',
    '🐢': '(slow)',
    '🎯': '', '📐': '', '📊': '', '🧠': '', '📋': '',
    '🌀': '', '📝': '', '💡': '', '📖': '', '🗺': '',
    '✅': 'OK', '✓': '*OK*',
    '❌': 'X', '✗': 'X',
    '⏱': '', '🔥': '', '⭐': '*', '✨': '',
    '📚': '', '🎓': '', '🚀': '', '🏆': '',
}


def replace_ratings(md: str) -> str:
    for k, v in RATING_REPLACE.items():
        md = md.replace(k, v)
    return md


def strip_decorations(md: str) -> str:
    md = replace_ratings(md)
    out = []
    for line in md.splitlines():
        line = BOX_RE.sub('', line)
        line = EMOJI_RE.sub('', line)
        out.append(line.rstrip())
    return '\n'.join(out)


def convert_chapter(filename: str, title: str) -> str:
    src = ROOT / filename
    md = src.read_text(encoding='utf-8')
    # Drop the FIRST H1 -- we'll add our own \chapter heading
    md = re.sub(r'^# .+$', '', md, count=1, flags=re.MULTILINE)
    # Mind-map headings always have an ASCII-art body that gets dropped
    # because we can't render box-drawing chars in a serif body font.
    # Drop the empty heading too.
    md = re.sub(r'^##+\s.*Mind Map.*$', '', md, flags=re.MULTILINE)
    # NOTE: strip_decorations (emoji + box-drawing) is applied AFTER
    # mathify so mathify can still detect ASCII-art boxes via the
    # original box-drawing characters and discard them entirely.
    # Demote remaining headings by one level so the original `# UNIT 1:`
    # becomes a section under our \chapter, `## Foo` becomes a subsection,
    # etc. Without this every UNIT heading would create a new chapter.
    def _demote(m):
        return '#' + m.group(0)
    # Process each line: prepend a `#` to any line that starts with `#`.
    # H1..H5 -> H2..H6 (H6 is max in markdown).
    new_lines = []
    for line in md.splitlines():
        m_h = re.match(r'^(#{1,5})(\s+)(.+)$', line)
        if m_h:
            level_marks, ws, title_text = m_h.groups()
            # Strip a leading "1.", "2.3.", "U-1:" etc. from the title so we
            # don't double-number when LaTeX adds 1.1, 1.2 itself.
            title_text = re.sub(r'^\d+(?:\.\d+)*\.\s*', '', title_text)
            line = '#' + level_marks + ws + title_text
        new_lines.append(line)
    md = '\n'.join(new_lines)
    # Replace rating symbols (✓, ★, ⚡, ✗, etc.) BEFORE mathify so they
    # don't block math-run expansion.  Decorative emoji + box-drawing
    # are stripped AFTER mathify so it can still detect ASCII art.
    md = replace_ratings(md)
    md = mathify.preprocess_markdown(md)
    md = strip_decorations(md)

    # Save preprocessed markdown for debugging
    debug = BUILD / (Path(filename).stem + '.pre.md')
    debug.write_text(md, encoding='utf-8')

    body_tex = md2tex.md_to_latex(md)
    # Save tex fragment for debugging
    (BUILD / (Path(filename).stem + '.tex')).write_text(body_tex,
                                                        encoding='utf-8')

    return f'\n\\chapter{{{title}}}\n\n{body_tex}\n'


def build():
    print('=' * 72)
    print('  Building MSc Mathematics Booklet')
    print('=' * 72)
    body = ''
    for fn, title in CHAPTERS:
        path = ROOT / fn
        if not path.exists():
            print(f'  SKIP missing: {fn}')
            continue
        print(f'  • {fn}')
        body += convert_chapter(fn, title)
    preamble = PREAMBLE.read_text(encoding='utf-8')
    full = preamble + '\n' + body + '\n\\end{document}\n'
    TEX_OUT.write_text(full, encoding='utf-8')
    print(f'\n  combined .tex: {TEX_OUT} ({len(full)} chars)')
    for run in (1, 2, 3):
        print(f'  xelatex pass {run} ...')
        proc = subprocess.run(
            ['xelatex', '-interaction=nonstopmode',
             '-halt-on-error', str(TEX_OUT.name)],
            cwd=str(BUILD), capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            print('  ERROR — last 60 lines of stdout:')
            print('\n'.join(proc.stdout.splitlines()[-60:]))
            log = BUILD / 'book.log'
            if log.exists():
                last = '\n'.join(log.read_text(errors='ignore')
                                 .splitlines()[-100:])
                print('  ===== last 100 lines of book.log =====')
                print(last)
            return False
    pdf = BUILD / 'book.pdf'
    if pdf.exists():
        shutil.copy(pdf, DESKTOP_PDF)
        size = pdf.stat().st_size
        try:
            info = subprocess.run(['pdfinfo', str(pdf)],
                                  capture_output=True, text=True)
            for line in info.stdout.splitlines():
                if line.startswith('Pages'):
                    print(f'  {line}')
        except FileNotFoundError:
            pass
        print(f'\n  ✓ DONE  {DESKTOP_PDF}  ({size/1024:.1f} KB)')
        return True
    print('  ✗ no PDF was produced')
    return False


if __name__ == '__main__':
    sys.exit(0 if build() else 1)
