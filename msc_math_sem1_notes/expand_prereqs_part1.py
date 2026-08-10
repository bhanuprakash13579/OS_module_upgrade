#!/usr/bin/env python3
"""Replace short prereq boxes with expanded mini-lessons."""
import re, os

NOTES_DIR = "/home/bhanu/Desktop/OS_module_upgrade/msc_math_sem1_notes"

def replace_prereqs(filepath, prereqs_dict):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove old short prereq blocks
    content = re.sub(
        r'\n> 📋 \*\*Prerequisites for this unit:\*\*\n> \*\*What you need:.*?\n\n',
        '\n', content
    )
    
    # Insert new expanded prereqs after each UNIT heading
    for unit_num, prereq_text in prereqs_dict.items():
        pattern = rf'(# UNIT {unit_num}[:\s][^\n]*\n)'
        box = f'\n{prereq_text}\n\n'
        content = re.sub(pattern, r'\1' + box, content, count=1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  ✅ {os.path.basename(filepath)}")

# ═══════════════════════════════════════════
# SUBJECT 1: LINEAR ALGEBRA
# ═══════════════════════════════════════════
LA = {
1: """> 📋 **Quick Refresher Before Starting:**
>
> **Matrix:** A rectangular grid of numbers. A 2×2 matrix looks like:
> ```
> A = | 2  3 |    We write A = [[2,3],[1,4]]
>     | 1  4 |
> ```
> **Matrix multiplication:** Row × Column. For AB, take each row of A, multiply element-by-element with each column of B, and add up.
> ```
> | 2 3 | × | 1 | = | 2×1 + 3×0 | = | 2 |
> | 1 4 |   | 0 |   | 1×1 + 4×0 |   | 1 |
> ```
> **Vector:** An ordered list of numbers, like v = (3, -1, 2) in ℝ³.
> **Linear combination:** c₁v₁ + c₂v₂ means scaling and adding vectors.
> **System Ax = b:** Finding x means solving multiple equations simultaneously.""",

2: """> 📋 **Quick Refresher Before Starting:**
>
> **Basis:** A set of vectors that (1) spans the space and (2) is linearly independent.
> Example: {(1,0), (0,1)} is the standard basis for ℝ². Every vector (a,b) = a(1,0) + b(0,1).
> **Dimension:** Number of vectors in a basis. dim(ℝ³) = 3.
> **Linear transformation T:** A function between vector spaces that preserves addition and scaling:
> T(u + v) = T(u) + T(v) and T(cv) = cT(v).
> Example: T(x,y) = (2x + y, x - y) is linear. T(x,y) = (x², y) is NOT (because T(2v) ≠ 2T(v)).""",

3: """> 📋 **Quick Refresher Before Starting:**
>
> **Linear functional:** A linear map from V to ℝ (or ℂ). It takes a vector, outputs a single number.
> Example: f(x,y,z) = 2x + 3y - z is a linear functional on ℝ³.
> **Dual space V*:** The set of ALL linear functionals on V. Surprisingly, dim(V*) = dim(V).
> **If V has basis {e₁, e₂, e₃}**, then V* has a dual basis {f₁, f₂, f₃} where fᵢ(eⱼ) = 1 if i=j, 0 otherwise.
> Think of dual basis as "coordinate extractors" — f₁ extracts the first coordinate.""",

4: """> 📋 **Quick Refresher Before Starting:**
>
> **Dot product** (from Class 12): For u = (u₁,u₂), v = (v₁,v₂):
> u · v = u₁v₁ + u₂v₂ (multiply corresponding entries and add)
> Example: (3,4) · (1,2) = 3×1 + 4×2 = 11
>
> **Key properties of dot product:**
> - u · v = |u||v|cosθ where θ is the angle between them
> - u ⊥ v (perpendicular) ⟺ u · v = 0
> - |u| = √(u · u) = √(u₁² + u₂²) (Pythagoras!)
>
> **Inner product** is a generalization of dot product. It can be defined on ANY vector space, not just ℝⁿ.
> For polynomials: ⟨p,q⟩ = ∫₀¹ p(x)q(x)dx is a valid inner product!""",

5: """> 📋 **Quick Refresher Before Starting:**
>
> **Orthogonal** = perpendicular (inner product = 0).
> **Orthonormal** = orthogonal AND each vector has length 1.
> Example: {(1,0), (0,1)} is orthonormal. {(1,1), (-1,1)} is orthogonal but NOT orthonormal (length = √2).
> To make it orthonormal: divide each by its length → {(1/√2, 1/√2), (-1/√2, 1/√2)}.
>
> **Gram-Schmidt Process** (you'll learn this here): Takes ANY basis and produces an orthonormal basis.
> It works by: take first vector, normalize it. For each next vector, subtract its projections onto previous orthonormal vectors, then normalize.""",

6: """> 📋 **Quick Refresher Before Starting:**
>
> **Isomorphism** = a perfect structural match between two spaces.
> If T: V → W is a bijective linear map, then V and W are "the same" structurally.
> **Key theorem:** V ≅ W (isomorphic) ⟺ dim(V) = dim(W). So ALL n-dimensional real vector spaces are "the same" as ℝⁿ!
> This unit shows: inner product spaces of the same dimension are isomorphic in a way that preserves lengths and angles.""",

7: """> 📋 **Quick Refresher Before Starting:**
>
> **Polynomial in a matrix:** If p(x) = x² - 3x + 2, then p(A) = A² - 3A + 2I.
> Example: A = [[1,0],[0,2]]. A² = [[1,0],[0,4]]. p(A) = [[1,0],[0,4]] - [[3,0],[0,6]] + [[2,0],[0,2]] = [[0,0],[0,0]].
> So A satisfies the polynomial x² - 3x + 2 = (x-1)(x-2)!
>
> **Hom(V,V)** = set of all linear transformations from V to itself. This set is itself a vector space AND an algebra (you can multiply = compose transformations).
> **Minimal polynomial:** The smallest-degree polynomial that A satisfies.""",

8: """> 📋 **Quick Refresher Before Starting:**
>
> **Eigenvalue and Eigenvector:** If Av = λv (A stretches v by factor λ), then:
> - λ is an eigenvalue, v is an eigenvector
> - To find eigenvalues: solve det(A - λI) = 0
>
> **Worked example:** A = [[2,1],[0,3]].
> det(A - λI) = det([[2-λ, 1],[0, 3-λ]]) = (2-λ)(3-λ) = 0
> So λ₁ = 2, λ₂ = 3.
> For λ=2: (A-2I)v = 0 → [[0,1],[0,1]]v = 0 → v = (1,0).
> For λ=3: (A-3I)v = 0 → [[-1,1],[0,0]]v = 0 → v = (1,1).
>
> **Diagonalization:** A = PDP⁻¹ where D = diagonal matrix of eigenvalues, P = matrix of eigenvectors. Only works if there are enough independent eigenvectors.""",

9: """> 📋 **Quick Refresher Before Starting:**
>
> **Characteristic polynomial:** p(λ) = det(A - λI). Its roots are the eigenvalues.
> **Cayley-Hamilton Theorem** (you'll prove here): Every matrix satisfies its own characteristic polynomial. p(A) = 0.
> Example: If char poly is λ² - 5λ + 6 = 0, then A² - 5A + 6I = 0 (the zero matrix!).
>
> **Jordan form:** When a matrix can't be diagonalized, Jordan form is the "next best thing."
> A Jordan block J₂(λ) = [[λ,1],[0,λ]] — it's almost diagonal, with 1's on the superdiagonal.""",

10: """> 📋 **Quick Refresher Before Starting:**
>
> **Quadratic form** = a homogeneous degree-2 polynomial in several variables.
> Examples: Q(x,y) = 3x² + 2xy - y² or Q(x,y,z) = x² + 4y² + z² - 2xz
> Every quadratic form can be written as Q(x) = xᵀAx where A is symmetric.
> Example: Q = 3x² + 2xy - y² corresponds to A = [[3,1],[1,-1]] (off-diagonal = half the xy coefficient).
>
> **Classification:**
> - Positive definite: Q > 0 for all x ≠ 0 (like x² + y² — a bowl shape)
> - Negative definite: Q < 0 for all x ≠ 0
> - Indefinite: Q takes both positive and negative values (like x² - y² — a saddle)""",
}

# ═══════════════════════════════════════════
# SUBJECT 2: ANALYSIS
# ═══════════════════════════════════════════
AN = {
1: """> 📋 **Quick Refresher Before Starting:**
>
> **Definite integral** (Class 12): ∫₀¹ x² dx = [x³/3]₀¹ = 1/3. It gives the area under the curve y = x².
> **Riemann sum:** Divide [a,b] into small intervals, approximate area by rectangles, sum them up.
> As rectangles get thinner, the sum → the integral.
>
> **Riemann-Stieltjes integral** (new concept): Instead of ∫f(x)dx, we compute ∫f(x)dα(x) where α is another function.
> Think of it as: α controls "how we weight" different parts of the interval.
> When α(x) = x, this reduces to the ordinary integral.""",

2: """> 📋 **Quick Refresher Before Starting:**
>
> **Integration by parts** (Class 12): ∫u dv = uv - ∫v du
> Example: ∫x·eˣ dx. Let u = x, dv = eˣdx. Then du = dx, v = eˣ.
> Result: xeˣ - ∫eˣdx = xeˣ - eˣ + C = eˣ(x-1) + C.
>
> This unit extends integration by parts to Stieltjes integrals: ∫f dα + ∫α df = f(b)α(b) - f(a)α(a).""",

3: """> 📋 **Quick Refresher Before Starting:**
>
> **Sequence:** a₁, a₂, a₃, ... (a list of numbers). Example: aₙ = 1/n gives 1, 1/2, 1/3, ...
> **Convergence:** aₙ → L means the terms get arbitrarily close to L. Example: 1/n → 0.
> **Series:** Σaₙ = a₁ + a₂ + a₃ + ... Example: Σ(1/2)ⁿ = 1 + 1/2 + 1/4 + ... = 2.
>
> **Pointwise convergence of functions:** fₙ(x) → f(x) means: for EACH fixed x, the sequence of numbers fₙ(x) converges to f(x).
> Example: fₙ(x) = xⁿ on [0,1]. For x < 1: xⁿ → 0. For x = 1: 1ⁿ → 1. So the limit is: f(x) = 0 if x < 1, f(1) = 1.
> Notice: each fₙ is continuous but the limit f is NOT! This motivates uniform convergence.""",

4: """> 📋 **Quick Refresher Before Starting:**
>
> **Pointwise vs Uniform convergence** (the key distinction):
> **Pointwise:** For each x, fₙ(x) eventually gets close to f(x). Different x's may converge at different rates.
> **Uniform:** ALL x's converge at the SAME rate. Formally: sup|fₙ(x) - f(x)| → 0.
>
> **Why it matters:** Uniform convergence preserves continuity, integrability, and (with extra conditions) differentiability. Pointwise does NOT.
> **Visual:** Imagine fₙ as a rubber band. Pointwise = each point of the band settles down. Uniform = the ENTIRE band settles down simultaneously.""",

5: """> 📋 **Quick Refresher Before Starting:**
>
> **Polynomial:** p(x) = aₙxⁿ + ... + a₁x + a₀. Continuous everywhere, easy to work with.
> **Weierstrass Approximation Theorem** (key result here): ANY continuous function on [a,b] can be uniformly approximated by polynomials.
> This is remarkable — even weird, jagged-looking continuous functions can be approximated by smooth polynomials!
> Stone-Weierstrass generalizes this to other function algebras.""",

6: """> 📋 **Quick Refresher Before Starting:**
>
> **Partial derivatives** (extending Class 12 calculus to several variables):
> If f(x,y) = x²y + 3y², then:
> ∂f/∂x = 2xy (differentiate treating y as a constant)
> ∂f/∂y = x² + 6y (differentiate treating x as a constant)
>
> **Gradient:** ∇f = (∂f/∂x, ∂f/∂y) points in the direction of steepest increase.
> Example: f = x² + y². ∇f = (2x, 2y), pointing radially outward (away from minimum at origin).""",

7: """> 📋 **Quick Refresher Before Starting:**
>
> **Chain rule** (Class 12): d/dx[f(g(x))] = f'(g(x))·g'(x).
> Example: d/dx[sin(x²)] = cos(x²)·2x.
>
> **Multivariable chain rule** (new): If z = f(x,y) where x = x(t), y = y(t):
> dz/dt = (∂f/∂x)(dx/dt) + (∂f/∂y)(dy/dt)
>
> **Total derivative:** The matrix of all partial derivatives — generalizes f'(x) to multiple dimensions.""",

8: """> 📋 **Quick Refresher Before Starting:**
>
> **Implicit function:** An equation F(x,y) = 0 that defines y as a function of x without explicitly solving for y.
> Example: x² + y² = 1 (circle). We can't write y = single formula for the whole circle, but near any point (except (±1,0)), we can locally solve for y.
>
> **Implicit differentiation** (Class 12): Differentiate both sides of F(x,y) = 0:
> Fₓ + Fᵧ·y' = 0, so y' = -Fₓ/Fᵧ
> Example: x² + y² = 1 → 2x + 2y·y' = 0 → y' = -x/y.""",

9: """> 📋 **Quick Refresher Before Starting:**
>
> **Finding max/min** (Class 12 for one variable): Set f'(x) = 0, check f''(x).
> **Two variables:** Set BOTH ∂f/∂x = 0 AND ∂f/∂y = 0 simultaneously. These give critical points.
>
> **Second derivative test (2D):** Compute D = fₓₓfᵧᵧ - (fₓᵧ)².
> - D > 0, fₓₓ > 0 → local MINIMUM
> - D > 0, fₓₓ < 0 → local MAXIMUM
> - D < 0 → SADDLE POINT (neither max nor min)
> - D = 0 → test inconclusive
>
> **Lagrange multipliers:** For extrema of f subject to constraint g = 0: solve ∇f = λ∇g and g = 0.""",

10: """> 📋 **Quick Refresher Before Starting:**
>
> **Determinant** (Class 12): For 2×2 matrix [[a,b],[c,d]], det = ad - bc.
> **Jacobian** = determinant of the matrix of partial derivatives.
> For transformation (u,v) → (x,y): J = |∂x/∂u  ∂x/∂v|
>                                        |∂y/∂u  ∂y/∂v|
>
> **Why it matters:** When changing variables in integrals:
> ∫∫f(x,y)dxdy = ∫∫f(x(u,v), y(u,v))|J|dudv
>
> **Example:** Polar coordinates x = rcosθ, y = rsinθ → J = r.
> So ∫∫f dxdy = ∫∫f·r drdθ (that's where the 'r' comes from!).""",
}

# ═══════════════════════════════════════════
# SUBJECT 3: TOPOLOGY
# ═══════════════════════════════════════════
TP = {
1: """> 📋 **Quick Refresher Before Starting:**
>
> **Open interval** (a,b) = {x ∈ ℝ : a < x < b}. Does NOT include endpoints.
> **Closed interval** [a,b] = {x ∈ ℝ : a ≤ x ≤ b}. INCLUDES endpoints.
>
> **Why (0,1) is "open":** Every point has wiggle room. Pick any x ∈ (0,1), say x = 0.3. Then (0.2, 0.4) ⊂ (0,1) is a small interval around x entirely inside (0,1). ✓
> **Why [0,1] is NOT open:** The point 0 has no wiggle room to the left — any interval around 0 escapes [0,1].
>
> **Topology** abstracts this: we declare which sets are "open" (have wiggle room) via axioms, WITHOUT needing distances or coordinates.""",

2: """> 📋 **Quick Refresher Before Starting:**
>
> **Set operations you need:**
> - A ∪ B (union) = elements in A OR B
> - A ∩ B (intersection) = elements in A AND B
> - Aᶜ (complement) = everything NOT in A
> - **De Morgan:** (A ∪ B)ᶜ = Aᶜ ∩ Bᶜ and (A ∩ B)ᶜ = Aᶜ ∪ Bᶜ
>
> **Key rule in topology:** A set is CLOSED if its complement is open.
> So [0,1] is closed in ℝ because ℝ\\[0,1] = (-∞,0) ∪ (1,∞) is open (union of open intervals).""",

3: """> 📋 **Quick Refresher Before Starting:**
>
> **Boundary intuition:** A boundary point is "on the edge" — every neighborhood contains points both INSIDE and OUTSIDE the set.
> Example: For (0,1) in ℝ, the boundary is {0, 1}. Around 0, any interval (-ε, ε) contains points both in (0,1) (like ε/2) and outside (like -ε/2).
> Example: For ℚ (rationals) in ℝ, EVERY real number is a boundary point! Because every interval contains both rationals and irrationals.""",

4: """> 📋 **Quick Refresher Before Starting:**
>
> **Basis for a topology** works like a basis for a vector space — a smaller collection that generates all open sets.
> Example: Open intervals (a,b) form a basis for the usual topology on ℝ. Every open set is a union of open intervals.
>
> **Product topology on X × Y:** Open sets are unions of "boxes" U × V where U is open in X and V is open in Y.
> Think of it as: the plane ℝ² gets its topology from open rectangles (a,b) × (c,d).""",

5: """> 📋 **Quick Refresher Before Starting:**
>
> **Continuous function** (Class 12): No jumps, no breaks. f is continuous at a if lim(x→a) f(x) = f(a).
> **Topological definition:** f: X → Y is continuous if the preimage of every open set is open.
> f⁻¹(V) = {x ∈ X : f(x) ∈ V}. This must be open in X whenever V is open in Y.
>
> **Homeomorphism:** A continuous bijection whose inverse is also continuous. If X ≅ Y (homeomorphic), they are "topologically the same."
> Example: (0,1) ≅ ℝ via f(x) = tan(π(x - 1/2)). They look different but are topologically identical!""",

6: """> 📋 **Quick Refresher Before Starting:**
>
> **Connected** = "one piece." A space X is connected if you CANNOT write X = A ∪ B where A,B are both open, both nonempty, and disjoint.
> **Example:** ℝ is connected. (0,1) ∪ (2,3) is NOT connected (two separate pieces).
> **Example:** ℚ is NOT connected! For any irrational r, ℚ = (-∞,r)∩ℚ ∪ (r,∞)∩ℚ splits it.
>
> **Path connected:** Any two points can be joined by a continuous curve. Path connected ⟹ connected (but not always vice versa).""",

7: """> 📋 **Quick Refresher Before Starting:**
>
> **Open cover:** A collection of open sets whose union contains X. Example: {(-n,n) : n = 1,2,...} covers ℝ.
> **Finite subcover:** Choosing finitely many sets from the cover that still cover X.
>
> **Compact:** Every open cover has a finite subcover. Intuitively: compact sets behave like finite sets.
> **In ℝⁿ (Heine-Borel):** Compact ⟺ closed AND bounded.
> Example: [0,1] is compact ✓ (closed + bounded). (0,1) is NOT compact ✗ (not closed). ℝ is NOT compact ✗ (not bounded).""",

8: """> 📋 **Quick Refresher Before Starting:**
>
> **Why compactness matters** — it guarantees things that can fail in non-compact spaces:
> - Continuous functions on compact sets are bounded and attain their max/min (Extreme Value Theorem)
> - Continuous functions on compact sets are uniformly continuous
> - In Hausdorff spaces: compact sets are closed
> - A continuous bijection from compact to Hausdorff is automatically a homeomorphism!""",

9: """> 📋 **Quick Refresher Before Starting:**
>
> **Separation axioms** describe how well a topology can "separate" points and sets:
> - **T₁:** For any two distinct points, each has a neighborhood not containing the other.
> - **T₂ (Hausdorff):** Any two distinct points have DISJOINT neighborhoods. Most "nice" spaces are Hausdorff.
> - **T₃ (Regular):** Points and closed sets can be separated by open sets.
> - **T₄ (Normal):** Any two disjoint closed sets can be separated by open sets.
>
> **Hierarchy:** T₄ ⟹ T₃ ⟹ T₂ ⟹ T₁. Every metric space is T₄.""",

10: """> 📋 **Quick Refresher Before Starting:**
>
> **Countable set:** Can be listed as a sequence: a₁, a₂, a₃, ... Examples: ℕ, ℤ, ℚ are countable. ℝ is UNcountable.
> **Dense set:** A ⊂ X is dense if every open set contains a point of A. Example: ℚ is dense in ℝ (every interval contains a rational).
> **Separable:** X has a countable dense subset. ℝ is separable (ℚ is countable and dense).
> **Second countable:** X has a countable basis. Example: ℝ has basis {(a,b) : a,b ∈ ℚ} which is countable.""",
}

ALL = {
    "01_Advanced_Linear_Algebra.md": LA,
    "02_Mathematical_Analysis.md": AN,
    "03_Topology.md": TP,
}

def main():
    print("Replacing prerequisites with expanded mini-lessons (Subjects 1-3)...\n")
    for filename, prereqs in ALL.items():
        filepath = os.path.join(NOTES_DIR, filename)
        if os.path.exists(filepath):
            replace_prereqs(filepath, prereqs)
    print("\nDone! Run Part 2 for subjects 4-6.")

if __name__ == "__main__":
    main()
