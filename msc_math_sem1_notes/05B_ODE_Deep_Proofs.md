# ⚙️ Differential Equations — Deep Proofs & Extended Examples

> **Supplement to 05_Advanced_Differential_Equations.md**

---

# CRITICAL PROOFS

## Proof 1: Picard-Lindelöf (Existence & Uniqueness) ⚡⚡⚡

**Theorem:** If f(t,y) is continuous and Lipschitz in y (|f(t,y₁)−f(t,y₂)| ≤ L|y₁−y₂|), then y' = f(t,y), y(t₀) = y₀ has a unique solution.

**Proof (Banach Fixed Point):**
Define operator T: C[t₀−α, t₀+α] → C by:
(Tφ)(t) = y₀ + ∫_{t₀}^{t} f(s, φ(s)) ds

**T is a contraction:** 
|Tφ₁(t) − Tφ₂(t)| ≤ ∫|f(s,φ₁)−f(s,φ₂)|ds ≤ L∫|φ₁−φ₂|ds ≤ Lα·||φ₁−φ₂||_∞ (sup-norm)

For α < 1/L, T is a contraction with constant Lα < 1.

By Banach fixed point theorem, T has a unique fixed point φ. This φ satisfies:
φ(t) = y₀ + ∫_{t₀}^{t} f(s, φ(s)) ds

Differentiating: φ'(t) = f(t, φ(t)) and φ(t₀) = y₀. So φ is the unique solution. ∎

---

## Proof 2: Gronwall's Inequality ⚡⚡⚡

**Theorem:** If u(t) ≤ α + ∫_{t₀}^{t} β(s)u(s)ds with u,β ≥ 0, α ≥ 0 constant, then u(t) ≤ α·exp(∫_{t₀}^{t} β(s)ds).

**Proof:**
Let v(t) = ∫_{t₀}^{t} β(s)u(s)ds. Then v' = βu ≤ β(α+v) = αβ + βv.

So v' − βv ≤ αβ. Multiply by e^(−∫β): d/dt[v·e^(−∫β)] ≤ αβ·e^(−∫β)

Integrate from t₀ to t:
v(t)·e^(−∫β) ≤ α(1 − e^(−∫β))

So v(t) ≤ α(e^(∫β) − 1), and u(t) ≤ α + v(t) ≤ α·e^(∫β). ∎

---

## Proof 3: Lyapunov Stability Theorem ⚡⚡⚡

**Theorem:** If V: D → ℝ satisfies V(0)=0, V(x)>0 for x≠0, and V̇(x) ≤ 0, then origin is stable. If V̇ < 0 for x≠0, then asymptotically stable.

**Proof (Stability):**
Given ε > 0, let m = min{V(x) : ||x|| = ε} > 0 (V positive on sphere).
Choose δ > 0 such that ||x₀|| < δ ⟹ V(x₀) < m.

If ||x(t₀)|| < δ, then V(x(t₀)) < m. Since V̇ ≤ 0, V(x(t)) ≤ V(x(t₀)) < m for all t ≥ t₀.
But V(x) ≥ m on ||x|| = ε, so ||x(t)|| < ε for all t ≥ t₀. This is stability.

**Asymptotic stability:** V̇ < 0 ⟹ V(x(t)) is strictly decreasing. V is bounded below by 0, so V(x(t)) → c ≥ 0. If c > 0, then x(t) stays in the compact set {c/2 ≤ V ≤ V(x₀)}, where V̇ ≤ −η < 0 for some η > 0. This forces V(x(t)) → −∞, contradicting V ≥ 0. So c = 0, meaning x(t) → 0. ∎

---

## Proof 4: Bendixson's Criterion ⚡⚡

**Theorem:** If ∂f/∂x + ∂g/∂y is of one sign (positive or negative, never zero) in a simply connected region D, then x' = f, y' = g has no periodic orbits in D.

**Proof (by contradiction):**
Suppose Γ is a periodic orbit in D enclosing region R. By Green's theorem:
∮_Γ (f dy − g dx) = ∬_R (∂f/∂x + ∂g/∂y) dA

LHS: On Γ, dx = f dt, dy = g dt. So ∮(f·g − g·f)dt = 0.
RHS: ≠ 0 since integrand has constant sign and is not identically zero.
Contradiction! ∎

---

# EXTENDED EXAMPLES

## Picard Iteration — 4 Complete Examples

**Ex 1:** y' = 1 + y², y(0) = 0.
φ₀ = 0, φ₁ = ∫₀ᵗ (1+0)ds = t, φ₂ = ∫₀ᵗ (1+s²)ds = t + t³/3
φ₃ = ∫₀ᵗ (1+(s+s³/3)²)ds = t + t³/3 + 2t⁵/15 + t⁷/63
Converging to tan(t) (which blows up at t = π/2).

**Ex 2:** y' = −2ty, y(0) = 1.
φ₀ = 1, φ₁ = 1 + ∫₀ᵗ (−2s)ds = 1 − t²
φ₂ = 1 + ∫₀ᵗ −2s(1−s²)ds = 1 − t² + t⁴/2
Converging to e^(−t²).

**Ex 3:** y' = y + t, y(0) = 1.
φ₀ = 1, φ₁ = 1 + ∫₀ᵗ (1+s)ds = 1 + t + t²/2
φ₂ = 1 + ∫₀ᵗ (1+s+s²/2+s)ds = 1 + t + t² + t³/6
Converging to 2eᵗ − t − 1.

**Ex 4 (Non-unique):** y' = 3y^(2/3), y(0) = 0.
Both y ≡ 0 and y = t³ are solutions. Lipschitz fails at y = 0 since |3y^(2/3)| has infinite slope there.

## Critical Point Classification — 6 Complete Examples

**Ex 1:** x' = −x, y' = −2y. A = diag(−1,−2). λ = −1,−2. **Stable node.**

**Ex 2:** x' = x, y' = −y. A = diag(1,−1). λ = 1,−1. **Saddle point (unstable).**

**Ex 3:** x' = −y, y' = x. A = [[0,−1],[1,0]]. λ = ±i. **Center (stable, not asymptotic).**

**Ex 4:** x' = −x+y, y' = −x−y. A = [[−1,1],[−1,−1]]. λ = −1±i. α = −1 < 0. **Stable spiral.**

**Ex 5:** x' = 2x−y, y' = x+2y. λ = 2±i (from det: λ²−4λ+5=0). α = 2 > 0. **Unstable spiral.**

**Ex 6 (Nonlinear):** x' = −x+y², y' = −y. Linearize at (0,0): A = [[−1,0],[0,−1]]. λ = −1,−1. Linear says stable node. Lyapunov confirms: V = x²+y², V̇ = 2x(−x+y²)+2y(−y) = −2x²−2y²+2xy² < 0 near origin. **Asymptotically stable.** ✓

## Lyapunov Function Construction — 5 Examples

**Ex 1:** x' = −x³, y' = −y. V = x²+y². V̇ = −2x⁴−2y² < 0. Asymp. stable. ✓

**Ex 2:** x' = y, y' = −x−y³. V = x²+y². V̇ = 2xy+2y(−x−y³) = −2y⁴ ≤ 0. Stable (not asymp. by this V alone, but by LaSalle: V̇=0 only when y=0, then x'=0 forces x=0. So asymp. stable). ✓

**Ex 3:** x' = −x+2y², y' = −y. V = x²+y⁴. V̇ = 2x(−x+2y²)+4y³(−y) = −2x²+4xy²−4y⁴ = −2(x−y²)²−2y⁴ ≤ 0. ✓

**Ex 4:** For linear system x' = Ax, find V = xᵀPx where AᵀP+PA = −I. Then V̇ = −xᵀx < 0. Solve the **Lyapunov equation** for P.

**Ex 5 (Showing instability):** x' = x³, y' = y. Try V = x²+y². V̇ = 2x⁴+2y² > 0 near origin. Origin is **unstable**. (Chetaev's theorem.)

---

# 15 PRACTICE PROBLEMS

**P1.** Classify: x' = −3x+4y, y' = −2x+3y. 
**Solution:** A = [[−3,4],[−2,3]]. tr = 0, det = −9+8 = −1 < 0. **Saddle point.**

**P2.** For the system x' = y, y' = −sin x − y, is the origin a center?
**Solution:** Linearize at (0,0): A = [[0,1],[−1,−1]]. Char poly λ²+λ+1 = 0, so λ = (−1 ± i√3)/2. Real part α = −1/2 < 0, complex eigenvalues → **stable spiral** (not a center). The damping term −y kills the would-be center.

**P3.** Find eᴬᵗ for A = [[0,1],[−1,0]].
**Solution:** λ = ±i. eᴬᵗ = [[cos t, sin t],[−sin t, cos t]] (rotation matrix).

**P4.** The system x' = x(1−x−y), y' = y(1−2x−y). Find all equilibria.

**Solution:** Set both x' = 0 and y' = 0. Three cases:

- **x = 0**: then y' = y(1−y) = 0 gives y = 0 or y = 1 → equilibria (0, 0) and (0, 1).
- **y = 0**: then x' = x(1−x) = 0 gives x = 0 or x = 1 → equilibria (0, 0) and (1, 0).
- **x ≠ 0 and y ≠ 0**: need 1−x−y = 0 and 1−2x−y = 0. Subtracting gives x = 0, contradicting x ≠ 0. No additional equilibria.

**Equilibria: (0, 0), (1, 0), (0, 1).**

**P5.** Show x' = −x(x²+y²), y' = −y(x²+y²) has asymptotically stable origin.
**Solution:** V = x²+y². V̇ = −2(x²+y²)² < 0 for (x,y)≠0. ✓

**P6.** Does x' = x²+y², y' = xy have periodic orbits?
**Solution:** div(f,g) = ∂(x²+y²)/∂x + ∂(xy)/∂y = 2x + x = 3x. This is positive for x>0 and negative for x<0, so it is NOT of constant sign on any simply connected region containing both half-planes. Bendixson's criterion is inconclusive. However, note that f = x²+y² ≥ 0 always, so ẋ ≥ 0 for all trajectories. Any periodic orbit would need to return to its starting x-coordinate, but x is non-decreasing along trajectories. Hence there are **no periodic orbits**.

**P7.** True/False: Every continuous function f: ℝ → ℝ satisfies Lipschitz condition on compact sets.
**Answer:** FALSE. f(x) = √|x| is continuous on [−1,1] but not Lipschitz at x=0: |f(x)−f(0)|/|x−0| = 1/√|x| → ∞ as x→0.
