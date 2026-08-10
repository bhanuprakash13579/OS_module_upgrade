#!/usr/bin/env python3
"""
Generate booklet with PROPER math rendering using matplotlib's LaTeX engine.
Converts LaTeX math expressions in markdown to SVG images embedded in HTML.
"""
import markdown
import re
import os
import io
import base64
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from weasyprint import HTML

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"
OUTPUT = os.path.expanduser("~/Desktop/MSc_Mathematics_Sem1_Complete_Booklet.pdf")
CACHE_DIR = os.path.join(NOTES_DIR, ".math_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# Math patterns to convert
MATH_REPLACEMENTS = [
    # Fractions
    (r'(\d+)/(\d+)', r'$\\frac{\1}{\2}$'),
    (r'ML²/(\d+)', r'$\\frac{ML^2}{\1}$'),
    (r'MR²/(\d+)', r'$\\frac{MR^2}{\1}$'),
    (r'(\w+)²/(\d+)', r'$\\frac{\1^2}{\2}$'),
    # Square roots
    (r'√\(([^)]+)\)', r'$\\sqrt{\1}$'),
    (r'√(\d+)', r'$\\sqrt{\1}$'),
    # Greek
    (r'(?<!\w)α(?!\w)', r'$\\alpha$'),
    (r'(?<!\w)β(?!\w)', r'$\\beta$'),
    (r'(?<!\w)λ(?!\w)', r'$\\lambda$'),
    (r'(?<!\w)ω(?!\w)', r'$\\omega$'),
    (r'(?<!\w)θ(?!\w)', r'$\\theta$'),
    (r'(?<!\w)π(?!\w)', r'$\\pi$'),
    (r'(?<!\w)ε(?!\w)', r'$\\varepsilon$'),
    (r'(?<!\w)δ(?!\w)', r'$\\delta$'),
    (r'(?<!\w)τ(?!\w)', r'$\\tau$'),
    (r'(?<!\w)ρ(?!\w)', r'$\\rho$'),
    (r'(?<!\w)φ(?!\w)', r'$\\varphi$'),
    (r'(?<!\w)Σ', r'$\\Sigma$'),
    (r'(?<!\w)Π', r'$\\Pi$'),
    (r'(?<!\w)Γ', r'$\\Gamma$'),
    # Symbols
    (r'∈', r'$\\in$'),
    (r'∉', r'$\\notin$'),
    (r'⊂', r'$\\subset$'),
    (r'⊆', r'$\\subseteq$'),
    (r'∪', r'$\\cup$'),
    (r'∩', r'$\\cap$'),
    (r'∅', r'$\\emptyset$'),
    (r'∀', r'$\\forall$'),
    (r'∃', r'$\\exists$'),
    (r'⟹', r'$\\Longrightarrow$'),
    (r'⟺', r'$\\Longleftrightarrow$'),
    (r'→', r'$\\to$'),
    (r'←', r'$\\leftarrow$'),
    (r'≤', r'$\\leq$'),
    (r'≥', r'$\\geq$'),
    (r'≠', r'$\\neq$'),
    (r'≈', r'$\\approx$'),
    (r'∞', r'$\\infty$'),
    (r'∎', r'$\\blacksquare$'),
    (r'ℝ', r'$\\mathbb{R}$'),
    (r'ℂ', r'$\\mathbb{C}$'),
    (r'ℚ', r'$\\mathbb{Q}$'),
    (r'ℤ', r'$\\mathbb{Z}$'),
    (r'ℕ', r'$\\mathbb{N}$'),
    # Superscripts
    (r'²', r'$^2$'),
    (r'³', r'$^3$'),
    (r'ⁿ', r'$^n$'),
    # Operators
    (r'∂', r'$\\partial$'),
    (r'∇', r'$\\nabla$'),
    (r'×', r'$\\times$'),
    # Integrals
    (r'∫', r'$\\int$'),
]


def latex_to_img_tag(latex_str, fontsize=12):
    """Render a LaTeX math string to a base64-encoded PNG <img> tag."""
    cache_key = hashlib.md5((latex_str + str(fontsize)).encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.png")
    
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            img_data = f.read()
    else:
        try:
            fig, ax = plt.subplots(figsize=(0.01, 0.01))
            ax.axis('off')
            fig.patch.set_alpha(0)
            text = ax.text(0, 0, latex_str, fontsize=fontsize,
                          ha='left', va='baseline',
                          transform=ax.transAxes)
            
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=150, 
                       bbox_inches='tight', pad_inches=0.02,
                       transparent=True)
            plt.close(fig)
            img_data = buf.getvalue()
            
            with open(cache_path, 'wb') as f:
                f.write(img_data)
        except Exception as e:
            return latex_str  # fallback to text
    
    b64 = base64.b64encode(img_data).decode()
    return f'<img src="data:image/png;base64,{b64}" style="vertical-align:middle;height:1.2em;" />'


def render_inline_math(html_text):
    """Find $...$ patterns and render them as images."""
    def replace_math(m):
        latex = m.group(1)
        return latex_to_img_tag(f'${latex}$')
    
    # Don't process inside <pre> or <code>
    parts = re.split(r'(<pre>.*?</pre>|<code>.*?</code>)', html_text, flags=re.DOTALL)
    result = []
    for part in parts:
        if part.startswith('<pre>') or part.startswith('<code>'):
            result.append(part)
        else:
            result.append(re.sub(r'\$([^$]+)\$', replace_math, part))
    return ''.join(result)


print("Testing math rendering...")
test = latex_to_img_tag(r'$\frac{ML^2}{12}$')
if '<img' in test:
    print("  ✅ Math rendering works!")
else:
    print("  ❌ Math rendering failed, will use text fallback")
    
print(f"  Cache dir: {CACHE_DIR}")
print("Math engine ready.\n")
print("NOTE: This script provides the math engine.")
print("The full booklet generator will use this for proper math.")
