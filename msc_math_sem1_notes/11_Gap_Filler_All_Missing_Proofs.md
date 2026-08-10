# 📋 Missing Proofs & Gap-Filler — All Subjects

> **This file plugs every remaining gap across all 6 subjects**

---

# 📊 ANALYSIS — Missing Proofs

## Arzelà-Ascoli Theorem (Full Proof) ⚡⚡

**Theorem:** A sequence {fₙ} in C[a,b] has a uniformly convergent subsequence iff it is uniformly bounded and equicontinuous.

**Proof (⟹):** If fₙₖ → f uniformly, then {fₙₖ} is uniformly bounded (f bounded + uniform tail < ε). Equicontinuity follows since f is uniformly continuous on [a,b] and the convergence is uniform.

**Proof (⟸ — the hard direction):**
**Step 1:** Let {rₖ} = ℚ ∩ [a,b] (countable dense set).
At r₁: {fₙ(r₁)} is bounded → extract convergent subsequence {f₁,ₙ}.
At r₂: {f₁,ₙ(r₂)} is bounded → extract subsequence {f₂,ₙ}.
Continue diagonally: {fₙ,ₙ} converges at EVERY rational.

**Step 2:** Show {fₙ,ₙ} is Cauchy in sup norm.
Given ε > 0, by equicontinuity: ∃δ such that |x−y| < δ ⟹ |fₙ(x)−fₙ(y)| < ε/3 for ALL n.

Cover [a,b] by finitely many intervals of length δ, picking rationals r₁,...,rₖ in each.
Choose N so that |fₘ,ₘ(rⱼ) − fₙ,ₙ(rⱼ)| < ε/3 for all j and m,n ≥ N.

For any x ∈ [a,b], pick rⱼ with |x−rⱼ| < δ:
|fₘ,ₘ(x) − fₙ,ₙ(x)| ≤ |fₘ,ₘ(x)−fₘ,ₘ(rⱼ)| + |fₘ,ₘ(rⱼ)−fₙ,ₙ(rⱼ)| + |fₙ,ₙ(rⱼ)−fₙ,ₙ(x)|
< ε/3 + ε/3 + ε/3 = ε

So {fₙ,ₙ} is uniformly Cauchy → uniformly convergent (C[a,b] is complete). ∎

---

## Stone-Weierstrass Theorem (Proof for polynomials) ⚡⚡

**Weierstrass version:** Every continuous function on [a,b] can be uniformly approximated by polynomials.

**Proof (Bernstein's constructive proof):**
Define the nth Bernstein polynomial:

Bₙ(f;x) = Σₖ₌₀ⁿ f(k/n) · C(n,k) · xᵏ(1−x)ⁿ⁻ᵏ

**Claim:** Bₙ(f;x) → f(x) uniformly on [0,1].

Key identity: Σₖ₌₀ⁿ C(n,k)xᵏ(1−x)ⁿ⁻ᵏ = 1 (binomial theorem).

Using f's uniform continuity: |f(x)−f(k/n)| < ε when |x−k/n| < δ.

Split the sum: terms with |k/n − x| < δ contribute < ε (by uniform continuity), terms with |k/n − x| ≥ δ are controlled by Chebyshev (their total weight is ≤ 1/(4nδ²) → 0).

So |Bₙ(f;x) − f(x)| < ε + 2M/(4nδ²). The second term < ε for all large enough n (namely n > M/(2εδ²)). Hence |Bₙ(f;x) − f(x)| < 2ε uniformly in x. Since ε is arbitrary, convergence is uniform. ∎

---

## Inverse Function Theorem (Complete) ⚡⚡

**Theorem:** If f: ℝⁿ → ℝⁿ is C¹ and det(Df(a)) ≠ 0, then f is a local diffeomorphism near a: there exist neighborhoods U of a and V of f(a) such that f: U → V is bijective with C¹ inverse.

**Proof sketch:**
1. WLOG f(a) = 0, Df(a) = I (compose with linear map).
2. Define g(x) = x − f(x). Then Dg(a) = 0, so ||Dg(x)|| < 1/2 near a.
3. For fixed y near 0, define T_y(x) = y + g(x) = y + x − f(x). Show T_y is a contraction on a small ball.
4. By Banach fixed point, T_y has unique fixed point x = T_y(x), giving f(x) = y.
5. Continuity of f⁻¹: follows from contraction estimates.
6. Differentiability of f⁻¹: D(f⁻¹)(y) = [Df(f⁻¹(y))]⁻¹ (by chain rule). ∎

---

## R-S Integral: Integration by Parts (Proof) ⚡

**Theorem:** ∫ₐᵇ f dα + ∫ₐᵇ α df = f(b)α(b) − f(a)α(a)

**Proof:**
For partition P, the Riemann-Stieltjes sum for ∫f dα is:
S₁ = Σ f(tᵢ)[α(xᵢ) − α(xᵢ₋₁)]

Similarly for ∫α df:
S₂ = Σ α(sᵢ)[f(xᵢ) − f(xᵢ₋₁)]

Now S₁ + S₂ = Σ [f(tᵢ)α(xᵢ) − f(tᵢ)α(xᵢ₋₁) + α(sᵢ)f(xᵢ) − α(sᵢ)f(xᵢ₋₁)]

By Abel summation (summation by parts), this telescopes to f(b)α(b) − f(a)α(a) in the limit as mesh → 0. ∎

---

# 🔷 TOPOLOGY — Missing Proofs

## Tychonoff's Theorem (Statement + Proof Idea) ⚡⚡

**Theorem:** The product of compact spaces is compact (in product topology).

**Proof idea (using Alexander subbasis theorem):**
1. **Alexander's Lemma:** If every cover of X by **subbasis** elements has a finite subcover, then X is compact.
2. Product topology has subbasis: S = { π_α⁻¹(Uα) : α index, Uα open in Xα }.
3. Suppose, for contradiction, that there exists a subbasic cover U ⊆ S of X with NO finite subcover.
4. For each index α, define U_α = { Uα ⊂ Xα open : π_α⁻¹(Uα) ∈ U }. **Claim:** U_α does NOT cover Xα. Otherwise, by compactness of Xα, finitely many of the Uα's would cover Xα; their preimages would lie in U and form a finite subcover of X — contradicting our assumption.
5. So for each α we can pick x_α ∈ Xα \ ∪U_α. Then the point x = (x_α) ∈ ∏ Xα satisfies: for every π_β⁻¹(Uβ) ∈ U, we have x_β ∉ Uβ, so x ∉ π_β⁻¹(Uβ). Thus x lies in NO element of U — contradicting that U covers X. ∎

**Note:** Full proof requires Zorn's lemma (equivalent to Axiom of Choice).

---

## Urysohn's Lemma (Complete) ⚡⚡

**Theorem:** If X is normal and A, B are disjoint closed sets, then ∃ continuous f: X → [0,1] with f(A) = {0}, f(B) = {1}.

**Proof sketch:**
1. By normality, separate A from B: A ⊂ U₁/₂ ⊂ Ū₁/₂ ⊂ X\B.
2. Iterate: separate A from X\U₁/₂ to get U₁/₄, and separate Ū₁/₂ from B to get U₃/₄.
3. Continue for all dyadic rationals r = p/2ⁿ ∈ [0,1]: get open sets Uᵣ with:
   A ⊂ Uᵣ ⊂ Ūᵣ ⊂ Uₛ whenever r < s.
4. Define f(x) = inf{r : x ∈ Uᵣ} (or 1 if x ∉ any Uᵣ).
5. f is continuous (check preimages of (a,∞) and (−∞,a) are open). ∎

---

## Bolzano-Weierstrass ⟺ Compactness in Metric Spaces ⚡⚡

**Theorem:** In a metric space, X is compact ⟺ every sequence has a convergent subsequence.

**Proof (⟹):** X compact. Let {xₙ} be a sequence in X. WLOG assume {xₙ} takes infinitely many distinct values (otherwise some value is repeated infinitely often, giving a constant subsequence). Suppose, for contradiction, that {xₙ} has no convergent subsequence. Then no point x ∈ X is a limit point of the set S = {xₙ : n ∈ ℕ}: for each x ∈ X there is an open ball Bₓ around x with {n : xₙ ∈ Bₓ} finite. The collection {Bₓ : x ∈ X} is an open cover of X; by compactness it has a finite subcover Bₓ₁, …, Bₓₖ. Each Bₓᵢ contains only finitely many xₙ, so the union contains only finitely many — but it must contain ALL xₙ (covers X). This contradicts S being infinite. ∎

**Proof (⟸):** Use: sequentially compact ⟹ totally bounded + complete ⟹ compact (in metric spaces). ∎

---

# 🌀 COMPLEX ANALYSIS — Missing Topics

## Schwarz Lemma ⚡⚡⚡ (frequently tested!)

**Theorem:** If f: D → D is analytic (D = unit disk), f(0) = 0, then:
1. |f(z)| ≤ |z| for all z ∈ D
2. |f'(0)| ≤ 1
3. If |f(z₀)| = |z₀| for some z₀ ≠ 0, or |f'(0)| = 1, then f(z) = e^(iθ)z (rotation).

**Proof:**
g(z) = f(z)/z is analytic in D (removable singularity at 0, g(0) = f'(0)).
On |z| = r < 1: |g(z)| = |f(z)|/r ≤ 1/r.
By maximum principle: |g(z)| ≤ 1/r for |z| ≤ r.
Let r → 1: |g(z)| ≤ 1 for all z ∈ D.
So |f(z)| ≤ |z| and |f'(0)| = |g(0)| ≤ 1.
Equality case: |g| attains maximum 1 inside D ⟹ g is constant e^(iθ) ⟹ f(z) = e^(iθ)z. ∎

---

## Rouché's Theorem ⚡⚡⚡ (for counting zeros)

**Theorem:** If f, g are analytic inside and on a simple closed curve C, and |g(z)| < |f(z)| on C, then f and f+g have the same number of zeros inside C.

**Example:** Zeros of z⁵ + 3z + 1 in |z| < 1.
Take f = 3z, g = z⁵+1. On |z|=1: |f| = 3, |g| ≤ 1+1 = 2 < 3. ✓
f = 3z has 1 zero inside. So z⁵+3z+1 has **1 zero** in |z| < 1.

---

## Residue Theorem Application ⚡⚡⚡

**Computing real integrals using residues:**

**Type 1:** ∫₀²π R(cosθ, sinθ) dθ. Substitute z = e^(iθ), use ∮.

**Type 2:** ∫_{-∞}^{∞} f(x)dx. Close contour in upper half-plane, sum residues.

**Example:** ∫_{-∞}^{∞} dx/(1+x⁴).
Poles of 1/(1+z⁴) at z = e^(iπ/4), e^(3iπ/4), e^(5iπ/4), e^(7iπ/4).
Upper half-plane: z₁ = e^(iπ/4), z₂ = e^(3iπ/4).
Res(z₁) = 1/(4z₁³) = e^(-3iπ/4)/4, Res(z₂) = e^(-9iπ/4)/4 = e^(-iπ/4)/4.
Sum = (e^(-3iπ/4) + e^(-iπ/4))/4 = (−1/√2 − i/√2 + 1/√2 − i/√2)/4 = −i/(2√2).
Integral = 2πi · (−i/(2√2)) = **π/√2**.

---

# ⚙️ ODE — Phase Portraits (Detailed Descriptions)

## How to Sketch Phase Portraits

**Step 1:** Find eigenvalues of A.
**Step 2:** Find eigenvectors.
**Step 3:** Draw eigenvector directions.
**Step 4:** Draw trajectories based on type:

### Stable Node (λ₁ < λ₂ < 0)
- Both eigenvector directions point INWARD
- Trajectories tangent to SLOW eigenvector (λ₂, less negative) far from origin
- Trajectories tangent to FAST eigenvector (λ₁, more negative) near origin
- ALL arrows point toward origin

### Unstable Node (0 < λ₁ < λ₂)
- Same as stable node but ALL arrows point AWAY from origin

### Saddle (λ₁ < 0 < λ₂)
- Stable manifold: along eigenvector of λ₁ (arrows IN)
- Unstable manifold: along eigenvector of λ₂ (arrows OUT)
- Generic trajectories: approach along unstable, then veer away following stable direction — hyperbola-like curves

### Stable Spiral (α ± βi, α < 0)
- No real eigenvectors to draw
- Trajectories spiral INWARD
- Direction (CW or CCW) determined by sign of β and matrix entries
- To determine direction: check where x' > 0 and y' > 0 at a test point

### Center (±βi)
- Closed elliptical orbits
- NO spiraling — orbits are periodic
- Direction determined same as spiral

### Star Node (λ₁ = λ₂, 2 eigenvectors)
- Trajectories are straight lines through origin (all directions)
- Inward if λ < 0, outward if λ > 0

### Improper Node (λ₁ = λ₂, 1 eigenvector)
- Single eigenvector direction is dominant
- Other trajectories curve toward this direction
- Like a node but with a "twist"

---

# 🔄 DYNAMICS — Missing Derivations

## Euler's Equations Derivation ⚡⚡

Starting from L̇ = N (torque) in the fixed frame. In the body frame (rotating with ω):

(dL/dt)_body + ω × L = N

With L = [I]ω and [I] = diag(I₁,I₂,I₃) in principal axes:

Component 1: I₁ω̇₁ + (ω × Iω)₁ = N₁
ω × Iω = (ω₂I₃ω₃ − ω₃I₂ω₂) ê₁ + ... = (I₃−I₂)ω₂ω₃ ê₁ + ...

So: **I₁ω̇₁ + (I₃−I₂)ω₂ω₃ = N₁**
Or equivalently: **I₁ω̇₁ − (I₂−I₃)ω₂ω₃ = N₁** ∎

## Compound Pendulum — Minimum Period ⚡

T² = 4π²(k²+h²)/(gh) where h = pivot-to-CM distance, k = radius of gyration about CM.

dT²/dh = 4π²(2h·gh − g(k²+h²))/(gh)² = 4π²(h²−k²)/(gh²)

Setting = 0: h² = k², so h = k.

T_min = 2π√(2k/g). This equals the period of a simple pendulum of length l = 2k. ∎
