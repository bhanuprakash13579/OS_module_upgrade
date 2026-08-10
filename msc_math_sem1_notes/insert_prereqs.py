#!/usr/bin/env python3
"""Insert prerequisite boxes at the start of each unit in all subject files."""
import re, os

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"

# Prerequisites for every unit across all 6 subjects
PREREQS = {
    "01_Advanced_Linear_Algebra.md": {
        1: "**What you need:** Matrices (addition, multiplication), determinants, solving Ax = b (Gaussian elimination), basic idea of vectors in ℝ² and ℝ³.",
        2: "**What you need:** Unit 1 concepts (linear transformations, matrix representation). Know what a basis is and how to express vectors as coordinates.",
        3: "**What you need:** Units 1-2. Understand basis, dimension, and linear functionals (a function that maps vectors to numbers, like f(v) = 2v₁ + 3v₂).",
        4: "**What you need:** Dot product from Class 12 (u·v = u₁v₁ + u₂v₂), concept of length/angle, Pythagoras theorem. Think of inner product as a generalized dot product.",
        5: "**What you need:** Unit 4 (inner products). Remember: two vectors are orthogonal if their dot product = 0. Normalization means dividing by length.",
        6: "**What you need:** Units 4-5. Know what an isomorphism is: a bijective linear map that preserves structure (like a perfect translation between two languages).",
        7: "**What you need:** Units 1-2, polynomials from Class 12. The key idea: a linear transformation T can be plugged into a polynomial, e.g., T² - 3T + 2I.",
        8: "**What you need:** Eigenvalues from basics — if Av = λv, then λ is an eigenvalue and v is an eigenvector. Characteristic polynomial: det(A - λI) = 0. Practice: find eigenvalues of [[2,1],[0,3]].",
        9: "**What you need:** Units 7-8 (eigenvalues, minimal polynomial). Cayley-Hamilton says: plug the matrix into its own characteristic polynomial and you get zero. Jordan form handles non-diagonalizable cases.",
        10: "**What you need:** Unit 4 (inner products). A quadratic form is Q(x) = xᵀAx — it generalizes ax² + bxy + cy² from Class 12 conics.",
    },
    "02_Mathematical_Analysis.md": {
        1: "**What you need:** Definite integrals from Class 12 (∫ₐᵇ f(x)dx), Riemann sums (adding up areas of rectangles). The Stieltjes integral generalizes this by integrating 'with respect to' another function α(x) instead of just x.",
        2: "**What you need:** Unit 1 concepts. Integration by parts from Class 12: ∫u dv = uv - ∫v du. Here we extend this to Stieltjes integrals.",
        3: "**What you need:** Sequences and series from Class 12, concept of convergence (aₙ → L). Pointwise convergence means checking limit at each individual point x.",
        4: "**What you need:** Unit 3. The key distinction: uniform convergence means the ENTIRE function converges at the same rate everywhere, not just point by point.",
        5: "**What you need:** Units 3-4. Continuous functions on [a,b], polynomials. Stone-Weierstrass says: continuous functions can be approximated by polynomials.",
        6: "**What you need:** Single-variable calculus (derivatives, partial derivatives). f(x,y) is a function of TWO variables. Partial derivative ∂f/∂x = differentiate treating y as constant.",
        7: "**What you need:** Unit 6, chain rule from Class 12. Here: chain rule for f(g(t), h(t)) gives df/dt = (∂f/∂x)(dx/dt) + (∂f/∂y)(dy/dt).",
        8: "**What you need:** Units 6-7. Implicit functions: given F(x,y) = 0, can you solve for y = g(x)? Example: x² + y² = 1 implicitly defines y = ±√(1-x²).",
        9: "**What you need:** Finding max/min from Class 12 (set derivative = 0). Here we do it for f(x,y) — set both ∂f/∂x = 0 and ∂f/∂y = 0, then use the second derivative test.",
        10: "**What you need:** Determinants, partial derivatives. Jacobian = determinant of the matrix of all partial derivatives. It measures how a transformation stretches/shrinks areas.",
    },
    "03_Topology.md": {
        1: "**What you need:** Sets (∪, ∩, complement), functions, open intervals (a,b) vs closed intervals [a,b] from Class 12. Topology generalizes the idea of 'nearness' without needing distances.",
        2: "**What you need:** Unit 1. Recall from calculus: (0,1) is open because every point has room around it; [0,1] is closed because it contains its boundary. We now define this abstractly.",
        3: "**What you need:** Units 1-2. Boundary points are those that are 'on the edge' — every neighborhood contains points both inside AND outside the set.",
        4: "**What you need:** Units 1-3. Basis/subbasis generate a topology like how a few vectors generate a vector space. Product topology is defined on X×Y.",
        5: "**What you need:** Continuous functions from calculus (no jumps). In topology: f is continuous if the preimage of every open set is open. Homeomorphism = continuous bijection with continuous inverse.",
        6: "**What you need:** Unit 5, intervals from ℝ. Connected = cannot be split into two separate open pieces. Intuition: a connected set is 'one piece.'",
        7: "**What you need:** Sequences, convergence, open covers. Compact ≈ 'finite-like' behavior. In ℝⁿ: compact = closed + bounded (Heine-Borel).",
        8: "**What you need:** Unit 7. This unit explores consequences: continuous functions on compact sets attain max/min, compact + Hausdorff = nice properties.",
        9: "**What you need:** Units 1-2. Separation axioms measure 'how well' points and sets can be separated by open sets. T₂ (Hausdorff) = distinct points have disjoint neighborhoods.",
        10: "**What you need:** Countable sets (ℚ is countable, ℝ is not). Separable = has a countable dense subset. Second countable = has a countable basis.",
    },
    "04_Advanced_Complex_Analysis.md": {
        1: "**What you need:** Complex numbers (z = a + bi, |z|, e^(iθ)), analytic functions (Cauchy-Riemann equations), Taylor series. An entire function is analytic EVERYWHERE in ℂ.",
        2: "**What you need:** Unit 1, Gamma function Γ(n) = (n-1)! for integers, and Riemann zeta function ζ(s) = Σ1/nˢ.",
        3: "**What you need:** Power series, radius of convergence. Analytic continuation extends a function beyond its original domain — like extending √x from [0,∞) to ℂ.",
        4: "**What you need:** Units 1-3, Laplace equation (∇²u = 0). Harmonic functions are the real/imaginary parts of analytic functions.",
        5: "**What you need:** Unit 4 (harmonic functions), mean value property, maximum principle.",
        6: "**What you need:** Unit 1 (entire functions, zeros). Infinite products: f(z) = Π(1 - z/aₙ) constructs a function with prescribed zeros.",
        7: "**What you need:** Units 1, 6. log M(r) where M(r) = max|f(z)| on |z|=r. The theorem relates values on three concentric circles.",
        8: "**What you need:** Units 1, 6-7. Order/type of entire functions, canonical products. Hadamard factorization = complete structure theorem.",
        9: "**What you need:** Units 1, 8. Liouville's theorem (bounded entire = constant). Picard goes further: entire functions can omit at MOST one value.",
        10: "**What you need:** Unit 1, Schwarz lemma, conformal mappings. Univalent = injective analytic. Bieberbach conjecture / de Branges theorem.",
    },
    "05_Advanced_Differential_Equations.md": {
        1: "**What you need:** Basic ODEs from BSc (y' = f(x,y), separation of variables, integrating factors). ε-approximate solutions are 'almost solutions' with small error.",
        2: "**What you need:** Unit 1, sequences, fixed point idea. Picard's theorem: if f is 'nice enough' (Lipschitz), then y' = f(t,y) has exactly one solution. This is the most important theorem in ODE.",
        3: "**What you need:** Matrices, vectors. A system: x' = Ax where x is a vector and A is a matrix. This is like having multiple ODEs coupled together.",
        4: "**What you need:** Units 2-3, eigenvalues of matrices, matrix exponential. Solution: x(t) = e^(At)x₀ where e^(At) = I + At + A²t²/2! + ...",
        5: "**What you need:** Units 1-4. Nonlinear means f(x) is not just Ax. Linearization: approximate near equilibrium by Taylor expansion.",
        6: "**What you need:** Unit 5, closed curves in ℝ². Poincaré-Bendixson: in 2D, bounded orbits must approach either an equilibrium or a periodic orbit.",
        7: "**What you need:** Eigenvalues, quadratic forms (positive definite). Stability: does a solution return to equilibrium after a small push? Lyapunov's method: find an 'energy function' V that decreases.",
        8: "**What you need:** Units 4, 7. Phase portraits of linear systems: eigenvalues determine whether trajectories spiral, converge, or diverge.",
        9: "**What you need:** Units 2-4. How do solutions change when you slightly change a parameter in the equation? Continuity and differentiability with respect to parameters.",
        10: "**What you need:** Units 5-6. Full proof and applications of the Poincaré-Bendixson theorem. Key tool for proving existence of limit cycles.",
    },
    "06_Dynamics_of_Rigid_Body.md": {
        1: "**What you need:** Mass, center of mass, integration. Moment of inertia I = ∫r²dm measures resistance to rotation, just like mass measures resistance to linear acceleration.",
        2: "**What you need:** Unit 1. Parallel axis theorem: I = I_cm + Md². Perpendicular axis theorem (for flat bodies): I_z = I_x + I_y.",
        3: "**What you need:** Newton's laws (F = ma), concept of virtual work from physics. D'Alembert's key idea: treat (F - ma) as zero, then use statics methods.",
        4: "**What you need:** Units 1-3, cross product (a × b), angular velocity ω. Angular momentum L = Iω. Euler's equations govern rotation of 3D bodies.",
        5: "**What you need:** Impulse = Force × time = change in momentum (from Class 12 physics). For rigid bodies: impulsive torque = change in angular momentum.",
        6: "**What you need:** Units 1-2, 4. Fixed axis means body can only rotate around one line (like a door on hinges). Equation: Iα = τ.",
        7: "**What you need:** Units 1-6. Rolling = translation + rotation. No-slip condition: v = Rω. Energy splits into translational (½mv²) + rotational (½Iω²).",
        8: "**What you need:** Units 1-7. Three equations: M·ẍ = ΣFx, M·ÿ = ΣFy, I·θ̈ = ΣN. Plus constraints (e.g., rolling).",
        9: "**What you need:** Units 5, 8. Combining impulsive forces with 2D rigid body motion. Both linear and angular impulse-momentum equations needed.",
        10: "**What you need:** Energy conservation (T + V = const), momentum conservation (no external force), angular momentum conservation (no external torque).",
    },
}

def insert_prereqs(filepath, unit_prereqs):
    """Insert prerequisite boxes after each UNIT heading."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for unit_num, prereq_text in unit_prereqs.items():
        # Match "# UNIT X:" or "# Unit X:" patterns
        pattern = rf'(# UNIT {unit_num}[:\s].*?\n)'
        prereq_box = f'\n> 📋 **Prerequisites for this unit:**\n> {prereq_text}\n\n'
        
        # Only insert if not already present
        if f'Prerequisites for this unit' not in content.split(f'UNIT {unit_num}')[0] if f'UNIT {unit_num}' in content else True:
            content = re.sub(pattern, r'\1' + prereq_box, content, count=1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {os.path.basename(filepath)}: {len(unit_prereqs)} prerequisite boxes added")

def main():
    print("Inserting prerequisites into all subject files...\n")
    for filename, prereqs in PREREQS.items():
        filepath = os.path.join(NOTES_DIR, filename)
        if os.path.exists(filepath):
            insert_prereqs(filepath, prereqs)
        else:
            print(f"  ❌ SKIP: {filename} not found")
    print("\nDone! Now regenerate the booklet.")

if __name__ == "__main__":
    main()
