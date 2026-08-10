# 📊 Mathematical Analysis — Complete Study Notes

> **CSIR NET Priority: ⭐⭐⭐⭐⭐ | Real Analysis is THE most tested area in CSIR NET**

---

## 🗺️ Subject Mind Map

```
                    MATHEMATICAL ANALYSIS
                           │
         ┌─────────┬───────┴────────┬──────────┐
         │         │                │          │
    Integration  Convergence    Multivariable  Applications
         │         │                │          │
    ┌────┴────┐  ┌─┴──┐        ┌───┴───┐   ┌──┴──┐
    Riemann   Uniform  Point-  Implicit  Extrema Jacobian
    Stieltjes Convg.   wise    Function
```

---

# UNIT 1: Riemann-Stieltjes Integral — Part I

> 📋 **Quick Refresher Before Starting:**
>
> **Definite integral** (Class 12): ∫₀¹ x² dx = [x³/3]₀¹ = 1/3. It gives the area under the curve y = x².
> **Riemann sum:** Divide [a,b] into small intervals, approximate area by rectangles, sum them up.
> As rectangles get thinner, the sum → the integral.
>
> **Riemann-Stieltjes integral** (new concept): Instead of ∫f(x)dx, we compute ∫f(x)dα(x) where α is another function.
> Think of it as: α controls "how we weight" different parts of the interval.
> When α(x) = x, this reduces to the ordinary integral.



## Why Beyond Riemann?

You know the Riemann integral ∫f(x)dx from Class 12. The **Riemann-Stieltjes integral** generalizes this by replacing dx with dα(x), where α is a monotonically increasing function.

**Notation:** ∫ₐᵇ f dα or ∫ₐᵇ f(x) dα(x)

**Intuition:** Instead of measuring "width" of intervals by (xᵢ − xᵢ₋₁), we measure by (α(xᵢ) − α(xᵢ₋₁)). This "reweights" the integral.

**Special case:** When α(x) = x, we get the ordinary Riemann integral.

## Formal Definition

**Partition:** P = {a = x₀ < x₁ < ... < xₙ = b}

**Upper and Lower Sums:**
```
U(P, f, α) = Σᵢ Mᵢ · Δαᵢ    where Mᵢ = sup f on [xᵢ₋₁, xᵢ], Δαᵢ = α(xᵢ) − α(xᵢ₋₁)
L(P, f, α) = Σᵢ mᵢ · Δαᵢ    where mᵢ = inf f on [xᵢ₋₁, xᵢ]
```

f is **Riemann-Stieltjes integrable** w.r.t. α if:

**sup L(P, f, α) = inf U(P, f, α)**

### Example 1: Step Function Integrator
Let α(x) = ⌊x⌋ (floor function) on [0, 3.5]. The interior jumps of α happen at x = 1, 2, 3 (each jump of size 1). Then:

∫₀^{3.5} f(x) dα = f(1) + f(2) + f(3) — it becomes a **sum**!

(Endpoint chosen as 3.5 to avoid endpoint-jump convention ambiguities. In general, ∫_a^b f dα = Σ f(cᵢ) · (jump of α at cᵢ) over the interior jump points cᵢ ∈ (a, b).)

This shows how R-S integral unifies sums and integrals.

### Example 2
Compute ∫₀¹ x dα where α(x) = x².

**Solution:** Here dα = 2x dx (α is differentiable), so:
∫₀¹ x · 2x dx = ∫₀¹ 2x² dx = [2x³/3]₀¹ = 2/3

### 🎯 Key Theorem: Integration by Parts
**∫ₐᵇ f dα + ∫ₐᵇ α df = f(b)α(b) − f(a)α(a)**

---

# UNIT 2: Riemann-Stieltjes Integral — Part II

> 📋 **Quick Refresher Before Starting:**
>
> **Integration by parts** (Class 12): ∫u dv = uv - ∫v du
> Example: ∫x·eˣ dx. Let u = x, dv = eˣdx. Then du = dx, v = eˣ.
> Result: xeˣ - ∫eˣdx = xeˣ - eˣ + C = eˣ(x-1) + C.
>
> This unit extends integration by parts to Stieltjes integrals: ∫f dα + ∫α df = f(b)α(b) - f(a)α(a).


## Existence Conditions

### Theorem 1
If f is continuous on [a,b] and α is monotonically increasing, then f ∈ R(α) (f is R-S integrable w.r.t. α).

### Theorem 2
If f is monotonic and α is continuous and monotonic on [a,b], then f ∈ R(α).

### Theorem 3 (Reduction to Riemann)
If f is continuous and α has a continuous derivative α', then:

**∫ₐᵇ f dα = ∫ₐᵇ f(x)α'(x) dx**

## Properties of the R-S Integral

1. **Linearity:** ∫(af + bg)dα = a∫f dα + b∫g dα
2. **Linearity in integrator:** ∫f d(cα + β) = c∫f dα + ∫f dβ
3. **Additivity:** ∫ₐᵇ f dα = ∫ₐᶜ f dα + ∫ᶜᵇ f dα (for a < c < b)
4. **|∫f dα| ≤ ∫|f| dα** (if both integrals exist)

### 🎯 CSIR NET Example
**Q:** Evaluate ∫₀^{1.5} f(x) dα where f(x) = x² and α(x) = x + ⌊x⌋.

**Solution:** α(x) = x + ⌊x⌋ has only **one interior jump** on (0, 1.5), namely at x = 1 where α jumps by 1. (No endpoint-jump ambiguity since 1.5 is not an integer.)

Split: ∫₀^{1.5} = ∫₀^{1−} (smooth part) + jump contribution at 1 + ∫₁^{1.5} (smooth part)

On [0,1): α(x) = x, dα = dx → ∫₀¹ x² dx = **1/3**
Jump at x=1: f(1)·(jump of α at 1) = 1·1 = **1**
On [1, 1.5]: α(x) = x+1, dα = dx → ∫₁^{1.5} x² dx = [x³/3]₁^{1.5} = (3.375 − 1)/3 = **2.375/3 = 19/24**

**Total = 1/3 + 1 + 19/24 = 8/24 + 24/24 + 19/24 = 51/24 = 17/8**

---

# UNIT 3: Uniform Convergence — Part I

> 📋 **Quick Refresher Before Starting:**
>
> **Sequence:** a₁, a₂, a₃, ... (a list of numbers). Example: aₙ = 1/n gives 1, 1/2, 1/3, ...
> **Convergence:** aₙ → L means the terms get arbitrarily close to L. Example: 1/n → 0.
> **Series:** Σaₙ = a₁ + a₂ + a₃ + ... Example: Σ(1/2)ⁿ = 1 + 1/2 + 1/4 + ... = 2.
>
> **Pointwise convergence of functions:** fₙ(x) → f(x) means: for EACH fixed x, the sequence of numbers fₙ(x) converges to f(x).
> Example: fₙ(x) = xⁿ on [0,1]. For x < 1: xⁿ → 0. For x = 1: 1ⁿ → 1. So the limit is: f(x) = 0 if x < 1, f(1) = 1.
> Notice: each fₙ is continuous but the limit f is NOT! This motivates uniform convergence.


## Pointwise vs Uniform Convergence

### Pointwise Convergence
{fₙ} converges **pointwise** to f on S if: for each x ∈ S and each ε > 0, ∃N(x,ε) such that |fₙ(x) − f(x)| < ε for all n ≥ N.

Note: N depends on BOTH x and ε.

### Uniform Convergence 🎯
{fₙ} converges **uniformly** to f on S if: for each ε > 0, ∃N(ε) such that |fₙ(x) − f(x)| < ε for ALL x ∈ S and all n ≥ N.

Note: N depends ONLY on ε, NOT on x. The same N works everywhere!

### Critical Example: Why This Matters
fₙ(x) = xⁿ on [0,1].

**Pointwise limit:**
- For x ∈ [0,1): lim xⁿ = 0
- For x = 1: lim 1ⁿ = 1

So f(x) = 0 for x ∈ [0,1) and f(1) = 1. Each fₙ is continuous, but f is NOT!

**This convergence is NOT uniform** because continuity is not preserved.

### Uniform Convergence Preserves Continuity
**Theorem:** If fₙ → f uniformly on S and each fₙ is continuous at c ∈ S, then f is continuous at c.

## Tests for Uniform Convergence

### Weierstrass M-Test 🎯 (CSIR NET FAVORITE)
If |fₙ(x)| ≤ Mₙ for all x ∈ S and Σ Mₙ converges, then Σ fₙ converges uniformly on S.

### Example
Σ sin(nx)/n² on all of ℝ. Here |sin(nx)/n²| ≤ 1/n² = Mₙ and Σ 1/n² converges (p-series, p=2 > 1).
By M-test, the series converges uniformly. ✓

---

# UNIT 4: Uniform Convergence — Part II

> 📋 **Quick Refresher Before Starting:**
>
> **Pointwise vs Uniform convergence** (the key distinction):
> **Pointwise:** For each x, fₙ(x) eventually gets close to f(x). Different x's may converge at different rates.
> **Uniform:** ALL x's converge at the SAME rate. Formally: sup|fₙ(x) - f(x)| → 0.
>
> **Why it matters:** Uniform convergence preserves continuity, integrability, and (with extra conditions) differentiability. Pointwise does NOT.
> **Visual:** Imagine fₙ as a rubber band. Pointwise = each point of the band settles down. Uniform = the ENTIRE band settles down simultaneously.


## Interchange Theorems 🎯

### Theorem 1: Limit and Integral
If fₙ → f uniformly on [a,b] and each fₙ is integrable, then:

**∫ₐᵇ lim fₙ = lim ∫ₐᵇ fₙ** (can swap limit and integral)

### Theorem 2: Limit and Derivative (Rudin 7.17)
Let {fₙ} be a sequence of functions **differentiable on a bounded interval [a,b]**. If
- {fₙ(x₀)} converges for some x₀ ∈ [a,b], AND
- {f'ₙ} converges uniformly on [a,b],

then:
1. {fₙ} converges uniformly on [a,b] to some f,
2. f is differentiable on [a,b], and
3. **(lim fₙ)'(x) = lim f'ₙ(x)** for every x ∈ [a,b] (can swap limit and derivative).

### 🎯 CSIR NET Application
**Q:** Does Σₙ₌₁^∞ xⁿ/n! converge uniformly on [−R, R] for any R > 0?

**Solution:** |xⁿ/n!| ≤ Rⁿ/n! on [−R,R]. Since Σ Rⁿ/n! = eᴿ < ∞, by M-test, YES — uniform convergence on any bounded interval. The limit is eˣ, and we can differentiate term by term.

## Abel's and Dirichlet's Tests

**Abel's Test:** If Σ aₙ converges and {bₙ} is monotonic and bounded, then Σ aₙbₙ converges.

**Dirichlet's Test:** If partial sums of Σ aₙ are bounded and bₙ → 0 monotonically, then Σ aₙbₙ converges.

---

# UNIT 5: Approximation and Convergence Theorems

> 📋 **Quick Refresher Before Starting:**
>
> **Polynomial:** p(x) = aₙxⁿ + ... + a₁x + a₀. Continuous everywhere, easy to work with.
> **Weierstrass Approximation Theorem** (key result here): ANY continuous function on [a,b] can be uniformly approximated by polynomials.
> This is remarkable — even weird, jagged-looking continuous functions can be approximated by smooth polynomials!
> Stone-Weierstrass generalizes this to other function algebras.


## Stone-Weierstrass Theorem 🎯

**Weierstrass Approximation Theorem:** Every continuous function on [a,b] can be uniformly approximated by polynomials.

**In plain English:** No matter how complicated a continuous function is on a closed interval, polynomials can get arbitrarily close to it everywhere simultaneously.

**Stone's Generalization:** Extends this to subalgebras of C(X) on compact spaces.

### Example
f(x) = |x| on [−1,1] is continuous. So there exist polynomials pₙ(x) such that pₙ → |x| uniformly on [−1,1], even though |x| is not differentiable at 0.

## Equicontinuity and Arzelà-Ascoli Theorem 🎯

**(Uniformly) equicontinuous family:** {fₙ} is **uniformly equicontinuous** on [a,b] if for every ε > 0, there exists δ > 0 (**independent of n, x, y**) such that |fₙ(x) − fₙ(y)| < ε whenever |x − y| < δ, for all n ∈ ℕ and all x, y ∈ [a,b]. (This single δ working for everyone is the strength Arzelà-Ascoli needs.)

**Arzelà-Ascoli Theorem:** A sequence {fₙ} in C[a,b] has a uniformly convergent subsequence if and only if {fₙ} is uniformly bounded and equicontinuous.

---

# UNIT 6: Calculus of Functions of Several Variables — Part I

> 📋 **Quick Refresher Before Starting:**
>
> **Partial derivatives** (extending Class 12 calculus to several variables):
> If f(x,y) = x²y + 3y², then:
> ∂f/∂x = 2xy (differentiate treating y as a constant)
> ∂f/∂y = x² + 6y (differentiate treating x as a constant)
>
> **Gradient:** ∇f = (∂f/∂x, ∂f/∂y) points in the direction of steepest increase.
> Example: f = x² + y². ∇f = (2x, 2y), pointing radially outward (away from minimum at origin).


## From Single Variable to Multivariable

Now we extend differentiation to functions f: ℝⁿ → ℝᵐ.

### Partial Derivatives
For f: ℝⁿ → ℝ, the **partial derivative** with respect to xᵢ:

∂f/∂xᵢ = lim_{h→0} [f(x₁,...,xᵢ+h,...,xₙ) − f(x₁,...,xᵢ,...,xₙ)] / h

### Example
f(x,y) = x²y + sin(xy)

∂f/∂x = 2xy + y·cos(xy)
∂f/∂y = x² + x·cos(xy)

### Total Derivative (Fréchet Derivative) 🎯

f: ℝⁿ → ℝᵐ is **differentiable** at a if there exists a linear map L: ℝⁿ → ℝᵐ such that:

lim_{h→0} ||f(a+h) − f(a) − L(h)|| / ||h|| = 0

L is called the **total derivative** Df(a). Its matrix is the **Jacobian matrix**.

**Key:** Existence of partial derivatives does NOT guarantee differentiability! But if partial derivatives exist and are continuous, then f IS differentiable.

---

# UNIT 7: Calculus of Functions of Several Variables — Part II

> 📋 **Quick Refresher Before Starting:**
>
> **Chain rule** (Class 12): d/dx[f(g(x))] = f'(g(x))·g'(x).
> Example: d/dx[sin(x²)] = cos(x²)·2x.
>
> **Multivariable chain rule** (new): If z = f(x,y) where x = x(t), y = y(t):
> dz/dt = (∂f/∂x)(dx/dt) + (∂f/∂y)(dy/dt)
>
> **Total derivative:** The matrix of all partial derivatives — generalizes f'(x) to multiple dimensions.


## Higher-Order Derivatives and Mixed Partials

### Clairaut's Theorem (Equality of Mixed Partials) 🎯
If f_xy and f_yx are both continuous at (a,b), then:

**∂²f/∂x∂y = ∂²f/∂y∂x**

### Example
f(x,y) = x³y² + e^(xy)

f_x = 3x²y² + ye^(xy)
f_xy = 6x²y + e^(xy) + xye^(xy)

f_y = 2x³y + xe^(xy)
f_yx = 6x²y + e^(xy) + xye^(xy) ✓ (Equal!)

## Chain Rule for Multivariable Functions

If f: ℝⁿ → ℝᵐ and g: ℝᵐ → ℝᵖ are differentiable, then:

**D(g∘f)(a) = Dg(f(a)) · Df(a)** (matrix multiplication of Jacobians)

### Example
x = r cos θ, y = r sin θ (polar coordinates)

If f(x,y) is given, then:
∂f/∂r = (∂f/∂x)cos θ + (∂f/∂y)sin θ
∂f/∂θ = −(∂f/∂x)r sin θ + (∂f/∂y)r cos θ

## Taylor's Theorem in Several Variables

f(a+h) = f(a) + Df(a)·h + ½ h^T · D²f(a) · h + ... (higher order terms)

where D²f is the **Hessian matrix** of second partial derivatives.

---

# UNIT 8: Implicit and Explicit Functions

> 📋 **Quick Refresher Before Starting:**
>
> **Implicit function:** An equation F(x,y) = 0 that defines y as a function of x without explicitly solving for y.
> Example: x² + y² = 1 (circle). We can't write y = single formula for the whole circle, but near any point (except (±1,0)), we can locally solve for y.
>
> **Implicit differentiation** (Class 12): Differentiate both sides of F(x,y) = 0:
> Fₓ + F_y·y' = 0, so y' = -Fₓ/F_y
> Example: x² + y² = 1 → 2x + 2y·y' = 0 → y' = -x/y.


## Implicit Function Theorem 🎯 (CSIR NET HIGH PRIORITY)

**Theorem:** Let F: ℝⁿ⁺ᵐ → ℝᵐ be continuously differentiable. If F(a,b) = 0 and the partial derivative matrix ∂F/∂y (m×m block) is invertible at (a,b), then:

Near (a,b), the equation F(x,y) = 0 implicitly defines y as a function of x: y = g(x).

Moreover: **Dg(a) = −[∂F/∂y]⁻¹ · [∂F/∂x]** evaluated at (a,b).

### Example
F(x,y) = x² + y² − 1 = 0 (unit circle)

∂F/∂y = 2y. This is non-zero when y ≠ 0.

So near any point with y ≠ 0, we can solve for y = g(x).
dy/dx = −F_x/F_y = −2x/(2y) = −x/y ✓ (matches implicit differentiation)

## Inverse Function Theorem 🎯

If f: ℝⁿ → ℝⁿ is C¹ and Df(a) is invertible, then f is a local diffeomorphism near a.

Moreover: **D(f⁻¹)(f(a)) = [Df(a)]⁻¹**

---

# UNIT 9: Extrema of Functions of Several Variables 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Finding max/min** (Class 12 for one variable): Set f'(x) = 0, check f''(x).
> **Two variables:** Set BOTH ∂f/∂x = 0 AND ∂f/∂y = 0 simultaneously. These give critical points.
>
> **Second derivative test (2D):** Compute D = fₓₓf_yy - (f_xy)².
> - D > 0, fₓₓ > 0 → local MINIMUM
> - D > 0, fₓₓ < 0 → local MAXIMUM
> - D < 0 → SADDLE POINT (neither max nor min)
> - D = 0 → test inconclusive
>
> **Lagrange multipliers:** For extrema of f subject to constraint g = 0: solve ∇f = λ∇g and g = 0.


## Local Extrema

For f: ℝⁿ → ℝ, at a critical point (where ∇f = 0), use the **Hessian matrix:**

```
H = [[f_xx, f_xy],
     [f_yx, f_yy]]
```

**Second Derivative Test (2 variables):**
Let D = f_xx·f_yy − (f_xy)² = det(H) at the critical point.

| Condition | Conclusion |
|-----------|-----------|
| D > 0, f_xx > 0 | Local minimum |
| D > 0, f_xx < 0 | Local maximum |
| D < 0 | Saddle point |
| D = 0 | Test inconclusive |

### Worked Example
f(x,y) = x³ + y³ − 3xy

∇f = (3x²−3y, 3y²−3x) = (0,0) → x²=y, y²=x → Critical points: (0,0) and (1,1)

At (0,0): H = [[0,−3],[−3,0]], D = (0)(0) − (−3)² = −9 < 0 → **Saddle point**

At (1,1): H = [[6,−3],[−3,6]], D = (6)(6) − (−3)² = 36−9 = 27 > 0, f_xx = 6 > 0 → **Local minimum**

## Lagrange Multipliers 🎯 (CSIR NET FAVORITE)

To optimize f(x) subject to constraint g(x) = 0:

**∇f = λ∇g** (at the optimum)

### Example
Maximize f(x,y) = xy subject to x² + y² = 1.

∇f = (y,x), ∇g = (2x,2y)
y = 2λx, x = 2λy → y/(2x) = x/(2y) → y² = x²

With constraint: 2x² = 1 → x = ±1/√2, y = ±1/√2
Maximum value: f = 1/2

---

# UNIT 10: Jacobian and Its Properties 🎯

> 📋 **Quick Refresher Before Starting:**
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
> So ∫∫f dxdy = ∫∫f·r drdθ (that's where the 'r' comes from!).


## Definition

For f: ℝⁿ → ℝⁿ, the **Jacobian** is:

J = det(Df) = det[∂fᵢ/∂xⱼ]

## Geometric Meaning
|J| represents the factor by which f changes areas (2D) or volumes (nD).

### Example: Polar Coordinates
x = r cos θ, y = r sin θ

```
J = |∂x/∂r  ∂x/∂θ| = |cos θ  −r sin θ| = r cos²θ + r sin²θ = r
    |∂y/∂r  ∂y/∂θ|   |sin θ   r cos θ|
```

So area element: dx dy = |J| dr dθ = r dr dθ (familiar from calculus!)

### Change of Variables Formula

**∫∫_D f(x,y) dx dy = ∫∫_D' f(x(u,v), y(u,v)) |J| du dv**

### Properties
1. If f and g are differentiable: **J(g∘f)(x) = J(g)(f(x)) · J(f)(x)** (chain rule — note evaluation points: J(g) at f(x), J(f) at x)
2. J(f⁻¹)(y) = 1/J(f)(f⁻¹(y)) (at corresponding points)
3. J = 0 means the mapping is singular (not locally invertible)

---

# 📝 CSIR NET Practice Problems — Real Analysis

**Q1.** The sequence fₙ(x) = x/(1+nx²) converges uniformly on ℝ to what function?

**Solution:** Pointwise limit: for each x, fₙ(x) → 0. Is it uniform?
|fₙ(x)| = |x|/(1+nx²) ≤ 1/(2√n) (by AM-GM). Since 1/(2√n) → 0, convergence IS uniform. Limit is f ≡ 0.

**Q2.** Let f(x,y) = (x²−y²)/(x²+y²) for (x,y) ≠ (0,0). Do iterated limits exist at origin?

**Solution:** lim_{x→0} lim_{y→0} f = lim_{x→0} 1 = 1
lim_{y→0} lim_{x→0} f = lim_{y→0} (−1) = −1
Iterated limits differ → limit does NOT exist at origin.

**Q3.** Is f(x,y) = √(|xy|) differentiable at (0,0)?

**Solution:** f_x(0,0) = 0, f_y(0,0) = 0 (check from definition). But along y = x with h > 0:
|f(h,h) − 0 − 0|/‖(h,h)‖ = √(h²) / (|h|√2) = |h| / (|h|√2) = 1/√2 ≠ 0. So the limit is not 0 — **NOT differentiable**!

---

> **📖 Recommended Reading:** Rudin "Principles of Mathematical Analysis", Apostol "Mathematical Analysis"
> **Next Subject:** [Topology →](./03_Topology.md)
