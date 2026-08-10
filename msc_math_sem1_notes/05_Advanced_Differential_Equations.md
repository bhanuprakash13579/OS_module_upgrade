# ⚙️ Advanced Differential Equations — Complete Study Notes

> **CSIR NET Priority: ⭐⭐⭐⭐ | ODE theory appears in Part B; stability/qualitative theory in Part C**

---

## 🗺️ Subject Mind Map

```
              ADVANCED DIFFERENTIAL EQUATIONS
                         │
       ┌─────────┬───────┴───────┬──────────┐
       │         │               │          │
   Existence  Systems       Nonlinear   Stability
       │         │               │          │
   ┌───┴───┐  ┌──┴──┐      ┌───┴───┐  ┌───┴───┐
   ε-Approx Linear  Nonlin  Poincaré  Lyapunov
   Picard   Systems Systems Bendixson Critical
   Uniquen. Matrix          Limit     Points
              Exp.          Cycles
```

---

# UNIT 1: ε-Approximate Solutions

> 📋 **Quick Refresher Before Starting:**
>
> **ODE** (Ordinary Differential Equation): An equation involving a function y and its derivatives y', y'', etc.
> **Example:** y' = 2y. Solution: y = Ce²ˣ (check: (Ce²ˣ)' = 2Ce²ˣ = 2y ✓).
> **Separation of variables** (Class 12): If dy/dx = f(x)g(y), then ∫dy/g(y) = ∫f(x)dx.
> **ε-approximate solution:** A function φ with |φ' - f(t,φ)| < ε — it "almost" satisfies the ODE.



## Setting the Stage

We study the initial value problem (IVP):

**y' = f(t, y), y(t₀) = y₀**

Before proving solutions exist, we need the concept of "almost-solutions."

## Definition

A continuous function φ(t) is an **ε-approximate solution** of y' = f(t,y) on [t₀, t₀+a] if:

1. φ(t₀) = y₀
2. φ'(t) exists almost everywhere
3. |φ'(t) − f(t, φ(t))| < ε wherever φ'(t) exists

**In plain English:** φ almost satisfies the equation — the error is less than ε everywhere.

### Example
For y' = y, y(0) = 1, the exact solution is eᵗ.

The function φ(t) = 1 + t + t²/2 is an ε-approximate solution for small t because:
φ'(t) = 1 + t, and f(t,φ(t)) = 1 + t + t²/2

|φ'(t) − f(t,φ(t))| = |−t²/2| = t²/2 < ε if t < √(2ε)

## Cauchy-Euler Polygonal Method

Construct ε-approximate solutions by piecewise linear interpolation:

```
Given: y' = f(t,y), y(t₀) = y₀
Step 1: From (t₀, y₀), draw line with slope f(t₀, y₀) to t₁ = t₀ + h
Step 2: At (t₁, y₁), draw line with slope f(t₁, y₁) to t₂ = t₁ + h
... Continue
```

This gives a piecewise linear function. As h → 0, these converge to the actual solution (under appropriate conditions).

---

# UNIT 2: Basic Existence and Uniqueness Theorems

> 📋 **Quick Refresher Before Starting:**
>
> **Existence:** Does a solution exist? **Uniqueness:** Is there exactly one solution?
> **Lipschitz condition:** |f(t,y₁) - f(t,y₂)| ≤ L|y₁-y₂|. It means f doesn't change too wildly in y.
> **Picard iteration:** Start with φ₀ = y₀, then φₙ₊₁(t) = y₀ + ∫f(s,φₙ(s))ds. Keep iterating — the sequence converges to the unique solution.
> Example: y' = y, y(0) = 1. φ₀ = 1, φ₁ = 1+t, φ₂ = 1+t+t²/2, ... → eᵗ ✓


## Peano's Existence Theorem

**If f(t,y) is continuous on a rectangle R = {|t−t₀| ≤ a, |y−y₀| ≤ b}, then the IVP has at least one solution on [t₀−α, t₀+α]** where α = min(a, b/M), M = max|f| on R.

**Note:** Continuity gives existence but NOT uniqueness!

### Example of Non-Uniqueness
y' = y^(2/3), y(0) = 0

Both y(t) = 0 and y(t) = (t/3)³ are solutions! (f is continuous but not Lipschitz at y = 0)

## Picard-Lindelöf Theorem 🎯 (CSIR NET HIGH PRIORITY)

**If f is continuous AND satisfies a Lipschitz condition:**

**|f(t,y₁) − f(t,y₂)| ≤ L|y₁ − y₂|**

**then the IVP has a UNIQUE solution.**

### Picard's Iteration Method

Starting with φ₀(t) = y₀, define:

**φₙ₊₁(t) = y₀ + ∫_{t₀}^{t} f(s, φₙ(s)) ds**

These converge uniformly to the unique solution.

### Worked Example 🎯
Solve y' = y, y(0) = 1 by Picard iteration:

```
φ₀(t) = 1
φ₁(t) = 1 + ∫₀ᵗ 1 ds = 1 + t
φ₂(t) = 1 + ∫₀ᵗ (1+s) ds = 1 + t + t²/2
φ₃(t) = 1 + ∫₀ᵗ (1+s+s²/2) ds = 1 + t + t²/2 + t³/6
...
φₙ(t) = Σₖ₌₀ⁿ tᵏ/k! → eᵗ  ✓
```

## Gronwall's Inequality 🎯

If u(t) ≤ α + ∫_{t₀}^{t} β(s)u(s)ds where u, β ≥ 0, then:

**u(t) ≤ α · exp(∫_{t₀}^{t} β(s) ds)**

Used extensively in proving uniqueness and continuous dependence.

---

# UNIT 3: Systems of Differential Equations

> 📋 **Quick Refresher Before Starting:**
>
> **System of ODEs:** Multiple equations coupled together.
> x' = 2x + y
> y' = x - y
> Written as: X' = AX where X = (x,y) and A = [[2,1],[1,-1]].
> **Why matrices matter:** Solving X' = AX requires eigenvalues of A!


## From Single ODE to Systems

An nth-order ODE can always be converted to a first-order SYSTEM:

**y⁽ⁿ⁾ = f(t, y, y', ..., y⁽ⁿ⁻¹⁾)**

Setting x₁ = y, x₂ = y', ..., xₙ = y⁽ⁿ⁻¹⁾:

```
x₁' = x₂
x₂' = x₃
...
xₙ' = f(t, x₁, x₂, ..., xₙ)
```

In vector form: **x' = F(t, x)** where x = (x₁,...,xₙ)ᵀ

### Example
y'' + 3y' + 2y = 0 becomes:

```
x₁' = x₂
x₂' = −2x₁ − 3x₂

Matrix form: x' = |0   1| x = Ax
                   |−2 −3|
```

## Linear Systems: x' = A(t)x + g(t)

### Homogeneous case: x' = Ax (constant coefficients)

**Solution: x(t) = eᴬᵗ x₀**

where the **matrix exponential** eᴬᵗ = I + At + A²t²/2! + A³t³/3! + ...

### Fundamental Matrix
A matrix Φ(t) whose columns are n linearly independent solutions. Then:

**General solution: x(t) = Φ(t)c** where c is an arbitrary constant vector.

**Wronskian:** W(t) = det(Φ(t)). By Abel's formula:

W(t) = W(t₀) · exp(∫_{t₀}^{t} tr(A(s)) ds)

---

# UNIT 4: Solutions of Systems

> 📋 **Quick Refresher Before Starting:**
>
> **Matrix exponential:** e^(At) = I + At + A²t²/2! + A³t³/3! + ... (like the scalar eˣ but for matrices).
> **Solution of X' = AX:** X(t) = e^(At) · X(0).
> **If A is diagonalizable** (A = PDP⁻¹): e^(At) = P · diag(e^(λ₁t), ..., e^(λₙt)) · P⁻¹.
> This is why eigenvalues determine everything about the system's behavior!


## Matrix Exponential Method 🎯

For x' = Ax with constant A, the key is computing eᴬᵗ.

### Case 1: A is Diagonalizable
If A = PDP⁻¹ where D = diag(λ₁,...,λₙ), then:

**eᴬᵗ = P · diag(e^(λ₁t),...,e^(λₙt)) · P⁻¹**

### Example
```
A = |1  1|, eigenvalues λ = 0, 2
    |1  1|

P = | 1  1|, D = |0  0|
    |−1  1|      |0  2|

eᴬᵗ = P |1    0  | P⁻¹ = ½|1+e²ᵗ   e²ᵗ−1|
         |0   e²ᵗ|         |e²ᵗ−1   1+e²ᵗ|
```

### Case 2: A has Repeated Eigenvalues (Jordan Form)
If A = PJP⁻¹ where J = Jordan form, compute eᴶᵗ block by block:

```
e^(Jₖ(λ)t) = e^(λt) |1   t   t²/2!  ...|
                      |0   1   t      ...|
                      |0   0   1      ...|
                      |⋮               ⋱ |
```

### Case 3: Complex Eigenvalues
If λ = α ± βi, real solutions involve e^(αt)cos(βt) and e^(αt)sin(βt).

### Variation of Parameters (Non-homogeneous)
For x' = Ax + g(t):

**x(t) = eᴬᵗx₀ + ∫₀ᵗ eᴬ⁽ᵗ⁻ˢ⁾ g(s) ds**

---

# UNIT 5: Nonlinear Differential Systems

> 📋 **Quick Refresher Before Starting:**
>
> **Linear system:** X' = AX. Behavior fully determined by eigenvalues of A.
> **Nonlinear system:** X' = F(X) where F is NOT just a matrix times X.
> Example: x' = x - x³ (the -x³ term is nonlinear).
> **Linearization:** Near an equilibrium point x₀ (where F(x₀) = 0), approximate: F(x) ≈ DF(x₀)·(x - x₀).
> So near equilibrium, the nonlinear system behaves like a linear one!


## Phase Plane Analysis

For a 2D autonomous system:
```
x' = f(x, y)
y' = g(x, y)
```

**Equilibrium points** (critical points): where f(x,y) = 0 AND g(x,y) = 0.

### Linearization at Equilibrium 🎯
Near an equilibrium (x₀, y₀), the system behaves like:

**u' = J · u** where J is the Jacobian matrix evaluated at (x₀, y₀):

```
J = |∂f/∂x  ∂f/∂y|
    |∂g/∂x  ∂g/∂y| evaluated at (x₀, y₀)
```

### Example: Predator-Prey (Lotka-Volterra)
```
x' = x(a − by)    (prey)
y' = y(−c + dx)   (predator)
```

Equilibria: (0,0) and (c/d, a/b)

At (c/d, a/b): J = |    0      −bc/d|, eigenvalues = ±i√(ac)
                     |  ad/b      0  |

Pure imaginary eigenvalues → center (periodic orbits around equilibrium).

---

# UNIT 6: Poincaré-Bendixson Theory 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Phase plane:** Plot (x,y) as t varies. The trajectory traces a curve in 2D.
> **Limit cycle:** A closed trajectory that nearby solutions spiral toward (or away from).
> **Poincaré-Bendixson theorem** (key result): In 2D, if a trajectory stays in a bounded region with no equilibria, it must approach a limit cycle.
> This is one of the few tools for proving periodic solutions exist in nonlinear systems!


## Limit Sets

For a trajectory γ(t) in ℝ²:
- **ω-limit set:** points that γ(t) approaches as t → +∞
- **α-limit set:** points that γ(t) approaches as t → −∞

## Poincaré-Bendixson Theorem 🎯 (VERY IMPORTANT)

**If a trajectory of a 2D system stays in a bounded region containing no equilibrium points, then its ω-limit set is a periodic orbit (limit cycle).**

### Why Only 2D?
In 3D, trajectories can exhibit chaos (strange attractors). The Poincaré-Bendixson theorem says this CANNOT happen in 2D — the only long-term behaviors are:
1. Approach an equilibrium
2. Approach a periodic orbit
3. Be a periodic orbit

### Application: Proving Existence of Limit Cycles
**Strategy:** Find a "trapping region" (bounded, no equilibria inside) → limit cycle must exist.

### Example: Van der Pol Oscillator
x'' − μ(1−x²)x' + x = 0 (μ > 0)

As system: x' = y, y' = μ(1−x²)y − x

For large μ, one can construct an annular trapping region → unique stable limit cycle exists.

## Bendixson's Criterion (Negative Result)
If ∂f/∂x + ∂g/∂y has **one sign (and is not identically zero)** throughout a **simply connected** region D, then there are no periodic orbits lying entirely in D. (Both hypotheses — simply connected, and not identically zero — are essential. Hamiltonian systems have div = 0 everywhere yet have periodic orbits in abundance.)

---

# UNIT 7: Critical Points, Stability, and Lyapunov Methods 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Equilibrium:** A point x₀ where F(x₀) = 0 (the system stays still).
> **Stable:** Small perturbations stay small. **Unstable:** Small perturbations grow.
> **Asymptotically stable:** Perturbations not only stay small but decay to zero.
>
> **Lyapunov's method:** Find an "energy function" V(x) > 0 that DECREASES along solutions (V̇ ≤ 0).
> If such V exists → stable. If V̇ < 0 → asymptotically stable.
> Think of V like a ball on a hill: if V always decreases, the ball rolls to the bottom (equilibrium).


## Classification of Critical Points (2D Linear Systems)

For x' = Ax, classify by eigenvalues of A:

| Eigenvalues | Type | Stability |
|-------------|------|-----------|
| λ₁, λ₂ real, both < 0 | Stable node | Asymptotically stable |
| λ₁, λ₂ real, both > 0 | Unstable node | Unstable |
| λ₁ < 0 < λ₂ | Saddle point | Unstable |
| α ± βi, α < 0 | Stable spiral (focus) | Asymptotically stable |
| α ± βi, α > 0 | Unstable spiral | Unstable |
| ±βi (pure imaginary) | Center | Stable (not asymptotic) |
| λ₁ = λ₂ < 0, one eigenvector | Stable improper node | Asymptotically stable |

```
Stability Summary (trace-determinant plane):

                  det(A)
                    ↑
   Stable Spiral    │    Unstable Spiral        ← above parabola det = tr²/4
        ╲           │           ╱
         ╲          │          ╱
          ╲ Stable  │  Unstable                 ← below parabola det = tr²/4
           ╲ Node   │  Node
            ╲       │       ╱
   ──────────●──────┼──────●──────────→ tr(A)
                    │                            (det = 0 boundary)
                    │
              S A D D L E S                     ← entire half-plane det < 0
                    │
                    ▼
```

Key regions:
- det < 0 (lower half) → **Saddle**, regardless of trace
- det > 0, tr < 0 → **Stable** (asymptotically): node below parabola det = tr²/4, spiral above
- det > 0, tr > 0 → **Unstable**: node below parabola, spiral above
- det > 0, tr = 0 → **Center** (Lyapunov-stable, not asymptotic)
- det > 0, det = tr²/4 → degenerate / improper node (repeated eigenvalue)

## Lyapunov's Direct Method 🎯

Instead of solving the equation, find a **Lyapunov function** V(x):

### Lyapunov Stability Theorem
If there exists V: D → ℝ with:
1. V(0) = 0 and V(x) > 0 for x ≠ 0 (positive definite)
2. V̇(x) = ∇V · f(x) ≤ 0 (negative semi-definite)

Then the origin is **stable**.

If additionally V̇(x) < 0 for x ≠ 0 (negative definite), then **asymptotically stable**.

### How to Find Lyapunov Functions
Common choices:
- V = x² + y² (energy-like)
- V = xᵀPx where P is positive definite (for linear systems, solve AᵀP + PA = −Q)

### Example
x' = −x³, y' = −y. Try V = x² + y²:

V̇ = 2x(−x³) + 2y(−y) = −2x⁴ − 2y² < 0 for (x,y) ≠ (0,0)

So origin is **asymptotically stable**. ✓

---

# UNIT 8: Paths of Linear Systems

> 📋 **Quick Refresher Before Starting:**
>
> **Phase portrait:** A picture showing ALL trajectories of a 2D linear system X' = AX.
> The eigenvalues of A determine the portrait type:
> - Both negative → stable node (all trajectories → origin)
> - Both positive → unstable node (all trajectories ← away)
> - Opposite signs → saddle (some approach, some flee)
> - Complex with negative real part → stable spiral
> - Pure imaginary → center (circles)


## Phase Portraits for 2D Linear Systems

### Stable Node (λ₁ < λ₂ < 0)
All trajectories approach origin along the eigenvector of the smaller (more negative) eigenvalue.

```
        ╲   │   ╱
         ╲  │  ╱
          ╲ │ ╱
           ╲│╱
    ────────●────────  (origin)
           ╱│╲
          ╱ │ ╲
         ╱  │  ╲
        ╱   │   ╲
    Arrows point INWARD
```

### Saddle Point (λ₁ < 0 < λ₂)
```
         ↗  │  ↖
          ╲ │ ╱
           ╲│╱
    ←───────●───────→  (origin)
           ╱│╲
          ╱ │ ╲
         ↙  │  ↘
    Stable direction: eigenvector of λ₁
    Unstable direction: eigenvector of λ₂
```

### Spiral (α ± βi)
Trajectories spiral inward (α < 0) or outward (α > 0) around origin.

### Center (±βi)
Closed elliptical orbits around origin. No spiral — periodic motion.

---

# UNIT 9: Dependence on Parameters

> 📋 **Quick Refresher Before Starting:**
>
> **Parameter dependence:** If the ODE is y' = f(t, y, μ) where μ is a parameter, how does the solution change when μ changes slightly?
> **Key question:** Is the solution a continuous/differentiable function of the parameter μ?
> **Answer:** Yes, under mild conditions! The solution varies smoothly with parameters.


## Continuous Dependence

Solutions depend continuously on:
1. **Initial conditions:** Small change in y₀ → small change in solution
2. **Parameters:** If f depends on parameter μ, solutions vary continuously with μ

### Theorem (Continuous Dependence on Initial Data)
If f satisfies Lipschitz condition with constant L, and φ, ψ are solutions with different initial values:

**|φ(t) − ψ(t)| ≤ |φ(t₀) − ψ(t₀)| · e^(L|t−t₀|)**

### Sensitivity to Parameters
For y' = f(t, y, μ), the **variational equation** describes how the solution changes with μ:

∂/∂μ [y(t,μ)] satisfies a linear ODE obtained by differentiating the original equation w.r.t. μ.

## Bifurcation Theory (Introduction)

A **bifurcation** occurs when the qualitative behavior of solutions changes as a parameter crosses a critical value.

### Saddle-Node Bifurcation
x' = μ − x²

- μ < 0: no equilibria
- μ = 0: one equilibrium at x = 0 (semi-stable)
- μ > 0: two equilibria at x = ±√μ (one stable, one unstable)

---

# UNIT 10: Poincaré-Bendixson Theorem (Detailed)

> 📋 **Quick Refresher Before Starting:**
>
> **Poincaré-Bendixson (full version):** In a 2D autonomous system, if:
> (1) A trajectory stays in a bounded region, AND
> (2) The region contains no equilibrium points,
> THEN the trajectory approaches a periodic orbit (limit cycle).
>
> **Why only 2D?** In 3D and higher, trajectories can exhibit chaos (like the Lorenz attractor). The theorem fails!


## Full Statement

Let γ⁺ be a positive semi-orbit of a C¹ planar system that is contained in a compact set K. Then the ω-limit set ω(γ⁺) is one of:

1. A single equilibrium point
2. A periodic orbit
3. A set of equilibria and orbits connecting them (homoclinic/heteroclinic orbits)

If K contains no equilibria, then ω(γ⁺) is a periodic orbit.

## Dulac's Criterion (Ruling Out Periodic Orbits)

If there exists B(x,y) such that ∂(Bf)/∂x + ∂(Bg)/∂y has constant sign in D (simply connected), then no periodic orbits exist in D.

### Example
x' = y, y' = −x − y³. Try B = 1:
∂f/∂x + ∂g/∂y = 0 + (−3y²) = −3y² ≤ 0

Since this is ≤ 0 (and = 0 only on y = 0, not on a whole orbit), no periodic orbits.

## Index Theory

The **index** of a closed curve C around equilibria:

I(C) = (1/2π) ∮_C dθ (net rotation of the vector field)

Key facts:
- Index of a node, focus, or center = +1
- Index of a saddle = −1
- A periodic orbit must enclose equilibria whose indices sum to +1

---

# 📝 CSIR NET Practice Problems — Differential Equations

**Q1.** Apply Picard iteration to y' = 2ty, y(0) = 1. Find φ₃(t).

**Solution:**
φ₀ = 1
φ₁ = 1 + ∫₀ᵗ 2s·1 ds = 1 + t²
φ₂ = 1 + ∫₀ᵗ 2s(1+s²) ds = 1 + t² + t⁴/2
φ₃ = 1 + ∫₀ᵗ 2s(1+s²+s⁴/2) ds = 1 + t² + t⁴/2 + t⁶/6
(Converging to e^(t²))

**Q2.** Classify the critical point of x' = −2x + y, y' = x − 2y.

**Solution:** A = |−2  1|, eigenvalues: (−2−λ)² − 1 = 0 → λ = −1, −3
                  | 1 −2|
Both negative → **Stable node**, asymptotically stable.

**Q3.** Show x' = x² + y², y' = −2xy has no periodic orbits in ℝ².

**Solution:** Note that x' = x² + y² ≥ 0 for all (x, y), with equality only at the origin. So along any non-trivial trajectory, x(t) is **non-decreasing** (strictly increasing whenever the trajectory is not at the origin).

If a trajectory γ were periodic with period T > 0, then x(T) = x(0), so

∫₀ᵀ ẋ(s) ds = x(T) − x(0) = 0.

But ẋ = x² + y² ≥ 0, so this forces ẋ ≡ 0 along γ, i.e. x² + y² ≡ 0, meaning γ is the single point (0, 0). Hence there are **no non-trivial periodic orbits** in ℝ². ∎

(The standard Bendixson/Dulac approach is inconclusive here: div(f, g) = 2x − 2x = 0 identically, and trying B = 1/(x²+y²) gives ∂(Bf)/∂x + ∂(Bg)/∂y = 2x(y²−x²)/(x²+y²)², which changes sign. The monotonicity argument above sidesteps this entirely.)

**Q4.** Find a Lyapunov function for x' = −x + y², y' = −y.

**Solution:** Try V = x² + y². V̇ = 2x(−x+y²) + 2y(−y) = −2x² + 2xy² − 2y².
For small (x,y): V̇ ≈ −2x² − 2y² < 0. So origin is locally asymptotically stable.

---

> **📖 Recommended Reading:** Coddington & Levinson "Theory of ODEs", Perko "Differential Equations and Dynamical Systems"
> **Next Subject:** [Dynamics of a Rigid Body →](./06_Dynamics_of_Rigid_Body.md)
