# 📐 Advanced Linear Algebra — Complete Study Notes

> **CSIR NET Priority: ⭐⭐⭐⭐⭐ | This is the HIGHEST weightage subject in CSIR NET**

---

## 🗺️ Subject Mind Map

```
                    ADVANCED LINEAR ALGEBRA
                           │
         ┌─────────┬───────┴────────┬──────────┐
         │         │                │          │
    Transforms   Spaces          Forms     Canonical
         │         │                │          │
    ┌────┴────┐  ┌─┴──┐        ┌───┴───┐   ┌──┴──┐
    Linear  Dual Inner  Orth.  Bilinear  Jordan Cayley
    Trans.  Basis Prod.  Trans. Quadratic Form  Hamilton
```

---

# UNIT 1: Linear Transformations

> 📋 **Quick Refresher Before Starting:**
>
> **Matrix:** A rectangular grid of numbers. A 2×2 matrix looks like:
> ```
> A = | 2  3 |    We write A = [[2,3],[1,4]]
>     | 1  4 |
> ```
> **Matrix multiplication:** Row × Column. For AB, take each row of A, multiply element-by-element with each column of B, and add up.
> ```
> | 2 3 | × | 1 | = | 2×1 + 3×0 | = | 2 |
> | 1 4 |   | 0 |   | 1×1 + 4×0 |   | 1 |
> ```
> **Vector:** An ordered list of numbers, like v = (3, -1, 2) in ℝ³.
> **Linear combination:** c₁v₁ + c₂v₂ means scaling and adding vectors.
> **System Ax = b:** Finding x means solving multiple equations simultaneously.



## Prerequisites from Class 12
You know matrices and solving equations. Now we go deeper — a **linear transformation** is the *abstract idea* behind matrix multiplication.

## What is a Linear Transformation?

**Definition:** Let V and W be vector spaces over a field F. A function T: V → W is a **linear transformation** if for all vectors u, v ∈ V and all scalars c ∈ F:

1. **T(u + v) = T(u) + T(v)** (preserves addition)
2. **T(cv) = cT(v)** (preserves scalar multiplication)

**In plain English:** A linear transformation is a function between vector spaces that "plays nice" with addition and scaling. No bending, no twisting — just stretching, rotating, reflecting, or projecting.

### 💡 Memory Aid
Think of a linear transformation as a "well-behaved machine": if you double the input, the output doubles. If you add two inputs, the output is the sum of individual outputs.

### Example 1: Rotation in ℝ²
The rotation by angle θ counterclockwise is T: ℝ² → ℝ² defined by:

```
T(x, y) = (x cos θ − y sin θ, x sin θ + y cos θ)
```

**Verification of linearity:**
Let u = (x₁, y₁), v = (x₂, y₂)

T(u + v) = T(x₁+x₂, y₁+y₂)
= ((x₁+x₂)cosθ − (y₁+y₂)sinθ, (x₁+x₂)sinθ + (y₁+y₂)cosθ)
= (x₁cosθ − y₁sinθ, x₁sinθ + y₁cosθ) + (x₂cosθ − y₂sinθ, x₂sinθ + y₂cosθ)
= T(u) + T(v) ✓

Similarly, T(cu) = cT(u) ✓

### Example 2: Differentiation
D: Pₙ(ℝ) → Pₙ₋₁(ℝ), where D(p) = p' (the derivative)

```
D(3x² + 2x + 1) = 6x + 2
```

This IS linear because: d/dx(f + g) = f' + g' and d/dx(cf) = cf'

### Example 3 (Non-example): T(x) = x² is NOT linear
T(2) = 4, but 2·T(1) = 2·1 = 2 ≠ 4. So T(cu) ≠ cT(u). ✗

## Key Concepts

### Kernel (Null Space)
**ker(T) = {v ∈ V : T(v) = 0}** — all vectors that T "kills" (maps to zero)

### Image (Range)
**Im(T) = {T(v) : v ∈ V}** — all possible outputs of T

### 🎯 CSIR NET Critical Theorem: Rank-Nullity Theorem

**dim(V) = dim(ker T) + dim(Im T)**

That is: **dim(domain) = nullity + rank**

**Example:** T: ℝ⁴ → ℝ³ with rank(T) = 2. Then nullity = 4 − 2 = 2.

### Worked Example (CSIR NET Style)
**Q:** Let T: ℝ³ → ℝ³ be defined by T(x,y,z) = (x+y, y+z, 0). Find rank and nullity.

**Solution:**
- Matrix of T: A = [[1,1,0],[0,1,1],[0,0,0]]
- Row reduce: already in echelon form. Rank = 2 (two non-zero rows)
- By Rank-Nullity: Nullity = 3 − 2 = 1
- ker(T): x+y=0, y+z=0 → y=−x, z=x → ker = span{(1,−1,1)}

---

# UNIT 2: Linear Transformations and Vector Spaces

> 📋 **Quick Refresher Before Starting:**
>
> **Basis:** A set of vectors that (1) spans the space and (2) is linearly independent.
> Example: {(1,0), (0,1)} is the standard basis for ℝ². Every vector (a,b) = a(1,0) + b(0,1).
> **Dimension:** Number of vectors in a basis. dim(ℝ³) = 3.
> **Linear transformation T:** A function between vector spaces that preserves addition and scaling:
> T(u + v) = T(u) + T(v) and T(cv) = cT(v).
> Example: T(x,y) = (2x + y, x - y) is linear. T(x,y) = (x², y) is NOT (because T(2v) ≠ 2T(v)).


## Matrix Representation of Linear Transformations

Every linear transformation between finite-dimensional spaces can be represented by a matrix (once you choose bases).

**Recipe:**
1. Choose ordered basis B = {v₁,...,vₙ} for V and B' = {w₁,...,wₘ} for W
2. Compute T(v₁), T(v₂), ..., T(vₙ)
3. Express each T(vⱼ) as a linear combination of w₁,...,wₘ
4. The coefficients form the columns of the matrix [T]

### Example
Let T: ℝ² → ℝ² be T(x,y) = (2x+y, x−y). With standard basis e₁=(1,0), e₂=(0,1):

```
T(e₁) = (2,1) = 2e₁ + 1e₂
T(e₂) = (1,−1) = 1e₁ + (−1)e₂

Matrix [T] = | 2   1 |
             | 1  −1 |
```

## Change of Basis

If B and B' are two bases for V, and P is the change-of-basis matrix from B to B', then:

$[T]_{B'} = P^{-1} [T]_B P$

This is called a **similarity transformation**. Two matrices A and B are **similar** if B = P⁻¹AP for some invertible P.

> **🎯 CSIR NET:** Similar matrices have the same eigenvalues, trace, determinant, rank, and characteristic polynomial!

## Isomorphisms

A linear transformation T: V → W is an **isomorphism** if it is bijective (one-to-one and onto).

**Key Result:** Two finite-dimensional vector spaces over F are isomorphic **if and only if** they have the same dimension.

So ℝ³ ≅ P₂(ℝ) ≅ M₁ₓ₃(ℝ) — they're all "the same" as vector spaces (all dimension 3).

---

# UNIT 3: Dual Basis, Annihilators, and Transformations

> 📋 **Quick Refresher Before Starting:**
>
> **Linear functional:** A linear map from V to ℝ (or ℂ). It takes a vector, outputs a single number.
> Example: f(x,y,z) = 2x + 3y - z is a linear functional on ℝ³.
> **Dual space V*:** The set of ALL linear functionals on V. Surprisingly, dim(V*) = dim(V).
> **If V has basis {e₁, e₂, e₃}**, then V* has a dual basis {f₁, f₂, f₃} where fᵢ(eⱼ) = 1 if i=j, 0 otherwise.
> Think of dual basis as "coordinate extractors" — f₁ extracts the first coordinate.


## Dual Space

**Definition:** The **dual space** V* of V is the vector space of all linear functionals on V.

A **linear functional** is a linear transformation f: V → F (from V to the scalar field).

### Example
On ℝ³, the function f(x,y,z) = 2x − 3y + z is a linear functional.

### Dual Basis
If B = {v₁,...,vₙ} is a basis for V, the **dual basis** B* = {f₁,...,fₙ} is defined by:

```
fᵢ(vⱼ) = δᵢⱼ = { 1 if i=j
                  { 0 if i≠j
```

**Key fact:** dim(V*) = dim(V)

### Example
For ℝ², with standard basis {e₁=(1,0), e₂=(0,1)}:
- f₁(x,y) = x (picks out the first coordinate)
- f₂(x,y) = y (picks out the second coordinate)

## Annihilators

For a subspace W ⊆ V, the **annihilator** W⁰ is:

**W⁰ = {f ∈ V* : f(w) = 0 for all w ∈ W}**

### 🎯 CSIR NET Key Formula:
**dim(W) + dim(W⁰) = dim(V)**

### Example
V = ℝ³, W = span{(1,0,0), (0,1,0)} (the xy-plane).
W⁰ = {f(x,y,z) = cz : c ∈ ℝ} — all functionals that vanish on the xy-plane.
dim(W) = 2, dim(W⁰) = 1, sum = 3 = dim(V) ✓

## Transpose (Dual) of a Transformation

If T: V → W is linear, the **transpose** T*: W* → V* is defined by:

**(T*f)(v) = f(T(v))** for all f ∈ W*, v ∈ V

The matrix of T* is the transpose of the matrix of T (with respect to dual bases).

---

# UNIT 4: Inner Product Spaces

> 📋 **Quick Refresher Before Starting:**
>
> **Dot product** (from Class 12): For u = (u₁,u₂), v = (v₁,v₂):
> u · v = u₁v₁ + u₂v₂ (multiply corresponding entries and add)
> Example: (3,4) · (1,2) = 3×1 + 4×2 = 11
>
> **Key properties of dot product:**
> - u · v = |u||v|cosθ where θ is the angle between them
> - u ⊥ v (perpendicular) ⟺ u · v = 0
> - |u| = √(u · u) = √(u₁² + u₂²) (Pythagoras!)
>
> **Inner product** is a generalization of dot product. It can be defined on ANY vector space, not just ℝⁿ.
> For polynomials: ⟨p,q⟩ = ∫₀¹ p(x)q(x)dx is a valid inner product!


## What is an Inner Product?

An **inner product** on a real vector space V is a function ⟨·,·⟩: V × V → ℝ satisfying:

1. **Symmetry:** ⟨u,v⟩ = ⟨v,u⟩
2. **Linearity in first argument:** ⟨au+bv, w⟩ = a⟨u,w⟩ + b⟨v,w⟩
3. **Positive definiteness:** ⟨v,v⟩ ≥ 0, and ⟨v,v⟩ = 0 iff v = 0

**Complex case:** On a complex vector space, the inner product satisfies conjugate symmetry: ⟨u,v⟩ = ⟨v,u⟩̄, and is sesquilinear (linear in the first argument, conjugate-linear in the second). The standard example on ℂⁿ is ⟨z,w⟩ = Σ zₖw̄ₖ.

**In plain English:** An inner product is a way to measure "angles" and "lengths" in abstract vector spaces.

### The Standard Inner Product on ℝⁿ
⟨(x₁,...,xₙ), (y₁,...,yₙ)⟩ = x₁y₁ + x₂y₂ + ... + xₙyₙ (the dot product you know!)

### Norm (Length)
||v|| = √⟨v,v⟩

### 🎯 CSIR NET: Cauchy-Schwarz Inequality
**|⟨u,v⟩| ≤ ||u|| · ||v||**

Equality holds iff u and v are linearly dependent (parallel).

### 🎯 CSIR NET: Triangle Inequality
**||u + v|| ≤ ||u|| + ||v||**

### Worked Example
In ℝ³ with standard inner product, let u = (1,2,3), v = (4,−1,2):

```
⟨u,v⟩ = 1(4) + 2(−1) + 3(2) = 4 − 2 + 6 = 8
||u|| = √(1+4+9) = √14
||v|| = √(16+1+4) = √21

Check C-S: |8| ≤ √14 · √21 = √294 ≈ 17.15 ✓
```

## Orthogonality

Two vectors u, v are **orthogonal** if ⟨u,v⟩ = 0.

A set {v₁,...,vₖ} is **orthogonal** if ⟨vᵢ,vⱼ⟩ = 0 for all i ≠ j.

It is **orthonormal** if additionally ||vᵢ|| = 1 for all i.

---

# UNIT 5: Orthonormal Systems and Orthogonal Transformations

> 📋 **Quick Refresher Before Starting:**
>
> **Orthogonal** = perpendicular (inner product = 0).
> **Orthonormal** = orthogonal AND each vector has length 1.
> Example: {(1,0), (0,1)} is orthonormal. {(1,1), (-1,1)} is orthogonal but NOT orthonormal (length = √2).
> To make it orthonormal: divide each by its length → {(1/√2, 1/√2), (-1/√2, 1/√2)}.
>
> **Gram-Schmidt Process** (you'll learn this here): Takes ANY basis and produces an orthonormal basis.
> It works by: take first vector, normalize it. For each next vector, subtract its projections onto previous orthonormal vectors, then normalize.


## Gram-Schmidt Process 🎯 (CSIR NET FAVORITE!)

Given a basis {v₁,...,vₙ}, produce an orthonormal basis {e₁,...,eₙ}:

```
Step 1: u₁ = v₁,  e₁ = u₁/||u₁||

Step 2: u₂ = v₂ − ⟨v₂,e₁⟩e₁,  e₂ = u₂/||u₂||

Step 3: u₃ = v₃ − ⟨v₃,e₁⟩e₁ − ⟨v₃,e₂⟩e₂,  e₃ = u₃/||u₃||

General: uₖ = vₖ − Σᵢ₌₁ᵏ⁻¹ ⟨vₖ,eᵢ⟩eᵢ,  eₖ = uₖ/||uₖ||
```

### Worked Example
Apply Gram-Schmidt to {v₁=(1,1,0), v₂=(1,0,1), v₃=(0,1,1)} in ℝ³:

**Step 1:**
u₁ = (1,1,0), ||u₁|| = √2, e₁ = (1/√2, 1/√2, 0)

**Step 2:**
⟨v₂,e₁⟩ = 1/√2 + 0 + 0 = 1/√2
u₂ = (1,0,1) − (1/√2)(1/√2, 1/√2, 0) = (1,0,1) − (1/2, 1/2, 0) = (1/2, −1/2, 1)
||u₂|| = √(1/4 + 1/4 + 1) = √(3/2)
e₂ = (1/√6, −1/√6, 2/√6)

**Step 3:**
⟨v₃,e₁⟩ = 1/√2, ⟨v₃,e₂⟩ = −1/√6 + 2/√6 = 1/√6
u₃ = (0,1,1) − (1/√2)e₁ − (1/√6)e₂ = (−2/3, 2/3, 2/3)... [normalize]
e₃ = (−1/√3, 1/√3, 1/√3)

## Orthogonal Matrices & Transformations

**Definition:** A matrix Q is **orthogonal** if Q^T Q = I (equivalently, Q^T = Q⁻¹).

**Properties of orthogonal matrices:**
- det(Q) = ±1
- Columns form an orthonormal set
- Preserves lengths: ||Qv|| = ||v||
- Preserves angles: ⟨Qu, Qv⟩ = ⟨u,v⟩

### 🎯 CSIR NET Type Question
**Q:** Which of the following is an orthogonal matrix?

```
A = |cos θ  −sin θ|    B = |1  1|    C = |1  0|
    |sin θ   cos θ|        |0  1|        |0  2|
```

**Answer:** A only. Check: A^T A = I ✓. B and C fail this test.

---

# UNIT 6: Inner Product Space Isomorphism

> 📋 **Quick Refresher Before Starting:**
>
> **Isomorphism** = a perfect structural match between two spaces.
> If T: V → W is a bijective linear map, then V and W are "the same" structurally.
> **Key theorem:** V ≅ W (isomorphic) ⟺ dim(V) = dim(W). So ALL n-dimensional real vector spaces are "the same" as ℝⁿ!
> This unit shows: inner product spaces of the same dimension are isomorphic in a way that preserves lengths and angles.


## Riesz Representation Theorem

**Theorem (Finite-dimensional version):** If V is a **finite-dimensional** inner product space, then for every linear functional f ∈ V*, there exists a unique vector v₀ ∈ V such that f(v) = ⟨v, v₀⟩ for all v ∈ V, and ‖f‖ = ‖v₀‖.

**Infinite-dimensional version (Hilbert space):** Every **continuous** linear functional φ on a Hilbert space H is φ(v) = ⟨v, v₀⟩ for a unique v₀ ∈ H (continuity is needed — there exist discontinuous linear functionals on infinite-dimensional spaces).

**In plain English:** Every (continuous) linear functional on a Hilbert space is "taking the inner product with some fixed vector."

### Example
On ℝ³, the functional f(x,y,z) = 2x − 3y + z is represented by v₀ = (2,−3,1) because:
f(v) = ⟨v, (2,−3,1)⟩ for all v.

## Orthogonal Complements

For a subspace W ⊆ V: **W⊥ = {v ∈ V : ⟨v,w⟩ = 0 for all w ∈ W}**

### Key Results:
- V = W ⊕ W⊥ (direct sum decomposition)
- dim(W) + dim(W⊥) = dim(V)
- (W⊥)⊥ = W

### Projection Theorem
Every v ∈ V can be uniquely written as v = w + w⊥ where w ∈ W, w⊥ ∈ W⊥.

The **orthogonal projection** onto W is: proj_W(v) = Σᵢ ⟨v,eᵢ⟩eᵢ (where {eᵢ} is an orthonormal basis for W)

---

# UNIT 7: Algebra of Hom(V,V)

> 📋 **Quick Refresher Before Starting:**
>
> **Polynomial in a matrix:** If p(x) = x² - 3x + 2, then p(A) = A² - 3A + 2I.
> Example: A = [[1,0],[0,2]]. A² = [[1,0],[0,4]]. p(A) = [[1,0],[0,4]] - [[3,0],[0,6]] + [[2,0],[0,2]] = [[0,0],[0,0]].
> So A satisfies the polynomial x² - 3x + 2 = (x-1)(x-2)!
>
> **Hom(V,V)** = set of all linear transformations from V to itself. This set is itself a vector space AND an algebra (you can multiply = compose transformations).
> **Minimal polynomial:** The smallest-degree polynomial that A satisfies.


## The Space of All Linear Operators

**Hom(V,V)** = {T: V → V | T is linear} is itself a vector space of dimension n².

It is also an **algebra** (you can compose/multiply transformations).

## Key Concepts

### Eigenvalues and Eigenvectors 🎯 (HIGHEST PRIORITY FOR CSIR NET)

**Definition:** λ is an eigenvalue of T if T(v) = λv for some v ≠ 0. Such v is an eigenvector.

**Characteristic polynomial:** p(λ) = det(A − λI)

**To find eigenvalues:** Solve det(A − λI) = 0

### Worked Example
```
A = |2  1|
    |1  2|

det(A − λI) = (2−λ)² − 1 = λ² − 4λ + 3 = (λ−1)(λ−3) = 0

Eigenvalues: λ₁ = 1, λ₂ = 3

For λ₁ = 1: (A−I)v = 0 → |1  1| |x| = |0| → x+y=0 → v₁ = (1,−1)
                            |1  1| |y|   |0|

For λ₂ = 3: (A−3I)v = 0 → |−1  1| |x| = |0| → −x+y=0 → v₂ = (1,1)
                             | 1 −1| |y|   |0|
```

### Minimal Polynomial
The **minimal polynomial** m(λ) is the monic polynomial of least degree such that m(A) = 0.

**Key facts:**
- m(λ) divides the characteristic polynomial p(λ)
- They have the same roots (but possibly different multiplicities)
- A is diagonalizable iff m(λ) has no repeated roots

---

# UNIT 8: Diagonalization and Invariant Subspaces

> 📋 **Quick Refresher Before Starting:**
>
> **Eigenvalue and Eigenvector:** If Av = λv (A stretches v by factor λ), then:
> - λ is an eigenvalue, v is an eigenvector
> - To find eigenvalues: solve det(A - λI) = 0
>
> **Worked example:** A = [[2,1],[0,3]].
> det(A - λI) = det([[2-λ, 1],[0, 3-λ]]) = (2-λ)(3-λ) = 0
> So λ₁ = 2, λ₂ = 3.
> For λ=2: (A-2I)v = 0 → [[0,1],[0,1]]v = 0 → v = (1,0).
> For λ=3: (A-3I)v = 0 → [[-1,1],[0,0]]v = 0 → v = (1,1).
>
> **Diagonalization:** A = PDP⁻¹ where D = diagonal matrix of eigenvalues, P = matrix of eigenvectors. Only works if there are enough independent eigenvectors.


## Diagonalization 🎯

A matrix A is **diagonalizable** if there exists an invertible P such that P⁻¹AP = D (diagonal).

**When is A diagonalizable?**
- A has n linearly independent eigenvectors
- Equivalently, the minimal polynomial has no repeated roots
- For each eigenvalue: geometric multiplicity = algebraic multiplicity

### Example (Diagonalizable)
```
A = |4  1|, eigenvalues: λ=4, λ=5
    |0  5|  (note: not symmetric, but still diagonalizable since distinct eigenvalues)

  Eigenvector for λ=4: (A−4I)v = 0 ⟹ v = (1, 0).
  Eigenvector for λ=5: (A−5I)v = 0 ⟹ v = (1, 1).

P = |1  1|, P⁻¹AP = |4  0|
    |0  1|           |0  5|
```

### Example (NOT Diagonalizable)
```
A = |1  1|, eigenvalue: λ=1 (repeated)
    |0  1|  Only one eigenvector: (1,0). Not diagonalizable!
```

## Invariant Subspaces

A subspace W ⊆ V is **T-invariant** if T(W) ⊆ W (T maps W into itself).

**Examples of invariant subspaces:**
- {0} and V (trivially)
- ker(T) and Im(T)
- Eigenspaces Eλ = ker(T − λI)

---

# UNIT 9: Cayley-Hamilton, Canonical Forms, Jordan Form 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Characteristic polynomial:** p(λ) = det(A - λI). Its roots are the eigenvalues.
> **Cayley-Hamilton Theorem** (you'll prove here): Every matrix satisfies its own characteristic polynomial. p(A) = 0.
> Example: If char poly is λ² - 5λ + 6 = 0, then A² - 5A + 6I = 0 (the zero matrix!).
>
> **Jordan form:** When a matrix can't be diagonalized, Jordan form is the "next best thing."
> A Jordan block J₂(λ) = [[λ,1],[0,λ]] — it's almost diagonal, with 1's on the superdiagonal.


## Cayley-Hamilton Theorem

**Every square matrix satisfies its own characteristic polynomial.**

If p(λ) = det(A − λI), then **p(A) = 0** (the zero matrix).

### Example
```
A = |1  2|
    |3  4|

p(λ) = λ² − 5λ − 2

Check: A² − 5A − 2I = |7  10| − |5  10| − |2  0| = |0  0| ✓
                        |15 22|   |15 20|   |0  2|   |0  0|
```

### 🎯 CSIR NET Application
Use Cayley-Hamilton to compute A⁻¹:
From A² − 5A − 2I = 0: A² = 5A + 2I → A(A − 5I) = 2I → A⁻¹ = (A − 5I)/2

## Jordan Canonical Form

When a matrix is NOT diagonalizable, we use the **Jordan form** — the "next best thing."

A **Jordan block** Jₖ(λ) is a k×k matrix:
```
Jₖ(λ) = |λ  1  0  ··· 0|
         |0  λ  1  ··· 0|
         |0  0  λ  ··· 0|
         |⋮        ⋱   1|
         |0  0  0  ··· λ|
```

**Jordan Normal Form Theorem:** Every square matrix over ℂ is similar to a block diagonal matrix of Jordan blocks.

### Example (3×3, hand-checkable)
```
A = |2  1  0|     Jordan form:  |2  1  0|
    |0  2  0|                    |0  2  0|
    |0  0  2|                    |0  0  2|
```

Here A is already in Jordan normal form: $J = J_2(2) \oplus J_1(2)$.

- Characteristic polynomial: $(\lambda-2)^3$ (algebraic multiplicity of $\lambda=2$ is 3).
- Minimal polynomial: $(\lambda-2)^2$ (because $(A-2I)^2 = 0$ but $A-2I \ne 0$).
- The size of the largest Jordan block for $\lambda=2$ equals the multiplicity of $(\lambda-2)$ in the minimal polynomial — namely $2$. So we get one $J_2(2)$ block. The remaining algebraic multiplicity $3-2=1$ contributes one $J_1(2)$ block.
- Geometric multiplicity (number of blocks) = 3 − dim(image of A−2I) = 3 − 1 = 2. ✓ (one J₂ + one J₁ = 2 blocks).

---

# UNIT 10: Forms on Vector Spaces

> 📋 **Quick Refresher Before Starting:**
>
> **Quadratic form** = a homogeneous degree-2 polynomial in several variables.
> Examples: Q(x,y) = 3x² + 2xy - y² or Q(x,y,z) = x² + 4y² + z² - 2xz
> Every quadratic form can be written as Q(x) = xᵀAx where A is symmetric.
> Example: Q = 3x² + 2xy - y² corresponds to A = [[3,1],[1,-1]] (off-diagonal = half the xy coefficient).
>
> **Classification:**
> - Positive definite: Q > 0 for all x ≠ 0 (like x² + y² — a bowl shape)
> - Negative definite: Q < 0 for all x ≠ 0
> - Indefinite: Q takes both positive and negative values (like x² - y² — a saddle)


## Bilinear Forms

A **bilinear form** on V is a function B: V × V → F that is linear in each argument:
- B(au+bv, w) = aB(u,w) + bB(v,w)
- B(u, av+bw) = aB(u,v) + bB(u,w)

**Matrix representation:** B(x,y) = x^T A y

### Types:
- **Symmetric:** B(u,v) = B(v,u) ↔ A^T = A
- **Skew-symmetric:** B(u,v) = −B(v,u) ↔ A^T = −A
- **Non-degenerate:** B(u,v) = 0 for all v implies u = 0

## Quadratic Forms 🎯

A **quadratic form** Q: V → F is Q(v) = B(v,v) for some symmetric bilinear form B.

### Example
Q(x,y,z) = 2x² + 3y² − z² + 4xy − 2xz

Matrix: A = | 2   2  −1|
            | 2   3   0|
            |−1   0  −1|

### Sylvester's Law of Inertia 🎯
Every real quadratic form can be reduced to: Q = x₁² + ... + xₚ² − xₚ₊₁² − ... − xᵣ²

The pair (p, r−p) is the **signature** — it's an invariant (doesn't change with basis).

### Classification:
- **Positive definite:** All eigenvalues > 0 (signature (n,0))
- **Negative definite:** All eigenvalues < 0
- **Indefinite:** Mixed signs
- **Positive semi-definite:** All eigenvalues ≥ 0

---

# 📝 CSIR NET Practice Problems — Linear Algebra

**Q1.** Let T: ℝ³ → ℝ³ be T(x,y,z) = (y+z, x+z, x+y). Find eigenvalues of T.

**Solution:** Matrix A = |0 1 1|, det(A−λI) = −λ³+3λ+2 = −(λ−2)(λ+1)² = 0
                          |1 0 1|
                          |1 1 0|
Eigenvalues: λ = 2 (once), λ = −1 (twice)

**Q2.** If A is a 5×5 matrix with characteristic polynomial (λ−2)³(λ+1)² and minimal polynomial (λ−2)²(λ+1), what are the possible Jordan forms?

**Solution:** Jordan blocks for λ=2: one J₂(2) + one J₁(2). For λ=−1: two J₁(−1).
Jordan form = diag(J₂(2), J₁(2), J₁(−1), J₁(−1))

**Q3.** True or False: Every real symmetric matrix is diagonalizable.
**Answer:** TRUE. (Spectral Theorem — orthogonally diagonalizable!)

**Q4.** Let V = P₃(ℝ). Define T(p) = p'. What is the Jordan form of T?
**Solution:** T is nilpotent: T⁴ = 0. Matrix is 4×4 with λ=0 only. Jordan form = J₄(0).

---

> **📖 Recommended Reading:** Hoffman & Kunze "Linear Algebra", Friedberg et al. "Linear Algebra"
> **Next Subject:** [Mathematical Analysis →](./02_Mathematical_Analysis.md)
