#!/usr/bin/env python3
r"""md2tex.py — Custom Markdown -> LaTeX converter for the MSc booklet.

Skipping pandoc: it sometimes mangles raw-tex blocks and fights tcolorbox
nesting. A small purpose-built converter gives us perfect control over
how each markdown construct maps into our preamble's environments.

Supported Markdown features (subset, but everything we use):
- # / ## / ### / #### / ##### headings
- bullet lists (-, *, +)
- numbered lists (1. ...)
- blockquotes (> ...) with detection of "Quick Refresher" -> prereqbox
- fenced code blocks (``` ... ```) -> verbatim or matrix
- pipe tables (| col | col |)
- bold (**...**), italic (*...*), inline code (`...`)
- thematic breaks (---) -> \medskip rule
- math: inline ($...$) and display ($$...$$) -- pass through unchanged
- raw LaTeX in fenced ```{=latex} blocks
- callout headings such as "### Worked Example" -> examplebox, etc.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------
#   LaTeX-safe escaping (text mode only).
# ---------------------------------------------------------------------
SPECIALS = {
    '\\': r'\textbackslash{}',
    '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
    '_': r'\_', '{': r'\{', '}': r'\}',
    '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
}


def latex_escape_text(s: str) -> str:
    """Escape characters that have a special meaning in LaTeX text mode.

    The input is *prose* (math has already been wrapped in $...$ by the
    preprocessor and is excluded from escaping here)."""
    # Walk char by char, but skip math segments
    out, i, n = [], 0, len(s)
    while i < n:
        ch = s[i]
        if ch == '$':
            # find matching $ (single $ -- not displaymath here)
            if i + 1 < n and s[i + 1] == '$':
                j = s.find('$$', i + 2)
                if j == -1:
                    j = n - 1
                # leave whole '$$...$$' as raw math
                out.append(s[i:j + 2])
                i = j + 2
            else:
                j = s.find('$', i + 1)
                if j == -1:
                    j = n - 1
                out.append(s[i:j + 1])
                i = j + 1
        else:
            if ch in SPECIALS:
                out.append(SPECIALS[ch])
            else:
                out.append(ch)
            i += 1
    return ''.join(out)


# ---------------------------------------------------------------------
#   Inline formatting: bold, italic, code  -- AFTER math has been wrapped.
# ---------------------------------------------------------------------
def apply_inline(s: str) -> str:
    """Convert markdown inline syntax to LaTeX, preserving math.

    Order:
      1. stash $...$ math and `...` code into placeholders
      2. detect bold/italic on the placeholder-laden text
      3. escape remaining text
      4. restore math (verbatim) and code (in \texttt with escaping)
    """
    saved_math: list[str] = []
    saved_code: list[str] = []

    def _stash(s: str) -> str:
        out = []
        i, n = 0, len(s)
        while i < n:
            if s[i] == '$':
                if i + 1 < n and s[i + 1] == '$':
                    j = s.find('$$', i + 2)
                    if j == -1:
                        j = n - 2
                    saved_math.append(s[i:j + 2])
                    out.append(f'\x00M{len(saved_math)-1}\x00')
                    i = j + 2
                else:
                    j = s.find('$', i + 1)
                    if j == -1:
                        j = n - 1
                    saved_math.append(s[i:j + 1])
                    out.append(f'\x00M{len(saved_math)-1}\x00')
                    i = j + 1
            elif s[i] == '`':
                j = s.find('`', i + 1)
                if j == -1:
                    j = n - 1
                saved_code.append(s[i + 1:j])
                out.append(f'\x00C{len(saved_code)-1}\x00')
                i = j + 1
            else:
                out.append(s[i])
                i += 1
        return ''.join(out)

    t = _stash(s)
    # Markdown links: `[text](url)` -> just the text (we don't render
    # external URLs in a print-only booklet).
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', t)
    # Escape FIRST so that `\` produced by bold/italic isn't escaped later.
    out = []
    i, n = 0, len(t)
    while i < n:
        if t[i] == '\x00':
            j = t.find('\x00', i + 1)
            if j == -1:
                out.append(t[i:])
                break
            out.append(t[i:j + 1])
            i = j + 1
        else:
            j = t.find('\x00', i)
            if j == -1:
                j = n
            for ch in t[i:j]:
                out.append(SPECIALS.get(ch, ch))
            i = j
    t = ''.join(out)
    # Bold/italic on already-escaped text: `*` is not in SPECIALS so survives.
    t = re.sub(r'\*\*\*(.+?)\*\*\*',
               lambda m: r'\textbf{\textit{' + m.group(1) + r'}}', t)
    t = re.sub(r'\*\*(.+?)\*\*',
               lambda m: r'\textbf{' + m.group(1) + r'}', t)
    t = re.sub(r'(?<![*\w])\*([^*\n]+?)\*(?!\*)',
               lambda m: r'\textit{' + m.group(1) + r'}', t)
    t = t.replace('**', '')
    # Restore math
    t = re.sub(r'\x00M(\d+)\x00',
               lambda m: saved_math[int(m.group(1))], t)
    # Restore code
    def _restore_code(m):
        body = saved_code[int(m.group(1))]
        esc = body.replace('\\', r'\textbackslash{}')
        esc = esc.replace('{', r'\{').replace('}', r'\}')
        esc = esc.replace('_', r'\_').replace('#', r'\#')
        esc = esc.replace('&', r'\&').replace('%', r'\%')
        return r'\texttt{' + esc + '}'
    t = re.sub(r'\x00C(\d+)\x00', _restore_code, t)
    return t


# ---------------------------------------------------------------------
#   Heading / callout detection.
# ---------------------------------------------------------------------
CALLOUT_PATTERNS = [
    # heading regex -> (env, default-title)
    (re.compile(r'^CSIR NET Critical Theorem[:\s]*(.+)?$', re.I),
        'theorembox', 'CSIR NET Critical Result'),
    (re.compile(r'^Memory Aid[:\s]*(.*)$', re.I),
        'mnemonicbox', 'Memory Aid'),
    (re.compile(r'^(Mnemonic)[:\s]*(.*)$', re.I),
        'mnemonicbox', 'Mnemonic'),
    (re.compile(r'^CSIR NET (?:FAVORITE|Favorite)[!]?[:\s]*(.*)$', re.I),
        'exambox', 'CSIR NET Favourite'),
    (re.compile(r'^CSIR NET HIGH PRIORITY[!]?[:\s]*(.*)$', re.I),
        'exambox', 'CSIR NET High Priority'),
    (re.compile(r'^CSIR NET Application[:\s]*(.*)$', re.I),
        'exambox', 'CSIR NET Application'),
    (re.compile(r'^CSIR NET Trick[:\s]*(.*)$', re.I),
        'exambox', 'CSIR NET Exam Trick'),
    (re.compile(r'^CSIR NET Pattern[:\s]*(.*)$', re.I),
        'exambox', 'CSIR NET Pattern'),
    (re.compile(r'^CSIR NET[:\s]+(.*)$', re.I),
        'exambox', 'CSIR NET Tip'),
    (re.compile(r'^Worked Example\s*\(?CSIR NET Style\)?\s*[:\s]*(.*)$', re.I),
        'examplebox', 'Worked Example (CSIR NET Style)'),
    (re.compile(r'^Worked Example[:\s]*(.*)$', re.I),
        'examplebox', 'Worked Example'),
    (re.compile(r'^Example\s*\d*[:\s]*(.*)$', re.I),
        'examplebox', 'Example'),
    (re.compile(r'^Common Pitfall[:\s]*(.*)$', re.I),
        'pitfallbox', 'Common Pitfall'),
    (re.compile(r'^Pitfall[:\s]*(.*)$', re.I),
        'pitfallbox', 'Common Pitfall'),
    (re.compile(r'^Plain English[:\s]*(.*)$', re.I),
        'intuitbox', 'Plain English'),
    (re.compile(r'^Intuition[:\s]*(.*)$', re.I),
        'intuitbox', 'Intuition'),
    (re.compile(r'^Definition[:\s]*(.*)$', re.I),
        'definitionbox', 'Definition'),
    (re.compile(r'^Theorem[:\s]*(.*)$', re.I),
        'theorembox', 'Theorem'),
    (re.compile(r'^Lemma[:\s]*(.*)$', re.I),
        'lemmabox', 'Lemma'),
    (re.compile(r'^Corollary[:\s]*(.*)$', re.I),
        'corollarybox', 'Corollary'),
    (re.compile(r'^Proof[:\s]*(.*)$', re.I),
        'proofbox', 'Proof'),
]


def callout_for(heading_text: str):
    """Return (env, suffix) if this heading is a callout, else None."""
    h = heading_text.strip()
    for rx, env, default_title in CALLOUT_PATTERNS:
        m = rx.match(h)
        if m:
            extra = ' '.join(g for g in m.groups() if g)
            extra = extra.strip(' :;-')
            return env, default_title, extra
    return None


# ---------------------------------------------------------------------
#   Per-line / per-block conversion.
# ---------------------------------------------------------------------
HEADER_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*#*\s*$')
HRULE_RE = re.compile(r'^-{3,}\s*$|^_{3,}\s*$|^\*{3,}\s*$')
BULLET_RE = re.compile(r'^(\s*)([-*+])\s+(.*)$')
NUMBER_RE = re.compile(r'^(\s*)(\d+)\.\s+(.*)$')
QUOTE_RE = re.compile(r'^>\s?(.*)$')
TABLE_ROW_RE = re.compile(r'^\s*\|.*\|\s*$')
TABLE_SEP_RE = re.compile(r'^\s*\|[-:|\s]+\|\s*$')
RAW_TEX_FENCE = re.compile(r'^```\{=latex\}\s*$')
CODE_FENCE = re.compile(r'^```\s*([A-Za-z0-9_+-]*)?\s*$')


def is_blank(s: str) -> bool:
    return not s.strip()


def render_paragraph(lines: list[str]) -> str:
    """Render a paragraph (already inline-processed)."""
    text = ' '.join(line.strip() for line in lines if line.strip())
    return apply_inline(text)


# ---------------------------------------------------------------------
#   Table rendering.
# ---------------------------------------------------------------------
def _split_row_pipes(row: str) -> list[str]:
    """Split a markdown table row at `|` separators, but ignore pipes that
    occur inside `$...$` math (e.g. absolute-value bars), and treat `\\|`
    as a literal pipe (markdown table escape convention)."""
    s = row.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|') and (len(s) < 2 or s[-2] != '\\'):
        s = s[:-1]
    cells = []
    cur = []
    in_math = False
    in_dmath = False
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        # Handle escaped pipe: \| → literal | (markdown table convention)
        if ch == '\\' and i + 1 < n and s[i + 1] == '|':
            cur.append('|'); i += 2; continue
        if ch == '$':
            if i + 1 < n and s[i + 1] == '$':
                in_dmath = not in_dmath
                cur.append('$$'); i += 2; continue
            in_math = not in_math
            cur.append('$'); i += 1; continue
        if ch == '|' and not in_math and not in_dmath:
            cells.append(''.join(cur))
            cur = []
            i += 1
            continue
        cur.append(ch); i += 1
    cells.append(''.join(cur))
    return cells


def render_table(rows: list[str]) -> str:
    # Drop separator rows
    data = [r for r in rows if not TABLE_SEP_RE.match(r)]
    if not data:
        return ''
    # Split each row into cells (math-aware so that |x| isn't a column split)
    table = []
    raw_table = []  # pre-inline-conversion cells, used for width estimation
    for row in data:
        raw_cells = [c.strip() for c in _split_row_pipes(row)]
        raw_table.append(raw_cells)
        cells = [apply_inline(c) for c in raw_cells]
        table.append(cells)
    if not table:
        return ''
    ncol = max(len(r) for r in table)
    table = [r + [''] * (ncol - len(r)) for r in table]
    raw_table = [r + [''] * (ncol - len(r)) for r in raw_table]

    # Adaptive column-1 width based on actual data content (skip header row).
    # Strip markdown bold/italic for accurate length measurement.
    def _content_len(s: str) -> int:
        s = re.sub(r'\*\*([^*]+)\*\*', r'\1', s)
        s = re.sub(r'\*([^*]+)\*', r'\1', s)
        s = re.sub(r'`([^`]+)`', r'\1', s)
        return len(s.strip())
    if len(raw_table) > 1:
        col1_data = [_content_len(r[0]) for r in raw_table[1:] if r[0].strip()]
        col1_max = max(col1_data) if col1_data else 0
    else:
        col1_max = _content_len(raw_table[0][0]) if raw_table[0] else 0
    if col1_max <= 3:
        col1_w = 0.05    # narrow: index, #, single digits
    elif col1_max <= 10:
        col1_w = 0.15    # short: brief labels like "Picard", "Q3", etc.
    else:
        col1_w = 0.30    # original behavior for substantive col-1 content

    other_w = (0.95 - col1_w) / max(1, ncol - 1)
    col_spec = ('@{}>{\\raggedright\\arraybackslash}p{%.3f\\linewidth}' % col1_w)
    col_spec += ('>{\\raggedright\\arraybackslash}p{%.3f\\linewidth}' % other_w) * (ncol - 1) + '@{}'
    out = ['\\begin{center}\\small',
           '\\begin{tabular}{' + col_spec + '}',
           '\\toprule']
    def _cell(c: str) -> str:
        # Brace-wrap so a leading `[` doesn't get parsed as the optional
        # arg of `\tabularnewline` / `\\`.
        return '{' + c + '}'
    if len(table) >= 1:
        head = ' & '.join('\\textbf' + _cell(c) for c in table[0])
        out.append(head + ' \\tabularnewline')
        out.append('\\midrule')
    for row in table[1:]:
        out.append(' & '.join(_cell(c) for c in row) + ' \\tabularnewline')
    out.append('\\bottomrule\\end{tabular}\\end{center}')
    return '\n'.join(out)


# ---------------------------------------------------------------------
#   Convert blockquote (> ...) -> prereqbox or quote.
# ---------------------------------------------------------------------
def render_blockquote(lines: list[str]) -> str:
    body = []
    for ln in lines:
        m = QUOTE_RE.match(ln)
        body.append(m.group(1) if m else ln)
    text = '\n'.join(body)
    # Detect "Quick Refresher" markers
    is_prereq = bool(re.search(
        r'(Quick Refresher|Prerequisites?\s*[—–\-]+\s*What You Need|Refresher Before Starting)',
        text, re.I))
    is_csir = bool(re.search(r'CSIR NET (?:Priority|FAVORITE|Favorite)', text, re.I))
    # Render the inner text as paragraphs
    inner = render_block(body)
    if is_prereq:
        return '\\begin{prereqbox}\n' + inner + '\n\\end{prereqbox}'
    if is_csir:
        return '\\begin{exambox}\n' + inner + '\n\\end{exambox}'
    return '\\begin{intuitbox}\n' + inner + '\n\\end{intuitbox}'


# ---------------------------------------------------------------------
#   Block-level driver.
# ---------------------------------------------------------------------
def render_block(lines: list[str]) -> str:
    """Convert a list of markdown lines into a LaTeX fragment."""
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if is_blank(line):
            out.append('')
            i += 1
            continue

        # Raw LaTeX fence: ```{=latex}
        if RAW_TEX_FENCE.match(line):
            j = i + 1
            buf = []
            while j < n and not lines[j].strip().startswith('```'):
                buf.append(lines[j])
                j += 1
            out.append('\n'.join(buf))
            i = j + 1
            continue

        # Generic code fence
        m = CODE_FENCE.match(line)
        if m:
            j = i + 1
            buf = []
            while j < n and not CODE_FENCE.match(lines[j]):
                buf.append(lines[j])
                j += 1
            # If the block contains math we already converted, treat as math
            joined = '\n'.join(buf)
            if '$' in joined or '\\begin{pmatrix}' in joined:
                # already display math from preprocessor
                out.append(joined)
            else:
                out.append('\\begin{verbatim}')
                out.extend(buf)
                out.append('\\end{verbatim}')
            i = j + 1
            continue

        # Headings
        m = HEADER_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            # Detect callout headings on level >= 3
            if level >= 3:
                co = callout_for(title)
                if co:
                    env, default_title, extra = co
                    # Collect body until next heading at same-or-higher level,
                    # blank line ending the section, hr, or end
                    j = i + 1
                    body_lines = []
                    while j < n:
                        ln = lines[j]
                        m2 = HEADER_RE.match(ln)
                        if m2 and len(m2.group(1)) <= level:
                            break
                        if HRULE_RE.match(ln):
                            break
                        body_lines.append(ln)
                        j += 1
                    while body_lines and not body_lines[-1].strip():
                        body_lines.pop()
                    body_tex = render_block(body_lines)
                    title_arg = ''
                    # If the body is empty, fall back to using `extra`
                    # (the bit after `:` in the heading) as the body.
                    if not body_tex.strip() and extra:
                        body_tex = apply_inline(extra)
                        extra = ''
                    if extra:
                        title_arg = '[--- ' + apply_inline(extra) + ']'
                    out.append('\\begin{' + env + '}' + title_arg)
                    out.append(body_tex)
                    out.append('\\end{' + env + '}')
                    i = j
                    continue
            # Regular heading
            cmd = {1: 'chapter', 2: 'section', 3: 'subsection',
                   4: 'subsubsection', 5: 'paragraph',
                   6: 'subparagraph'}[level]
            tex_title = apply_inline(title)
            # If the heading carries math, wrap in \texorpdfstring so
            # hyperref's PDF bookmarks don't choke on $.
            if '$' in tex_title:
                plain = re.sub(r'\$[^$]*\$', '', title)
                plain = re.sub(r'\*\*?', '', plain)
                # Escape PDF-string-unsafe chars in the plain version
                plain = plain.replace('\\', '\\textbackslash{}')
                plain = plain.replace('%', '\\%').replace('#', '\\#')
                plain = plain.replace('&', '\\&').replace('_', '\\_')
                plain = plain.strip()
                tex_title = '\\texorpdfstring{' + tex_title + '}{' + plain + '}'
            out.append('\\' + cmd + '{' + tex_title + '}')
            i += 1
            continue

        # Horizontal rule
        if HRULE_RE.match(line):
            out.append('\\medskip\\hrule\\medskip')
            i += 1
            continue

        # Blockquote
        if QUOTE_RE.match(line):
            j = i
            buf = []
            while j < n and (QUOTE_RE.match(lines[j]) or
                             (j > i and not lines[j].strip())):
                buf.append(lines[j])
                j += 1
            # trim trailing blanks
            while buf and not buf[-1].strip():
                buf.pop()
            out.append(render_blockquote(buf))
            i = j
            continue

        # Table
        if TABLE_ROW_RE.match(line):
            j = i
            buf = []
            while j < n and TABLE_ROW_RE.match(lines[j]):
                buf.append(lines[j])
                j += 1
            out.append(render_table(buf))
            i = j
            continue

        # Bullet / numbered list
        if BULLET_RE.match(line) or NUMBER_RE.match(line):
            ordered = bool(NUMBER_RE.match(line))
            j = i
            buf_items = []
            cur_item = []
            while j < n:
                ln = lines[j]
                if not ln.strip():
                    cur_item.append('')
                    j += 1
                    # End list on double blank
                    if j < n and not lines[j].strip():
                        break
                    continue
                m_bul = BULLET_RE.match(ln)
                m_num = NUMBER_RE.match(ln)
                if m_bul or m_num:
                    if cur_item:
                        buf_items.append(cur_item)
                        cur_item = []
                    rest = (m_bul or m_num).group(3)
                    cur_item = [rest]
                    j += 1
                    continue
                # Continuation line
                if ln.startswith(' ') or ln.startswith('\t'):
                    cur_item.append(ln.strip())
                    j += 1
                    continue
                break
            if cur_item:
                buf_items.append(cur_item)
            env = 'enumerate' if ordered else 'itemize'
            out.append('\\begin{' + env + '}')
            for item in buf_items:
                # Strip trailing blanks
                while item and not item[-1].strip():
                    item.pop()
                joined = ' '.join(s.strip() for s in item if s)
                out.append('  \\item ' + apply_inline(joined))
            out.append('\\end{' + env + '}')
            i = j
            continue

        # Paragraph: collect until blank or block-marker
        j = i
        buf = []
        while j < n and lines[j].strip() \
                and not BULLET_RE.match(lines[j]) \
                and not NUMBER_RE.match(lines[j]) \
                and not HEADER_RE.match(lines[j]) \
                and not HRULE_RE.match(lines[j]) \
                and not QUOTE_RE.match(lines[j]) \
                and not TABLE_ROW_RE.match(lines[j]) \
                and not CODE_FENCE.match(lines[j]) \
                and not RAW_TEX_FENCE.match(lines[j]):
            buf.append(lines[j])
            j += 1
        out.append(render_paragraph(buf))
        i = j
    return '\n'.join(out)


def md_to_latex(md: str) -> str:
    return render_block(md.splitlines())


def main(argv):
    if len(argv) < 2:
        print('Usage: md2tex.py <input.md> [output.tex]')
        sys.exit(1)
    src = Path(argv[1])
    dst = Path(argv[2]) if len(argv) > 2 else src.with_suffix('.tex')
    dst.write_text(md_to_latex(src.read_text(encoding='utf-8')),
                   encoding='utf-8')
    print(f'wrote {dst}')


if __name__ == '__main__':
    main(sys.argv)
