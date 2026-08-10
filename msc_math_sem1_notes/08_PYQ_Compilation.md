# 📝 Previous Year Questions — CSIR NET & University Exams

> **Curated PYQs mapped to your Semester 1 syllabus**
> **Sources: CSIR NET (2019-2025), SET/SLET exams, University recruitment tests**

---

## 📐 LINEAR ALGEBRA PYQs

### CSIR NET June 2024
**Q1.** Let A be a 4×4 real matrix with characteristic polynomial (x−1)²(x−2)² and minimal polynomial (x−1)(x−2). Then A is:
(a) Diagonalizable  (b) Not diagonalizable  (c) Nilpotent  (d) Idempotent

**Answer: (a)** Minimal polynomial has no repeated roots → diagonalizable.

---

**Q2.** Let V be the vector space of 2×2 real matrices. Define T(A) = AᵀA. Is T linear?

**Answer: NO.** T(A+B) = (A+B)ᵀ(A+B) = AᵀA + AᵀB + BᵀA + BᵀB ≠ T(A) + T(B).

---

### CSIR NET Dec 2023
**Q3.** Let A be an n×n real matrix with Aⁿ = 0 but Aⁿ⁻¹ ≠ 0. The Jordan form of A is:
(a) Single Jordan block Jₙ(0)  (b) Diagonal  (c) nJ₁(0)  (d) Cannot determine

**Answer: (a)** A is nilpotent with nilpotency index n → single Jordan block.

---

**Q4.** If A is a 3×3 orthogonal matrix with det(A) = 1, which eigenvalue is guaranteed?
(a) 0  (b) 1  (c) −1  (d) i

**Answer: (b)** det(A) = product of eigenvalues = 1. Eigenvalues of orthogonal matrices have |λ|=1. Complex eigenvalues come in conjugate pairs. For odd-sized matrix, at least one real eigenvalue. Since det=1 and |λ|=1, one eigenvalue must be 1.

---

### CSIR NET June 2023
**Q5.** Dimension of the space of 3×3 real symmetric matrices with trace 0?

**Answer: 5.** Symmetric 3×3 has dim = 6. Trace = 0 is one linear constraint. So dim = 5.

---

**Q6.** T: ℝ³ → ℝ³ defined by T(x,y,z) = (x+2y, y−z, x+2y−z). Find nullity(T).

**Answer:** Matrix: [[1,2,0],[0,1,−1],[1,2,−1]]. Row reduce: R3 ← R3 − R1 = [0,0,−1]. Rows now [1,2,0], [0,1,−1], [0,0,−1] — three pivots, so rank = 3, nullity = 3 − 3 = **0**. (T is injective; det = −1 ≠ 0.)

---

### SET/SLET Exam Questions
**Q7.** The number of linearly independent eigenvectors of [[2,1],[0,2]] is:
(a) 0  (b) 1  (c) 2  (d) 3

**Answer: (b)** Eigenvalue λ=2 (repeated). Eigenspace: (A−2I)v=0 → [[0,1],[0,0]]v=0 → span{(1,0)}. Dimension = 1.

---

**Q8.** A quadratic form Q(x,y) = 5x² + 2y² + 6xy. Classify it.

**Answer:** Matrix: [[5,3],[3,2]]. Eigenvalues: (5−λ)(2−λ)−9 = λ²−7λ+1 = 0. λ = (7±√45)/2 ≈ 6.85, 0.15. Both positive → **Positive definite.**

---

## 📊 REAL ANALYSIS PYQs

### CSIR NET Dec 2024
**Q9.** The sequence fₙ(x) = nx(1−x²)ⁿ on [0,1]. Find the pointwise limit and determine if convergence is uniform.

**Answer:** For x=0: fₙ(0) = 0. For x ∈ (0,1]: fₙ(x) = nx(1−x²)ⁿ → 0 (exponential beats linear). Pointwise limit f ≡ 0. But ∫₀¹ fₙ = n·[−(1−x²)ⁿ⁺¹/(2(n+1))]₀¹ = n/(2(n+1)) → 1/2 ≠ 0. So convergence is **NOT uniform**.

---

### CSIR NET June 2024
**Q10.** f(x,y) = xy/√(x²+y²) for (x,y)≠(0,0), f(0,0)=0. Is f differentiable at origin?

**Answer:** fₓ(0,0) = lim_{h→0} f(h,0)/h = 0. Similarly f_y(0,0) = 0. For differentiability, need |f(h,k)−0−0|/√(h²+k²) = |hk|/(h²+k²) → 0. Along h=k: this = h²/(2h²) = 1/2 ≠ 0. Since the limit along this path is not 0, f is **not differentiable** at (0,0).

---

### CSIR NET Dec 2023
**Q11.** Which of the following series converges uniformly on ℝ?
(a) Σ xⁿ/n!  (b) Σ sin(nx)/n²  (c) Σ xⁿ  (d) Σ 1/(n+x²)

**Answer: (b)** By M-test: |sin(nx)/n²| ≤ 1/n² and Σ1/n² < ∞. Series (a) = eˣ converges to eˣ pointwise on ℝ but not uniformly: sup_x |eˣ − Σ_{k=0}^n xᵏ/k!| = ∞ for every n. Series (c) diverges for |x|≥1. Series (d): terms don't go to 0 uniformly.

---

**Q12.** The Jacobian of the transformation x = r sinφ cosθ, y = r sinφ sinθ, z = r cosφ is:

**Answer: r² sinφ** (spherical coordinates). Volume element: dV = r² sinφ dr dφ dθ.

---

### SET Exam Questions
**Q13.** True/False: A uniformly convergent sequence of differentiable functions converges to a differentiable function.

**Answer: FALSE.** Uniform convergence preserves continuity but NOT differentiability. Need uniform convergence of derivatives too.

---

## 🔷 TOPOLOGY PYQs

### CSIR NET June 2024
**Q14.** In the standard topology on ℝ, which of the following is/are connected?
(a) ℚ  (b) ℝ\ℚ  (c) [0,1]∪[2,3]  (d) (0,1)

**Answer: (d) only.** Both ℚ and ℝ\ℚ are **totally disconnected** in the standard topology — between any two distinct rationals there is an irrational separating them, and vice versa. So (a) and (b) are NOT connected. [0,1]∪[2,3] is disconnected (split at any point in (1,2)). Only (d) is an interval, hence connected. ⚠ This is a CSIR-NET trap: irrationals are NOT connected.

---

### CSIR NET Dec 2023
**Q15.** Which of the following subsets of ℝ² is compact?
(a) {(x,y): x²+y² < 1}  (b) {(x,y): x²+y² ≤ 1}  (c) {(x,y): x²+y² = 1}  (d) Both (b) and (c)

**Answer: (d)** Heine-Borel: compact ⟺ closed and bounded. (a) is open (not closed). Both (b) and (c) are closed and bounded.

---

**Q16.** The cofinite topology on an uncountable set X is:
(a) Hausdorff  (b) T₁ but not T₂  (c) Connected  (d) Both (b) and (c)

**Answer: (d)** Singletons are closed (T₁). Any two non-empty open sets intersect (not T₂). Cannot split X into two non-empty cofinite open sets (connected).

---

### CSIR NET June 2023
**Q17.** A topological space X is such that every subset is compact. Then X must be:
(a) Finite  (b) Countable  (c) Discrete  (d) Indiscrete

**Answer: (a) Finite.** Every subset compact ⟹ every singleton {x} and finite set is compact (trivially), and every subset is closed (in T₁ spaces, compact ⟹ closed) ⟹ X has the discrete topology ⟹ X itself is compact and discrete ⟹ X is finite.

---

### SET Exam Questions
**Q18.** Give an example of a space that is compact but not sequentially compact.

**Answer:** The product space {0,1}^[0,1] with product topology is compact (Tychonoff) but not sequentially compact (not first countable).

---

## 🌀 COMPLEX ANALYSIS PYQs

### CSIR NET Dec 2024
**Q19.** If f is entire with f(1/n) = 1/n² for all n ∈ ℕ, then f(z) = ?

**Answer: f(z) = z².** By identity theorem: f and g(z)=z² agree on {1/n} which has limit point 0. So f = g on all of ℂ.

---

### CSIR NET June 2024
**Q20.** The number of zeros of eᶻ − 4z in the disk |z| < 1 is:

**Answer:** By Rouché's theorem, take f(z) = −4z and g(z) = eᶻ. On |z| = 1: |f(z)| = 4 and |g(z)| = |eᶻ| = e^(Re z) ≤ e¹ ≈ 2.718 < 4 = |f(z)|. Hence |f| > |g| on |z| = 1, so f + g = eᶻ − 4z has the same number of zeros inside |z| < 1 as f = −4z, namely **1 zero**.

(Note: the variant "zeros of eᶻ − z in |z|<1" is *not* a clean Rouché problem because |eᶻ| can exceed |z| at z=1 — caution if you see this on an exam.)

---

### CSIR NET Dec 2023
**Q21.** The order of the entire function f(z) = cos(√z) is:

**Answer:** cos(√z) = Σ (−1)ⁿ zⁿ/(2n)!. Growth: |cos(√z)| ≤ e^|√z| = e^√|z|. So log M(r) ≈ √r, log log M(r) ≈ ½ log r. Order ρ = ½.

---

**Q22.** True/False: There exists a non-constant analytic function from ℂ to the open unit disk.

**Answer: FALSE.** Such a function would be entire and bounded by 1. By Liouville's theorem, it must be constant.

---

## ⚙️ DIFFERENTIAL EQUATIONS PYQs

### CSIR NET June 2024
**Q23.** The system x' = x − y, y' = x + y has the origin as:
(a) Stable node  (b) Unstable spiral  (c) Saddle  (d) Center

**Answer: (b)** A = [[1,−1],[1,1]], eigenvalues: (1−λ)²+1=0 → λ = 1±i. Real part α = 1 > 0 → **Unstable spiral.**

---

### CSIR NET Dec 2023
**Q24.** For which value(s) of α does y' = |y|^α, y(0) = 0 have a unique solution?
(a) α = 1/2  (b) α = 1  (c) α = 2  (d) α ≥ 1

**Answer: (d)** Uniqueness requires Lipschitz condition. |y|^α is Lipschitz near y=0 iff α ≥ 1. For α = 1/2, y = t²/4 (for t ≥ 0) is a second solution (non-unique); for α ≥ 1, uniqueness holds.

---

**Q25.** The critical point (0,0) of the system x' = −y − x³, y' = x − y³ is:
(a) Stable  (b) Unstable  (c) Asymptotically stable  (d) Center

**Answer: (c)** Try V = x² + y². V̇ = 2x(−y−x³) + 2y(x−y³) = −2x⁴ − 2y⁴ < 0 for (x,y) ≠ 0. **Asymptotically stable** by Lyapunov.

---

## 🔄 DYNAMICS PYQs

### University Recruitment Exam
**Q26.** A uniform solid cylinder of mass M and radius R rolls down a rough incline of angle 30°. The acceleration is:

**Answer:** a = g sin30°/(1 + I/(MR²)) = (g/2)/(1 + 1/2) = **g/3 ≈ 3.27 m/s²**

---

**Q27.** Two equal masses are attached to the ends of a light rod of length 2a. The moment of inertia about an axis through the center perpendicular to the rod is:

**Answer:** I = ma² + ma² = **2ma²**

---

**Q28.** A compound pendulum oscillates with period T. The distance between pivot and center of mass is h, and I_O = Mh²(1 + k²/h²). Express T.

**Answer:** T = 2π√(I_O/(Mgh)) = 2π√((k² + h²)/(gh))

The equivalent simple pendulum length = (k² + h²)/h.

---

## 📊 Topic-wise Frequency Analysis (CSIR NET 2019-2025)

| Topic | Avg Questions/Exam | Difficulty | Your Priority |
|-------|-------------------|------------|---------------|
| Linear Algebra | 4-5 | Medium | 🔴 Maximum |
| Real Analysis | 4-5 | Medium-Hard | 🔴 Maximum |
| Abstract Algebra | 3-4 | Hard | 🟡 Sem 2-3 topic |
| Complex Analysis | 2-3 | Medium | 🟠 High |
| Topology | 2-3 | Hard | 🟠 High |
| ODE/PDE | 2-3 | Medium | 🟠 High |
| Probability/Stats | 1-2 | Easy-Medium | 🟡 Sem 3-4 topic |
| Numerical Analysis | 1-2 | Easy | 🟢 Quick prep |
| Classical Mechanics | 1-2 | Medium | 🟢 Via Dynamics |

---

> **💡 Study Tip:** Solve at least 10 years of CSIR NET papers. Focus on Linear Algebra and Real Analysis first — they give you the best score-per-hour-studied ratio.

> **📖 PYQ Resources:**
> - CSIR NET official papers: csirnet.nta.ac.in
> - DIPS Academy question bank: dipsacademy.com
> - IFAS solved papers: ifasonline.com
> - pkalika.in (free solved PYQs for math)
