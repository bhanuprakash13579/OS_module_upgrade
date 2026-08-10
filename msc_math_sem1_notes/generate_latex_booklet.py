#!/usr/bin/env python3
"""
Generate publication-quality LaTeX booklet.
Enhanced converter: detects theorems, proofs, examples, definitions
and wraps them in proper LaTeX environments with tcolorbox styling.
"""
import os, re, subprocess, shutil

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"
OUTPUT_TEX = os.path.join(NOTES_DIR, "full_booklet.tex")
OUTPUT_PDF = os.path.expanduser("~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf")


def escape_latex(text):
    """Escape LaTeX special chars, preserving already-escaped ones."""
    # Don't escape inside $...$ blocks
    parts = re.split(r'(\$[^$]+\$)', text)
    result = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # inside math
            result.append(part)
        else:
            part = part.replace('\\', '\\textbackslash{}')
            part = part.replace('&', r'\&')
            part = part.replace('%', r'\%')
            part = part.replace('#', r'\#')
            part = part.replace('{', r'\{')
            part = part.replace('}', r'\}')
            part = part.replace('~', r'\textasciitilde{}')
            part = part.replace('^', r'\textasciicircum{}')
            # Don't escape _ in common math contexts
            part = re.sub(r'_(?=[a-zA-Z0-9])', r'\_', part)
            result.append(part)
    return ''.join(result)


def unicode_to_latex(text):
    """Convert Unicode math symbols to LaTeX commands."""
    replacements = [
        ('ℝ', r'$\mathbb{R}$'), ('ℂ', r'$\mathbb{C}$'), ('ℚ', r'$\mathbb{Q}$'),
        ('ℤ', r'$\mathbb{Z}$'), ('ℕ', r'$\mathbb{N}$'),
        ('∈', r'$\in$'), ('∉', r'$\notin$'), ('⊂', r'$\subset$'),
        ('⊆', r'$\subseteq$'), ('⊃', r'$\supset$'),
        ('∪', r'$\cup$'), ('∩', r'$\cap$'), ('∅', r'$\emptyset$'),
        ('∀', r'$\forall$'), ('∃', r'$\exists$'),
        ('⟹', r'$\Longrightarrow$'), ('⟸', r'$\Longleftarrow$'),
        ('⟺', r'$\Longleftrightarrow$'),
        ('→', r'$\to$'), ('←', r'$\leftarrow$'),
        ('≤', r'$\leq$'), ('≥', r'$\geq$'), ('≠', r'$\neq$'),
        ('≈', r'$\approx$'), ('∞', r'$\infty$'),
        ('α', r'$\alpha$'), ('β', r'$\beta$'), ('γ', r'$\gamma$'),
        ('δ', r'$\delta$'), ('ε', r'$\varepsilon$'), ('ζ', r'$\zeta$'),
        ('η', r'$\eta$'), ('θ', r'$\theta$'), ('λ', r'$\lambda$'),
        ('μ', r'$\mu$'), ('ν', r'$\nu$'), ('π', r'$\pi$'),
        ('ρ', r'$\rho$'), ('σ', r'$\sigma$'), ('τ', r'$\tau$'),
        ('φ', r'$\varphi$'), ('ψ', r'$\psi$'), ('ω', r'$\omega$'),
        ('Γ', r'$\Gamma$'), ('Δ', r'$\Delta$'), ('Σ', r'$\Sigma$'),
        ('Π', r'$\Pi$'), ('Ω', r'$\Omega$'), ('Φ', r'$\Phi$'),
        ('∂', r'$\partial$'), ('∇', r'$\nabla$'),
        ('×', r'$\times$'), ('·', r'$\cdot$'), ('∘', r'$\circ$'),
        ('±', r'$\pm$'), ('∎', r'$\blacksquare$'),
        ('²', '$^2$'), ('³', '$^3$'), ('ⁿ', '$^n$'),
        ('ˣ', '$^x$'), ('ᵗ', '$^t$'), ('⁻', '$^{-}$'),
        ('⁰', '$^0$'), ('¹', '$^1$'), ('⁴', '$^4$'),
        ('₁', '$_1$'), ('₂', '$_2$'), ('₃', '$_3$'),
        ('ₙ', '$_n$'), ('ᵢ', '$_i$'), ('ⱼ', '$_j$'), ('ₖ', '$_k$'),
        ('₀', '$_0$'), ('ₘ', '$_m$'),
        ('∫', r'$\int$'), ('⊥', r'$\perp$'), ('≅', r'$\cong$'),
        ('⊕', r'$\oplus$'), ('⊗', r'$\otimes$'),
        ('ẍ', r'$\ddot{x}$'), ('ÿ', r'$\ddot{y}$'),
        ('θ̈', r'$\ddot{\theta}$'), ('ẋ', r'$\dot{x}$'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    
    # Fix consecutive math modes: $^2$$_1$ → $^2_1$
    # Run multiple passes to catch all sequences
    for _ in range(5):
        text = re.sub(r'\$([^$]+)\$\$([^$]+)\$', r'$\1\2$', text)
    # Also clean up any remaining empty math modes
    text = re.sub(r'\$\s*\$', '', text)
    
    # Fix double subscripts: $_i_j → _{ij}
    text = re.sub(r'_(\w)_(\w)', r'_{\1\2}', text)
    # Fix double superscripts: ^a^b → ^{ab}
    text = re.sub(r'\^(\w)\^(\w)', r'^{\1\2}', text)
    # Fix triple subscripts
    text = re.sub(r'_\{(\w+)\}_(\w)', r'_{\1\2}', text)
    
    # Convert fractions: digits/digits
    text = re.sub(r'(?<![a-zA-Z/\\])(\d+)/(\d+)(?![a-zA-Z/])', r'$\\frac{\1}{\2}$', text)
    
    # Square roots
    text = re.sub(r'√\(([^)]+)\)', r'$\\sqrt{\1}$', text)
    text = re.sub(r'√(\w+)', r'$\\sqrt{\1}$', text)
    
    
    return text


def process_line(line):
    """Process a single line of markdown content."""
    # Remove emoji and box-drawing characters
    line = re.sub(r'[\U0001F000-\U0001FFFF\U00002500-\U00002580\U00002190-\U000021FF\U00002700-\U000027BF\U0001F300-\U0001F9FF]', '', line)
    line = re.sub(r'[│─├└┌┐┘┤┬┴┼╔╗╚╝║═╠╣╩╦╬]', '', line)
    
    # Convert Unicode math
    line = unicode_to_latex(line)
    
    # Bold and italic — only on single line, ensure matched pairs
    line = re.sub(r'\*\*\*(.+?)\*\*\*', r'\\textbf{\\textit{\1}}', line)
    line = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', line)
    line = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'\\textit{\1}', line)
    # Remove any leftover unmatched ** or * that would break LaTeX
    line = line.replace('**', '')
    # Safety: verify brace balance
    opens = line.count('{') - line.count('\\{')
    closes = line.count('}') - line.count('\\}')
    if opens > closes:
        line += '}' * (opens - closes)
    
    # Inline code
    line = re.sub(r'`([^`]+)`', r'\\texttt{\1}', line)
    
    return line


def md_to_latex(md_text):
    """Convert markdown to high-quality LaTeX with proper environments."""
    lines = md_text.split('\n')
    output = []
    in_code = False
    in_list = False
    in_blockquote = False
    blockquote_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Code blocks
        if line.strip().startswith('```'):
            if in_code:
                output.append('\\end{verbatim}')
                in_code = False
            else:
                if in_list:
                    output.append('\\end{itemize}')
                    in_list = False
                output.append('\\begin{verbatim}')
                in_code = True
            i += 1
            continue
        
        if in_code:
            output.append(line)
            i += 1
            continue
        
        # Blockquotes (prerequisite boxes)
        if line.startswith('>'):
            if not in_blockquote:
                in_blockquote = True
                blockquote_lines = []
            content = line.lstrip('> ').lstrip('>')
            blockquote_lines.append(content)
            i += 1
            continue
        elif in_blockquote:
            # End of blockquote
            in_blockquote = False
            bq_text = '\n'.join(blockquote_lines)
            if 'Quick Refresher' in bq_text or 'Prerequisites' in bq_text:
                bq_processed = '\n'.join(process_line(l) for l in blockquote_lines if l.strip())
                output.append('\\begin{prereqbox}')
                output.append(bq_processed)
                output.append('\\end{prereqbox}')
            else:
                bq_processed = '\n'.join(process_line(l) for l in blockquote_lines if l.strip())
                output.append('\\begin{quote}')
                output.append(bq_processed)
                output.append('\\end{quote}')
            # Don't increment i, process current line below
        
        # Empty lines
        if not line.strip():
            if in_list:
                output.append('\\end{itemize}')
                in_list = False
            output.append('')
            i += 1
            continue
        
        # Headers
        unit_match = re.match(r'^# UNIT (\d+):\s*(.+)$', line)
        if unit_match:
            if in_list:
                output.append('\\end{itemize}')
                in_list = False
            num, title = unit_match.groups()
            title = process_line(title)
            output.append(f'\\section{{Unit {num}: {title}}}')
            i += 1
            continue
        
        h2_match = re.match(r'^## (.+)$', line)
        if h2_match:
            if in_list:
                output.append('\\end{itemize}')
                in_list = False
            title = process_line(h2_match.group(1))
            output.append(f'\\subsection{{{title}}}')
            i += 1
            continue
        
        h3_match = re.match(r'^### (.+)$', line)
        if h3_match:
            if in_list:
                output.append('\\end{itemize}')
                in_list = False
            title = process_line(h3_match.group(1))
            output.append(f'\\subsubsection{{{title}}}')
            i += 1
            continue
        
        h4_match = re.match(r'^#### (.+)$', line)
        if h4_match:
            title = process_line(h4_match.group(1))
            output.append(f'\\paragraph{{{title}}}')
            i += 1
            continue
        
        # Skip top-level H1 (handled as \chapter)
        if re.match(r'^# .+$', line):
            i += 1
            continue
        
        # Horizontal rules
        if re.match(r'^---+$', line):
            output.append('\\bigskip\\noindent\\rule{\\textwidth}{0.4pt}\\bigskip')
            i += 1
            continue
        
        # Tables
        if line.startswith('|'):
            table_lines = []
            while i < len(lines) and lines[i].startswith('|'):
                table_lines.append(lines[i])
                i += 1
            # Remove separator line
            table_lines = [l for l in table_lines if not re.match(r'^\|[-:| ]+\|$', l)]
            if table_lines:
                cols = len(table_lines[0].split('|')) - 2
                col_spec = '|' + 'l|' * cols
                output.append(f'\\begin{{center}}')
                output.append(f'\\begin{{tabular}}{{{col_spec}}}')
                output.append('\\hline')
                for j, tl in enumerate(table_lines):
                    cells = [process_line(c.strip()) for c in tl.split('|')[1:-1]]
                    if j == 0:
                        row = ' & '.join(f'\\textbf{{{c}}}' for c in cells)
                    else:
                        row = ' & '.join(cells)
                    output.append(f'{row} \\\\')
                    output.append('\\hline')
                output.append('\\end{tabular}')
                output.append('\\end{center}')
            continue
        
        # List items
        if re.match(r'^[-*] ', line):
            if not in_list:
                output.append('\\begin{itemize}[leftmargin=*]')
                in_list = True
            content = process_line(line[2:])
            output.append(f'  \\item {content}')
            i += 1
            continue
        
        if re.match(r'^\d+\. ', line):
            # Use enumerate for numbered lists
            if not in_list:
                output.append('\\begin{enumerate}')
                in_list = True
            content = process_line(re.sub(r'^\d+\. ', '', line))
            output.append(f'  \\item {content}')
            i += 1
            continue
        
        # Regular paragraph
        processed = process_line(line)
        
        # Detect theorem/definition/proof patterns and wrap them
        if re.match(r'\\textbf\{(Theorem|THEOREM)', processed):
            output.append(f'\\begin{{tcolorbox}}[colback=lightblue,colframe=thmblue,title=\\textbf{{Theorem}},breakable,boxrule=1.5pt]')
            output.append(processed)
            # Collect until blank line
            i += 1
            while i < len(lines) and lines[i].strip():
                output.append(process_line(lines[i]))
                i += 1
            output.append('\\end{tcolorbox}')
            continue
        
        if re.match(r'\\textbf\{(Definition|DEFINITION)', processed):
            output.append(f'\\begin{{tcolorbox}}[colback=lightblue!30,colframe=defgreen,title=\\textbf{{Definition}},breakable,boxrule=1.5pt]')
            output.append(processed)
            i += 1
            while i < len(lines) and lines[i].strip():
                output.append(process_line(lines[i]))
                i += 1
            output.append('\\end{tcolorbox}')
            continue
        
        if re.match(r'\\textbf\{(Proof|PROOF)', processed):
            output.append('\\begin{proof}')
            output.append(processed.replace('\\textbf{Proof:}', '').replace('\\textbf{Proof}', '').strip())
            i += 1
            while i < len(lines) and lines[i].strip():
                output.append(process_line(lines[i]))
                i += 1
            output.append('\\end{proof}')
            continue
        
        if re.match(r'\\textbf\{(Example|EXAMPLE|Worked Example)', processed):
            output.append(f'\\begin{{tcolorbox}}[colback=examplebg!30,colframe=exampleborder,title=\\textbf{{Worked Example}},breakable,boxrule=1pt]')
            output.append(processed)
            i += 1
            while i < len(lines) and lines[i].strip():
                output.append(process_line(lines[i]))
                i += 1
            output.append('\\end{tcolorbox}')
            continue
        
        if re.match(r'\\textbf\{(Lemma|LEMMA)', processed):
            output.append(f'\\begin{{tcolorbox}}[colback=lightblue!20,colframe=accentblue!70,title=\\textbf{{Lemma}},breakable,boxrule=1pt]')
            output.append(processed)
            i += 1
            while i < len(lines) and lines[i].strip():
                output.append(process_line(lines[i]))
                i += 1
            output.append('\\end{tcolorbox}')
            continue
        
        # Important/exam alert patterns
        if re.match(r'\\textbf\{(Important|IMPORTANT|Exam|EXAM|Key|KEY|Warning|Remember)', processed):
            output.append(f'\\begin{{tcolorbox}}[colback=warningbg!30,colframe=warningborder,title=\\textbf{{Important -- Exam Alert}},breakable,boxrule=1.5pt]')
            output.append(processed)
            i += 1
            while i < len(lines) and lines[i].strip():
                output.append(process_line(lines[i]))
                i += 1
            output.append('\\end{tcolorbox}')
            continue
        
        output.append(processed)
        i += 1
    
    # Close any open environments
    if in_list:
        output.append('\\end{itemize}')
    if in_blockquote:
        bq_processed = '\n'.join(process_line(l) for l in blockquote_lines if l.strip())
        output.append('\\begin{quote}')
        output.append(bq_processed)
        output.append('\\end{quote}')
    
    return '\n'.join(output)


PREAMBLE = r"""\documentclass[12pt,a4paper,openany]{book}
\maxdeadcycles=1000

\usepackage{fontspec}
\setmainfont{Latin Modern Roman}
\setmonofont{Latin Modern Mono}
\usepackage{amsmath,amssymb,amsthm,amsfonts}
\usepackage{mathtools}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,calc}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{tcolorbox}
\tcbuselibrary{theorems,skins,breakable}
\usepackage{enumitem}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{geometry}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{multicol}

\geometry{a4paper,margin=2.5cm,top=3cm,bottom=3cm}

% B&W-friendly colors
\definecolor{deepblue}{HTML}{1a1a6e}
\definecolor{accentblue}{HTML}{333366}
\definecolor{lightblue}{HTML}{f0f0f0}
\definecolor{prereqbg}{HTML}{f5f5f0}
\definecolor{prereqborder}{HTML}{444444}
\definecolor{examplebg}{HTML}{f0f0f0}
\definecolor{exampleborder}{HTML}{333333}
\definecolor{warningbg}{HTML}{f5f0f0}
\definecolor{warningborder}{HTML}{222222}
\definecolor{thmblue}{HTML}{222255}
\definecolor{defgreen}{HTML}{224422}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE]{\textit{\nouppercase{\leftmark}}}
\fancyhead[RO]{\textit{\nouppercase{\rightmark}}}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

\titleformat{\chapter}[display]
  {\normalfont\Huge\bfseries\color{deepblue}}
  {\chaptertitlename\ \thechapter}{20pt}{\Huge}
\titleformat{\section}
  {\normalfont\Large\bfseries\color{accentblue}}
  {\thesection}{1em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries\color{accentblue!80!black}}
  {\thesubsection}{1em}{}

\newtcolorbox{prereqbox}{
  colback=prereqbg, colframe=prereqborder,
  title={\textbf{Prerequisites -- What You Need to Know}},
  fonttitle=\bfseries\color{black},
  breakable, left=8pt, right=8pt, boxrule=2pt, arc=4pt,
}

\renewcommand{\qedsymbol}{$\blacksquare$}
\hypersetup{colorlinks=true,linkcolor=deepblue,urlcolor=accentblue}

\begin{document}

% Cover
\begin{titlepage}
\begin{tikzpicture}[remember picture,overlay]
  \fill[deepblue] (current page.south west) rectangle (current page.north east);
  \node[anchor=center,white,font=\fontsize{48}{56}\selectfont\bfseries] 
    at ([yshift=4cm]current page.center) {MSc Mathematics};
  \node[anchor=center,white,font=\fontsize{28}{34}\selectfont] 
    at ([yshift=1.5cm]current page.center) {Semester 1 --- Complete Study Guide};
  \draw[white,line width=2pt] ([yshift=-0.5cm,xshift=-5cm]current page.center) -- 
    ([yshift=-0.5cm,xshift=5cm]current page.center);
  \node[anchor=center,white!80,font=\fontsize{14}{18}\selectfont] 
    at ([yshift=-2cm]current page.center) {Manipal University Jaipur --- Distance Education};
  \node[anchor=center,white!70,font=\fontsize{12}{16}\selectfont\itshape] 
    at ([yshift=-3.5cm]current page.center) {Prepared for CSIR NET Qualification \& Assistant Professorship};
  \node[anchor=center,white!60,font=\fontsize{10}{14}\selectfont] 
    at ([yshift=-5.5cm]current page.center) {6 Subjects $\cdot$ 60 Units $\cdot$ 35+ Proofs $\cdot$ 120+ Examples};
\end{tikzpicture}
\end{titlepage}

\tableofcontents
\newpage

"""

CHAPTERS = [
    ("00A_Prerequisites.md", "Prerequisites --- Class 12 Refresher"),
    ("00_MASTER_INDEX.md", "Study Roadmap \\& CSIR NET Guide"),
    ("09_Hit_Rate_Analysis.md", "Topic Hit-Rate Priority Analysis"),
    ("01_Advanced_Linear_Algebra.md", "Advanced Linear Algebra"),
    ("01B_Linear_Algebra_Deep_Proofs.md", "Linear Algebra --- Proofs \\& Problems"),
    ("02_Mathematical_Analysis.md", "Mathematical Analysis"),
    ("02B_Analysis_Deep_Proofs.md", "Analysis --- Proofs \\& Problems"),
    ("03_Topology.md", "Topology-1"),
    ("03B_Topology_Deep_Proofs.md", "Topology --- Proofs \\& Counterexamples"),
    ("04_Advanced_Complex_Analysis.md", "Advanced Complex Analysis"),
    ("04B_Complex_Analysis_Deep_Proofs.md", "Complex Analysis --- Proofs \\& Problems"),
    ("05_Advanced_Differential_Equations.md", "Advanced Differential Equations"),
    ("05B_ODE_Deep_Proofs.md", "Differential Equations --- Proofs \\& Problems"),
    ("06_Dynamics_of_Rigid_Body.md", "Dynamics of a Rigid Body"),
    ("06B_Dynamics_Deep_Proofs.md", "Dynamics --- Proofs \\& Problems"),
    ("07_CSIR_NET_Quick_Revision.md", "CSIR NET Quick Revision"),
    ("08_PYQ_Compilation.md", "Previous Year Questions --- Solved"),
    ("11_Gap_Filler_All_Missing_Proofs.md", "Additional Proofs \\& Gap Filler"),
]


def main():
    print("=" * 60)
    print("  Building Publication-Quality LaTeX Booklet")
    print("=" * 60)
    
    tex = PREAMBLE
    
    for filename, title in CHAPTERS:
        filepath = os.path.join(NOTES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP: {filename}")
            continue
        
        print(f"  Converting: {title}")
        with open(filepath, 'r', encoding='utf-8') as f:
            md_text = f.read()
        
        # Remove first H1
        md_text = re.sub(r'^# .+$', '', md_text, count=1, flags=re.MULTILINE)
        
        latex_body = md_to_latex(md_text)
        tex += f"\\chapter{{{title}}}\n"
        tex += latex_body + "\n\\newpage\n\n"
    
    tex += "\\end{document}\n"
    
    with open(OUTPUT_TEX, 'w', encoding='utf-8') as f:
        f.write(tex)
    print(f"\n  .tex written ({len(tex)} chars)")
    
    # Post-process: fix common LaTeX issues
    print("  Post-processing .tex...")
    with open(OUTPUT_TEX, 'r') as f:
        tex = f.read()
    
    # Fix unescaped # — only fix lines that aren't LaTeX commands
    # (skip \#, \chapter, etc.)
    lines_h = tex.split('\n')
    fixed_h = []
    for line in lines_h:
        if '\\#' not in line and '#' in line and not line.strip().startswith('\\'):
            line = line.replace('#', '\\#')
        fixed_h.append(line)
    tex = '\n'.join(fixed_h)
    
    # Fix enumerate ended by itemize
    tex = tex.replace('\\begin{enumerate}\n', '\\begin{itemize}\n')
    tex = tex.replace('\\begin{enumerate}', '\\begin{itemize}')
    
    # Fix \textbf spanning paragraphs
    for _ in range(20):
        tex = re.sub(r'(\\textbf\{[^}]{0,300}?)\n\n', r'\1}\n\n', tex, count=100)
        tex = re.sub(r'(\\textit\{[^}]{0,300}?)\n\n', r'\1}\n\n', tex, count=100)
    
    # Fix line-level brace balance
    lines = tex.split('\n')
    fixed = []
    for line in lines:
        o = line.count('{')
        c = line.count('}')
        if o > c:
            line += '}' * (o - c)
        fixed.append(line)
    tex = '\n'.join(fixed)
    
    # Fix odd dollar signs per line (outside verbatim)
    in_verb = False
    lines2 = tex.split('\n')
    fixed2 = []
    for line in lines2:
        if '\\begin{verbatim}' in line:
            in_verb = True
        elif '\\end{verbatim}' in line:
            in_verb = False
        if not in_verb and line.count('$') % 2 == 1:
            idx = line.rfind('$')
            line = line[:idx] + line[idx+1:]
        fixed2.append(line)
    tex = '\n'.join(fixed2)
    
    with open(OUTPUT_TEX, 'w') as f:
        f.write(tex)
    
    o = tex.count('{')
    c = tex.count('}')
    print(f"  Braces: {o} open, {c} close (diff={o-c}), $ signs: {tex.count('$')}")
    
    # Compile 2 passes - pipe empty enters to bypass error prompts
    for pass_num in [1, 2]:
        print(f"  xelatex pass {pass_num}...")
        result = subprocess.run(
            f'yes "" | xelatex -output-directory {NOTES_DIR} {OUTPUT_TEX}',
            shell=True, cwd=NOTES_DIR, capture_output=True, timeout=600
        )
    
    pdf_path = OUTPUT_TEX.replace('.tex', '.pdf')
    if os.path.exists(pdf_path):
        shutil.copy(pdf_path, OUTPUT_PDF)
        size_mb = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
        # Count pages
        try:
            info = subprocess.run(['pdfinfo', OUTPUT_PDF], capture_output=True, text=True)
            pages = [l for l in info.stdout.split('\n') if 'Pages' in l]
            page_info = pages[0] if pages else "?"
        except:
            page_info = "?"
        print(f"\n{'=' * 60}")
        print(f"  DONE: {OUTPUT_PDF}")
        print(f"  Size: {size_mb:.1f} MB | {page_info}")
        print(f"{'=' * 60}")
    else:
        print("\n  ERROR! Checking log for errors...")
        log_path = OUTPUT_TEX.replace('.tex', '.log')
        if os.path.exists(log_path):
            with open(log_path, encoding='latin-1') as f:
                for l in f:
                    if l.startswith('!'):
                        print(f"    {l.rstrip()}")


if __name__ == "__main__":
    main()
