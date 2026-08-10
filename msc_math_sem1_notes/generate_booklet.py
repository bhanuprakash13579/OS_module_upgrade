#!/usr/bin/env python3
"""Generate a single booklet PDF with cover page and table of contents."""

import markdown
import os
import re
import sys
from weasyprint import HTML
sys.path.insert(0, os.path.dirname(__file__))
from math_engine import render_inline_math, MATH_REPLACEMENTS

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"
OUTPUT = os.path.expanduser("~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf")

# Ordered list of all content files
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
    ("07_CSIR_NET_Quick_Revision.md", "CSIR NET Quick Revision Flash Cards"),
    ("08_PYQ_Compilation.md", "Previous Year Questions — Solved"),
    ("11_Gap_Filler_All_Missing_Proofs.md", "Additional Proofs & Gap Filler"),
]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&family=JetBrains+Mono&display=swap');

@page {
    size: A4;
    margin: 2cm 1.8cm 2.5cm 1.8cm;
    @bottom-center { 
        content: counter(page); 
        font-family: 'Inter', sans-serif;
        font-size: 10px; 
        color: #888; 
    }
    @top-right { 
        content: string(chaptertitle); 
        font-family: 'Inter', sans-serif;
        font-size: 8px; 
        color: #aaa;
        font-style: italic;
    }
}

@page :first {
    margin: 0;
    @bottom-center { content: none; }
    @top-right { content: none; }
}

@page cover {
    margin: 0;
    @bottom-center { content: none; }
    @top-right { content: none; }
}

@page toc {
    @top-right { content: "Table of Contents"; }
}

body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 10.5pt;
    line-height: 1.6;
    color: #1a1a2e;
}

/* COVER PAGE */
.cover-page {
    page: cover;
    width: 210mm;
    height: 297mm;
    background-color: #1a1a4e;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: #ffffff;
    page-break-after: always;
}

.cover-page .icon { font-size: 60pt; margin-bottom: 20px; }
.cover-page h1 { 
    font-size: 32pt; 
    font-weight: 800; 
    margin: 10px 40px;
    line-height: 1.2;
    letter-spacing: -0.5px;
    color: #ffffff;
    border-bottom: none;
}
.cover-page .subtitle { 
    font-size: 16pt; 
    font-weight: 300; 
    margin: 15px 40px;
    color: #e0e0ff;
    border-top: 2px solid #6666aa;
    border-bottom: 2px solid #6666aa;
    padding: 12px 0;
}
.cover-page .university { 
    font-size: 13pt; 
    margin-top: 30px; 
    color: #b0b0dd;
    font-weight: 300;
}
.cover-page .goal {
    font-size: 11pt;
    margin-top: 8px;
    color: #9999cc;
    font-style: italic;
}
.cover-page .badge {
    margin-top: 40px;
    background-color: #2d2b70;
    border: 1px solid #6666aa;
    border-radius: 30px;
    padding: 8px 24px;
    font-size: 10pt;
    font-weight: 600;
    letter-spacing: 1px;
    color: #ffffff;
}
.cover-page .contains {
    margin-top: 40px;
    font-size: 9pt;
    color: #8888bb;
    font-weight: 300;
}

/* TABLE OF CONTENTS */
.toc-page {
    page: toc;
    page-break-after: always;
}
.toc-page h2 {
    font-size: 20pt;
    color: #1a1a6e;
    border-bottom: 3px solid #4a47a3;
    padding-bottom: 8px;
    margin-bottom: 20px;
}
.toc-item {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 6px 0;
    border-bottom: 1px dotted #ddd;
    font-size: 10.5pt;
}
.toc-item.section {
    font-weight: 700;
    color: #2d2b55;
    font-size: 12pt;
    margin-top: 14px;
    border-bottom: 2px solid #e0e0f0;
    padding-bottom: 4px;
}
.toc-item .num { 
    color: #4a47a3; 
    font-weight: 600;
    min-width: 30px;
}
.toc-item .dots {
    flex: 1;
    border-bottom: 1px dotted #ccc;
    margin: 0 8px;
    min-width: 20px;
}

/* CHAPTER HEADERS */
.chapter-break {
    page-break-before: always;
    margin-top: 0;
}

h1 {
    font-size: 20pt;
    color: #1a1a6e;
    border-bottom: 3px solid #4a47a3;
    padding-bottom: 8px;
    margin-top: 10px;
    margin-bottom: 15px;
    string-set: chaptertitle content();
    page-break-after: avoid;
}
h2 {
    font-size: 14pt;
    color: #2d2b55;
    margin-top: 22px;
    margin-bottom: 8px;
    border-left: 4px solid #667eea;
    padding-left: 10px;
    page-break-after: avoid;
}
h3 {
    font-size: 12pt;
    color: #4a47a3;
    margin-top: 16px;
    margin-bottom: 6px;
    page-break-after: avoid;
}
h4 { font-size: 11pt; color: #555; margin-top: 12px; page-break-after: avoid; }

p { margin: 5px 0; text-align: justify; }
strong { color: #1a1a4e; }

code {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 9pt;
    background: #f0f0f8;
    padding: 1px 4px;
    border-radius: 3px;
    color: #c7254e;
}

pre {
    background: #f5f5ff;
    border: 1px solid #ddd;
    border-left: 4px solid #667eea;
    border-radius: 5px;
    padding: 10px 14px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 8.5pt;
    line-height: 1.45;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    page-break-inside: avoid;
    margin: 8px 0;
}
pre code { background: none; padding: 0; color: #333; }

blockquote {
    background: #f0f4ff;
    border-left: 4px solid #667eea;
    padding: 8px 14px;
    margin: 10px 0;
    border-radius: 0 6px 6px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}
th {
    background: #2d2b55;
    color: white;
    padding: 6px 8px;
    text-align: left;
    font-weight: 600;
    font-size: 9pt;
}
td { padding: 5px 8px; border-bottom: 1px solid #e0e0e0; }
tr:nth-child(even) { background: #f8f8fc; }

hr { border: none; border-top: 2px solid #e0e0f0; margin: 18px 0; }
ul, ol { margin: 5px 0 5px 18px; }
li { margin: 2px 0; }
a { color: #4a47a3; text-decoration: none; }

/* Mathematical fraction styling */
.frac {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    vertical-align: middle;
    margin: 0 2px;
    font-size: 0.85em;
}
.frac .num {
    border-bottom: 1.5px solid #1a1a2e;
    padding: 0 4px 1px 4px;
    line-height: 1.2;
}
.frac .den {
    padding: 1px 4px 0 4px;
    line-height: 1.2;
}
"""

COVER = """
<div class="cover-page">
    <div class="icon">📚</div>
    <h1>MSc Mathematics<br>Semester 1</h1>
    <div class="subtitle">Complete Study Notes & Exam Preparation Guide</div>
    <div class="university">Manipal University Jaipur — Online Education</div>
    <div class="goal">Prepared for CSIR NET Qualification & Assistant Professorship</div>
    <div class="badge">SEMESTER 1 • ALL 6 SUBJECTS • 60 UNITS</div>
    <div class="contains">
        6 Subjects · 35+ Proofs · 120+ Examples · 80+ Practice Problems · 28 Solved PYQs
    </div>
</div>
"""


def build_toc():
    html = '<div class="toc-page"><h2>Table of Contents</h2>\n'

    # Foundation
    html += '<div class="toc-item section"><span>Foundation</span></div>\n'
    html += '<div class="toc-item"><span class="num">0</span> Prerequisites — Class 12 Refresher &amp; Foundations<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">I</span> Study Roadmap &amp; CSIR NET Guide<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">II</span> Topic Hit-Rate Priority Analysis<span class="dots"></span></div>\n'

    # Subject 1
    html += '<div class="toc-item section"><span>Subject 1 — Advanced Linear Algebra</span></div>\n'
    la_units = [
        "Unit 1 — Linear Transformations",
        "Unit 2 — Linear Transformations and Vector Spaces",
        "Unit 3 — Dual Basis, Annihilators and Transformations",
        "Unit 4 — Inner-Product Spaces",
        "Unit 5 — Orthonormal Systems and Orthogonal Transformations",
        "Unit 6 — Inner Product Space Isomorphism",
        "Unit 7 — Algebra of HOM(V,V)",
        "Unit 8 — Diagonalization of Matrices and Invariant Subspaces",
        "Unit 9 — Cayley-Hamilton Theorem, Canonical Form, Jordan Form",
        "Unit 10 — Forms on Vector Spaces",
    ]
    for u in la_units:
        html += f'<div class="toc-item"><span class="num">&nbsp;</span> {u}<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">+</span> Linear Algebra — Proofs &amp; Extended Problems<span class="dots"></span></div>\n'

    # Subject 2
    html += '<div class="toc-item section"><span>Subject 2 — Mathematical Analysis</span></div>\n'
    an_units = [
        "Unit 1 — Introduction to the Riemann-Stieltjes Integral - I",
        "Unit 2 — Introduction to the Riemann-Stieltjes Integral - II",
        "Unit 3 — Uniform Convergence - I",
        "Unit 4 — Uniform Convergence - II",
        "Unit 5 — Approximation and Convergence Theorems",
        "Unit 6 — Calculus of Functions of Several Variables - I",
        "Unit 7 — Calculus of Functions of Several Variables - II",
        "Unit 8 — Explicit and Implicit Functions and Applications",
        "Unit 9 — Extrema of Functions of Several Variables",
        "Unit 10 — Jacobian and Its Properties",
    ]
    for u in an_units:
        html += f'<div class="toc-item"><span class="num">&nbsp;</span> {u}<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">+</span> Analysis — Proofs &amp; Extended Problems<span class="dots"></span></div>\n'

    # Subject 3
    html += '<div class="toc-item section"><span>Subject 3 — Topology-1</span></div>\n'
    tp_units = [
        "Unit 1 — Basic Concepts",
        "Unit 2 — Open and Closed Sets",
        "Unit 3 — Boundary of a Set",
        "Unit 4 — Constructing Topologies",
        "Unit 5 — Topological Maps with Neighbourhood Bases and Connectedness",
        "Unit 6 — Connected Spaces",
        "Unit 7 — Compactness",
        "Unit 8 — Compact Spaces",
        "Unit 9 — Separation Axioms",
        "Unit 10 — Separable and Second Countable Spaces",
    ]
    for u in tp_units:
        html += f'<div class="toc-item"><span class="num">&nbsp;</span> {u}<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">+</span> Topology — Proofs &amp; Counterexamples<span class="dots"></span></div>\n'

    # Subject 4
    html += '<div class="toc-item section"><span>Subject 4 — Advanced Complex Analysis</span></div>\n'
    ca_units = [
        "Unit 1 — Integral Functions",
        "Unit 2 — Special Functions and Fundamental Theorems",
        "Unit 3 — Analytic Continuation",
        "Unit 4 — Advanced Topics in Complex Analysis and Harmonic Functions",
        "Unit 5 — Harnack Inequality, Harnack Theorem, Dirichlet Region, Green Function",
        "Unit 6 — Canonical Product, Jensen Formula, Poisson-Jensen Formula",
        "Unit 7 — Hadamard Three Circles Theorem",
        "Unit 8 — Borel Theorem, Hadamard Factorisation Theorem, Range of Analytic Function",
        "Unit 9 — Bloch Theorem, Schottky Theorem, Little Picard Theorem",
        "Unit 10 — Advanced Topics in Analytic and Univalent Function Theory",
    ]
    for u in ca_units:
        html += f'<div class="toc-item"><span class="num">&nbsp;</span> {u}<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">+</span> Complex Analysis — Proofs &amp; Extended Problems<span class="dots"></span></div>\n'

    # Subject 5
    html += '<div class="toc-item section"><span>Subject 5 — Advanced Differential Equations</span></div>\n'
    ode_units = [
        "Unit 1 — ε-Approximate Solutions",
        "Unit 2 — Basic Theorems (Existence and Uniqueness)",
        "Unit 3 — Systems of Differential Equations",
        "Unit 4 — Solution of System of Differential Equations",
        "Unit 5 — Nonlinear Differential Systems",
        "Unit 6 — Poincaré-Bendixson Theory",
        "Unit 7 — Critical Points, Stability Classification, and Lyapunov Methods",
        "Unit 8 — Paths of Linear Systems",
        "Unit 9 — Dependence on Parameters",
        "Unit 10 — Poincaré-Bendixson Theorem (Detailed)",
    ]
    for u in ode_units:
        html += f'<div class="toc-item"><span class="num">&nbsp;</span> {u}<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">+</span> Differential Equations — Proofs &amp; Extended Problems<span class="dots"></span></div>\n'

    # Subject 6
    html += '<div class="toc-item section"><span>Subject 6 — Dynamics of a Rigid Body</span></div>\n'
    dy_units = [
        "Unit 1 — Moments and Products of Inertia",
        "Unit 2 — Special Cases and Theorems",
        "Unit 3 — D'Alembert's Principle and Particle Motion",
        "Unit 4 — Angular Momentum and Equations of Motion",
        "Unit 5 — Motion Under Impulsive Forces",
        "Unit 6 — Motion About a Fixed Axis",
        "Unit 7 — Rotational Dynamics",
        "Unit 8 — Motion in Two Dimensions",
        "Unit 9 — Impulsive Forces in Two Dimensions",
        "Unit 10 — Conservation Principles and Initial Motion",
    ]
    for u in dy_units:
        html += f'<div class="toc-item"><span class="num">&nbsp;</span> {u}<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">+</span> Dynamics — Proofs &amp; Solved Problems<span class="dots"></span></div>\n'

    # Exam Prep
    html += '<div class="toc-item section"><span>Exam Preparation</span></div>\n'
    html += '<div class="toc-item"><span class="num">XV</span> CSIR NET Quick Revision Flash Cards<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">XVI</span> Previous Year Questions — Solved<span class="dots"></span></div>\n'
    html += '<div class="toc-item"><span class="num">XVII</span> Additional Proofs &amp; Gap Filler<span class="dots"></span></div>\n'

    html += "</div>"
    return html


def convert_fractions(html_text):
    """Convert common math fraction patterns to proper HTML fractions."""
    import re
    # Match patterns like: word/word, number/number, expression/expression
    # but NOT inside URLs, file paths, or code blocks
    # Pattern: something/something where both sides are math-like
    def frac_replace(m):
        num = m.group(1)
        den = m.group(2)
        return f'<span class="frac"><span class="num">{num}</span><span class="den">{den}</span></span>'
    
    # Split on <pre> and <code> to avoid converting fractions inside code blocks
    parts = re.split(r'(<pre>.*?</pre>|<code>.*?</code>)', html_text, flags=re.DOTALL)
    result = []
    for i, part in enumerate(parts):
        if part.startswith('<pre>') or part.startswith('<code>'):
            result.append(part)
        else:
            # Convert common fraction patterns (be conservative)
            # Pattern: (math_expr)/(math_expr) — things like ML²/12, MR²/2, etc
            converted = re.sub(
                r'(?<![<a-zA-Z/])(\b\d+(?:[a-zA-Z²³⁴⁵ⁿ]*)?)\s*/\s*(\d+(?:[a-zA-Z²³⁴⁵ⁿ]*)?)\b',
                frac_replace, part
            )
            # Also convert patterns like (expression)/(expression)
            converted = re.sub(
                r'\(([^()]+)\)\s*/\s*\(([^()]+)\)',
                lambda m: f'<span class="frac"><span class="num">{m.group(1)}</span><span class="den">{m.group(2)}</span></span>',
                converted
            )
            result.append(converted)
    return ''.join(result)


def preprocess_math(md_text):
    """Convert Unicode math symbols to LaTeX $...$ notation before markdown parsing."""
    # Don't convert inside code blocks
    lines = md_text.split('\n')
    in_code = False
    result = []
    for line in lines:
        if line.strip().startswith('```'):
            in_code = not in_code
            result.append(line)
            continue
        if in_code:
            result.append(line)
            continue
        # Apply math replacements
        for pattern, replacement in MATH_REPLACEMENTS:
            try:
                line = re.sub(pattern, replacement, line)
            except:
                pass
        result.append(line)
    return '\n'.join(result)


def md_to_html_body(md_path, chapter_title):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    # Convert Unicode math to LaTeX
    md_text = preprocess_math(md_text)
    extensions = ["tables", "fenced_code", "sane_lists"]
    body = markdown.markdown(md_text, extensions=extensions)
    # Render LaTeX math as images
    body = render_inline_math(body)
    return f'<div class="chapter-break"><h1>{chapter_title}</h1>\n{body}\n</div>'


def main():
    print("Building booklet...")

    # Assemble full HTML
    chapters_html = ""
    for filename, title in CHAPTERS:
        path = os.path.join(NOTES_DIR, filename)
        if os.path.exists(path):
            print(f"  Adding: {title}")
            chapters_html += md_to_html_body(path, title)
        else:
            print(f"  SKIP: {filename}")

    toc = build_toc()

    full_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>
{COVER}
{toc}
{chapters_html}
</body></html>"""

    print("  Generating PDF (this may take a minute)...")
    HTML(string=full_html).write_pdf(OUTPUT)

    size_mb = os.path.getsize(OUTPUT) / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"  ✅ Booklet generated: {OUTPUT}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
