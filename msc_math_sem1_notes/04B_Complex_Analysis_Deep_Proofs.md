# 🌀 Complex Analysis — Deep Proofs & Extended Examples

> **Supplement to 04_Advanced_Complex_Analysis.md**

---

# CRITICAL PROOFS

## Proof 1: Liouville's Theorem ⚡⚡⚡

**Theorem:** If f is entire and bounded (|f(z)| ≤ M for all z), then f is constant.

**Proof:**
By Cauchy's integral formula for derivatives:
f'(z₀) = (1/2πi) ∮_{|z-z₀|=R} f(z)/(z-z₀)² dz

Taking modulus:
|f'(z₀)| ≤ (1/2π) · (M/R²) · 2πR = M/R

This holds for ALL R > 0. Letting R → ∞: |f'(z₀)| = 0 for every z₀.

So f' ≡ 0 everywhere, meaning f is constant. ∎

**Application: Fundamental Theorem of Algebra**
If p(z) is a non-constant polynomial with no zeros, then 1/p(z) is entire and bounded (since |p(z)| → ∞ as |z| → ∞). By Liouville, 1/p is constant → p is constant. Contradiction! So every non-constant polynomial has a zero. ∎

---

## Proof 2: Maximum Modulus Principle ⚡⚡⚡

**Theorem:** If f is analytic and non-constant on a connected open set D, then |f| has no local maximum in D.

**Proof:**
Suppose |f| attains maximum at z₀ ∈ D. By mean value property:
f(z₀) = (1/2π) ∫₀²π f(z₀ + re^(iθ)) dθ

So |f(z₀)| ≤ (1/2π) ∫₀²π |f(z₀ + re^(iθ))| dθ ≤ max|f| on circle = |f(z₀)|

Equality throughout forces |f(z₀ + re^(iθ))| = |f(z₀)| for all θ. This holds for all small r, so |f| is constant on a neighbourhood of z₀. Since f is analytic and |f| is constant near z₀, the open mapping theorem forces f to be constant on that neighbourhood. By the identity theorem, f is constant on all of D. Contradiction! ∎

---

## Proof 3: Little Picard Theorem (Statement + Proof Idea) ⚡⚡⚡

**Theorem:** A non-constant entire function takes every value with at most one exception.

**Proof idea (using Schottky's theorem):**
Suppose f omits both a and b. WLOG a=0, b=1 (compose with Möbius transformation).
Then g(z) = f(Rz) (for large R) also omits 0 and 1, with g(0) = f(0).
By Schottky's theorem, |g| is bounded on |z| ≤ 1/2 by a quantity depending only on |g(0)| = |f(0)| (fixed) — so the bound does NOT grow with R. Hence |f| is bounded on |z| ≤ R/2 uniformly in R.
Since R is arbitrary, f is bounded on ℂ. By Liouville, f is constant. Contradiction! ∎

---

## Proof 4: Identity Theorem ⚡⚡

**Theorem:** If f, g are analytic on connected D and f = g on a set S with a limit point in D, then f = g on all of D.

**Proof:**
Let h = f − g. Then h has a zero set Z with a limit point z₀ ∈ D.
Since h is analytic at z₀ and h vanishes on a sequence converging to z₀, by the power series representation, h ≡ 0 in a neighborhood of z₀.
The set {z ∈ D : h ≡ 0 near z} is open (by analyticity) and closed (by continuity).
Since D is connected and this set is nonempty, it equals D. So h ≡ 0 on D. ∎

---

## Proof 5: Open Mapping Theorem ⚡⚡

**Theorem:** A non-constant analytic function maps open sets to open sets.

**Proof sketch:**
Let w₀ = f(z₀) and U a neighborhood of z₀. Need to show w₀ is interior to f(U).
Since f − w₀ has an isolated zero at z₀, on a small circle C around z₀: |f(z) − w₀| ≥ δ > 0.
For |w − w₀| < δ: by Rouché's theorem, f(z) − w and f(z) − w₀ have the same number of zeros inside C.
So f(z) = w has a solution inside C ⊂ U. Hence B(w₀, δ) ⊂ f(U). ∎

---

# EXTENDED EXAMPLES

## Liouville Applications — 5 Variations

**Ex 1:** f entire, |f(z)| ≤ 5|z|³ + 7 for all z. Then f is a polynomial of degree ≤ 3.
*Proof:* g(z) = f(z)/z⁴ → 0 as |z| → ∞. By extended Liouville, f⁽⁴⁾ ≡ 0, so f is polynomial of deg ≤ 3.

**Ex 2:** f entire, Re(f) ≤ 100 for all z. Then f is constant.
*Proof:* g(z) = e^(f(z)). Then |g| = e^(Re f) ≤ e¹⁰⁰. So g is entire and bounded → g constant → f constant.

**Ex 3:** f entire, |f(z)| ≥ 1 for all z. Then f is constant.
*Proof:* 1/f is entire with |1/f| ≤ 1. By Liouville, 1/f constant → f constant.

**Ex 4:** f entire, f maps ℝ to ℝ and maps iℝ to iℝ. Show f(z) = f(z̄)̄, the Taylor coefficients are real, and f is odd (a_{2k} = 0 for all k ≥ 0).
*Proof:* g(z) = f(z̄)̄ is also entire and agrees with f on ℝ. By identity theorem, f = g on ℂ.

**Ex 5 (identity-theorem trap):** f entire with f(n) = n/(n+1) for n = 1, 2, 3, .... Is f uniquely determined?

*Answer:* **No.** The set {1, 2, 3, ...} has **no limit point in ℂ** (the only accumulation is at ∞, which is outside the domain). The Identity Theorem requires a limit point INSIDE the domain, so it does NOT apply here. Consequently:

- The rational function $z/(z+1)$ takes the value $n/(n+1)$ at every positive integer, but it is **not entire** (pole at $z = -1$).
- However, $f(z) = z/(z+1) + \sin(\pi z) \cdot h(z)$ does NOT define an entire $f$ either (still has pole at $-1$).
- Instead: any entire function of the form $f(z) = \big(\text{entire interpolant of } \{(n, n/(n+1))\}\big) + \sin(\pi z) \cdot h(z)$ for any entire $h$ takes the right values at positive integers, since $\sin(\pi n) = 0$. So **infinitely many entire** functions satisfy the condition.

**Lesson:** The Identity Theorem fails over a discrete (no limit point) sample set. CSIR-NET trap: the "obvious" guess $z/(z+1)$ is not entire, and entirety + values on the positive integers leaves enormous freedom.

## Harmonic Conjugate — 4 Examples

**Ex 1:** u = x³ − 3xy². Find v.
vₓ = −u_y = 6xy → v = 3x²y + φ(y)
v_y = uₓ = 3x² − 3y² → 3x² + φ'(y) = 3x² − 3y² → φ'(y) = −3y² → φ = −y³
v = 3x²y − y³. So f(z) = z³ + C. ✓

**Ex 2:** u = log(x²+y²) (= 2 log|z|). Harmonic on ℂ\{0}, but ℂ\{0} is **not simply connected**, so there is **no single-valued harmonic conjugate** on the whole punctured plane. Restricting to a simply connected subdomain (e.g., the slit plane ℂ \ (−∞, 0]):
v = 2 Arg(z) (principal branch, Arg ∈ (−π, π)).
f(z) = 2 Log z (principal branch).

**Ex 3:** u = eˣ cos y. v = eˣ sin y. f(z) = eᶻ. (Standard result.)

**Ex 4:** u = x/(x²+y²). Find v.
uₓ = (y²−x²)/(x²+y²)², u_y = −2xy/(x²+y²)²
vₓ = 2xy/(x²+y²)², integrate: v = −y/(x²+y²) + φ(y)
Check v_y = uₓ: confirms φ'(y) = 0. v = −y/(x²+y²).
f(z) = 1/z. ✓

---

# 15 PRACTICE PROBLEMS

**P1.** f is entire with |f(z)| ≤ e^(|Re z|). What can you conclude about the order of f?
**Answer:** log M(r) ≤ r (since |Re z| ≤ |z| = r). Order ρ ≤ 1.

**P2.** Find the order of f(z) = sin z.
**Answer:** M(r) = max_{|z|=r} |sin z| = sinh r ~ e^r/2 (achieved at z = ir). So log M(r)/r → 1, giving ρ = 1, type σ = 1.

**P3.** How many zeros does z⁷ − 5z³ + 12 have in |z| < 1?
**Answer:** On |z|=1: |12| = 12 > |z⁷−5z³| ≤ 1+5 = 6. By Rouché: same as 12 (constant) → **0 zeros**.

**P4.** How many zeros does z⁴ − 6z + 3 have in |z| < 2?
**Answer:** On |z|=2: |z⁴| = 16 > |−6z+3| ≤ 12+3 = 15. By Rouché: same as z⁴ → **4 zeros**.

**P5.** True/False: An analytic function that maps the unit disk to itself and fixes two points is the identity.
**Answer:** TRUE (by Schwarz-Pick lemma — if f fixes two points, it's a rotation that fixes them, hence identity).

**P6.** Prove that a non-constant polynomial takes every complex value.
**Proof:** If p(z) ≠ w₀ for all z, then 1/(p(z)−w₀) is entire and bounded (since |p(z)| → ∞). By Liouville, constant. Contradiction.

**P7.** Find ∫₀²π dθ/(2+cosθ) using residue calculus.
**Answer:** z = e^(iθ), cosθ = (z+z⁻¹)/2. Integral = ∮ dz/[iz(2+(z+z⁻¹)/2)] = ∮ 2dz/[i(z²+4z+1)].
Poles at z = −2±√3. Only z = −2+√3 ∈ unit disk. Residue = 1/√3. Answer = 2π/√3.

**P8.** Construct an entire function with zeros exactly at z = n² (n = 1,2,3,...).
**Answer:** Use Weierstrass: f(z) = Π E₀(z/n²) = Π(1−z/n²) converges since Σ1/n² < ∞.
