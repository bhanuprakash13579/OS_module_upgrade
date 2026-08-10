# 🎯 CSIR NET Quick Revision — All Semester 1 Topics

> **Use this sheet for last-minute revision before CSIR NET or semester exams**
> **Format: Theorem/Concept → One-line statement → Key formula**

---

## 📐 ADVANCED LINEAR ALGEBRA — Flash Cards

### Must-Know Theorems
| # | Theorem | Statement |
|---|---------|-----------|
| 1 | Rank-Nullity | dim(V) = rank(T) + nullity(T) |
| 2 | Cayley-Hamilton | Every matrix satisfies its characteristic polynomial: p(A) = 0 |
| 3 | Spectral Theorem | Real symmetric matrices are orthogonally diagonalizable |
| 4 | Sylvester's Law | Signature (p, q) of a quadratic form is invariant under change of basis |
| 5 | Jordan Form | Every matrix over ℂ is similar to a block-diagonal of Jordan blocks |
| 6 | Riesz Representation | Every **continuous** linear functional φ on a **Hilbert** space H satisfies φ(x) = ⟨x, v₀⟩ for a unique v₀ ∈ H, with ‖φ‖ = ‖v₀‖ (also true for finite-dim IPS without "continuous") |

### Key Formulas
```
Eigenvalues:        det(A − λI) = 0
Diagonalizable iff: minimal polynomial has no repeated roots
Orthogonal matrix:  QᵀQ = I, det(Q) = ±1
Cauchy-Schwarz:     |⟨u,v⟩| ≤ ‖u‖·‖v‖
Gram-Schmidt:       uₖ = vₖ − Σᵢ₌₁^{k−1} ⟨vₖ, eᵢ⟩ eᵢ;  then eₖ = uₖ/‖uₖ‖
dim(W) + dim(W⊥) = dim(V)
dim(W) + dim(W⁰) = dim(V)  (annihilator)
```

### 🚨 Common Traps
- Eigenvectors of DIFFERENT eigenvalues are linearly independent
- Symmetric ≠ orthogonal (symmetric: Aᵀ=A; orthogonal: AᵀA=I)
- Nilpotent matrix: all eigenvalues = 0, but NOT the zero matrix
- Similar matrices have same eigenvalues, BUT same eigenvalues ≠ similar

---

## 📊 MATHEMATICAL ANALYSIS — Flash Cards

### Must-Know Theorems
| # | Theorem | Statement |
|---|---------|-----------|
| 1 | Weierstrass M-test | \|fₙ(x)\| ≤ Mₙ with ΣMₙ < ∞ ⟹ Σfₙ converges uniformly |
| 2 | Stone-Weierstrass | Continuous functions on [a,b] can be uniformly approximated by polynomials |
| 3 | Arzelà-Ascoli | Uniformly bounded + equicontinuous ⟹ has uniformly convergent subsequence |
| 4 | Implicit Function Thm | F(a,b)=0 and ∂F/∂y invertible ⟹ y=g(x) locally |
| 5 | Inverse Function Thm | f ∈ C¹ near a AND Df(a) invertible ⟹ f is a local C¹ diffeomorphism near a |

### Key Formulas
```
R-S integral:       ∫f dα = ∫f(x)α'(x)dx  (when α ∈ C¹ or absolutely continuous)
Integration by parts: ∫f dα + ∫α df = f(b)α(b) − f(a)α(a)
Uniform convergence: sup|fₙ(x) − f(x)| → 0
Jacobian:           J = det[∂fᵢ/∂xⱼ], area element: |J|du dv
Lagrange multiplier: ∇f = λ∇g at constrained extremum
Second deriv test:  D = fₓₓ·f_yy − (f_xy)² (D>0, fₓₓ>0: min; D>0, fₓₓ<0: max; D<0: saddle)
```

### 🚨 Common Traps
- Pointwise convergence does NOT preserve continuity (xⁿ on [0,1])
- Partial derivatives exist does NOT imply differentiable
- Continuous partials DOES imply differentiable
- Clairaut: f_xy = f_yx only when both are continuous

---

## 🔷 TOPOLOGY — Flash Cards

### Must-Know Theorems
| # | Theorem | Statement |
|---|---------|-----------|
| 1 | Heine-Borel | Subset of ℝⁿ is compact ⟺ closed and bounded |
| 2 | Tychonoff | Product of compact spaces is compact |
| 3 | Bolzano-Weierstrass | Infinite subset of compact space has limit point |
| 4 | IVT (topological) | Continuous image of connected space is connected |
| 5 | Urysohn's Lemma | Normal space: disjoint closed sets separated by continuous function |
| 6 | Extreme Value Thm | Continuous real function on compact space attains max and min |

### Key Facts
```
Topology axioms:     ∅,X ∈ τ; finite ∩; arbitrary ∪
Closed = complement of open
Ā = A ∪ A' (closure = set ∪ limit points)
∂A = Ā \ Int(A)
Connected: no partition into 2 nonempty disjoint open sets
Path connected ⟹ Connected (converse FALSE)
Compact + Hausdorff ⟹ Normal
In metric spaces: Separable ⟺ Second Countable ⟺ Lindelöf
```

### Separation Axioms Quick Reference
```
T₀: distinguishable    T₁: singletons closed    T₂: Hausdorff (disjoint nbhds)
T₃: Regular (pt & closed set separated)    T₄: Normal (closed sets separated)
```

### 🚨 Common Traps
- Open and closed are NOT opposites (a set can be both, or neither)
- Compact does NOT mean closed (only in Hausdorff spaces)
- ℚ is NOT connected, NOT compact, NOT locally compact
- Cofinite topology: T₁ but NOT T₂; every infinite set is dense; space is compact

---

## 🌀 ADVANCED COMPLEX ANALYSIS — Flash Cards

### Must-Know Theorems
| # | Theorem | Statement |
|---|---------|-----------|
| 1 | Liouville | Entire + bounded ⟹ constant |
| 2 | Little Picard | Non-constant entire function omits at most 1 value |
| 3 | Great Picard | Near essential singularity: takes every value (except maybe 1) infinitely often |
| 4 | Hadamard Factorization | Entire f of order ρ: f(z) = z^m · e^{P(z)} · (canonical product over zeros), where deg P ≤ ρ. The polynomial lives in the **exponent**, not as a multiplicative factor. |
| 5 | Maximum Principle | \|f\| has no interior maximum for non-constant analytic f |
| 6 | Open Mapping | Non-constant analytic function is an open map |

### Key Formulas
```
Order of entire function:     ρ = lim sup [log log M(r)]/[log r]
Jensen's formula:             log|f(0)| + Σ log(R/|aₖ|) = (1/2π) ∫ log|f(R·e^(iθ))| dθ
Poisson integral:             u(r·e^(iθ)) = (1/2π) ∫ P(r,θ−t) f(e^(it)) dt
Weierstrass product:          f(z) = e^(g(z)) · Π Eₚ(z/aₙ)
sin(πz) = πz · Π(1−z²/n²)
Hadamard 3 circles:           log M(r) is convex in log r
```

---

## ⚙️ ADVANCED DIFFERENTIAL EQUATIONS — Flash Cards

### Must-Know Theorems
| # | Theorem | Statement |
|---|---------|-----------|
| 1 | Picard-Lindelöf | f(t,y) continuous on R = [t₀−a, t₀+a]×[y₀−b, y₀+b] **AND Lipschitz in y uniformly in t** ⟹ unique local C¹ solution to y' = f(t,y), y(t₀) = y₀ |
| 2 | Peano | f continuous ⟹ solution exists (may not be unique) |
| 3 | Gronwall | u ≤ α + ∫βu ⟹ u ≤ α·exp(∫β) |
| 4 | Poincaré-Bendixson | Bounded orbit in 2D with no equilibria ⟹ limit cycle |
| 5 | Bendixson Criterion | If div(f,g) = ∂f/∂x + ∂g/∂y has **one sign (not identically zero) on a simply connected region D**, then there is **no periodic orbit lying entirely in D** |
| 6 | Lyapunov Stability | V>0, V̇≤0 ⟹ stable; V̇<0 ⟹ asymptotically stable |

### Critical Point Classification (2D)
```
λ₁,λ₂ < 0:           Stable node
λ₁,λ₂ > 0:           Unstable node
λ₁ < 0 < λ₂:         Saddle (unstable)
α±βi, α<0:           Stable spiral
α±βi, α>0:           Unstable spiral
±βi:                  Center (stable, not asymptotic)
```

### Key Formulas
```
Matrix exponential:    eᴬᵗ = Σ (At)ⁿ/n!
If A = PDP⁻¹:         eᴬᵗ = P·diag(eλᵢt)·P⁻¹
Variation of params:   x(t) = eᴬᵗx₀ + ∫₀ᵗ eᴬ⁽ᵗ⁻ˢ⁾g(s)ds
Wronskian:             W(t) = W(t₀)·exp(∫tr(A)ds)
```

---

## 🔄 DYNAMICS OF A RIGID BODY — Flash Cards

### Must-Know Formulas
```
Moment of inertia:     I = ∫r²dm
Parallel axis:         I = I_cm + Md²
Perpendicular axis:    Iz = Ix + Iy (planar bodies only)
Euler's equations:     I₁ω̇₁ + (I₃−I₂)ω₂ω₃ = N₁ (cyclic)
Rolling (no slip):     v = Rω,  a = Rα
KE of rigid body:      T = ½Mv_cm² + ½I_cm·ω²
Compound pendulum:     T = 2π√(I_O/(Mgh))  where I_O = MoI about pivot O, h = pivot→CM distance
Angular momentum:      L = Iω
```

### Standard Moments of Inertia
```
Rod (center):    ML²/12       Rod (end):      ML²/3
Disk (center):   MR²/2        Ring:           MR²
Solid sphere:    2MR²/5       Hollow sphere:  2MR²/3
```

---

## 🏆 CSIR NET EXAM DAY STRATEGY

### Time Allocation (3 hours = 180 min)
```
Part A (General Aptitude):  30 min — attempt 15/20
Part B (Subject MCQs):      80 min — attempt 20/25
Part C (Advanced MSQs):     60 min — attempt 8-10/20
Buffer/Review:              10 min
```

### Subject-wise Question Distribution (Typical)
```
Linear Algebra:        4-5 questions (Part B+C)  ← YOUR STRONGEST BET
Real Analysis:         4-5 questions (Part B+C)  ← HIGH ROI
Complex Analysis:      2-3 questions (Part B)
Topology:              2-3 questions (Part B+C)
ODE/PDE:               2-3 questions (Part B)
Algebra (Groups/Rings): 3-4 questions           ← Semester 2/3 topic
Classical Mechanics:    1-2 questions (Part B)
```

### Golden Rules
1. **Attempt Part A fully** — easy marks, low negative marking
2. **Never guess in Part C** — high negative marking (-1.0)
3. **Start with your strongest subject** in Part B
4. **Skip and return** — don't get stuck on one problem
5. **Use elimination** — plug in options for MCQs
