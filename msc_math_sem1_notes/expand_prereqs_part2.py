#!/usr/bin/env python3
"""Part 2: Expanded prereqs for subjects 4-6."""
import re, os

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"

def replace_prereqs(filepath, prereqs_dict):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'\n> 📋 \*\*Prerequisites for this unit:\*\*\n> \*\*What you need:.*?\n\n', '\n', content)
    for unit_num, prereq_text in prereqs_dict.items():
        pattern = rf'(# UNIT {unit_num}[:\s][^\n]*\n)'
        content = re.sub(pattern, r'\1' + f'\n{prereq_text}\n\n', content, count=1)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {os.path.basename(filepath)}")

CA = {
1: """> 📋 **Quick Refresher Before Starting:**
>
> **Complex number** z = a + bi where i² = -1. |z| = √(a²+b²). Polar form: z = re^(iθ).
> **Analytic function:** f(z) is analytic if it's complex-differentiable. Must satisfy Cauchy-Riemann equations:
> If f = u + iv, then ∂u/∂x = ∂v/∂y and ∂u/∂y = -∂v/∂x.
> **Entire function:** Analytic EVERYWHERE in ℂ. Examples: eᶻ, sin z, polynomials. NOT entire: 1/z (pole at 0).
> **Taylor series:** f(z) = Σ aₙzⁿ. Converges in a disk. Entire = infinite radius of convergence.""",

2: """> 📋 **Quick Refresher Before Starting:**
>
> **Gamma function:** Γ(n) = (n-1)! for positive integers. Γ(1/2) = √π. Defined by Γ(s) = ∫₀^∞ t^(s-1)e^(-t)dt.
> **Functional equation:** Γ(s+1) = s·Γ(s). This extends factorial to all complex numbers!
> **Riemann zeta function:** ζ(s) = Σ 1/nˢ = 1 + 1/2ˢ + 1/3ˢ + ... Converges for Re(s) > 1.""",

3: """> 📋 **Quick Refresher Before Starting:**
>
> **Power series** (Class 12): f(x) = Σ aₙxⁿ converges inside a disk of radius R (radius of convergence).
> Outside R: diverges. On the boundary: depends on the specific series.
>
> **Analytic continuation:** If f is defined by a power series in one disk, can we "extend" it to a larger region?
> Example: f(z) = Σ zⁿ = 1/(1-z) converges only for |z| < 1, but 1/(1-z) makes sense everywhere except z = 1.
> So 1/(1-z) is the analytic continuation of Σ zⁿ beyond the unit disk.""",

4: """> 📋 **Quick Refresher Before Starting:**
>
> **Harmonic function:** u(x,y) satisfying Laplace's equation: ∂²u/∂x² + ∂²u/∂y² = 0 (written ∇²u = 0).
> **Connection to analytic functions:** If f = u + iv is analytic, then BOTH u and v are harmonic!
> **Harmonic conjugate:** Given u, find v such that u + iv is analytic. Use Cauchy-Riemann: vₓ = -uᵧ, vᵧ = uₓ.
> Example: u = x² - y² → uₓ = 2x, uᵧ = -2y → vₓ = 2y, vᵧ = 2x → v = 2xy. So f = z².""",

5: """> 📋 **Quick Refresher Before Starting:**
>
> **Mean value property:** For harmonic u: u(center) = average of u on any circle around the center.
> **Maximum principle:** A harmonic function on a region attains its max/min on the BOUNDARY, never inside.
> **Harnack's inequality** (new): Bounds harmonic functions from above and below on compact subsets.
> **Green's function:** Solves the Dirichlet problem (find harmonic u with given boundary values).""",

6: """> 📋 **Quick Refresher Before Starting:**
>
> **Infinite product:** Π(1 + aₙ) = (1+a₁)(1+a₂)(1+a₃)... Like infinite series but with multiplication.
> Converges if Σ|aₙ| converges (analogous to absolute convergence of series).
> **Canonical product:** Builds an entire function with prescribed zeros {aₙ}:
> f(z) = Π Eₚ(z/aₙ) where Eₚ is an "elementary factor" that ensures convergence.""",

7: """> 📋 **Quick Refresher Before Starting:**
>
> **M(r) = max|f(z)| on |z| = r** — the maximum modulus on a circle of radius r.
> As r grows, M(r) tells you how fast the entire function grows.
> **Hadamard's three circles theorem:** log M(r) is a CONVEX function of log r.
> This means: knowing M on two circles constrains M on any circle between them.""",

8: """> 📋 **Quick Refresher Before Starting:**
>
> **Order of an entire function:** ρ = lim sup (log log M(r))/(log r). Measures growth rate.
> - Polynomials: ρ = 0. eᶻ: ρ = 1. e^(z²): ρ = 2.
> **Hadamard factorization:** An entire function of finite order can be completely written as:
> f(z) = z^m · e^(polynomial) · Π Eₚ(z/aₙ) where aₙ are its zeros.""",

9: """> 📋 **Quick Refresher Before Starting:**
>
> **Liouville's theorem:** Bounded entire function = constant. (If |f(z)| ≤ M for ALL z, then f is constant.)
> **Picard goes much further:**
> - **Little Picard:** A non-constant entire function takes EVERY value, with at most ONE exception.
> - Example: eᶻ is entire and takes every value except 0. That one exception is the maximum allowed.
> **Bloch's theorem:** Every analytic function on the unit disk contains a disk of a certain minimum size in its image.""",

10: """> 📋 **Quick Refresher Before Starting:**
>
> **Univalent (schlicht) function:** Analytic AND injective (one-to-one). f(z₁) = f(z₂) ⟹ z₁ = z₂.
> **Schwarz lemma:** If f maps the unit disk to itself with f(0) = 0, then |f(z)| ≤ |z|.
> **Conformal mapping:** Analytic + non-zero derivative. Preserves angles between curves.
> **Riemann mapping theorem:** Any simply connected region (≠ ℂ) can be conformally mapped to the unit disk.""",
}

ODE = {
1: """> 📋 **Quick Refresher Before Starting:**
>
> **ODE** (Ordinary Differential Equation): An equation involving a function y and its derivatives y', y'', etc.
> **Example:** y' = 2y. Solution: y = Ce²ˣ (check: (Ce²ˣ)' = 2Ce²ˣ = 2y ✓).
> **Separation of variables** (Class 12): If dy/dx = f(x)g(y), then ∫dy/g(y) = ∫f(x)dx.
> **ε-approximate solution:** A function φ with |φ' - f(t,φ)| < ε — it "almost" satisfies the ODE.""",

2: """> 📋 **Quick Refresher Before Starting:**
>
> **Existence:** Does a solution exist? **Uniqueness:** Is there exactly one solution?
> **Lipschitz condition:** |f(t,y₁) - f(t,y₂)| ≤ L|y₁-y₂|. It means f doesn't change too wildly in y.
> **Picard iteration:** Start with φ₀ = y₀, then φₙ₊₁(t) = y₀ + ∫f(s,φₙ(s))ds. Keep iterating — the sequence converges to the unique solution.
> Example: y' = y, y(0) = 1. φ₀ = 1, φ₁ = 1+t, φ₂ = 1+t+t²/2, ... → eᵗ ✓""",

3: """> 📋 **Quick Refresher Before Starting:**
>
> **System of ODEs:** Multiple equations coupled together.
> x' = 2x + y
> y' = x - y
> Written as: X' = AX where X = (x,y) and A = [[2,1],[1,-1]].
> **Why matrices matter:** Solving X' = AX requires eigenvalues of A!""",

4: """> 📋 **Quick Refresher Before Starting:**
>
> **Matrix exponential:** e^(At) = I + At + A²t²/2! + A³t³/3! + ... (like the scalar eˣ but for matrices).
> **Solution of X' = AX:** X(t) = e^(At) · X(0).
> **If A is diagonalizable** (A = PDP⁻¹): e^(At) = P · diag(e^(λ₁t), ..., e^(λₙt)) · P⁻¹.
> This is why eigenvalues determine everything about the system's behavior!""",

5: """> 📋 **Quick Refresher Before Starting:**
>
> **Linear system:** X' = AX. Behavior fully determined by eigenvalues of A.
> **Nonlinear system:** X' = F(X) where F is NOT just a matrix times X.
> Example: x' = x - x³ (the -x³ term is nonlinear).
> **Linearization:** Near an equilibrium point x₀ (where F(x₀) = 0), approximate: F(x) ≈ DF(x₀)·(x - x₀).
> So near equilibrium, the nonlinear system behaves like a linear one!""",

6: """> 📋 **Quick Refresher Before Starting:**
>
> **Phase plane:** Plot (x,y) as t varies. The trajectory traces a curve in 2D.
> **Limit cycle:** A closed trajectory that nearby solutions spiral toward (or away from).
> **Poincaré-Bendixson theorem** (key result): In 2D, if a trajectory stays in a bounded region with no equilibria, it must approach a limit cycle.
> This is one of the few tools for proving periodic solutions exist in nonlinear systems!""",

7: """> 📋 **Quick Refresher Before Starting:**
>
> **Equilibrium:** A point x₀ where F(x₀) = 0 (the system stays still).
> **Stable:** Small perturbations stay small. **Unstable:** Small perturbations grow.
> **Asymptotically stable:** Perturbations not only stay small but decay to zero.
>
> **Lyapunov's method:** Find an "energy function" V(x) > 0 that DECREASES along solutions (V̇ ≤ 0).
> If such V exists → stable. If V̇ < 0 → asymptotically stable.
> Think of V like a ball on a hill: if V always decreases, the ball rolls to the bottom (equilibrium).""",

8: """> 📋 **Quick Refresher Before Starting:**
>
> **Phase portrait:** A picture showing ALL trajectories of a 2D linear system X' = AX.
> The eigenvalues of A determine the portrait type:
> - Both negative → stable node (all trajectories → origin)
> - Both positive → unstable node (all trajectories ← away)
> - Opposite signs → saddle (some approach, some flee)
> - Complex with negative real part → stable spiral
> - Pure imaginary → center (circles)""",

9: """> 📋 **Quick Refresher Before Starting:**
>
> **Parameter dependence:** If the ODE is y' = f(t, y, μ) where μ is a parameter, how does the solution change when μ changes slightly?
> **Key question:** Is the solution a continuous/differentiable function of the parameter μ?
> **Answer:** Yes, under mild conditions! The solution varies smoothly with parameters.""",

10: """> 📋 **Quick Refresher Before Starting:**
>
> **Poincaré-Bendixson (full version):** In a 2D autonomous system, if:
> (1) A trajectory stays in a bounded region, AND
> (2) The region contains no equilibrium points,
> THEN the trajectory approaches a periodic orbit (limit cycle).
>
> **Why only 2D?** In 3D and higher, trajectories can exhibit chaos (like the Lorenz attractor). The theorem fails!""",
}

DY = {
1: """> 📋 **Quick Refresher Before Starting:**
>
> **Moment of inertia I** = resistance to rotation (like mass is resistance to linear motion).
> For a point mass m at distance r from axis: I = mr².
> For a continuous body: I = ∫r²dm (integrate over the body).
>
> **Common results you'll derive:**
> - Thin rod about center: I = ML²/12
> - Thin rod about end: I = ML²/3
> - Solid disk about center: I = MR²/2
> - Solid sphere about diameter: I = 2MR²/5""",

2: """> 📋 **Quick Refresher Before Starting:**
>
> **Parallel axis theorem:** I = I_cm + Md² (shift axis by distance d from center of mass).
> Example: Rod about center: ML²/12. Rod about end (d = L/2): ML²/12 + M(L/2)² = ML²/3.
>
> **Perpendicular axis theorem** (flat bodies only): I_z = I_x + I_y
> Example: Disk: I_x = I_y = MR²/4 (by symmetry), so I_z = MR²/2 ✓""",

3: """> 📋 **Quick Refresher Before Starting:**
>
> **Newton's second law:** F = ma (force = mass × acceleration).
> **D'Alembert's principle:** Rewrite as F - ma = 0, treating -ma as a "fictitious force." Now it looks like a statics problem!
> **Virtual work:** If we imagine a small displacement δr, the work done by all forces (including -ma) is zero: Σ(Fᵢ - mᵢaᵢ)·δrᵢ = 0.
> This powerful idea leads directly to Lagrangian mechanics.""",

4: """> 📋 **Quick Refresher Before Starting:**
>
> **Angular momentum** L = Iω (analogous to linear momentum p = mv).
> **Torque** τ = Iα = dL/dt (analogous to F = dp/dt).
> **Cross product** (Class 12): a × b is perpendicular to both a and b. |a × b| = |a||b|sinθ.
> **Euler's equations:** Govern rotation of a 3D rigid body about its center of mass. They couple the three components of angular velocity.""",

5: """> 📋 **Quick Refresher Before Starting:**
>
> **Impulse** (Class 12): J = FΔt = change in momentum (Δp).
> For very short time (like a bat hitting a ball), force is huge but time is tiny. The product is finite.
> **For rigid bodies:** Impulsive force → sudden change in velocity.
> Impulsive torque → sudden change in angular velocity. τΔt = ΔL = I·Δω.""",

6: """> 📋 **Quick Refresher Before Starting:**
>
> **Fixed axis rotation:** Body can ONLY rotate about one fixed line (like a door on hinges).
> **Key equation:** τ = Iα where I is moment of inertia about the fixed axis, α = angular acceleration.
> **Compound pendulum:** A rigid body swinging about a fixed point (not just a point mass on a string).
> Period: T = 2π√(I/(Mgh)) where h = distance from pivot to center of mass.""",

7: """> 📋 **Quick Refresher Before Starting:**
>
> **Kinetic energy of rolling:** T = ½mv² + ½Iω² (translational + rotational).
> **Rolling without slipping:** v = Rω (the contact point has zero velocity).
> **Energy conservation:** For a body rolling down an incline: mgh = ½mv² + ½Iω².
> Substituting v = Rω: v = √(2gh/(1 + I/mR²)). Higher I → slower rolling!""",

8: """> 📋 **Quick Refresher Before Starting:**
>
> **2D rigid body motion = translation + rotation.** Three equations govern it:
> M·ẍ = ΣFₓ (horizontal forces)
> M·ÿ = ΣFᵧ (vertical forces)
> I·θ̈ = ΣN (torques about center of mass)
> Plus constraint equations (e.g., rolling: ẍ = Rθ̈).""",

9: """> 📋 **Quick Refresher Before Starting:**
>
> **Combining impulsive forces with 2D motion:**
> Linear impulse: J = M·Δv (change in linear velocity of CM)
> Angular impulse: Moment of J about CM = I·Δω (change in angular velocity)
> **Centre of percussion:** The point where a blow produces NO reaction at the pivot.""",

10: """> 📋 **Quick Refresher Before Starting:**
>
> **Conservation laws** (from Class 12 physics):
> - **Energy:** T + V = constant (if no non-conservative forces)
> - **Linear momentum:** If no external force, p = constant
> - **Angular momentum:** If no external torque, L = constant
>
> **Initial motion problems:** At t = 0, find the initial accelerations and reactions just as motion begins from rest.""",
}

ALL = {
    "04_Advanced_Complex_Analysis.md": CA,
    "05_Advanced_Differential_Equations.md": ODE,
    "06_Dynamics_of_Rigid_Body.md": DY,
}

def main():
    print("Replacing prerequisites with expanded mini-lessons (Subjects 4-6)...\n")
    for filename, prereqs in ALL.items():
        filepath = os.path.join(NOTES_DIR, filename)
        if os.path.exists(filepath):
            replace_prereqs(filepath, prereqs)
    print("\nDone! Now regenerate booklet.")

if __name__ == "__main__":
    main()
