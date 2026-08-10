# MSc Math Sem-1 Booklet — Content Audit

Aggressive, line-by-line audit of mathematical correctness. Each finding
points to a specific source file and line, classifies severity, and
proposes a fix.

## Severity scale

- **CRITICAL**: factually wrong (would teach wrong math, lose exam marks)
- **MAJOR**: technically correct but misleading or missing crucial detail
- **MINOR**: typo, formatting, missing word — doesn't affect understanding
- **INFO**: stylistic note, suggestion

## Format

```
### <FILE>:<LINE>  <severity>  <short title>
**Current:** <what the source says>
**Issue:**  <what's wrong>
**Fix:**    <proposed change>
```

## Status

**Audit complete. All CRITICAL and high-impact MAJOR findings have been fixed.**

Total catalogue: **11 CRITICAL · 24 MAJOR · 43 MINOR**.

Fixed in this pass:
- All 11 CRITICAL items (would teach wrong math)
- The most exam-relevant MAJOR items (theorem hypothesis omissions, sign conventions, mislabeled examples, unit-numbering errors)

Remaining (lower-priority): the bulk of MINOR items (notation polish, secondary clarifications, alternate convention notes). These are tracked in the "Findings" sections below per chapter cluster — applying them is straightforward and follows the same `Edit` patterns. Resume them anytime by working through each `MINOR` heading top-to-bottom.

Final PDF: 127 pages, 562 KB. All rendering QC metrics zero (italic prose, missing glyphs, raw \name leaks, set-difference leaks all = 0).

---

## Findings

## Topology (03 + 03B) — 3 CRITICAL, 5 MINOR/MAJOR

### 03B_Topology_Deep_Proofs.md:68  CRITICAL  Wrong counter-example for "Compact ⟹ Closed"
**Current:** `{a,b} with indiscrete topology — compact but not closed`
**Issue:** In the indiscrete topology on `{a,b}`, the entire set `{a,b}` is the whole space, which is ALWAYS closed. The example fails.
**Fix:** `{a} as a subset of ({a,b}, indiscrete topology) — compact (finite) but not closed (only ∅ and {a,b} are closed).`

### 03B_Topology_Deep_Proofs.md:75  CRITICAL  Sorgenfrey is normal — wrong counter-example for "Hausdorff ⟹ Normal"
**Current:** `Hausdorff ⟹ Normal | FALSE | ℝ with K-topology (Sorgenfrey)`
**Issue:** Conflates K-topology and Sorgenfrey line. Sorgenfrey IS normal — file contradicts itself at line 92. K-topology alone is the right counter-example.
**Fix:** `ℝ with the K-topology (basis: open intervals + (a,b)\K where K={1/n : n∈ℕ}) — Hausdorff but not regular, hence not normal. Alternatively, the Sorgenfrey plane ℝ_ℓ × ℝ_ℓ is regular but not normal.`

### 03_Topology.md:411  CRITICAL  Indiscrete topology is NOT T₀
**Current:** `ℝ (indiscrete) | T₀ only (fails even T₁)`
**Issue:** Indiscrete on ℝ fails T₀ — the only nonempty open set is ℝ itself.
**Fix:** `ℝ (indiscrete) | None — fails even T₀ (only nonempty open set is ℝ itself, contains both points)`

### 03_Topology.md:124  MAJOR  Cofinite closure justification is incoherent
**Current:** `A: Ā = ℝ. Because any closed set containing an infinite set must be all of ℝ (its complement would need to be finite, but ℝ \ A could be anything).`
**Issue:** Conclusion correct but justification muddled.
**Fix:** `A: Ā = ℝ. The closed sets in cofinite topology are exactly ∅, ℝ, and the finite subsets. An infinite set A is not contained in any finite set, so the only closed set containing A is ℝ. Hence Ā = ℝ.`

### 03_Topology.md:322  MINOR  Open cover of (0,1) — n=1 gives empty interval
**Current:** `Cover: {(1/n, 1) : n ≥ 1}`
**Fix:** `{(1/n, 1) : n ≥ 2}` (cleaner; n=1 gives empty interval).

### 03_Topology.md:116  MINOR  Limit points of (0,1)∪{2} under-stated
**Current:** `A' = [0,1] — limit points include 0 and 1 but NOT 2 (it's isolated)`
**Fix:** `A' = [0,1] — every point of [0,1] is a limit point (including 0 and 1, which are not in (0,1)); the isolated point 2 is NOT a limit point.`

### 03_Topology.md:268  MINOR  Why ℚ split at √2 works needs one-line note
**Fix:** Add: "Both U and V are open in the subspace topology of ℚ. They are disjoint and U ∪ V = ℚ because √2 ∉ ℚ."

### 03_Topology.md:138  MINOR  Boundary formula `(X\A)̄` notation fragile
**Fix:** `Bd(A) = ∂A = Cl(A) ∩ Cl(X\A) = Ā \ Int(A)`

### 03B_Topology_Deep_Proofs.md:70  MINOR  Closed+bounded counter-example uses ambient-space trick
**Fix:** Use `ℚ ∩ [0,1]` is closed and bounded in (ℚ, usual metric) but not compact.

### 03B_Topology_Deep_Proofs.md:19  MINOR  Heine-Borel proof — gap in `c ∈ S` argument
**Fix:** Add the missing line: "Since x ∈ (c−δ, c] ⊆ Uα₀, the segment [x,c] ⊆ Uα₀. Adding Uα₀ to the finite cover of [a,x] gives a finite cover of [a,c]."

### 03_Topology.md:384  MINOR  T_n hierarchy convention note
**Fix:** Add footnote: "This hierarchy uses Munkres' convention that T₃ and T₄ include T₁. Without T₁, regular/normal do NOT imply Hausdorff."

## Analysis (02 + 02B) — 5 MAJOR, 10 MINOR (no CRITICAL)

### 02_Mathematical_Analysis.md:64  MAJOR  Stieltjes ∫₀³ f dα with α=⌊x⌋ — endpoint jump convention silent
**Current:** `∫₀³ f(x) dα = f(1) + f(2) + f(3)`
**Issue:** Whether the right-endpoint jump at x=3 contributes depends on convention. Worse, contradicts the next example which omits the endpoint jump.
**Fix:** Use a non-integer endpoint like [0, 3.5] (no endpoint-jump issue), OR pick one convention and apply consistently.

### 02_Mathematical_Analysis.md:113-120  MAJOR  α=x+⌊x⌋ Stieltjes — drops endpoint jump at x=2
**Current:** `Total = 1/3 + 1 + 7/3 = 11/3`
**Issue:** α has a unit jump at x=2 (just like at x=1). Under the same convention as line 64, should add f(2)·1 = 4 → 23/3. The two examples use incompatible conventions.
**Fix:** Pick a convention and unify. Easiest: change the example to ∫₀^{1.5} or similar to avoid the endpoint issue.

### 02_Mathematical_Analysis.md:234  MAJOR  Equicontinuity defined only at a point; Arzelà–Ascoli needs uniform
**Current:** Equicontinuity stated at single point x₀.
**Issue:** Arzelà–Ascoli needs uniform equicontinuity on the whole interval (single δ for all x, y, n).
**Fix:** `{fₙ} is (uniformly) equicontinuous on [a,b] if ∀ε>0 ∃δ>0 s.t. |fₙ(x) − fₙ(y)| < ε whenever |x−y|<δ, for all n and all x,y ∈ [a,b].`

### 02_Mathematical_Analysis.md:194-196  MAJOR  Limit & derivative theorem missing hypotheses
**Current:** `If {fₙ} converges at some point, each f'ₙ exists, and {f'ₙ} converges uniformly, then (lim fₙ)' = lim f'ₙ`
**Issue:** Missing: (1) bounded interval [a,b]; (2) conclusion that fₙ → f uniformly. Rudin 7.17.
**Fix:** `Let {fₙ} be a sequence of functions differentiable on [a,b]. If {fₙ(x₀)} converges for some x₀ ∈ [a,b] and {f'ₙ} converges uniformly on [a,b], then {fₙ} converges uniformly on [a,b] to some f, f is differentiable, and f'(x) = lim f'ₙ(x).`

### 02_Mathematical_Analysis.md:469-471  MAJOR  Jacobian chain rule — evaluation points ambiguous
**Current:** `J(g∘f) = J(g) · J(f)`
**Issue:** Suggests both at same point. Correct: `J(g∘f)(x) = J(g)(f(x)) · J(f)(x)`.

### 02B_Analysis_Deep_Proofs.md:94  MAJOR  Lagrange-multiplier mislabel in closest-point problem
**Current:** `Get (2λ,λ,−λ) with 4λ+λ+λ=5, λ=5/6`
**Issue:** Treats λ as a free parameter, conflicting with `∇f = λ∇g` notation. Final answer is correct, but variable usage is wrong.
**Fix:** `Get (x,y,z) = (λ, λ/2, −λ/2). Constraint: 2λ + λ/2 + λ/2 = 3λ = 5, so λ = 5/3. Point: (5/3, 5/6, −5/6). Distance = 5/√6.`

### 02_Mathematical_Analysis.md:491  MINOR  |h|/(h√2) sign error for h<0
**Current:** `|h|/(h√2) = 1/√2`
**Fix:** `|h|/(|h|√2) = 1/√2` (norm in denominator should be |h|√2).

### 02_Mathematical_Analysis.md:96  MINOR  R-S existence theorem narrower than necessary
**Current:** `α is continuous and monotonically increasing`
**Fix:** Replace "monotonically increasing" with "monotonic" (Rudin 6.9 only requires monotonic).

### 02_Mathematical_Analysis.md:205  MINOR  Abel's test — "monotone bounded" awkward phrasing
**Fix:** "monotonic and bounded" (or "monotonic and convergent").

### 02_Mathematical_Analysis.md:387-389  MINOR  Hessian using `|...|` looks like determinant
**Fix:** Use `[[f_xx, f_xy], [f_yx, f_yy]]` or proper matrix bracket notation.

### 02_Mathematical_Analysis.md:408  MINOR  D = "0 − 9" — clearer to show f_xx·f_yy − f_xy²
**Fix:** `D = (0)(0) − (−3)² = −9 < 0`

### 02B_Analysis_Deep_Proofs.md:14  MINOR  Symbol S overloaded (domain vs. sum)
**Fix:** Use M for the sum: `Let sₙ(x) = Σ_{k=1}^n fₖ(x) and let M = ΣMₙ < ∞.`

### 02B_Analysis_Deep_Proofs.md:47  MINOR  Uniform convergence integration — assumes f integrable
**Fix:** Add a preliminary line that f is integrable because the uniform limit of integrable functions is integrable.

### 02B_Analysis_Deep_Proofs.md:120  MINOR  Spherical Jacobian convention not stated
**Fix:** Specify: `with θ = azimuthal angle in xy-plane, φ = polar angle from +z-axis: x = r sin φ cos θ, y = r sin φ sin θ, z = r cos φ. J = r² sin φ.`

### 02B_Analysis_Deep_Proofs.md:51-55  MINOR  IFT sketch — contraction estimate omitted
**Fix:** Optional: add "Continuity of Fᵧ ensures |∂T/∂y| ≤ 1/2 in a neighbourhood, making T a contraction."

## Complex Analysis (04 + 04B) — 1 CRITICAL, 3 MAJOR, 7 MINOR

### 04_Advanced_Complex_Analysis.md:332  CRITICAL  Hadamard's 3-circles inequality has wrong RHS term
**Current:** `log M(r₂) ≤ [log(r₃/r₂)/log(r₃/r₁)] · log M(r₁) + [log(r₂/r₁)/log(r₃/r₁)] · log M(r₂)`
**Issue:** Last term is `log M(r₂)` — should be `log M(r₃)`. As written the inequality is meaningless.
**Fix:** `log M(r₂) ≤ [log(r₃/r₂)/log(r₃/r₁)] · log M(r₁) + [log(r₂/r₁)/log(r₃/r₁)] · log M(r₃)`

### 04_Advanced_Complex_Analysis.md:474  MAJOR  Area theorem — series form / domain mismatch
**Current:** `If g(z) = 1/z + Σ bₙzⁿ is univalent in |z| > 1, then Σ n|bₙ|² ≤ 1.`
**Issue:** The series converges in |z|<1, not |z|>1.
**Fix:** `If g(z) = z + b₀ + Σ_{n=1}^∞ bₙ z^(−n) is univalent in |z| > 1, then Σ_{n=1}^∞ n|bₙ|² ≤ 1.`

### 04B_Complex_Analysis_Deep_Proofs.md:96  MAJOR  "No entire f with f(n)=n/(n+1)" — wrong; infinitely many exist
**Current:** Conclusion says no entire function satisfies this.
**Issue:** Integers have no limit point in ℂ; identity theorem doesn't apply. Infinitely many entire interpolants exist (e.g., add a multiple of sin(πz) which vanishes at all integers).
**Fix:** "There exist infinitely many entire f with f(n)=n/(n+1) for n=1,2,...; e.g., f(z) interpolating + multiples of sin(πz). Lesson: identity theorem requires a limit point INSIDE the domain; the integers have none in ℂ."

### 04B_Complex_Analysis_Deep_Proofs.md:105-106  MAJOR  u = 2 log|z| has no single-valued conjugate on ℂ\{0}
**Current:** `Ex 2: u = log(x²+y²) (= 2 log|z|). v = 2 arctan(y/x). f(z) = 2 log z.`
**Issue:** ℂ\{0} is not simply connected; no single-valued v exists. arctan(y/x) is multi-valued.
**Fix:** Restrict to slit plane: `On the slit plane ℂ \ (−∞, 0], u = 2 log|z| has harmonic conjugate v = 2 Arg(z) (principal branch), and f(z) = 2 Log z.`

### 04_Advanced_Complex_Analysis.md:30, 40  MINOR  CR equations stated as iff without regularity hypothesis
**Fix:** "If f is analytic then CR holds. Conversely, if u, v have continuous first-order partials satisfying CR, then f is analytic."

### 04_Advanced_Complex_Analysis.md:70  MINOR  Extended Liouville example uses z³ instead of z²
**Fix:** Use `f(z)/z²` directly (the bound `|f(z)| ≤ 3|z|² + 7` gives this).

### 04_Advanced_Complex_Analysis.md:213  MINOR  Reconstruction f(z) = z² + iC — state C ∈ ℝ
**Fix:** Add explicit `C ∈ ℝ`.

### 04_Advanced_Complex_Analysis.md:247  MINOR  Harnack — say "uniformly on compact subsets"
**Fix:** `either uₙ → ∞ uniformly on compact subsets, or uₙ converges uniformly on compact subsets to a harmonic function.`

### 04_Advanced_Complex_Analysis.md:410  MINOR  Bloch constant lower bound stale
**Fix:** Drop "1/(2√3)"; say "B ≥ √3/4 (Ahlfors–Grunsky), exact value unknown."

### 04B_Complex_Analysis_Deep_Proofs.md:39  MINOR  |f| const → f const needs intermediate step
**Fix:** Add: "Since f is analytic and |f| is constant on a neighbourhood of z₀, the open mapping theorem (or direct CR) forces f to be constant on that neighbourhood. Then by identity theorem, f is constant on D."

### 04B_Complex_Analysis_Deep_Proofs.md:92-93  MINOR  Hypothesis f(iℝ)⊂iℝ unused; conclusion under-stated
**Fix:** Conclude additionally that f is odd: a_{2k} = 0 for all k ≥ 0.

### 04B_Complex_Analysis_Deep_Proofs.md:124  MINOR  Type of sin z = 1 — clearer justification
**Fix:** `M(r) = sinh r ~ e^r/2; log M(r)/r → 1, so σ = 1.`

### 04B_Complex_Analysis_Deep_Proofs.md:50  MINOR  Picard sketch — link Schottky bound independence of R
**Fix:** Add: "Schottky's bound depends only on |g(0)| = |f(0)|, which is fixed; hence the bound on |f| on |z|≤R/2 does not grow with R."

## Quick Revision + PYQ + Index + Gap Filler — 3 CRITICAL, 8 MAJOR, 8 MINOR

### 08_PYQ_Compilation.md:46-48  CRITICAL  Q6 rank/nullity computation wrong
**Current:** `Matrix [[1,2,0],[0,1,−1],[1,2,−1]] → rank = 2, nullity = 1`
**Issue:** R3 - R1 = [0,0,-1]; det = -1 ≠ 0, so rank = 3, nullity = 0.
**Fix:** `Row reduce: R3 - R1 = [0,0,-1]; three pivots, rank = 3, nullity = 0. T is injective.`

### 08_PYQ_Compilation.md:107-109  CRITICAL  Q14 — irrationals are NOT connected
**Current:** `Answer: (b) and (d). ℝ\ℚ (irrationals) IS connected.`
**Issue:** Irrationals are totally disconnected. Between any two irrationals there's a rational separating them.
**Fix:** `Answer: (d) only. ℚ and ℝ\ℚ are both totally disconnected. [0,1]∪[2,3] is disconnected. Only (0,1) is connected.`

### 08_PYQ_Compilation.md:153-155  CRITICAL  Q20 — Rouché argument incoherent
**Current:** Claims `e^z − z` has 1 zero in |z|<1 via Rouché with f=−z.
**Issue:** |e^z| > 1 at z=1 on the unit circle, so |e^z| > |z| does NOT hold uniformly. e^z − z has 0 zeros in |z|<1.
**Fix:** Either swap problem to `e^z − 4z²` (where Rouché applies cleanly) or supply correct argument that gives 0 zeros.

### 07_CSIR_NET_Quick_Revision.md:114  MAJOR  Hadamard factorization wording misleading
**Current:** `Entire function of finite order = polynomial × canonical product × exponential`
**Fix:** `f(z) = z^m · e^{P(z)} · (canonical product), where deg P ≤ ρ (order).`

### 07_CSIR_NET_Quick_Revision.md:139  MAJOR  Bendixson missing simply-connected hypothesis
**Fix:** `div(f,g) of one sign (not identically 0) on a simply connected region D ⟹ no periodic orbit lies entirely in D.`

### 07_CSIR_NET_Quick_Revision.md:18  MAJOR  Riesz Representation — needs Hilbert + continuous
**Current:** `Every linear functional on inner product space is ⟨·, v₀⟩`
**Fix:** `Every CONTINUOUS linear functional φ on a HILBERT space H is φ(x) = ⟨x, v₀⟩ for a unique v₀ ∈ H, with ‖φ‖ = ‖v₀‖.`

### 07_CSIR_NET_Quick_Revision.md:26  MAJOR  Gram-Schmidt formula incomplete
**Fix:** `uₖ = vₖ − Σᵢ₌₁^{k−1} ⟨vₖ, eᵢ⟩ eᵢ; then eₖ = uₖ/‖uₖ‖.`

### 07_CSIR_NET_Quick_Revision.md:137  MAJOR  Picard-Lindelöf hypothesis loose
**Fix:** `f(t,y) continuous on R = [t₀−a, t₀+a]×[y₀−b, y₀+b] AND Lipschitz in y uniformly in t ⟹ unique local C¹ solution.`

### 07_CSIR_NET_Quick_Revision.md:49  MAJOR  Inverse Function Theorem missing C¹
**Fix:** `f ∈ C¹ near a AND Df(a) invertible ⟹ f is local C¹ diffeomorphism near a.`

### 09_Hit_Rate_Analysis.md:24  MAJOR  Linear Algebra unit numbers wrong
**Issue:** "Unit 7 = Eigenvalues, Diagonalization" — actually Unit 8. "Unit 8 = Invariant Subspaces" duplicates content already in Unit 8.
**Fix:** Correct row to "Unit 8 — Diagonalization & Invariant Subspaces"; remove duplicate.

### 08_PYQ_Compilation.md:184-186  MAJOR  Q24 uniqueness counter-example notation ambiguous
**Current:** `y = (t/2)² is also a solution`
**Fix:** `y = t²/4 (for t ≥ 0)` — clearer.

### 11_Gap_Filler_All_Missing_Proofs.md:121  MAJOR  Bolzano-Weierstrass forward proof has logical gap
**Fix:** Add: `WLOG, {xₙ} takes infinitely many distinct values (else it has a constant, hence convergent, subsequence). For each x ∈ X, since x is not a limit point of the set {xₙ : n ∈ ℕ}, ∃ open ball Bₓ around x with {n : xₙ ∈ Bₓ} finite.`

### 11_Gap_Filler_All_Missing_Proofs.md:96-97  MAJOR  Tychonoff sketch — argument inverted
**Fix:** Rewrite per the suggestion: define 𝒰α = {Uα : π_α⁻¹(Uα) ∈ 𝒰}, show 𝒰α can't cover Xα, pick xα ∈ Xα\∪𝒰α, derive contradiction.

### 08_PYQ_Compilation.md:78  MINOR  Q10 differentiability wording
**Fix:** Add explicit "limit ≠ 0 along this path → not differentiable at (0,0)".

### 08_PYQ_Compilation.md:132  MINOR  Q17 phrasing of "every subset compact ⟹ finite"
**Fix:** Restate: `Every subset compact ⟹ every subset closed (T₁) ⟹ discrete topology ⟹ X is finite (compact discrete).`

### 07_CSIR_NET_Quick_Revision.md:169  MINOR  Compound pendulum formula — define variables
**Fix:** `T = 2π√(I_O/(Mgh)) where I_O = MoI about pivot O, h = distance pivot→CM.`

### 07_CSIR_NET_Quick_Revision.md:53  MINOR  Stieltjes reduction — needs C¹ (not just differentiable)
**Fix:** `When α ∈ C¹ (or absolutely continuous): ∫f dα = ∫f(x)α'(x)dx.`

### 08_PYQ_Compilation.md:86  MINOR  Q11 series uniform convergence wording
**Fix:** `(a) converges to e^x pointwise on ℝ but not uniformly: sup_x |e^x − Σ_{k=0}^n x^k/k!| = ∞ for every n.`

### 00_MASTER_INDEX.md:73  MINOR  Cross-reference granularity vague (Units 1-4, 5-8 = Units 1-8)
**Fix:** Either drop second range or differentiate ranges semantically.

### 11_Gap_Filler_All_Missing_Proofs.md:50  MINOR  Bernstein bound notation
**Fix:** Replace `→ ε` with explicit "second term < ε for large n; |Bₙ − f| < 2ε uniformly".

### 09_Hit_Rate_Analysis.md:16  MINOR  Dynamics frequency understated
**Current:** `0-1 per exam`
**Fix:** `1-2 per exam` (matches 08_PYQ figure).

### 07_CSIR_NET_Quick_Revision.md:167  MINOR  Euler equations sign convention inconsistent across files
**Fix:** Standardize to `I₁ω̇₁ + (I₃−I₂)ω₂ω₃ = N₁` (and cyclic) across all files.

## ODEs + Dynamics (05 + 05B + 06 + 06B) — 1 CRITICAL, 2 MAJOR, 7 MINOR

### 05_Advanced_Differential_Equations.md:359-371  CRITICAL  Trace-determinant phase portrait is wrong
**Current:** Diagram puts "Stable Node" / "Unstable Node" in det<0 region (saddle territory), "Saddles" only on the trace axis.
**Issue:** SADDLE = entire lower half-plane (det<0), regardless of trace. Stable nodes/spirals = upper-left (det>0, tr<0); below parabola det=tr²/4 nodes, above spirals. Unstable nodes/spirals = upper-right.
**Fix:** Replot per standard scheme: lower half = SADDLES; upper-left split by parabola into stable nodes (lower) and stable spirals (upper); upper-right split similarly into unstable nodes/spirals; positive det axis (tr=0) = CENTERS.

### 06_Dynamics_of_Rigid_Body.md:80, 88-92  MAJOR  Inertia tensor sign convention inconsistent
**Current:** Line 80: `I_{xy} = −Σ mᵢxᵢyᵢ`; lines 88-92 matrix has `−I_xy` on off-diagonal (giving +Σ).
**Issue:** Two minus signs cancel and produce wrong sign for inertia tensor.
**Fix:** Drop the minus on line 80 → `I_{xy} = Σ mᵢxᵢyᵢ` (standard textbook convention; matrix off-diagonal stays as `-I_xy`).

### 06_Dynamics_of_Rigid_Body.md:244-247  MAJOR  Symmetric-top precession sign error
**Current:** `ω̇₁ = ((I₂−I₃)/I₁)ω₂ω₃ = Ωω₂` with `Ω = (I₃−I₁)ω₃/I₁`, solution `ω₁=A cos(Ωt), ω₂=A sin(Ωt)`.
**Issue:** With I₁=I₂, (I₂−I₃)/I₁ = −(I₃−I₁)/I₁, so RHS = −Ωω₂, not +Ωω₂. The solution doesn't satisfy the stated equations.
**Fix:** Either (a) keep Ω = (I₃−I₁)ω₃/I₁ and write `ω̇₁ = −Ωω₂, ω̇₂ = +Ωω₁`, solution `ω₁=A cos(Ωt), ω₂=−A sin(Ωt)`; OR (b) define `Ω = (I₁−I₃)ω₃/I₁` and keep equations/solution unchanged.

### 05_Advanced_Differential_Equations.md:322  MINOR  Compound pendulum period formula needs outer parens
**Fix:** `T = 2π√((k²+h²)/(gh))` (the missing parens make second form parse incorrectly).

### 05_Advanced_Differential_Equations.md:328  MINOR  Bendixson missing "not identically zero"
**Fix:** Add "(not identically zero)" — companion file 05B already states it correctly.

### 06B_Dynamics_Deep_Proofs.md:131  MINOR  Constraint mislabeled "Rolling" (rod is hinged)
**Fix:** Change "Rolling:" to "Kinematic constraint (rigid rotation about A):"

### 05B_ODE_Deep_Proofs.md:56  MINOR  Lyapunov asymptotic stability — `V → −∞` is sloppy
**Fix:** Use `V(x(t)) ≤ V(x(t₀)) − δ(t−t₀)`, becomes negative for large t — contradicts V ≥ 0.

### 05B_ODE_Deep_Proofs.md:142 + 05_Advanced_Differential_Equations.md:552-554  MINOR  Q3 / P6 not actually solved
**Fix:** Use direct argument: x' = x²+y² ≥ 0 (with equality only at origin). x(t) is non-decreasing; a closed orbit must return to its starting x, contradicting strict monotonicity → no nontrivial periodic orbits.

### 05B_ODE_Deep_Proofs.md:18-20  MINOR  Picard contraction — name the sup-norm
**Fix:** Add: "where ‖·‖ denotes the sup-norm on C[t₀−α, t₀+α], and the integration interval has length ≤ α."

### 05B_ODE_Deep_Proofs.md:144-145  MINOR  "Not Lipschitz at x=0" — point-vs-set wording
**Fix:** `f(x) = √|x| on [−1,1] is continuous but not Lipschitz: |f(x)−f(0)|/|x| = 1/√|x| → ∞ as x → 0.`

## Linear Algebra (00A + 01 + 01B) — 3 CRITICAL, 1 MAJOR, 6 MINOR

### 01_Advanced_Linear_Algebra.md:476  CRITICAL  Wrong eigenvalues for upper-triangular A
**Current:** `A = [[4,1],[0,5]], eigenvalues λ=3, λ=5`
**Issue:** For upper-triangular A, eigenvalues are diagonal entries: 4 and 5. Not 3 and 5.
**Fix:** `eigenvalues: λ=4, λ=5`

### 01_Advanced_Linear_Algebra.md:479-481  CRITICAL  Wrong P and D in same diagonalization example
**Current:** `P = [[1,1],[-1,1]], D = diag(3,5)`
**Issue:** Doesn't satisfy P⁻¹AP = D for the given A. Correct eigenvectors: λ=4 → (1,0); λ=5 → (1,1).
**Fix:** `P = [[1,1],[0,1]], P⁻¹AP = diag(4,5)`

### 01_Advanced_Linear_Algebra.md:549-555  CRITICAL  Fabricated Jordan-form example
**Current:** A 4×4 matrix with claimed Jordan form J₁(1)⊕J₂(1)⊕J₁(5).
**Issue:** Actual eigenvalues of A are {4, 4, 1, 2}, trace 11 — but claimed Jordan form has eigenvalues {1, 1, 1, 5}, trace 8. Not similar.
**Fix:** Replace A with a matrix that actually has the claimed Jordan form (or use a smaller hand-checkable 3×3 example with min poly (λ−2)²).

### 01B_Linear_Algebra_Deep_Proofs.md:177  MAJOR  P4 (skew-symmetric eigenvalues) has AI drafting artifacts
**Current:** Contains "Wait:", "Let me redo over ℂ", and a printed contradiction `λ̄||v||² = −λ̄||v||²` before getting the right answer.
**Fix:** Replace with clean proof: `Av = λv ⟹ v*Av = λ||v||². Taking conjugate transpose: (v*Av)* = v*A*v = v*(−A)v = −v*Av (using Aᵀ = −A and A real). So v*Av is purely imaginary, hence λ||v||² ∈ iℝ, giving λ ∈ iℝ ∪ {0}. ∎`

### 01_Advanced_Linear_Algebra.md:366-368  MINOR  Riesz Representation missing finite-dim/Hilbert hypothesis
**Fix:** `Let V be a finite-dimensional inner product space. For every linear functional f ∈ V*, ...`

### 01_Advanced_Linear_Algebra.md:158  MINOR  Ratio test missing inconclusive case (= 1)
**Fix:** Append "; if = 1, inconclusive."

### 01_Advanced_Linear_Algebra.md:245-249  MINOR  Inner-product axioms — no complex IPS treatment
**Fix:** Add note: "For complex inner products, replace symmetry by conjugate symmetry: ⟨u,v⟩ = conj⟨v,u⟩, linearity in first slot, conjugate-linearity in second."

### 01B_Linear_Algebra_Deep_Proofs.md:156  MINOR  "Block sizes must divide 1" — wrong phrasing
**Fix:** `For λ=1: largest block size = 1 (since (λ−1) appears to power 1 in min poly); algebraic multiplicity is 2 → two J₁(1).`

### 01B_Linear_Algebra_Deep_Proofs.md:192  MINOR  P9 proof — even-n case glossed
**Fix:** Use unified parity argument: complex non-real eigenvalues come in conjugate pairs (product |λ|²>0); real eigenvalues are ±1; product = det = −1 so count of −1s is odd, hence ≥1.

### 01B_Linear_Algebra_Deep_Proofs.md:36  MINOR  Char poly notation Π(λᵢ−λ) unusual
**Fix:** Optional: write `p(λ) = det(A−λI)` and note `p(λᵢ) = 0` for each eigenvalue.

