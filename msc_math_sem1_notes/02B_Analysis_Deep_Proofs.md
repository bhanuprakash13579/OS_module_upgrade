# 📊 Mathematical Analysis — Deep Proofs & Extended Examples

> **Supplement to 02_Mathematical_Analysis.md**

---

# CRITICAL PROOFS

## Proof 1: Weierstrass M-Test ⚡⚡⚡

**Theorem:** If |fₙ(x)| ≤ Mₙ for all x ∈ S and ΣMₙ converges, then Σfₙ converges uniformly on S.

**Proof:**
Let sₙ(x) = Σₖ₌₁ⁿ fₖ(x) and let M = ΣMₙ < ∞.

For m > n: |sₘ(x) − sₙ(x)| = |Σₖ₌ₙ₊₁ᵐ fₖ(x)| ≤ Σₖ₌ₙ₊₁ᵐ |fₖ(x)| ≤ Σₖ₌ₙ₊₁ᵐ Mₖ

Since ΣMₙ converges, the tail Σₖ₌ₙ₊₁^∞ Mₖ → 0 as n → ∞.

Given ε > 0, choose N so that Σₖ₌ₙ₊₁^∞ Mₖ < ε for all n ≥ N.
Then |sₘ(x) − sₙ(x)| < ε for ALL x ∈ S and all m > n ≥ N.

By Cauchy criterion for uniform convergence, Σfₙ converges uniformly. ∎

---

## Proof 2: Uniform Convergence Preserves Continuity ⚡⚡⚡

**Theorem:** If fₙ → f uniformly on S and each fₙ is continuous at c, then f is continuous at c.

**Proof:**
|f(x) − f(c)| ≤ |f(x) − fₙ(x)| + |fₙ(x) − fₙ(c)| + |fₙ(c) − f(c)|

Given ε > 0:
- By uniform convergence, ∃N: |fₙ(x) − f(x)| < ε/3 for ALL x, for n ≥ N (choose such n)
- By continuity of fₙ at c, ∃δ: |fₙ(x) − fₙ(c)| < ε/3 when |x−c| < δ

Then |f(x) − f(c)| < ε/3 + ε/3 + ε/3 = ε when |x−c| < δ. ∎

---

## Proof 3: Uniform Convergence and Integration ⚡⚡

**Theorem:** If fₙ → f uniformly on [a,b] and each fₙ is integrable, then f is integrable and ∫fₙ → ∫f.

**Proof:**
First, f is integrable: the uniform limit of integrable (Riemann) functions is integrable, since uniform convergence gives uniform control on oscillations.

Then: |∫ₐᵇ fₙ − ∫ₐᵇ f| = |∫ₐᵇ (fₙ − f)| ≤ ∫ₐᵇ |fₙ − f| ≤ (b−a) · sup|fₙ − f| → 0. ∎

---

## Proof 4: Implicit Function Theorem (2D case) ⚡⚡

**Theorem:** If F(a,b) = 0, F is C¹, and F_y(a,b) ≠ 0, then near (a,b), y = g(x) with g'(a) = −Fₓ(a,b)/F_y(a,b).

**Proof idea:** Apply Banach fixed point theorem to the map T(y) = y − F(x,y)/F_y(a,b) for fixed x near a. Since F_y(a,b) ≠ 0 and F is C¹, continuity of F_y ensures |∂T/∂y| = |1 − F_y/F_y(a,b)| ≤ 1/2 in a neighbourhood of (a,b), making T a contraction. The derivative formula follows by implicit differentiation of F(x,g(x)) = 0. ∎

---

## Proof 5: Second Derivative Test (2D) ⚡⚡⚡

**Theorem:** At critical point (a,b) with D = fₓₓf_yy − f_xy² > 0, fₓₓ > 0 ⟹ local min.

**Proof:** By Taylor: f(a+h,b+k) − f(a,b) = ½(fₓₓh² + 2f_xyhk + f_yyk²) + higher order
= ½fₓₓ[(h + f_xyk/fₓₓ)² + (D/fₓₓ²)k²]

When D > 0 and fₓₓ > 0, the bracketed expression is sum of squares → positive. ∎

---

# EXTENDED EXAMPLES

## Uniform Convergence — 6 Examples

**Ex 1:** fₙ(x) = x/n on [0,1]. sup|fₙ| = 1/n → 0. UNIFORM. ✓
**Ex 2:** fₙ(x) = xⁿ on [0,1]. sup|fₙ − f| = sup on [0,1) of xⁿ = 1 (at x→1⁻). NOT uniform.
**Ex 3:** fₙ(x) = xⁿ on [0, 1/2]. sup = (1/2)ⁿ → 0. UNIFORM on [0, 1/2]. ✓
**Ex 4:** fₙ(x) = sin(x/n) on ℝ. |sin(x/n)| ≤ |x/n| → need bound independent of x. On ℝ: NOT uniform. On [−M,M]: uniform.
**Ex 5:** Σ xⁿ/n! on [−R,R]. By M-test with Mₙ = Rⁿ/n!. UNIFORM on bounded intervals.
**Ex 6:** fₙ(x) = nx·e^(−nx²). Max at x = 1/√(2n), max value = √(n/(2e)) → ∞. NOT uniform on [0,1].

## Lagrange Multipliers — 5 Examples

**Ex 1:** Max/min f = x+y on x²+y² = 1.
∇f = (1,1) = λ(2x,2y). So x=y=1/(2λ). Constraint: 2/(4λ²)=1, λ=±1/√2.
Max = √2 at (1/√2, 1/√2). Min = −√2 at (−1/√2, −1/√2).

**Ex 2:** Min f = x²+y²+z² subject to x+y+z = 3.
∇f = λ∇g: (2x,2y,2z) = λ(1,1,1). So x=y=z. From constraint: x=y=z=1. Min = 3.

**Ex 3:** Max f = xyz subject to x+y+z = 12, x,y,z > 0.
By AM-GM or Lagrange: x=y=z=4. Max = 64.

**Ex 4:** Closest point on plane 2x+y−z = 5 to origin.
Minimize f = x²+y²+z² subject to g = 2x+y−z−5 = 0. Lagrange: ∇f = λ∇g.
∇f = (2x, 2y, 2z), ∇g = (2, 1, −1). So 2x = 2λ, 2y = λ, 2z = −λ ⟹ (x, y, z) = (λ, λ/2, −λ/2).
Substitute in constraint: 2λ + λ/2 − (−λ/2) = 2λ + λ = 3λ = 5, so **λ = 5/3**.
Closest point: (5/3, 5/6, −5/6). Distance = √((5/3)² + (5/6)² + (5/6)²) = **5/√6**.

**Ex 5 (CSIR NET style):** Max of x²y³ on x²+y² = 1, x,y ≥ 0.
Use substitution x = cosθ, y = sinθ. Maximize cos²θ·sin³θ. Take derivative, set = 0.
Or Lagrange: 2xy³ = 2λx and 3x²y² = 2λy. From first: λ = y³ (if x≠0). From second: λ = 3x²y/2.
So y³ = 3x²y/2, y² = 3x²/2, with x²+y² = 1: x²+3x²/2 = 1, x² = 2/5, y² = 3/5.
Max = (2/5)(3/5)^(3/2) = (2/5)·3√3/(5√5) = 6√3/(25√5).

---

# 20 ADDITIONAL PRACTICE PROBLEMS

**P1.** Show fₙ(x) = x²/(x²+n) → 0 pointwise on ℝ. Is convergence uniform?
**Solution:** |fₙ(x)| = x²/(x²+n) < x²/n. But sup over ℝ = lim_{x→∞} x²/(x²+n) = 1 for all n. NOT uniform.

**P2.** Compute ∫₀¹ x³ d(x²).
**Solution:** α(x) = x², α'(x) = 2x. ∫₀¹ x³·2x dx = 2∫₀¹ x⁴ dx = 2/5.

**P3.** f(x,y) = x²y/(x⁴+y²). Does lim_{(x,y)→(0,0)} f exist?
**Solution:** Along y = x²: f = x⁴/(2x⁴) = 1/2. Along y = 0: f = 0. Different paths → limit does NOT exist.

**P4.** Is f(x,y) = (x²+y²)sin(1/(x²+y²)) differentiable at (0,0)?
**Solution:** fₓ(0,0) = 0 (check). |f(h,k)−0−0|/√(h²+k²) = √(h²+k²)|sin(1/(h²+k²))| ≤ √(h²+k²) → 0. YES, differentiable.

**P5.** Jacobian of spherical coordinates (r,θ,φ) → (x,y,z).
**Convention:** θ = azimuthal angle in xy-plane, φ = polar angle from +z-axis: x = r sinφ cosθ, y = r sinφ sinθ, z = r cosφ.
**Answer:** J = r² sinφ. (Memorize this!)

**P6.** Find extrema of f(x,y) = x²+y²−2x−4y+5.
**Solution:** fₓ = 2x−2 = 0, f_y = 2y−4 = 0. Critical point (1,2). D = fₓₓf_yy−f_xy² = 4−0 = 4 > 0, fₓₓ = 2 > 0. Local minimum = f(1,2) = 1+4−2−8+5 = 0.

**P7.** Prove: if Σfₙ converges uniformly and each fₙ is continuous, then Σfₙ is continuous.
**Hint:** Apply "uniform limit preserves continuity" to partial sums.

**P8.** Stone-Weierstrass: Can every continuous function on [0,1] be uniformly approximated by polynomials with integer coefficients?
**Answer:** NO. The set of such polynomials is countable at each point, but C[0,1] is uncountable.
