#!/usr/bin/env python3
"""
Generate MSc Math booklet v8.
Key fix: Remove code fences around math, convert matrices to LaTeX,
wrap math expressions properly.
"""
import os, re, subprocess, shutil

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"
OUTPUT_PDF = os.path.expanduser("~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf")
BUILD_DIR = os.path.join(NOTES_DIR, "build")
os.makedirs(BUILD_DIR, exist_ok=True)

CHAPTERS = [
    ("00A_Prerequisites.md", "Prerequisites — Class 12 Refresher"),
    ("00_MASTER_INDEX.md", "Study Roadmap & CSIR NET Guide"),
    ("09_Hit_Rate_Analysis.md", "Topic Hit-Rate Priority Analysis"),
    ("01_Advanced_Linear_Algebra.md", "Advanced Linear Algebra"),
    ("01B_Linear_Algebra_Deep_Proofs.md", "Linear Algebra — Proofs & Problems"),
    ("02_Mathematical_Analysis.md", "Mathematical Analysis"),
    ("02B_Analysis_Deep_Proofs.md", "Analysis — Proofs & Problems"),
    ("03_Topology.md", "Topology-1"),
    ("03B_Topology_Deep_Proofs.md", "Topology — Proofs & Counterexamples"),
    ("04_Advanced_Complex_Analysis.md", "Advanced Complex Analysis"),
    ("04B_Complex_Analysis_Deep_Proofs.md", "Complex Analysis — Proofs & Problems"),
    ("05_Advanced_Differential_Equations.md", "Advanced Differential Equations"),
    ("05B_ODE_Deep_Proofs.md", "Differential Equations — Proofs & Problems"),
    ("06_Dynamics_of_Rigid_Body.md", "Dynamics of a Rigid Body"),
    ("06B_Dynamics_Deep_Proofs.md", "Dynamics — Proofs & Problems"),
    ("07_CSIR_NET_Quick_Revision.md", "CSIR NET Quick Revision"),
    ("08_PYQ_Compilation.md", "Previous Year Questions — Solved"),
    ("11_Gap_Filler_All_Missing_Proofs.md", "Additional Proofs & Gap Filler"),
]

PREAMBLE = r"""\usepackage{amsmath,amssymb,amsthm,mathtools}
\usepackage{tcolorbox}
\tcbuselibrary{breakable,skins}
\usepackage{tikz}
\usepackage{xcolor}
\usepackage{fancyhdr}

% Vibrant colors
\definecolor{deepblue}{HTML}{1a1a6e}
\definecolor{accentblue}{HTML}{4a47a3}
\definecolor{prereqbg}{HTML}{fff8e1}
\definecolor{prereqborder}{HTML}{f9a825}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\textit{\nouppercase{\leftmark}}}
\fancyhead[R]{\textit{\nouppercase{\rightmark}}}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

% Style blockquotes as prerequisite boxes
\renewenvironment{quote}{%
  \begin{tcolorbox}[colback=prereqbg,colframe=prereqborder,
    title=\textbf{Prerequisites — What You Need to Know},
    fonttitle=\bfseries\color{black},
    breakable,boxrule=1.5pt,arc=4pt,left=8pt,right=8pt]
}{%
  \end{tcolorbox}
}

\renewcommand{\qedsymbol}{$\blacksquare$}
\let\cleardoublepage\clearpage
"""

PREAMBLE_FILE = os.path.join(BUILD_DIR, "preamble.tex")
with open(PREAMBLE_FILE, 'w') as f:
    f.write(PREAMBLE)


# Unicode → LaTeX mappings
MATH_MAP = [
    ('ℝ', r'\mathbb{R}'), ('ℂ', r'\mathbb{C}'), ('ℚ', r'\mathbb{Q}'),
    ('ℤ', r'\mathbb{Z}'), ('ℕ', r'\mathbb{N}'),
    ('∈', r'\in'), ('∉', r'\notin'), ('⊂', r'\subset'),
    ('⊆', r'\subseteq'), ('⊃', r'\supset'), ('⊇', r'\supseteq'),
    ('∪', r'\cup'), ('∩', r'\cap'), ('∅', r'\emptyset'),
    ('∀', r'\forall'), ('∃', r'\exists'),
    ('⟹', r'\Longrightarrow'), ('⟸', r'\Longleftarrow'),
    ('⟺', r'\Longleftrightarrow'),
    ('⇒', r'\Rightarrow'), ('⇐', r'\Leftarrow'), ('⇔', r'\Leftrightarrow'),
    ('→', r'\to'), ('←', r'\leftarrow'), ('↔', r'\leftrightarrow'),
    ('≤', r'\leq'), ('≥', r'\geq'), ('≠', r'\neq'),
    ('≈', r'\approx'), ('≡', r'\equiv'), ('∞', r'\infty'),
    ('≅', r'\cong'), ('∼', r'\sim'),
    ('α', r'\alpha'), ('β', r'\beta'), ('γ', r'\gamma'),
    ('δ', r'\delta'), ('ε', r'\varepsilon'), ('ζ', r'\zeta'),
    ('η', r'\eta'), ('θ', r'\theta'), ('λ', r'\lambda'),
    ('μ', r'\mu'), ('ν', r'\nu'), ('π', r'\pi'),
    ('ρ', r'\rho'), ('σ', r'\sigma'), ('τ', r'\tau'),
    ('φ', r'\varphi'), ('ψ', r'\psi'), ('ω', r'\omega'),
    ('κ', r'\kappa'), ('ξ', r'\xi'), ('χ', r'\chi'),
    ('Γ', r'\Gamma'), ('Δ', r'\Delta'), ('Σ', r'\Sigma'),
    ('Π', r'\Pi'), ('Ω', r'\Omega'), ('Φ', r'\Phi'),
    ('Λ', r'\Lambda'), ('Θ', r'\Theta'), ('Ψ', r'\Psi'),
    ('×', r'\times'), ('·', r'\cdot'), ('∘', r'\circ'),
    ('±', r'\pm'), ('∓', r'\mp'),
    ('∂', r'\partial'), ('∇', r'\nabla'),
    ('∫', r'\int'), ('∑', r'\sum'), ('∏', r'\prod'),
    ('⊕', r'\oplus'), ('⊗', r'\otimes'),
    ('⊥', r'\perp'), ('∎', r'\blacksquare'),
]

SUB_MAP = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9',
           'ₙ':'n','ₘ':'m','ₖ':'k','ᵢ':'i','ⱼ':'j'}
SUP_MAP = {'⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9',
           'ⁿ':'n','⁻':'-','ˣ':'x','ᵗ':'t'}


def has_math_chars(text):
    """Check if text contains math Unicode chars."""
    math_chars = set('ℝℂℚℤℕ∈∉⊂⊆⊃⊇∪∩∅∀∃⟹⟸⟺⇒⇐⇔→←↔≤≥≠≈≡∞≅∼αβγδεζηθλμνπρστφψωκξχΓΔΣΠΩΦΛΘΨ×·∘±∓∂∇∫∑∏⊕⊗⊥∎₀₁₂₃₄₅₆₇₈₉ₙₘₖᵢⱼ⁰¹²³⁴⁵⁶⁷⁸⁹ⁿ⁻ˣᵗ')
    return any(c in math_chars for c in text)


def convert_math_line(line):
    """Convert a line that contains math Unicode to proper LaTeX."""
    # Replace subscripts: letter₁ → letter_1  (keeping together)
    for u, l in SUB_MAP.items():
        line = line.replace(u, f'_{l}')
    # Replace superscripts: letter² → letter^2
    for u, l in SUP_MAP.items():
        line = line.replace(u, f'^{l}')
    # Group consecutive subscripts: _1_2 → _{12}
    for _ in range(5):
        line = re.sub(r'_(\w)_(\w)', r'_{\1\2}', line)
        line = re.sub(r'_\{(\w+)\}_(\w)', r'_{\1\2}', line)
    for _ in range(5):
        line = re.sub(r'\^(\w)\^(\w)', r'^{\1\2}', line)
        line = re.sub(r'\^\{(\w+)\}\^(\w)', r'^{\1\2}', line)
    # ^{-}1 → ^{-1}
    line = re.sub(r'\^\{-\}(\w)', r'^{-\1}', line)
    
    # Replace math symbols
    for u, l in MATH_MAP:
        line = line.replace(u, l)
    
    # Now wrap the whole line in $...$ if it has LaTeX commands
    # But only if it's a math-heavy line (formulas, equations)
    return line


def process_code_block(block_content):
    """Process a code block — if it contains math, convert to proper LaTeX.
    If it's actual code, keep as verbatim."""
    if has_math_chars(block_content) or re.search(r'[=≠≤≥<>]\s*\d', block_content):
        # This is math, not code. Convert each line.
        lines = block_content.strip().split('\n')
        result = []
        for line in lines:
            if not line.strip():
                result.append('')
                continue
            converted = convert_math_line(line)
            # Wrap in display math
            result.append(f'$${converted}$$')
        return '\n'.join(result)
    else:
        # Actual code — keep as code block
        return f'```\n{block_content}```'


def process_inline_math(line):
    """Convert inline Unicode math in regular text lines."""
    if not has_math_chars(line):
        return line
    
    # Find runs of math characters and wrap them in $...$
    # Strategy: replace unicode math chars with LaTeX, then wrap
    result = line
    
    # Replace subscripts WITH preceding char: e₁ → $e_1$
    for u, l in SUB_MAP.items():
        result = re.sub(r'(\w)' + re.escape(u), r'$\1_' + l + '$', result)
        # Also handle standalone
        result = result.replace(u, '$_' + l + '$')
    
    # Replace superscripts WITH preceding char: x² → $x^2$
    for u, l in SUP_MAP.items():
        result = re.sub(r'(\w)' + re.escape(u), r'$\1^' + l + '$', result)
        result = result.replace(u, '$^' + l + '$')
    
    # Replace math symbols — wrap each in inline math
    for u, l in MATH_MAP:
        if u in result:
            result = result.replace(u, f'${l}$')
    
    # Merge adjacent math: $..$ $..$ → $.. ..$
    for _ in range(10):
        result = re.sub(r'\$([^$]+)\$\s*\$([^$]+)\$', r'$\1 \2$', result)
    
    # Fix double sub/superscripts inside math
    for _ in range(5):
        result = re.sub(r'_(\w)\s*_(\w)', r'_{\1\2}', result)
        result = re.sub(r'_\{(\w+)\}\s*_(\w)', r'_{\1\2}', result)
        result = re.sub(r'\^(\w)\s*\^(\w)', r'^{\1\2}', result)
        result = re.sub(r'\^\{(\w+)\}\s*\^(\w)', r'^{\1\2}', result)
    result = re.sub(r'\^\{-\}\s*\^?(\w)', r'^{-\1}', result)
    
    return result


def preprocess(content):
    """Full preprocessing pipeline."""
    # Remove emoji
    content = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FAFF\U00002702-\U000027B0]', '', content)
    # Remove combining chars
    content = re.sub(r'[\u0304\u0308\u0307\u0332]', '', content)
    # Remove box-drawing
    content = re.sub(r'[\u2500-\u257F]', ' ', content)
    # Fix set complement: X\A → X∖A
    content = re.sub(r'(?<=[A-Za-z)])\\(?=[A-Za-z])', '∖', content)
    # Replace ∖ with \setminus in math context
    content = content.replace('∖', '$\\setminus$')
    
    # Process code blocks: convert math code blocks to display math
    def replace_code_block(match):
        lang = match.group(1) or ''
        block = match.group(2)
        if lang.strip().lower() in ('python', 'js', 'javascript', 'bash', 'shell', 'sh', 'sql', 'json', 'html', 'css'):
            return match.group(0)  # Keep actual code
        return process_code_block(block)
    
    content = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, content, flags=re.DOTALL)
    
    # Process inline math in non-code lines
    lines = content.split('\n')
    processed = []
    in_code = False
    for line in lines:
        if line.strip().startswith('```'):
            in_code = not in_code
            processed.append(line)
            continue
        if in_code:
            processed.append(line)
            continue
        
        # Process math in regular text
        if line.startswith('#') or line.startswith('|'):
            # Headers and table rows — light processing only
            processed.append(process_inline_math(line))
        else:
            processed.append(process_inline_math(line))
    
    return '\n'.join(processed)


def main():
    print("=" * 60)
    print("  Building MSc Math Booklet v8 (proper math conversion)")
    print("=" * 60)

    combined_md = os.path.join(BUILD_DIR, "combined.md")
    with open(combined_md, 'w', encoding='utf-8') as out:
        for filename, title in CHAPTERS:
            filepath = os.path.join(NOTES_DIR, filename)
            if not os.path.exists(filepath):
                print(f"  SKIP: {filename}")
                continue

            print(f"  Processing: {title}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            content = preprocess(content)
            content = re.sub(r'^# .+$', '', content, count=1, flags=re.MULTILINE)
            
            out.write(f"\n# {title}\n\n")
            out.write(content)
            out.write("\n\n")

    print(f"\n  Combined markdown: {combined_md}")
    
    # Generate .tex first, then compile with nonstopmode
    print("  pandoc → .tex...")
    tex_out = os.path.join(BUILD_DIR, "booklet.tex")
    subprocess.run([
        'pandoc', combined_md, '-o', tex_out,
        '--toc', '--toc-depth=2',
        '-V', 'documentclass=report',
        '-V', 'classoption=12pt,a4paper',
        '-V', 'mainfont=Latin Modern Roman',
        '-V', 'monofont=Latin Modern Mono',
        '-V', 'geometry:margin=2.5cm',
        '-V', f'title=MSc Mathematics — Semester 1',
        '-V', f'subtitle=Complete Study Guide',
        '-V', f'author=CSIR NET & University Exam Preparation',
        '-H', PREAMBLE_FILE,
        '--highlight-style=tango',
        '--top-level-division=chapter',
    ], capture_output=True, text=True, timeout=120)
    
    if not os.path.exists(tex_out):
        print("  ERROR: pandoc failed to generate .tex")
        return
    
    print("  xelatex pass 1...")
    subprocess.run(
        ['xelatex', '-interaction=nonstopmode', '-output-directory', BUILD_DIR, tex_out],
        cwd=BUILD_DIR, capture_output=True, timeout=600
    )
    print("  xelatex pass 2...")
    subprocess.run(
        ['xelatex', '-interaction=nonstopmode', '-output-directory', BUILD_DIR, tex_out],
        cwd=BUILD_DIR, capture_output=True, timeout=600
    )
    
    pdf_path = tex_out.replace('.tex', '.pdf')
    if os.path.exists(pdf_path):
        shutil.copy(pdf_path, OUTPUT_PDF)
        size_mb = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
        try:
            info = subprocess.run(['pdfinfo', OUTPUT_PDF], capture_output=True, text=True)
            pages = [l for l in info.stdout.split('\n') if 'Pages' in l]
            pg = pages[0].strip() if pages else "?"
        except:
            pg = "?"
        
        # Count errors
        log_path = tex_out.replace('.tex', '.log')
        errs = 0
        if os.path.exists(log_path):
            with open(log_path, encoding='latin-1') as f:
                errs = sum(1 for l in f if l.startswith('!'))
        
        print(f"\n{'=' * 60}")
        print(f"  DONE: {OUTPUT_PDF}")
        print(f"  {pg} | Size: {size_mb:.1f} MB | Warnings: {errs}")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
