# 🌀 Advanced Complex Analysis — Complete Study Notes

> **CSIR NET Priority: ⭐⭐⭐⭐ | Complex Analysis basics are heavily tested; advanced topics appear in Part C**

---

## 🗺️ Subject Mind Map

```
                   ADVANCED COMPLEX ANALYSIS
                           │
       ┌───────────┬───────┴────────┬───────────┐
       │           │                │           │
   Entire      Analytic        Harmonic     Advanced
   Functions   Continuation    Functions    Theorems
       │           │                │           │
   ┌───┴───┐   ┌──┴──┐        ┌───┴───┐   ┌───┴───┐
   Order   Canonical  Dirichlet  Green  Picard  Bloch
   Growth  Products   Problem    Func.  Theorems Schottky
```

---

# UNIT 1: Integral Functions (Entire Functions)

> 📋 **Quick Refresher Before Starting:**
>
> **Complex number** z = a + bi where i² = -1. |z| = √(a²+b²). Polar form: z = re^(iθ).
> **Analytic function:** f(z) is analytic if it's complex-differentiable. Must satisfy Cauchy-Riemann equations:
> If f = u + iv, then ∂u/∂x = ∂v/∂y and ∂u/∂y = -∂v/∂x.
> **Entire function:** Analytic EVERYWHERE in ℂ. Examples: eᶻ, sin z, polynomials. NOT entire: 1/z (pole at 0).
> **Taylor series:** f(z) = Σ aₙzⁿ. Converges in a disk. Entire = infinite radius of convergence.



## Prerequisites Refresher

An **analytic function** (holomorphic function) is one that is complex-differentiable in a region. Key facts from basic complex analysis:

- **Cauchy-Riemann equations:** If f(z) = u(x,y) + iv(x,y), then f analytic ⟹ ∂u/∂x = ∂v/∂y and ∂u/∂y = −∂v/∂x. Conversely, if u, v have continuous first-order partials satisfying CR, then f is analytic.
- **Cauchy's theorem:** ∮_C f(z)dz = 0 for analytic f on simply connected domain
- **Power series:** f(z) = Σ aₙzⁿ converges in a disk |z| < R

## What is an Entire Function?

An **entire function** is a function that is analytic on ALL of ℂ (the entire complex plane).

### Examples
| Function | Entire? | Why |
|----------|---------|-----|
| eᶻ | Yes | Power series converges everywhere |
| sin z, cos z | Yes | Power series converge everywhere |
| Polynomials p(z) | Yes | Analytic everywhere |
| 1/z | No | Singularity at z = 0 |
| tan z | No | Poles at z = π/2 + nπ |
| log z | No | Branch point at z = 0 |

## Liouville's Theorem 🎯

**If f is entire and bounded, then f is constant.**

This is remarkably powerful! It immediately proves the Fundamental Theorem of Algebra.

### Proof Sketch
By Cauchy's integral formula, |f'(z₀)| ≤ M/R for any R > 0. As R → ∞, f'(z₀) = 0 everywhere, so f is constant.

### 🎯 CSIR NET Application
**Q:** f is entire with |f(z)| ≤ 3|z|² + 7 for all z. What can you say about f?

**Solution:** f(z)/z² is entire (the bound |f(z)| ≤ 3|z|² + 7 gives |f(z)/z²| bounded as |z| → ∞). By an extended Liouville theorem, f must be a polynomial of degree ≤ 2. So f(z) = az² + bz + c.

## Growth and Order of Entire Functions

The **order** of an entire function f is:

**ρ = lim sup_{r→∞} [log log M(r)] / [log r]**

where M(r) = max_{|z|=r} |f(z)|.

| Function | Order ρ |
|----------|---------|
| Polynomial | 0 |
| eᶻ | 1 |
| e^(z²) | 2 |
| sin z | 1 |
| e^(eᶻ) | ∞ |

The **type** σ of an entire function of order ρ is:

**σ = lim sup_{r→∞} log M(r) / r^ρ**

- σ = 0: minimal type
- 0 < σ < ∞: normal (mean) type
- σ = ∞: maximal type

### Example
f(z) = eᶻ: M(r) = eʳ, so log M(r) = r, log log M(r) = log r.
ρ = lim (log r)/(log r) = 1. Type σ = lim r/r¹ = 1. So eᶻ has order 1, type 1.

---

# UNIT 2: Special Functions and Fundamental Theorems

> 📋 **Quick Refresher Before Starting:**
>
> **Gamma function:** Γ(n) = (n-1)! for positive integers. Γ(1/2) = √π. Defined by Γ(s) = ∫₀^∞ t^(s-1)e^(-t)dt.
> **Functional equation:** Γ(s+1) = s·Γ(s). This extends factorial to all complex numbers!
> **Riemann zeta function:** ζ(s) = Σ 1/nˢ = 1 + 1/2ˢ + 1/3ˢ + ... Converges for Re(s) > 1.


## The Gamma Function

**Γ(z) = ∫₀^∞ t^(z-1) e^(-t) dt** for Re(z) > 0

Key properties:
- Γ(n+1) = n! for positive integers
- Γ(z+1) = zΓ(z) (functional equation)
- Γ(1/2) = √π
- Has poles at z = 0, −1, −2, ... (simple poles)
- Never zero: Γ(z) ≠ 0 for all z

### Euler's Reflection Formula
**Γ(z)Γ(1−z) = π / sin(πz)**

## The Zeta Function

**ζ(s) = Σ_{n=1}^∞ 1/nˢ** for Re(s) > 1

- Extends to a meromorphic function on all of ℂ
- Only pole: simple pole at s = 1 with residue 1
- Riemann Hypothesis: all non-trivial zeros have Re(s) = 1/2 (unsolved!)

## Mittag-Leffler Theorem

Given prescribed poles and principal parts, there exists a meromorphic function with exactly those singularities. This is the "partial fractions" theorem for meromorphic functions.

### Example
To construct a function with simple poles at z = n (n ∈ ℤ) with residue 1:
The function π cot(πz) has exactly these properties!

---

# UNIT 3: Analytic Continuation

> 📋 **Quick Refresher Before Starting:**
>
> **Power series** (Class 12): f(x) = Σ aₙxⁿ converges inside a disk of radius R (radius of convergence).
> Outside R: diverges. On the boundary: depends on the specific series.
>
> **Analytic continuation:** If f is defined by a power series in one disk, can we "extend" it to a larger region?
> Example: f(z) = Σ zⁿ = 1/(1-z) converges only for |z| < 1, but 1/(1-z) makes sense everywhere except z = 1.
> So 1/(1-z) is the analytic continuation of Σ zⁿ beyond the unit disk.


## The Big Idea

If f is analytic on a region D₁ and g is analytic on D₂, with D₁ ∩ D₂ ≠ ∅ and f = g on D₁ ∩ D₂, then g is the **analytic continuation** of f to D₂.

### Identity Theorem 🎯
Let D ⊆ ℂ be a **connected** open set (a region). If f, g are analytic on D and agree on a set S ⊆ D that has a **limit point in D**, then f = g on all of D.

**Why connectedness matters:** Without it, f could equal g on one component and differ on another. The limit point must lie *inside* D, not just on the boundary or at infinity.

**In plain English:** An analytic function is completely determined by its values on ANY set with a limit point.

### Example: Extending the Geometric Series
f(z) = Σ_{n=0}^∞ zⁿ = 1/(1−z) is defined for |z| < 1.

But g(z) = 1/(1−z) is analytic on ℂ \ {1}.

So g is the analytic continuation of f to ℂ \ {1}.

### Example: The Gamma Function
Γ(z) is initially defined for Re(z) > 0 by the integral. Using Γ(z) = Γ(z+1)/z, we analytically continue to Re(z) > −1 (except z = 0), then to Re(z) > −2, etc.

## Monodromy Theorem
If f can be analytically continued along every path in a simply connected domain D, then the continuation defines a single-valued analytic function on D.

## Natural Boundary
Some functions CANNOT be continued beyond their circle of convergence.

**Example:** f(z) = Σ z^(2ⁿ) = z + z² + z⁴ + z⁸ + ... has |z| = 1 as a **natural boundary** — every point on the unit circle is a singularity!

---

# UNIT 4: Advanced Topics and Harmonic Functions

> 📋 **Quick Refresher Before Starting:**
>
> **Harmonic function:** u(x,y) satisfying Laplace's equation: ∂²u/∂x² + ∂²u/∂y² = 0 (written ∇²u = 0).
> **Connection to analytic functions:** If f = u + iv is analytic, then BOTH u and v are harmonic!
> **Harmonic conjugate:** Given u, find v such that u + iv is analytic. Use Cauchy-Riemann: vₓ = -u_y, v_y = uₓ.
> Example: u = x² - y² → uₓ = 2x, u_y = -2y → vₓ = 2y, v_y = 2x → v = 2xy. So f = z².


## Harmonic Functions

A real-valued function u(x,y) is **harmonic** if:

**∇²u = ∂²u/∂x² + ∂²u/∂y² = 0** (Laplace's equation)

### Connection to Analytic Functions 🎯
If f(z) = u + iv is analytic, then BOTH u and v are harmonic. Moreover, v is the **harmonic conjugate** of u.

### Finding the Harmonic Conjugate
Given u, find v using Cauchy-Riemann equations:
∂v/∂y = ∂u/∂x and ∂v/∂x = −∂u/∂y

### Example
u(x,y) = x² − y² (harmonic: u_xx + u_yy = 2 + (−2) = 0 ✓)

∂v/∂x = −∂u/∂y = 2y → v = 2xy + φ(y)
∂v/∂y = ∂u/∂x = 2x → 2x + φ'(y) = 2x → φ'(y) = 0 → φ(y) = C

So v = 2xy + C (C ∈ ℝ), and f(z) = (x²−y²) + i(2xy) + iC = z² + iC ✓

## Mean Value Property 🎯
If u is harmonic in a disk and continuous on its closure:

**u(center) = (1/2π) ∫₀²π u(center + re^(iθ)) dθ**

The value at the center equals the average over any circle around it!

## Maximum Principle 🎯
A non-constant harmonic function on a connected open set has no interior maximum or minimum. Extremes occur only on the boundary.

---

# UNIT 5: Harnack's Inequality and Dirichlet Problem

> 📋 **Quick Refresher Before Starting:**
>
> **Mean value property:** For harmonic u: u(center) = average of u on any circle around the center.
> **Maximum principle:** A harmonic function on a region attains its max/min on the BOUNDARY, never inside.
> **Harnack's inequality** (new): Bounds harmonic functions from above and below on compact subsets.
> **Green's function:** Solves the Dirichlet problem (find harmonic u with given boundary values).


## Harnack's Inequality

If u is harmonic and non-negative in |z − z₀| ≤ R, then for |z − z₀| = r < R:

**(R−r)/(R+r) · u(z₀) ≤ u(z) ≤ (R+r)/(R−r) · u(z₀)**

### Intuition
A positive harmonic function can't oscillate too wildly — it's "controlled" by its center value.

## Harnack's Theorem
If {uₙ} is a monotone increasing sequence of harmonic functions on a connected open set, then either uₙ → ∞ uniformly on compact subsets, or uₙ converges uniformly on compact subsets to a harmonic function.

## The Dirichlet Problem

**Problem:** Given a region D and continuous boundary data f on ∂D, find a harmonic function u on D with u|_{∂D} = f.

### Solution for the Disk (Poisson Integral Formula) 🎯
For the unit disk, if f is continuous on |z| = 1:

**u(re^(iθ)) = (1/2π) ∫₀²π [(1−r²) / (1 − 2r cos(θ−t) + r²)] · f(e^(it)) dt**

The kernel P(r,θ−t) = (1−r²)/(1 − 2r cos(θ−t) + r²) is the **Poisson kernel**.

## Green's Function
G(z, z₀) for a region D is harmonic in D \ {z₀}, zero on ∂D, and G(z,z₀) + log|z−z₀| is harmonic near z₀.

For the unit disk: **G(z, z₀) = −log|(z−z₀)/(1−z̄₀z)|**

---

# UNIT 6: Canonical Products, Jensen & Poisson-Jensen Formulas

> 📋 **Quick Refresher Before Starting:**
>
> **Infinite product:** Π(1 + aₙ) = (1+a₁)(1+a₂)(1+a₃)... Like infinite series but with multiplication.
> Converges if Σ|aₙ| converges (analogous to absolute convergence of series).
> **Canonical product:** Builds an entire function with prescribed zeros {aₙ}:
> f(z) = Π Eₚ(z/aₙ) where Eₚ is an "elementary factor" that ensures convergence.


## Weierstrass Factorization Theorem 🎯

Every entire function f with zeros at a₁, a₂, ... (with f(0) ≠ 0) can be written as:

**f(z) = e^(g(z)) · Π_{n=1}^∞ E_pₙ(z/aₙ)**

where E_p(z) = (1−z)exp(z + z²/2 + ... + zᵖ/p) are **elementary factors** and g is entire.

### Elementary Factors
- E₀(z) = 1 − z
- E₁(z) = (1−z)eᶻ
- E₂(z) = (1−z)e^(z+z²/2)

### Example: sin(πz)
**sin(πz) = πz · Π_{n=1}^∞ (1 − z²/n²)**

This expresses sin as an infinite product over its zeros z = 0, ±1, ±2, ...

## Canonical Product
If {aₙ} are the zeros, the **canonical product** is:

P(z) = Π E_p(z/aₙ) where p is chosen minimally to ensure convergence.

The **genus** of the canonical product is the smallest p that works.

## Jensen's Formula 🎯

If f is analytic in |z| ≤ R, f(0) ≠ 0, and a₁,...,aₙ are the zeros in |z| < R, then:

**log|f(0)| + Σ log(R/|aₖ|) = (1/2π) ∫₀²π log|f(Re^(iθ))| dθ**

### Intuition
Jensen's formula connects the growth of f on circles to the number and location of its zeros inside.

## Poisson-Jensen Formula
Generalizes Jensen's formula to give the value of log|f(z)| at any point inside the disk, not just the center.

---

# UNIT 7: Hadamard's Three Circles Theorem

> 📋 **Quick Refresher Before Starting:**
>
> **M(r) = max|f(z)| on |z| = r** — the maximum modulus on a circle of radius r.
> As r grows, M(r) tells you how fast the entire function grows.
> **Hadamard's three circles theorem:** log M(r) is a CONVEX function of log r.
> This means: knowing M on two circles constrains M on any circle between them.


## Statement

Let f be analytic in the annulus r₁ ≤ |z| ≤ r₃. Let M(r) = max_{|z|=r} |f(z)|.

For r₁ < r₂ < r₃:

**log M(r₂) ≤ [log(r₃/r₂)/log(r₃/r₁)] · log M(r₁) + [log(r₂/r₁)/log(r₃/r₁)] · log M(r₃)**

Equivalently: **log M(r) is a convex function of log r**.

### Geometric Meaning
```
log M(r)
    │         ╱
    │       ╱  ← actual curve lies BELOW the straight line
    │     ●    
    │   ╱  ╲
    │ ●      ● 
    └──────────── log r
     r₁  r₂  r₃
```

The maximum modulus on intermediate circles can't exceed the linear interpolation between the maximum on the inner and outer circles.

### Application
Used to prove results about the growth rate of entire functions and in the theory of Phragmén-Lindelöf.

---

# UNIT 8: Borel, Hadamard Factorization, Range of Analytic Functions

> 📋 **Quick Refresher Before Starting:**
>
> **Order of an entire function:** ρ = lim sup (log log M(r))/(log r). Measures growth rate.
> - Polynomials: ρ = 0. eᶻ: ρ = 1. e^(z²): ρ = 2.
> **Hadamard factorization:** An entire function of finite order can be completely written as:
> f(z) = z^m · e^(polynomial) · Π Eₚ(z/aₙ) where aₙ are its zeros.


## Borel's Theorem
An entire function of finite order ρ cannot have more than a "sparse" set of values that it avoids.

**Borel's version of Picard:** If f is entire of order ρ, then f takes every value with at most one exception, and the exponent of convergence of the a-points equals ρ for all a (with at most one exception).

## Hadamard Factorization Theorem 🎯

Every entire function f of finite order ρ with zeros a₁, a₂, ... can be written as:

**f(z) = z^m · e^(Q(z)) · Π E_p(z/aₙ)**

where:
- m = order of zero at origin
- Q(z) is a polynomial of degree ≤ ρ
- p ≤ ρ (the genus is at most the order)

### Example
eᶻ − 1 has order 1, zeros at z = 2πin (n ∈ ℤ, n ≠ 0):

eᶻ − 1 = z · e^(z/2) · Π_{n≠0} E₁(z/(2πin))

## Range of Analytic Functions

### Open Mapping Theorem 🎯
A non-constant analytic function is an open map (maps open sets to open sets).

**Consequence:** A non-constant analytic function cannot have a local maximum of |f| in the interior of its domain (Maximum Modulus Principle).

---

# UNIT 9: Bloch, Schottky, Little Picard Theorem 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Liouville's theorem:** Bounded entire function = constant. (If |f(z)| ≤ M for ALL z, then f is constant.)
> **Picard goes much further:**
> - **Little Picard:** A non-constant entire function takes EVERY value, with at most ONE exception.
> - Example: eᶻ is entire and takes every value except 0. That one exception is the maximum allowed.
> **Bloch's theorem:** Every analytic function on the unit disk contains a disk of a certain minimum size in its image.


## Bloch's Theorem
There exists a universal constant B > 0 such that: if f is analytic in |z| < 1 with f'(0) = 1, then f(|z| < 1) contains a disk of radius B.

Best known lower bound: B ≥ √3/4 (Ahlfors–Grunsky). The exact value is still an open problem.

## Schottky's Theorem
If f is analytic in |z| < 1 and omits the values 0 and 1, then |f(z)| is bounded by a quantity depending only on |f(0)| and |z| (not on f itself).

This is key to proving Picard's theorems.

## Little Picard Theorem 🎯

**A non-constant entire function takes every complex value with at most ONE exception.**

### Examples
- eᶻ omits 0 (eᶻ ≠ 0 for any z), but takes every other value. One exception — OK!
- sin z takes EVERY value (no exceptions)
- A polynomial of degree n takes every value (by FTA)

### 🎯 CSIR NET Question
**Q:** True or False: There exists an entire function that omits both 0 and 1.
**A:** FALSE — by Little Picard, at most one value can be omitted.

## Great Picard Theorem
In every neighborhood of an essential singularity, an analytic function takes every complex value (with at most one exception) infinitely many times.

### Example
e^(1/z) near z = 0: for any w ≠ 0, the equation e^(1/z) = w has solutions z = 1/(log w + 2πin) accumulating at 0.

---

# UNIT 10: Univalent Function Theory

> 📋 **Quick Refresher Before Starting:**
>
> **Univalent (schlicht) function:** Analytic AND injective (one-to-one). f(z₁) = f(z₂) ⟹ z₁ = z₂.
> **Schwarz lemma:** If f maps the unit disk to itself with f(0) = 0, then |f(z)| ≤ |z|.
> **Conformal mapping:** Analytic + non-zero derivative. Preserves angles between curves.
> **Riemann mapping theorem:** Any simply connected region (≠ ℂ) can be conformally mapped to the unit disk.


## Univalent (Schlicht) Functions

A function f is **univalent** (schlicht) on a domain D if it is one-to-one (injective) on D.

The class **S** consists of all univalent functions f on the unit disk with f(0) = 0 and f'(0) = 1:

f(z) = z + a₂z² + a₃z³ + ...

## Bieberbach Conjecture (de Branges' Theorem)

**|aₙ| ≤ n for all n ≥ 2**, with equality only for the Koebe function k(z) = z/(1−z)².

This was conjectured in 1916 and proved by de Branges in 1985.

## Key Results in S

### Koebe 1/4 Theorem
If f ∈ S, then f(D) contains the disk |w| < 1/4.

### Growth and Distortion Theorems
For f ∈ S and |z| = r < 1:

**r/(1+r)² ≤ |f(z)| ≤ r/(1−r)²** (Growth)

**(1−r)/(1+r)³ ≤ |f'(z)| ≤ (1+r)/(1−r)³** (Distortion)

## Area Theorem
If $g(z) = z + b_0 + \sum_{n=1}^\infty b_n z^{-n}$ is univalent in $|z| > 1$, then $\sum_{n=1}^\infty n|b_n|^2 \le 1$.

---

# 📝 CSIR NET Practice Problems — Complex Analysis

**Q1.** If f is entire and |f(z)| ≤ e^|z| for all z, what is the maximum order of f?
**Answer:** Order ρ ≤ 1.

**Q2.** How many values can a non-constant entire function omit?
**Answer:** At most 1 (Little Picard Theorem).

**Q3.** Find the harmonic conjugate of u(x,y) = eˣ cos y.
**Solution:** v_x = −u_y = eˣ sin y → v = eˣ sin y + φ(y)
v_y = eˣ cos y + φ'(y) = u_x = eˣ cos y → φ'(y) = 0 → v = eˣ sin y
So f(z) = eˣ(cos y + i sin y) = eᶻ ✓

**Q4.** Express sin(πz) as an infinite product.
**Answer:** sin(πz) = πz · Π_{n=1}^∞ (1 − z²/n²)

**Q5.** State whether true/false: The Poisson integral of a continuous function on ∂D is harmonic in D.
**Answer:** TRUE.

---

> **📖 Recommended Reading:** Ahlfors "Complex Analysis", Conway "Functions of One Complex Variable II"
> **Next Subject:** [Advanced Differential Equations →](./05_Advanced_Differential_Equations.md)
