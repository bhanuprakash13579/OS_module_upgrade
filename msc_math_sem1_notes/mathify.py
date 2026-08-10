#!/usr/bin/env python3
r"""mathify.py — robust Unicode-rich Markdown -> Pandoc-friendly Markdown.

Strategy
========
The original "wrap every Unicode char in its own ``$...$``" approach was
broken: it ate spaces, wrapped English words, and produced gibberish. We
take a *minimal* wrapping approach instead.

For every line:

1. Convert ASCII-art matrices (``| a b | / | c d |``) into proper
   LaTeX ``pmatrix`` display math.
2. Identify *small* math fragments and wrap them.

A *math fragment* is built by starting at the smallest mathy "atom" and
expanding LEFT/RIGHT through neighbours that are clearly math (operators,
sub/super, numerals, single-letter variables) but **never** through a
multi-character ASCII English word that is not a known math name.

3. Inside every wrapped fragment, replace Unicode chars with their LaTeX
   commands and fold ``₁₂``/``²ⁿ`` runs into ``_{12}``/``^{2n}``.
4. Translate ``√`` and bare ``\sqrt`` into ``\sqrt{...}``.
5. Translate well-known function names (``sin``, ``ker``, ``dim``...) so
   they render as ``\sin``, ``\ker``, ``\dim``.

This keeps prose untouched while producing valid LaTeX math.
"""
from __future__ import annotations
import re
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------
#   Character maps
# ---------------------------------------------------------------------
GREEK_LOWER = {
    'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta',
    'ε': r'\varepsilon', 'ϵ': r'\epsilon', 'ζ': r'\zeta', 'η': r'\eta',
    'θ': r'\theta', 'ϑ': r'\vartheta', 'ι': r'\iota', 'κ': r'\kappa',
    'λ': r'\lambda', 'μ': r'\mu', 'ν': r'\nu', 'ξ': r'\xi',
    'π': r'\pi', 'ϖ': r'\varpi', 'ρ': r'\rho', 'ϱ': r'\varrho',
    'σ': r'\sigma', 'ς': r'\varsigma', 'τ': r'\tau', 'υ': r'\upsilon',
    'φ': r'\varphi', 'ϕ': r'\phi', 'χ': r'\chi',
    'ψ': r'\psi', 'ω': r'\omega',
}
GREEK_UPPER = {
    'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda',
    'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Υ': r'\Upsilon',
    'Φ': r'\Phi', 'Ψ': r'\Psi', 'Ω': r'\Omega',
}

UNI_SYMBOL = {
    'ℝ': r'\mathbb{R}', 'ℂ': r'\mathbb{C}', 'ℚ': r'\mathbb{Q}',
    'ℤ': r'\mathbb{Z}', 'ℕ': r'\mathbb{N}', '𝔽': r'\mathbb{F}',
    'ℙ': r'\mathbb{P}', '𝕂': r'\mathbb{K}', '𝔼': r'\mathbb{E}',
    'ℓ': r'\ell', 'ℏ': r'\hbar', 'ℜ': r'\Re', 'ℑ': r'\Im',
    '∈': r'\in', '∉': r'\notin', '∋': r'\ni', '∌': r'\not\ni',
    '⊂': r'\subset', '⊆': r'\subseteq', '⊊': r'\subsetneq',
    '⊃': r'\supset', '⊇': r'\supseteq',
    '∪': r'\cup', '∩': r'\cap', '∅': r'\emptyset', '∖': r'\setminus',
    '∀': r'\forall', '∃': r'\exists', '∄': r'\nexists',
    '¬': r'\neg', '∧': r'\land', '∨': r'\lor',
    '→': r'\to', '←': r'\leftarrow', '↔': r'\leftrightarrow',
    '⇒': r'\Rightarrow', '⇐': r'\Leftarrow', '⇔': r'\Leftrightarrow',
    '⟹': r'\implies', '⟸': r'\impliedby', '⟺': r'\iff',
    '⟶': r'\longrightarrow', '⟵': r'\longleftarrow',
    '⟷': r'\longleftrightarrow',
    '↦': r'\mapsto', '⟶': r'\longrightarrow', '⟵': r'\longleftarrow',
    '↑': r'\uparrow', '↓': r'\downarrow',
    '≤': r'\le', '≥': r'\ge', '≠': r'\ne', '≈': r'\approx',
    '≡': r'\equiv', '≢': r'\not\equiv', '≅': r'\cong', '≃': r'\simeq',
    '∼': r'\sim', '≪': r'\ll', '≫': r'\gg', '≺': r'\prec', '≻': r'\succ',
    '∞': r'\infty', '∂': r'\partial', '∇': r'\nabla',
    '∫': r'\int', '∬': r'\iint', '∭': r'\iiint',
    '∮': r'\oint', '∯': r'\oiint',
    '∑': r'\sum', '∏': r'\prod', '∐': r'\coprod',
    '⨁': r'\bigoplus', '⨂': r'\bigotimes',
    '∝': r'\propto', '∴': r'\therefore', '∵': r'\because',
    '∎': r'\blacksquare', '□': r'\square',
    'Σ': r'\sum', 'Π': r'\prod',  # uppercase sigma/pi used as operators
    '×': r'\times', '·': r'\cdot', '⋅': r'\cdot', '∘': r'\circ',
    '−': '-',  # U+2212 minus
    '–': '-',  # en-dash sometimes used as minus
    '÷': r'\div',
    '⊕': r'\oplus', '⊗': r'\otimes', '⊙': r'\odot',
    '±': r'\pm', '∓': r'\mp', '√': r'\sqrt',
    '⊥': r'\perp', '∥': r'\parallel', '∠': r'\angle',
    '′': "'", '″': "''", '‴': "'''",
    '⌊': r'\lfloor', '⌋': r'\rfloor', '⌈': r'\lceil', '⌉': r'\rceil',
    '⟨': r'\langle', '⟩': r'\rangle',
    'ẍ': r'\ddot{x}', 'ÿ': r'\ddot{y}',
    'ẋ': r'\dot{x}', 'ẏ': r'\dot{y}', 'ż': r'\dot{z}',
    'ȧ': r'\dot{a}', 'ḃ': r'\dot{b}', 'ċ': r'\dot{c}', 'ḋ': r'\dot{d}',
    'ė': r'\dot{e}', 'ḟ': r'\dot{f}', 'ġ': r'\dot{g}', 'ḣ': r'\dot{h}',
    'ḳ': r'\dot{k}', 'ṁ': r'\dot{m}', 'ṅ': r'\dot{n}', 'ȯ': r'\dot{o}',
    'ṗ': r'\dot{p}', 'q̇': r'\dot{q}', 'ṙ': r'\dot{r}', 'ṡ': r'\dot{s}',
    'ṫ': r'\dot{t}', 'u̇': r'\dot{u}', 'v̇': r'\dot{v}', 'ẇ': r'\dot{w}',
    'Ȧ': r'\dot{A}', 'Ḃ': r'\dot{B}', 'Ċ': r'\dot{C}',
    'q̈': r'\ddot{q}', 'r̈': r'\ddot{r}', 'p̈': r'\ddot{p}',
    'θ̇': r'\dot{\theta}', 'θ̈': r'\ddot{\theta}',
    'φ̇': r'\dot{\varphi}', 'φ̈': r'\ddot{\varphi}',
    'ϕ̇': r'\dot{\phi}', 'ϕ̈': r'\ddot{\phi}',
    'ψ̇': r'\dot{\psi}', 'ψ̈': r'\ddot{\psi}',
    'ω̇': r'\dot{\omega}', 'ω̈': r'\ddot{\omega}',
    'ρ̇': r'\dot{\rho}',
    # Letters with macron — used for closure of a set, conjugates, means
    'Ā': r'\overline{A}', 'B̄': r'\overline{B}', 'C̄': r'\overline{C}',
    'Ē': r'\overline{E}', 'F̄': r'\overline{F}', 'Ḡ': r'\overline{G}',
    'Ī': r'\overline{I}', 'J̄': r'\overline{J}', 'K̄': r'\overline{K}',
    'L̄': r'\overline{L}', 'M̄': r'\overline{M}', 'N̄': r'\overline{N}',
    'Ō': r'\overline{O}', 'P̄': r'\overline{P}', 'Q̄': r'\overline{Q}',
    'R̄': r'\overline{R}', 'S̄': r'\overline{S}', 'T̄': r'\overline{T}',
    'Ū': r'\overline{U}', 'V̄': r'\overline{V}', 'W̄': r'\overline{W}',
    'X̄': r'\overline{X}', 'Ȳ': r'\overline{Y}', 'Z̄': r'\overline{Z}',
    'ā': r'\overline{a}', 'b̄': r'\overline{b}', 'c̄': r'\overline{c}',
    'ē': r'\overline{e}', 'ī': r'\overline{i}', 'm̄': r'\overline{m}',
    'n̄': r'\overline{n}', 'ō': r'\overline{o}', 'p̄': r'\overline{p}',
    'ū': r'\overline{u}', 'v̄': r'\overline{v}', 'x̄': r'\overline{x}',
    'ȳ': r'\overline{y}', 'z̄': r'\overline{z}',
    'z̄': r'\overline{z}',
    # Hat / tilde versions
    'â': r'\hat{a}', 'î': r'\hat{i}', 'ĵ': r'\hat{j}', 'k̂': r'\hat{k}',
    'r̂': r'\hat{r}', 'n̂': r'\hat{n}', 'û': r'\hat{u}',
}

SUPER = {'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5',
         '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
         '⁺': '+', '⁻': '-', '⁼': '=', '⁽': '(', '⁾': ')',
         'ⁿ': 'n', 'ⁱ': 'i', 'ᵃ': 'a', 'ᵇ': 'b', 'ᶜ': 'c',
         'ᵈ': 'd', 'ᵉ': 'e', 'ᶠ': 'f', 'ᵍ': 'g', 'ʰ': 'h',
         'ʲ': 'j', 'ᵏ': 'k', 'ˡ': 'l', 'ᵐ': 'm', 'ᵒ': 'o',
         'ᵖ': 'p', 'ʳ': 'r', 'ˢ': 's', 'ᵗ': 't', 'ᵘ': 'u',
         'ᵛ': 'v', 'ʷ': 'w', 'ˣ': 'x', 'ʸ': 'y', 'ᶻ': 'z',
         # Superscript uppercase letters (modifier-letter block)
         'ᴬ': 'A', 'ᴮ': 'B', 'ᴰ': 'D', 'ᴱ': 'E', 'ᴳ': 'G',
         'ᴴ': 'H', 'ᴵ': 'I', 'ᴶ': 'J', 'ᴷ': 'K', 'ᴸ': 'L',
         'ᴹ': 'M', 'ᴺ': 'N', 'ᴼ': 'O', 'ᴾ': 'P', 'ᴿ': 'R',
         'ᵀ': 'T', 'ᵁ': 'U', 'ⱽ': 'V', 'ᵂ': 'W'}
SUB = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5',
       '₆': '6', '₇': '7', '₈': '8', '₉': '9',
       '₊': '+', '₋': '-', '₌': '=', '₍': '(', '₎': ')',
       'ₐ': 'a', 'ₑ': 'e', 'ₕ': 'h', 'ᵢ': 'i', 'ⱼ': 'j',
       'ₖ': 'k', 'ₗ': 'l', 'ₘ': 'm', 'ₙ': 'n', 'ₒ': 'o',
       'ₚ': 'p', 'ᵣ': 'r', 'ₛ': 's', 'ₜ': 't', 'ᵤ': 'u',
       'ᵥ': 'v', 'ₓ': 'x',
       # Greek-looking subscripts (IPA modifier letters)
       # NOTE: 'ᵧ' (Unicode subscript gamma) is widely misused in our source
       # files as a stand-in for subscript y (which has no Unicode codepoint).
       # We map it to 'y' so 'Fᵧ', 'fᵧᵧ', 'vᵧ', 'Iᵧ' etc. render correctly as
       # F_y, f_yy, v_y, I_y. If you ever need a real gamma subscript, write
       # `_\gamma` explicitly in math mode.
       'ᵦ': r'\beta ', 'ᵧ': 'y', 'ᵨ': r'\rho ',
       'ᵩ': r'\varphi ', 'ᵪ': r'\chi '}

ALL_UNI_MATH = set(GREEK_LOWER) | set(GREEK_UPPER) | set(UNI_SYMBOL)
ALL_SUPER, ALL_SUB = set(SUPER), set(SUB)

UNI2TEX = {**GREEK_LOWER, **GREEK_UPPER, **UNI_SYMBOL}

# Function names that have a SAFE built-in LaTeX command \name.
# We auto-rewrite these inside math fragments. Conflicting / user-only
# names (span, im, rank, nullity, trace ...) stay as plain text — the
# preamble's \DeclareMathOperator handles them when wrapped manually.
MATH_FUNCS_TEX = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc',
                  'sinh', 'cosh', 'tanh', 'coth',
                  'log', 'ln', 'exp', 'lim', 'sup', 'inf',
                  'min', 'max', 'det', 'gcd', 'arg', 'ker', 'dim',
                  'deg']

# Math operators that map to \name commands declared in preamble_v2.tex.
# These get rewritten inside math mode so the operator renders upright
# (`rank` → `\rank` → "rank" upright) instead of italic letter-soup.
# `\Span` capitalised because TeX reserves \span; preamble exports \Span.
# `\bmod` is a builtin for the "mod" infix operator.
MATH_OP_REWRITES = {
    'rank': r'\rank', 'nullity': r'\nullity', 'null': r'\nul',
    'diag': r'\diag', 'span': r'\Span', 'Span': r'\Span',
    'Hom': r'\Hom', 'End': r'\End',
    'Tr': r'\Tr', 'tr': r'\Tr', 'sgn': r'\sgn',
    'proj': r'\proj', 'Var': r'\Var', 'Cov': r'\Cov',
    'iff': r'\iff', 'mod': r'\bmod',
}
# Identifiers that look like English words but are valid math names —
# we DON'T treat them as a "long English word" boundary.
MATH_IDENT = set(MATH_FUNCS_TEX) | {
    'iff', 'mod', 'div', 'st', 'tr', 'lcm',
    'Hom', 'End', 'Aut', 'GL', 'SL', 'O', 'SO', 'U', 'SU',
    'span', 'im', 'Im', 're', 'Re', 'rank', 'null', 'nullity',
    'trace', 'sgn', 'diag', 'rad', 'deg', 'gcd', 'lcm', 'codim',
}

# ---------------------------------------------------------------------
#   Subscript / superscript folding
# ---------------------------------------------------------------------
def fold_supersub(s: str) -> str:
    out, i, n = [], 0, len(s)
    while i < n:
        ch = s[i]
        if ch in ALL_SUPER:
            j = i; buf = ''
            while j < n and s[j] in ALL_SUPER:
                buf += SUPER[s[j]]; j += 1
            out.append('^{' + buf + '}')
            i = j
        elif ch in ALL_SUB:
            j = i; buf = ''
            while j < n and s[j] in ALL_SUB:
                buf += SUB[s[j]]; j += 1
            out.append('_{' + buf + '}')
            i = j
        else:
            out.append(ch); i += 1
    return ''.join(out)

# ---------------------------------------------------------------------
#   Replace Unicode math chars with LaTeX (used inside math fragments)
# ---------------------------------------------------------------------
def unimath_to_tex(s: str) -> str:
    # Pre-pass: replace any multi-char keys (combining-mark sequences
    # like `q̇` = q + U+0307) with their LaTeX equivalent.
    for k, v in UNI2TEX.items():
        if len(k) > 1 and k in s:
            s = s.replace(k, v + ' ')
    # Generic combining marks (above & dot) handled per-letter so we
    # don't need a precomposed entry for every base letter.
    s = re.sub(r'([A-Za-z])̇', r'\\dot{\1}', s)   # combining dot above
    s = re.sub(r'([A-Za-z])̈', r'\\ddot{\1}', s)  # combining diaeresis
    s = re.sub(r'([A-Za-z])̄', r'\\overline{\1}', s)  # combining macron
    s = re.sub(r'([A-Za-z])̂', r'\\hat{\1}', s)   # combining circumflex
    s = re.sub(r'([A-Za-z])̃', r'\\tilde{\1}', s) # combining tilde
    s = re.sub(r'([A-Za-z])̅', r'\\bar{\1}', s)   # combining overline
    out = []
    for ch in s:
        if ch in UNI2TEX:
            cmd = UNI2TEX[ch]
            # Add a trailing space for \alpha-style commands so the next
            # letter doesn't get glued onto the command name. We strip
            # spurious spaces later.
            if cmd.startswith('\\') and cmd[-1].isalpha():
                out.append(cmd + ' ')
            else:
                out.append(cmd)
        else:
            out.append(ch)
    res = ''.join(out)
    # Tidy: \cmd  -> \cmd (single space)
    # Collapse runs of spaces after a LaTeX command to one space, but
    # always keep at least one space (safe in math mode and avoids
    # gluing the command name to a Unicode letter that follows).
    res = re.sub(r'(\\[A-Za-z]+) +', r'\1 ', res)
    return res

# ---------------------------------------------------------------------
#   sqrt: bare and parenthesised
# ---------------------------------------------------------------------
def fix_sqrt(s: str) -> str:
    s = re.sub(r'√\(([^()]*)\)', r'\\sqrt{\1}', s)
    s = re.sub(r'√\s*([A-Za-z0-9]+)', r'\\sqrt{\1}', s)
    s = re.sub(r'\\sqrt\s*\(([^()]*)\)', r'\\sqrt{\1}', s)
    s = re.sub(r'\\sqrt\s+([A-Za-z0-9])\b', r'\\sqrt{\1}', s)
    # \sqrt followed by \langle ... \rangle -> \sqrt{\langle ... \rangle}
    s = re.sub(r'\\sqrt\s*\\langle\s*([^\\]+?)\s*\\rangle',
               r'\\sqrt{\\langle \1 \\rangle}', s)
    # \sqrt followed by a Greek/LaTeX command -> \sqrt{\command}
    s = re.sub(r'\\sqrt\s*(\\[A-Za-z]+)\b', r'\\sqrt{\1}', s)
    # \sqrt|...| -> \sqrt{|...|}
    s = re.sub(r'\\sqrt\s*\|([^|]+)\|', r'\\sqrt{|\1|}', s)
    # \sqrt followed by \langle ... \rangle  -> \sqrt{\langle ... \rangle}
    s = re.sub(r'\\sqrt\s*\\langle\s*([^,]+?)\s*,\s*([^,]+?)\s*\\rangle',
               r'\\sqrt{\\langle \1, \2 \\rangle}', s)
    # Bare \sqrt at end of math span — drop it (no operand)
    s = re.sub(r'\\sqrt\s*$', '', s)
    s = re.sub(r'\\sqrt\s+(?=[+\-*/=)\]}])', '', s)
    return s

# ---------------------------------------------------------------------
#   Inside-math touch-ups (function names etc.)
# ---------------------------------------------------------------------
def _fix_double_sub_super(s: str) -> str:
    """Rewrite `X_a_{...}` -> `X_{a_{...}}` to avoid LaTeX's
    'double subscript' / 'double superscript' errors."""
    # _<letter>_{...}  ->  _{<letter>_{...}}
    s = re.sub(r'_([A-Za-z0-9])_\{([^{}]+)\}', r'_{\1_{\2}}', s)
    s = re.sub(r'\^([A-Za-z0-9])\^\{([^{}]+)\}', r'^{\1^{\2}}', s)
    # _{x}_{y}  ->  _{xy}  (concatenate same-level subs)
    for _ in range(3):
        s = re.sub(r'_\{([^{}]+)\}_\{([^{}]+)\}', r'_{\1\2}', s)
        s = re.sub(r'\^\{([^{}]+)\}\^\{([^{}]+)\}', r'^{\1\2}', s)
    return s


def normalise_inside_math(s: str) -> str:
    # Set-difference handling MUST run BEFORE unimath_to_tex, otherwise
    # `\cdot` etc. introduced by unimath_to_tex get mangled.
    # `X\Y`, `R\[a,b]`, `R\(a,b)`, `ℝ\[a,b]` (no spaces). Excludes
    # `\{`, `\}` so the explicit braces our set-builder pre-pass
    # injects survive.
    # The trailing `(?![A-Za-z])` prevents matching LaTeX commands
    # like `\in`, `\mathbb`, `\cdot` — those have 2+ letters after `\`.
    # Real set-difference is `X\Y` with Y a single letter / `(` / `[`,
    # never followed by more letters.
    s = re.sub(r'([A-Za-z0-9\)\]ℝℂℚℤℕ𝔽ℙ𝕂𝔼])\\([A-Za-z\(\[ℝℂℚℤℕ𝔽ℙ𝕂𝔼])(?![A-Za-z])',
               r'\1\\setminus \2', s)
    # `X \ Y` form (backslash flanked by whitespace) → setminus.
    s = re.sub(r'(?<!\\)\\(?=\s|$)', r'\\setminus ', s)
    s = unimath_to_tex(s)
    s = fold_supersub(s)
    # `\sqrt` must be glued to its argument BEFORE we wrap sub/super
    # operators in braces (otherwise `e^\sqrt|z|` becomes `e^{\sqrt}|z|`).
    s = fix_sqrt(s)
    s = _fix_double_sub_super(s)
    # `X'_{i}^{2}` would produce a double-superscript error in LaTeX
    # (the `'` already acts as a superscript).  Reorder/group:
    # X'_{i}^{2}  ->  X^{\prime 2}_{i}
    s = re.sub(r"'(_\{[^{}]+\})\^\{([^{}]+)\}", r'^{\\prime \2}\1', s)
    # X'^{2}  -> X^{\prime 2}
    s = re.sub(r"'\^\{([^{}]+)\}", r'^{\\prime \1}', s)
    # Function names → \name
    for f in MATH_FUNCS_TEX:
        # only standalone; not preceded by '\' or letter
        s = re.sub(r'(?<![A-Za-z\\])' + re.escape(f) + r'(?![A-Za-z])',
                   r'\\' + f, s)
    # Operator rewrites (rank → \rank, span → \Span, ...)
    for src, tgt in MATH_OP_REWRITES.items():
        s = re.sub(r'(?<![A-Za-z\\])' + re.escape(src) + r'(?![A-Za-z])',
                   tgt.replace('\\', r'\\'), s)
    # Tidy duplicated backslashes from earlier pass
    s = re.sub(r'\\\\([A-Za-z]+)', r'\\\1', s)
    # Wrap `\cmd{arg}` first: `e^\sqrt{x}` -> `e^{\sqrt{x}}`
    s = re.sub(r'(_|\^)(\\[A-Za-z]+\{[^{}]*\})', r'\1{\2}', s)
    # Then wrap a bare `\cmd` (with no argument) in braces: T_\min -> T_{\min}
    s = re.sub(r'(_|\^)\\([A-Za-z]+)\b(?!\{)', r'\1{\\\2}', s)
    # ^(stuff) -> ^{stuff}, _(stuff) -> _{stuff}
    s = re.sub(r'\^\(([^()]+?)\)', r'^{\1}', s)
    s = re.sub(r'_\(([^()]+?)\)', r'_{\1}', s)
    # \lim(x \to a) and friends -> \lim_{x \to a}
    s = re.sub(r'\\lim\(\s*([^()]+?)\s*\\to\s*([^()]+?)\s*\)',
               r'\\lim_{\1 \\to \2}', s)
    s = re.sub(r'\\sup\(\s*([^()]+?)\s*\\to\s*([^()]+?)\s*\)',
               r'\\sup_{\1 \\to \2}', s)
    s = re.sub(r'\\inf\(\s*([^()]+?)\s*\\to\s*([^()]+?)\s*\)',
               r'\\inf_{\1 \\to \2}', s)
    s = re.sub(r'\\max\(\s*([^()]+?)\s*\\to\s*([^()]+?)\s*\)',
               r'\\max_{\1 \\to \2}', s)
    s = re.sub(r'\\min\(\s*([^()]+?)\s*\\to\s*([^()]+?)\s*\)',
               r'\\min_{\1 \\to \2}', s)
    # Tidy multi-spaces (math mode collapses, but for source clarity)
    s = re.sub(r'  +', ' ', s)
    return s.strip()

# ---------------------------------------------------------------------
#   Math fragment finder
# ---------------------------------------------------------------------
_COMBINING = set('̀́̂̃̄̅̆̇'
                 '̧̨̈̊̋̌')  # accents, dots, etc


def is_strong_math_char(ch: str) -> bool:
    """Characters that strongly indicate this is math content."""
    return (ch in ALL_UNI_MATH or ch in ALL_SUPER or ch in ALL_SUB
            or ch == '√' or ch in _COMBINING)


# Literal LaTeX-style sub/super patterns the user sometimes writes in
# raw markdown (e.g. `I_{xy}`, `lim_{x \to 0}`).  We need to recognise
# the `_` or `^` followed by `{...}` as a math trigger so the run gets
# wrapped in `$...$`.
def _has_literal_sub_super(text: str) -> bool:
    return bool(re.search(r'[A-Za-z0-9)\]][_^]\{[^{}]+\}', text))


def is_neutral_math_char(ch: str) -> bool:
    """Characters that can sit inside math but are also OK in prose."""
    return (ch.isalnum() or ch in "+-*/=<>()[]{}^_,.;:|'!? ")


_ASCII_ALPHA = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")


def _is_ascii_alpha(ch: str) -> bool:
    return ch in _ASCII_ALPHA


def expand_run(text: str, start: int, end: int) -> tuple[int, int]:
    """Given an initial mathy span [start,end), expand to include adjacent
    operators / single-letter variables / sub-super constructs but NOT
    English words. Returns the expanded (s,e).

    Strategy: do LEFT expansion first, then carry over any unmatched
    openers it captured into RIGHT expansion's depth counters so right
    expansion can properly accept their matching closers.
    """
    n = len(text)
    s, e = start, end

    # --- Expand left FIRST, so right-side knows about openers we picked.
    while s > 0:
        ch = text[s - 1]
        if is_strong_math_char(ch):
            s -= 1; continue
        if ch in "+-/=<>^_|\\'":
            s -= 1; continue
        if ch == '*' and (s - 2 < 0 or text[s - 2] != '*') \
                and (s >= len(text) or text[s] != '*'):
            s -= 1; continue
        if ch in ')]}':
            break
        if ch in '([{':
            # Don't cross openers going left -- if we do, the right side
            # has to find a matching closer, which often forces math to
            # eat English prose ("(α is differentiable)" → "(α is")
            # only to be killed by balance_parens. Stop here; the run
            # starts after the opener, parens stay as body-text glyphs.
            break
        if ch == ':':
            # set-builder colon: keep crossing left
            s -= 1; continue
        if ch == ',':
            k = s - 2
            while k >= 0 and text[k] == ' ':
                k -= 1
            if k >= 0 and (is_strong_math_char(text[k])
                           or text[k].isalnum() or text[k] in ')]}'):
                s -= 1; continue
            break
        if ch == '.':
            if s - 2 >= 0 and text[s-2].isdigit() and s < n and text[s].isdigit():
                s -= 1; continue
            if s - 2 >= 0 and text[s-2] == '.':
                while s > 0 and text[s-1] == '.':
                    s -= 1
                continue
            break
        if ch.isdigit():
            s -= 1; continue
        if _is_ascii_alpha(ch):
            k = s
            while k > 0 and _is_ascii_alpha(text[k - 1]):
                k -= 1
            word = text[k:s]
            if (len(word) == 1 or word in MATH_IDENT
                    or all(c in 'ijknmrstuvwxyz' for c in word) and len(word) <= 2):
                s = k
                continue
            break
        if ch == ' ':
            k = s - 1
            while k > 0 and text[k - 1] == ' ':
                k -= 1
            if k <= 0:
                break
            prev = text[k - 1]
            if (is_strong_math_char(prev) or prev in "+-/=<>^_)]}\\'"):
                s = k; continue
            if prev.isdigit():
                s = k; continue
            # Set-builder colon `{... : x ∈ X}` -- crossing the colon to
            # the left is fine; we'll trim at the end if it stays orphan.
            if prev == ':':
                s = k; continue
            if _is_ascii_alpha(prev):
                kk = k
                while kk > 0 and _is_ascii_alpha(text[kk - 1]):
                    kk -= 1
                w = text[kk:k]
                if len(w) == 1 or w in MATH_IDENT:
                    s = k; continue
            break
        break

    # Initialise right-side depth counters from left-side captures.
    left_body = text[s:e]
    paren_depth = max(0, left_body.count('(') - left_body.count(')'))
    bracket_depth = max(0, left_body.count('[') - left_body.count(']'))
    brace_depth = max(0, left_body.count('{') - left_body.count('}'))

    # --- Expand right -------------------------------------------------
    while e < n:
        ch = text[e]
        if is_strong_math_char(ch):
            e += 1
            continue
        if ch in "+-/=<>^_|\\'":
            # punctuation that's almost always math context
            e += 1
            continue
        # Single `*` (e.g. `V*` for dual space) -- but not the `**` of
        # markdown bold.
        if ch == '*' and (e == 0 or text[e - 1] != '*') \
                and (e + 1 >= n or text[e + 1] != '*'):
            e += 1
            continue
        if ch == '(':
            # Don't cross openers going right -- mirror image of the
            # left-side fix. Keeps prose like "(α is differentiable)"
            # from getting the whole parenthetical sucked into math.
            break
        if ch == '[':
            break
        if ch == '{':
            break
        if ch == ')':
            if paren_depth > 0:
                paren_depth -= 1; e += 1; continue
            # Asymmetric interval `[a, b)` -- close the bracket.
            if bracket_depth > 0:
                bracket_depth -= 1; e += 1; continue
            break
        if ch == ']':
            if bracket_depth > 0:
                bracket_depth -= 1; e += 1; continue
            # Asymmetric interval `(a, b]` -- close the paren.
            if paren_depth > 0:
                paren_depth -= 1; e += 1; continue
            break
        if ch == '}':
            if brace_depth > 0:
                brace_depth -= 1; e += 1; continue
            break
        if ch == ',':
            # comma inside parens or between math tokens — include
            # only if next non-space is mathy (or an ellipsis `...`)
            k = e + 1
            while k < n and text[k] == ' ':
                k += 1
            if k < n and (is_strong_math_char(text[k])
                          or text[k].isalnum() or text[k] in '({[|\\'):
                e += 1; continue
            if k + 1 < n and text[k] == '.' and text[k + 1] == '.':
                e += 1; continue
            break
        if ch == ':':
            # colon as separator inside any open scope: set-builder
            # {x : P(x)}, or annotated equation `(D>0, fxx>0: min; ...)`.
            if brace_depth > 0 or paren_depth > 0 or bracket_depth > 0:
                e += 1; continue
            break
        if ch == ';':
            if brace_depth > 0 or paren_depth > 0 or bracket_depth > 0:
                e += 1; continue
            break
        if ch == '.':
            # decimal point between digits, OR ellipsis ...
            if e + 1 < n and text[e+1].isdigit() and \
               e > 0 and text[e-1].isdigit():
                e += 1; continue
            if e + 1 < n and text[e+1] == '.':
                # ellipsis -- consume the dots
                while e < n and text[e] == '.':
                    e += 1
                continue
            break
        if ch.isdigit():
            e += 1; continue
        if _is_ascii_alpha(ch):
            # ASCII letter run -- check if it's a single var or math id.
            k = e
            while k < n and _is_ascii_alpha(text[k]):
                k += 1
            word = text[e:k]
            if len(word) == 1 or word in MATH_IDENT:
                e = k
                continue
            # Inside an unmatched bracket scope, cautiously accept a SHORT
            # word (≤2 letters) so we keep going to find the closing
            # bracket -- this catches differentials like `dx`, `ds`, `dn`.
            # Longer words are almost always English prose ("different",
            # "where", "for"); breaking here keeps prose out of math mode.
            if (paren_depth > 0 or bracket_depth > 0 or brace_depth > 0) \
                    and len(word) <= 2:
                e = k
                continue
            break
        if ch == ' ':
            k = e + 1
            while k < n and text[k] == ' ':
                k += 1
            if k >= n:
                break
            if (is_strong_math_char(text[k]) or text[k] in "+-/=<>^_|\\'"):
                e = k; continue
            if text[k].isdigit():
                e = k; continue
            if text[k] == '.' and k + 1 < n and text[k + 1] == '.':
                e = k; continue
            # Set-builder colon `{x : P(x)}` or annotated `(.. : ..)`
            if text[k] in ':;' and (brace_depth > 0 or paren_depth > 0 or bracket_depth > 0):
                e = k; continue
            # Single `*` (e.g. dual `V*`)
            if text[k] == '*' and (k == 0 or text[k - 1] != '*') \
                    and (k + 1 >= n or text[k + 1] != '*'):
                e = k; continue
            if _is_ascii_alpha(text[k]):
                kk = k
                while kk < n and _is_ascii_alpha(text[kk]):
                    kk += 1
                w = text[k:kk]
                if len(w) == 1 or w in MATH_IDENT:
                    e = k; continue
                # Inside an unmatched bracket scope, accept SHORT words
                # only (≤2 letters) -- catches `dx`, `ds`, `dn`
                # differentials but keeps prose out of math mode.
                if (paren_depth > 0 or bracket_depth > 0 or brace_depth > 0) \
                        and len(w) <= 2:
                    e = k; continue
            break
        break

    # Trim leading / trailing whitespace and pure punctuation
    while s < e and text[s] in ' \t':
        s += 1
    while e > s and text[e - 1] in ' \t':
        e -= 1
    while e > s and text[e - 1] in '.,;:?!':
        e -= 1
    # Drop a leading colon (set-builder separator that we crossed but
    # didn't reach the opening brace).
    while s < e and text[s] in ':,;':
        s += 1
    # Drop any leading closer characters or trailing opener characters
    # that crept in via aggressive expansion.
    while s < e and text[s] in ')]}':
        s += 1
    while e > s and text[e - 1] in '([{':
        e -= 1
    # Trim a dangling sub/super operator at the end (no operand).
    while e > s and text[e - 1] in '^_+-*/=<>':
        e -= 1
    while s < e and text[s] in ' \t':
        s += 1
    while e > s and text[e - 1] in ' \t':
        e -= 1
    return s, e


def find_math_runs(text: str) -> list[tuple[int, int]]:
    """Return a list of (start, end) spans to wrap in $...$."""
    runs = []
    i, n = 0, len(text)
    while i < n:
        if is_strong_math_char(text[i]):
            s, e = expand_run(text, i, i + 1)
            if s < e:
                runs.append((s, e))
                i = e
                continue
        i += 1
    # Merge overlapping / adjacent
    if not runs:
        return runs
    runs.sort()
    merged = [list(runs[0])]
    for s, e in runs[1:]:
        if s <= merged[-1][1] + 0:   # adjacent or overlap
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [tuple(r) for r in merged]


def _balance_parens(text: str, s: int, e: int) -> tuple[int, int]:
    """Trim the span [s,e) so its paren/bracket/brace counts match.

    Asymmetric intervals like `[a,b)` or `(a,b]` are accepted as long as
    the TOTAL count of `[+(` matches `)+]`, even if `[` and `(` don't
    individually pair with their own kind.

    For genuinely unmatched OPENERS we cut from the rightmost opener;
    for unmatched CLOSERS we cut from the leftmost orphan closer.
    """
    # Brace mismatches we always treat strictly.
    while True:
        body = text[s:e]
        changed = False
        n_op = body.count('{')
        n_cl = body.count('}')
        if n_op > n_cl:
            idx = body.rfind('{')
            if idx >= 0:
                e = s + idx
                changed = True
        elif n_cl > n_op:
            idx = body.find('}')
            if idx >= 0:
                s = s + idx + 1
                changed = True
        if not changed:
            break
    # Paren + bracket: combined accounting (interval-friendly).
    while True:
        body = text[s:e]
        changed = False
        n_open = body.count('(') + body.count('[')
        n_close = body.count(')') + body.count(']')
        if n_open > n_close:
            i_p = body.rfind('(')
            i_b = body.rfind('[')
            idx = max(i_p, i_b)
            if idx >= 0:
                e = s + idx
                changed = True
        elif n_close > n_open:
            i_p = body.find(')')
            i_b = body.find(']')
            idx = min(x for x in (i_p, i_b) if x >= 0) if (i_p >= 0 or i_b >= 0) else -1
            if idx >= 0:
                s = s + idx + 1
                changed = True
        if not changed:
            break
    return s, e


_KNOWN_MATH_BASES = ('lim', 'sup', 'inf', 'max', 'min', 'log', 'ker',
                     'dim', 'arg', 'gcd', 'lcm', 'det', 'span', 'rank',
                     'proj', 'Var', 'Cov', 'tr', 'Tr')
# NOTE: 'Re' and 'Im' are deliberately NOT in this list: in our source
# files `Re^iθ` means R·e^(iθ) (radius times exponential), not the
# real-part operator. Auto-wrapping `Re` to `\Re` would corrupt these
# expressions into the fraktur-R real-part symbol. The real-part form
# `Re(z)` still renders correctly as plain "Re(z)" without auto-wrapping.

# Bases that should be emitted with `\` prefix (have a builtin LaTeX
# command or `\DeclareMathOperator` in our preamble).
_BACKSLASH_BASES = {'lim', 'sup', 'inf', 'max', 'min', 'log', 'ker',
                    'dim', 'arg', 'gcd', 'lcm', 'det',
                    'span', 'rank', 'proj', 'tr', 'Tr'}


_FILENAME_EXTS = ('.md', '.tex', '.txt', '.py', '.pdf',
                  '.html', '.htm', '.csv', '.json')


def _bracewrap_bare_subsuper(tail: str) -> str:
    """Wrap multi-char bare sub/sup runs in braces so LaTeX renders them
    correctly: `_xx` -> `_{xx}`, `^21` -> `^{21}`. Single-char `_x` and
    already-braced `_{...}` are left alone. Multi-letter alpha runs are
    additionally wrapped in `\\mathrm{...}` for upright readability
    (`_external` -> `_{\\mathrm{external}}`); short alpha runs (≤2
    letters that look like math indices) and digit-only runs stay
    italic."""

    def repl(m):
        op = m.group(1)
        body = m.group(2)
        # Pure alpha, ≥3 letters: abbreviation, render upright
        if body.isalpha() and len(body) >= 3:
            return op + '{\\mathrm{' + body + '}}'
        return op + '{' + body + '}'

    return re.sub(r'([_^])([A-Za-z0-9]{2,})', repl, tail)


def _looks_like_filename_after(text: str, end_idx: int) -> bool:
    """Heuristic: would wrapping match[start:end] mangle a filename?"""
    snippet = text[end_idx:end_idx + 8]
    return any(snippet.startswith(ext) for ext in _FILENAME_EXTS)


def _wrap_literal_subsuper(text: str) -> str:
    """Wrap `X_{...}`, `X^{...}`, `X_y` and `X^y` patterns in `$...$` so
    they render as real LaTeX subscripts/superscripts instead of literal
    text. Recognises a multi-letter base if it's a known math operator
    (lim, sup, proj, ...). Won't touch text already inside `$...$`."""
    # Inner alternation matches one sub/sup chunk:
    #   `_{...}` / `^{...}`         braced form (any content)
    #   `_xx` / `^21`               bare alphanumeric run (≥1 char)
    #   `^*`, `^+`, `^-`, `^\dagger` etc. — common single-symbol superscripts
    SUBSUP = r'(?:[_^]\{[^{}]+\}|[_^][A-Za-z0-9]+|[_^][*+\-\'])'
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] == '$':
            j = text.find('$', i + 1)
            if j == -1:
                out.append(text[i:]); break
            out.append(text[i:j + 1])
            i = j + 1
            continue
        # Try multi-letter math bases first (lim, max, sup, proj, ...).
        matched = False
        for base in _KNOWN_MATH_BASES:
            if text[i:i + len(base)].lower() == base.lower() \
                    and i + len(base) < n \
                    and text[i + len(base)] in '_^':
                m = re.match(
                    r'(' + re.escape(text[i:i + len(base)]) + r')'
                    r'(' + SUBSUP + r'+)',
                    text[i:])
                if m:
                    # Don't grab inside a word ("alim" inside "calim...")
                    # Don't wrap a filename like `lim_foo.md`.
                    if (i == 0 or not _is_ascii_alpha(text[i - 1])) and \
                            not _looks_like_filename_after(text, i + m.end()):
                        tail = _bracewrap_bare_subsuper(m.group(2))
                        prefix = ('\\' + base) if base in _BACKSLASH_BASES \
                            else base
                        out.append('$' + prefix + tail + '$')
                        i += m.end()
                        matched = True
                        break
        if matched:
            continue
        # Short multi-letter base (≤3 letters) preceded by word boundary.
        # Catches `Mv_cm`, `Ma_cm`, `xy_z` etc. without grabbing whole
        # variable names like `file_name`.
        m = re.match(r'([A-Za-z]{2,3})(' + SUBSUP + r'+)', text[i:])
        if m:
            if (i == 0 or not _is_ascii_alpha(text[i - 1])
                    and text[i - 1] not in '_.') \
                    and not _looks_like_filename_after(text, i + m.end()):
                tail = _bracewrap_bare_subsuper(m.group(2))
                out.append('$' + m.group(1) + tail + '$')
                i += m.end()
                continue
        # Single-character base + sub/sup (braced or bare)
        m = re.match(r'([A-Za-z0-9)\]])(' + SUBSUP + r'+)', text[i:])
        if m:
            # Don't grab the last letter of a word (avoid `lim_{...}` being
            # chopped to `m_{...}`, or `file_name` becoming `e_name`).
            # Don't wrap a filename either (`01_Advanced_LA.md`).
            if (i == 0 or not _is_ascii_alpha(text[i - 1])) and \
                    not _looks_like_filename_after(text, i + m.end()):
                tail = _bracewrap_bare_subsuper(m.group(2))
                out.append('$' + m.group(1) + tail + '$')
                i += m.end()
                continue
        out.append(text[i])
        i += 1
    return ''.join(out)


_SET_BUILDER_PHRASES = (
    'for all', 'for some', 'such that', 'there exists',
    'there exist', 'whenever',
)


def _texify_setbuilder_body(body: str) -> str:
    """Inside an auto-wrapped set-builder, wrap multi-word phrases and
    multi-letter prose words in `\\text{ ... }` so spaces survive math
    mode (the leading/trailing space inside \\text{} preserves visual
    separation from neighbouring math glyphs). Known math identifiers
    (sin, lim, span, ...) are left as-is."""
    # Multi-word phrases first (so 'for all' becomes one \text{}).
    for phrase in _SET_BUILDER_PHRASES:
        body = re.sub(r'\b' + re.escape(phrase) + r'\b',
                      r'\\text{ ' + phrase + r' }', body)

    def repl(m):
        word = m.group(0)
        if word in MATH_IDENT:
            return word
        # Wrap with surrounding spaces so it doesn't glue to neighbour
        # math atoms when math-mode collapses whitespace.
        return r'\text{ ' + word + r' }'

    # Match 3+ letter alpha words OR specific 2-letter English words,
    # but only if not already inside a \text{...} block.  Two-pass:
    # first protect existing \text{...}, then transform, then restore.
    placeholders = []

    def _protect(m):
        placeholders.append(m.group(0))
        return f'\x02PH{len(placeholders)-1}\x02'

    body = re.sub(r'\\text\{[^{}]*\}', _protect, body)
    body = re.sub(r'\b[A-Za-z]{3,}\b', repl, body)
    # Restore protected blocks
    body = re.sub(r'\x02PH(\d+)\x02',
                  lambda m: placeholders[int(m.group(1))], body)
    return body


def _wrap_set_builder(text: str) -> str:
    """Wrap `{x ∈ X : ... for all y ∈ Y}` set-builder constructs in
    `$...$`. Recognises a brace span that (a) is balanced, (b) lives on
    one line, (c) contains a strong math char, and (d) doesn't already
    sit inside `$...$`. Prose phrases like 'for all' are converted to
    `\\text{for all}` so spaces survive math mode."""
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == '$':
            # Toggle math mode.  Don't touch anything inside.
            j = text.find('$', i + 1)
            if j == -1:
                out.append(text[i:]); break
            out.append(text[i:j + 1])
            i = j + 1
            continue
        if ch == '{':
            # Find matching `}` on the same line, tracking nested braces.
            depth = 1
            j = i + 1
            while j < n:
                if text[j] == '\n':
                    break
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if depth == 0:
                inner = text[i + 1:j]
                # Heuristic: must contain a strong math char and not
                # already contain `$` (would be already-wrapped math).
                if any(is_strong_math_char(c) for c in inner) \
                        and '$' not in inner \
                        and len(inner) < 200:
                    body = _texify_setbuilder_body(inner)
                    out.append(r'$\{' + body + r'\}$')
                    i = j + 1
                    continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _wrap_set_difference(text: str) -> str:
    """Wrap `X\\A` (set difference) and `Int(X\\A)` patterns in `$...$`
    so the backslash renders as a proper `\\setminus`. Avoids touching
    text inside existing `$...$` and Windows-style paths like `C:\\foo`."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] == '$':
            j = text.find('$', i + 1)
            if j == -1:
                out.append(text[i:]); break
            out.append(text[i:j + 1])
            i = j + 1
            continue
        # Pattern: <single uppercase letter or digit> \ <single uppercase letter>
        # tightened to single-char operands so we don't grab other things.
        m = re.match(r'([A-Z])\\([A-Z])(?![A-Za-z])', text[i:])
        if m:
            # Don't grab if preceded by alpha (would be inside a word).
            if i == 0 or not _is_ascii_alpha(text[i - 1]):
                out.append('$' + m.group(1) + r' \setminus ' + m.group(2) + '$')
                i += m.end()
                continue
        out.append(text[i])
        i += 1
    return ''.join(out)


def wrap_math_in_text(text: str) -> str:
    text = _wrap_set_builder(text)
    text = _wrap_set_difference(text)
    text = _wrap_literal_subsuper(text)
    # After literal wrapping, fall back to split_existing_math so any
    # Unicode math chars sitting INSIDE the new $...$ span are normalised
    # rather than being grabbed again by find_math_runs.
    if '$' in text:
        segs = split_existing_math(text)
        out = []
        for kind, body in segs:
            if kind == 'math':
                out.append('$' + normalise_inside_math(body) + '$')
            elif kind == 'dmath':
                out.append('$$' + normalise_inside_math(body) + '$$')
            else:
                out.append(_wrap_math_runs(body))
        return ''.join(out)
    return _wrap_math_runs(text)


def _wrap_math_runs(text: str) -> str:
    if not any(is_strong_math_char(c) for c in text):
        return text
    # Strip and remember a leading markdown bullet ('- ', '* ', '+ ', or '1. ')
    bullet_match = re.match(r'^(\s*)(?:[-*+]\s+|\d+\.\s+)', text)
    bullet = ''
    if bullet_match:
        bullet = text[:bullet_match.end()]
        text = text[bullet_match.end():]
    runs = find_math_runs(text)
    if not runs:
        return bullet + text
    out, last = [], 0
    for s, e in runs:
        s, e = _balance_parens(text, s, e)
        if s >= e:
            continue
        out.append(text[last:s])
        body = text[s:e]
        body_tex = normalise_inside_math(body)
        if body_tex:
            out.append('$' + body_tex + '$')
        else:
            out.append(body)
        last = e
    out.append(text[last:])
    return bullet + ''.join(out)

# ---------------------------------------------------------------------
#   ASCII matrix art
# ---------------------------------------------------------------------
# A matrix row is one `|...|` pair, possibly with arbitrary prefix text
# ending in `=` and a short tail (comment).  Capturing the LAST `|...|` on
# the line so prose-prefixed examples still parse.
MATRIX_ROW_RE = re.compile(
    r'^(?P<lead>\s*)(?P<prefix>.*?=\s*)?'
    r'\|(?P<body>[^|]+)\|\s*(?P<tail>.*)$')


def is_matrix_art_row(line: str) -> bool:
    """Detect a single matrix-art row.  Matches:
       `| 2 3 |`                    (bare row)
       `A = | 2 3 |`                (with simple LHS prefix)
       `A = | 2 3 |    2x2 matrix`  (LHS prefix + trailing comment)
       `Matrix [T] = | 2 3 |`       (with longer prefix ending in `=`)
    Rejects:
     - lines with > 2 pipe characters (markdown table rows)
     - prose words with 3+ letters inside the `|...|` payload
    """
    s = line.rstrip()
    if s.count('|') != 2:
        return False
    m = re.search(r'(.*?)\|([^|]+)\|\s*(.*)$', s)
    if not m:
        return False
    prefix = m.group(1).strip()
    body = m.group(2).strip()
    if not body or re.match(r'^[-:]+$', body):
        return False
    if prefix and not prefix.endswith('='):
        return False
    # Trailing comment is fine — we'll drop it during conversion.
    # Reject if any cell looks like a real English word.
    for cell in re.split(r'\s{2,}|\s+', body):
        cell = cell.strip()
        if not cell:
            continue
        m2 = re.fullmatch(r'[A-Za-z]+', cell)
        if m2 and len(cell) >= 3 and cell.lower() not in MATH_IDENT \
                and cell not in MATH_IDENT:
            return False
    return True


def collect_matrix(lines: list[str], i: int) -> tuple[str | None, int]:
    j = i
    rows = []
    prefix = ''
    while j < len(lines):
        ln = lines[j].rstrip()
        m = MATRIX_ROW_RE.match(ln)
        if not m:
            break
        if not rows and m.group('prefix'):
            prefix = m.group('prefix').rstrip(' =').strip()
        body = m.group('body').strip()
        # Cells are split by 2+ spaces, single space inside short tokens
        cells = re.split(r'\s{2,}', body)
        if len(cells) == 1:
            cells = re.split(r'\s+', cells[0])
        cells = [normalise_inside_math(c) for c in cells if c.strip() != '']
        rows.append(cells)
        j += 1
    if len(rows) < 2:
        return None, i
    ncol = max(len(r) for r in rows)
    rows = [r + [''] * (ncol - len(r)) for r in rows]
    body = ' \\\\\n'.join(' & '.join(r) for r in rows)
    if prefix:
        # Wrap 3+ letter prose words in \text{...} so they render upright
        # in display-math (otherwise "Matrix" becomes 6 italic letters).
        prefix_tex = re.sub(r'([A-Za-z]{3,})', r'\\text{\1}', prefix)
        latex = (f"$$\n{prefix_tex} = \\begin{{pmatrix}}\n{body}\n"
                 f"\\end{{pmatrix}}\n$$\n")
    else:
        latex = (f"$$\n\\begin{{pmatrix}}\n{body}\n"
                 f"\\end{{pmatrix}}\n$$\n")
    return latex, j

# ---------------------------------------------------------------------
#   Inline math segments (already in $...$) preservation
# ---------------------------------------------------------------------
def split_existing_math(line: str) -> list[tuple[str, str]]:
    """Split a line into ('text', body) and ('math', body) segments
    based on existing $...$ delimiters."""
    segs, i, n = [], 0, len(line)
    while i < n:
        if line[i] == '$':
            if i + 1 < n and line[i + 1] == '$':
                j = line.find('$$', i + 2)
                if j == -1:
                    segs.append(('text', line[i:])); return segs
                segs.append(('dmath', line[i+2:j]))
                i = j + 2
            else:
                j = line.find('$', i + 1)
                if j == -1:
                    segs.append(('text', line[i:])); return segs
                segs.append(('math', line[i+1:j]))
                i = j + 1
        else:
            j = line.find('$', i)
            if j == -1:
                segs.append(('text', line[i:])); return segs
            segs.append(('text', line[i:j]))
            i = j
    return segs


def _is_md_table_row(line: str) -> bool:
    """Markdown pipe-table row: starts with `|`, ends with `|`, ≥3 pipes."""
    s = line.strip()
    if not (s.startswith('|') and s.endswith('|')):
        return False
    return s.count('|') >= 3


def process_line(line: str) -> str:
    if not line.strip():
        return line
    # Preserve a leading blockquote marker `>` so it doesn't get pulled
    # into a math run.
    m_q = re.match(r'^(\s*>+\s?)(.*)$', line)
    if m_q:
        return m_q.group(1) + process_line(m_q.group(2))
    # Markdown table row: process each cell separately so `|` separators
    # are not eaten into a single math run.
    if _is_md_table_row(line):
        # Preserve leading whitespace
        leading = line[:len(line) - len(line.lstrip())]
        body = line.strip()
        # Protect any `|chunk|` that looks like absolute value (no
        # whitespace adjacent to either bar) by replacing with a sentinel
        # we'll put back after splitting.
        abs_runs: list[str] = []

        def _cap_abs(m):
            abs_runs.append(m.group(1))
            return f'\x01ABS{len(abs_runs)-1}\x01'
        body = re.sub(r'(?<=[\s|])\|([^|\s][^|]*?[^|\s])\|(?=[\s,)\].])',
                      _cap_abs, body)
        cells = body.split('|')
        # Restore absolute-value bars in each cell.
        if abs_runs:
            cells = [re.sub(r'\x01ABS(\d+)\x01',
                            lambda m: '|' + abs_runs[int(m.group(1))] + '|',
                            c) for c in cells]
        # cells[0] and cells[-1] are empty strings
        new_cells = []
        for c in cells:
            if not c.strip():
                new_cells.append(c)
                continue
            new_cells.append(process_cell_content(c))
        return leading + '|'.join(new_cells)
    return process_cell_content(line)


def process_cell_content(text: str) -> str:
    segs = split_existing_math(text)
    out = []
    for kind, body in segs:
        if kind == 'math':
            out.append('$' + normalise_inside_math(body) + '$')
        elif kind == 'dmath':
            out.append('$$' + normalise_inside_math(body) + '$$')
        else:
            out.append(wrap_math_in_text(body))
    return ''.join(out)

# ---------------------------------------------------------------------
#   Document-level processing
# ---------------------------------------------------------------------
CODE_FENCE = re.compile(r'^[ \t]*```')


def _block_contains_math(block: list[str]) -> bool:
    return any(any(is_strong_math_char(c) for c in ln) for ln in block)


def _block_is_box_art(block: list[str]) -> bool:
    return any(c in '│─├└┌┐┘┤┬┴┼╔╗╚╝║═╠╣╩╦╬'
               for ln in block for c in ln)


def preprocess_markdown(md: str) -> str:
    md = unicodedata.normalize('NFC', md)
    lines = md.splitlines()
    out, i, in_code = [], 0, False
    while i < len(lines):
        line = lines[i]
        m_fence = CODE_FENCE.match(line)
        if m_fence:
            if in_code:
                in_code = False
                out.append(line)
                i += 1
                continue
            # Look ahead inside the fence
            j = i + 1
            block = []
            while j < len(lines) and not CODE_FENCE.match(lines[j]):
                block.append(lines[j]); j += 1

            # 1) Matrix art?
            has_matrix = any(is_matrix_art_row(b) for b in block)
            has_math = _block_contains_math(block)
            is_box_art = _block_is_box_art(block)

            if has_matrix or (has_math and not is_box_art):
                # Emit each line as its own paragraph so md2tex makes a
                # standalone block (good vertical rhythm for equations).
                k = 0
                # Add a blank line marker before so the surrounding text
                # ends a paragraph
                out.append('')
                while k < len(block):
                    if is_matrix_art_row(block[k]):
                        latex, new_k = collect_matrix(block, k)
                        if latex is not None:
                            out.append(latex)
                            out.append('')
                            k = new_k
                            continue
                    if not block[k].strip():
                        out.append('')
                        k += 1
                        continue
                    # Each fenced-block line becomes its own paragraph.
                    # We do NOT split on multi-space alignment because that
                    # alignment is the source author's visual choice -- it
                    # collapses naturally when rendered, and the paired
                    # comment ("Natural numbers") belongs on the same line.
                    raw = block[k].strip()
                    if raw:
                        out.append(process_line(raw))
                        out.append('')
                    k += 1
                i = j + 1
                continue
            elif is_box_art:
                # mind-map: drop entirely (box-drawing won't render in
                # a serif body font and adds no exam value)
                i = j + 1
                continue
            else:
                # genuine code block — keep verbatim
                out.append('```')
                out.extend(block)
                out.append('```')
                in_code = False
                i = j + 1
                continue
        # Non-code line
        # ASCII matrix outside code fences too?
        if is_matrix_art_row(line) and i + 1 < len(lines) \
                and is_matrix_art_row(lines[i + 1]):
            latex, new_i = collect_matrix(lines, i)
            if latex is not None:
                out.append(latex)
                i = new_i
                continue
        out.append(process_line(line))
        i += 1
    text = '\n'.join(out)
    # Earlier we tried to remove "empty $<space>$" spans here but the
    # regex also eats the gap between two adjacent inline-math spans
    # (e.g. `$\omega \times$ $r_{P/cm}$` -> `$\omega \timesr_{P/cm}$`).
    # An empty `$ $` is harmless in LaTeX, so we just leave them.
    return text


def main(argv):
    if len(argv) < 2:
        print("Usage: mathify.py <input.md> [output.md]")
        sys.exit(1)
    src = Path(argv[1])
    dst = Path(argv[2]) if len(argv) > 2 else src.with_suffix('.processed.md')
    md = src.read_text(encoding='utf-8')
    md = unicodedata.normalize('NFC', md)
    dst.write_text(preprocess_markdown(md), encoding='utf-8')
    print(f"wrote {dst}")


if __name__ == '__main__':
    main(sys.argv)
