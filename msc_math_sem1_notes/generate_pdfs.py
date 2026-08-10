#!/usr/bin/env python3
"""Convert MSc Math study notes from Markdown to beautifully styled PDFs."""

import markdown
import os
import re
from weasyprint import HTML

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"
OUTPUT_DIR = os.path.expanduser("~/Desktop/MSc_Mathematics_Sem1_Notes")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono&display=swap');

@page {
    size: A4;
    margin: 2cm 1.8cm;
    @bottom-center { content: counter(page); font-size: 10px; color: #888; }
    @top-right { content: string(doctitle); font-size: 9px; color: #aaa; }
}

body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #1a1a2e;
    max-width: 100%;
}

h1 {
    font-size: 22pt;
    color: #1a1a6e;
    border-bottom: 3px solid #4a47a3;
    padding-bottom: 8px;
    margin-top: 30px;
    margin-bottom: 15px;
    string-set: doctitle content();
    page-break-after: avoid;
}

h2 {
    font-size: 16pt;
    color: #2d2b55;
    margin-top: 25px;
    margin-bottom: 10px;
    border-left: 4px solid #667eea;
    padding-left: 12px;
    page-break-after: avoid;
}

h3 {
    font-size: 13pt;
    color: #4a47a3;
    margin-top: 18px;
    margin-bottom: 8px;
    page-break-after: avoid;
}

h4 { font-size: 11.5pt; color: #555; margin-top: 14px; page-break-after: avoid; }

p { margin: 6px 0; text-align: justify; }

strong { color: #1a1a4e; }

em { color: #555; }

code {
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 9.5pt;
    background: #f0f0f8;
    padding: 1px 5px;
    border-radius: 3px;
    color: #c7254e;
}

pre {
    background: #f5f5ff;
    border: 1px solid #ddd;
    border-left: 4px solid #667eea;
    border-radius: 6px;
    padding: 12px 16px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 9pt;
    line-height: 1.5;
    overflow-wrap: break-word;
    white-space: pre-wrap;
    page-break-inside: avoid;
    margin: 10px 0;
}

pre code {
    background: none;
    padding: 0;
    color: #333;
}

blockquote {
    background: #f0f4ff;
    border-left: 4px solid #667eea;
    padding: 10px 16px;
    margin: 12px 0;
    border-radius: 0 8px 8px 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

th {
    background: #2d2b55;
    color: white;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
}

td {
    padding: 7px 10px;
    border-bottom: 1px solid #e0e0e0;
}

tr:nth-child(even) { background: #f8f8fc; }

hr {
    border: none;
    border-top: 2px solid #e0e0f0;
    margin: 20px 0;
}

ul, ol {
    margin: 6px 0 6px 20px;
}

li {
    margin: 3px 0;
}

/* Emoji visual markers */
a { color: #4a47a3; text-decoration: none; }
"""


def md_to_html(md_text):
    """Convert markdown text to HTML with extensions."""
    extensions = ['tables', 'fenced_code', 'nl2br', 'sane_lists']
    html_body = markdown.markdown(md_text, extensions=extensions)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{html_body}</body></html>"""


def convert_file(md_path, pdf_path):
    """Convert a single markdown file to PDF."""
    print(f"  Converting: {os.path.basename(md_path)}")
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    html_content = md_to_html(md_text)
    HTML(string=html_content).write_pdf(pdf_path)
    
    size_kb = os.path.getsize(pdf_path) / 1024
    print(f"    -> {os.path.basename(pdf_path)} ({size_kb:.0f} KB)")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    files = [
        ("00_MASTER_INDEX.md", "00_Study_Roadmap.pdf"),
        ("01_Advanced_Linear_Algebra.md", "01_Advanced_Linear_Algebra.pdf"),
        ("02_Mathematical_Analysis.md", "02_Mathematical_Analysis.pdf"),
        ("03_Topology.md", "03_Topology.pdf"),
        ("04_Advanced_Complex_Analysis.md", "04_Advanced_Complex_Analysis.pdf"),
        ("05_Advanced_Differential_Equations.md", "05_Advanced_Differential_Equations.pdf"),
        ("06_Dynamics_of_Rigid_Body.md", "06_Dynamics_of_Rigid_Body.pdf"),
        ("07_CSIR_NET_Quick_Revision.md", "07_CSIR_NET_Quick_Revision.pdf"),
        ("08_PYQ_Compilation.md", "08_PYQ_Compilation.pdf"),
    ]
    
    print(f"\n{'='*60}")
    print(f"  MSc Mathematics Sem 1 — PDF Generation")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}\n")
    
    for md_name, pdf_name in files:
        md_path = os.path.join(NOTES_DIR, md_name)
        pdf_path = os.path.join(OUTPUT_DIR, pdf_name)
        if os.path.exists(md_path):
            convert_file(md_path, pdf_path)
        else:
            print(f"  SKIP (not found): {md_name}")
    
    # Also convert the HTML visual aids
    html_path = os.path.join(NOTES_DIR, "visual_study_aids.html")
    if os.path.exists(html_path):
        print(f"  Converting: visual_study_aids.html")
        pdf_path = os.path.join(OUTPUT_DIR, "09_Visual_Study_Aids.pdf")
        HTML(filename=html_path).write_pdf(pdf_path)
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"    -> 09_Visual_Study_Aids.pdf ({size_kb:.0f} KB)")
    
    print(f"\n{'='*60}")
    print(f"  ✅ All PDFs generated at: {OUTPUT_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
