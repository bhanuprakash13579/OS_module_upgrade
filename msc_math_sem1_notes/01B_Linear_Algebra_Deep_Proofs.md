# 📐 Linear Algebra — Deep Proofs & Extended Examples Supplement

> **This supplements 01_Advanced_Linear_Algebra.md with complete proofs and extra examples needed for >95%**

---

# CRITICAL PROOFS (University "State and Prove" Questions)

## Proof 1: Rank-Nullity Theorem ⚡⚡⚡

**Theorem:** If T: V → W is linear and V is finite-dimensional, then dim(V) = dim(ker T) + dim(Im T).

**Proof:**
Let dim(ker T) = k. Choose basis {v₁,...,vₖ} for ker T.
Extend to basis {v₁,...,vₖ, vₖ₊₁,...,vₙ} for V.

**Claim:** {T(vₖ₊₁),...,T(vₙ)} is a basis for Im T.

**Spanning:** Any w ∈ Im T has form w = T(c₁v₁+...+cₙvₙ) = c₁T(v₁)+...+cₙT(vₙ) = 0+...+0+cₖ₊₁T(vₖ₊₁)+...+cₙT(vₙ). ✓

**Independence:** Suppose cₖ₊₁T(vₖ₊₁)+...+cₙT(vₙ) = 0.
Then T(cₖ₊₁vₖ₊₁+...+cₙvₙ) = 0, so cₖ₊₁vₖ₊₁+...+cₙvₙ ∈ ker T.
So cₖ₊₁vₖ₊₁+...+cₙvₙ = a₁v₁+...+aₖvₖ for some aᵢ.
Since {v₁,...,vₙ} is a basis, all coefficients = 0. In particular cₖ₊₁=...=cₙ=0. ✓

Therefore dim(Im T) = n − k, giving n = k + (n−k). ∎

---

## Proof 2: Cayley-Hamilton Theorem ⚡⚡⚡

**Theorem:** Every matrix satisfies its characteristic polynomial.

**Proof (for diagonalizable case — exam-friendly version):**
Let A = PDP⁻¹ where D = diag(λ₁,...,λₙ).
Characteristic polynomial: p(λ) = det(λI − A) = Π(λ − λᵢ).

p(A) = P·p(D)·P⁻¹ = P·diag(p(λ₁),...,p(λₙ))·P⁻¹

But p(λᵢ) = 0 for each eigenvalue λᵢ (by definition of characteristic polynomial).

So p(A) = P·0·P⁻¹ = 0. ∎

**Proof (general case via adjugate):**
Let B(λ) = adj(λI − A) be the adjugate. Then:
(λI − A)·B(λ) = det(λI − A)·I = p(λ)·I

B(λ) is a matrix polynomial: B(λ) = Bₙ₋₁λⁿ⁻¹ + ... + B₁λ + B₀

Expanding (λI − A)(Bₙ₋₁λⁿ⁻¹ + ... + B₀) and comparing coefficients of λⁿ, λⁿ⁻¹, ..., λ⁰:

Bₙ₋₁ = I
Bₙ₋₂ − ABₙ₋₁ = cₙ₋₁I
...
−AB₀ = c₀I

Multiply these by Aⁿ, Aⁿ⁻¹, ..., A⁰ respectively and add:
0 = Aⁿ + cₙ₋₁Aⁿ⁻¹ + ... + c₀I = p(A). ∎

---

## Proof 3: Spectral Theorem (Real Symmetric Matrices) ⚡⚡⚡

**Theorem:** Every real symmetric matrix is orthogonally diagonalizable (A = QDQᵀ where Q is orthogonal).

**Proof sketch (exam-level):**

**Step 1:** Eigenvalues of symmetric matrices are real.

Let A be real symmetric, Av = λv with v ∈ ℂⁿ and v ≠ 0. Write $v^*$ for the conjugate transpose of v, and $\bar\lambda$ for the complex conjugate of λ.

- Multiply Av = λv on the left by $v^*$:   $v^* A v = \lambda \, v^* v = \lambda \|v\|^2$.
- Take the conjugate transpose of Av = λv:  $v^* A^* = \bar\lambda \, v^*$. Since A is real symmetric, $A^* = A$, so $v^* A = \bar\lambda \, v^*$. Now multiply on the right by v:  $v^* A v = \bar\lambda \, v^* v = \bar\lambda \|v\|^2$.

Equating the two expressions: $(\lambda - \bar\lambda) \|v\|^2 = 0$. Since v ≠ 0 we have $\|v\|^2 > 0$, hence $\lambda = \bar\lambda$, so λ ∈ ℝ. ✓

**Step 2:** Eigenvectors for distinct eigenvalues are orthogonal.
Av₁ = λ₁v₁, Av₂ = λ₂v₂ with λ₁ ≠ λ₂.
λ₁⟨v₁,v₂⟩ = ⟨Av₁,v₂⟩ = ⟨v₁,Aᵀv₂⟩ = ⟨v₁,Av₂⟩ = λ₂⟨v₁,v₂⟩.
So (λ₁−λ₂)⟨v₁,v₂⟩ = 0, giving ⟨v₁,v₂⟩ = 0. ✓

**Step 3:** Induction on dimension to get full orthogonal eigenbasis. ∎

---

## Proof 4: Cauchy-Schwarz Inequality ⚡⚡⚡

**Theorem:** |⟨u,v⟩| ≤ ||u||·||v|| with equality iff u, v linearly dependent.

**Proof:**
If v = 0, both sides = 0. ✓
If v ≠ 0, for any scalar t ∈ ℝ:
0 ≤ ||u − tv||² = ⟨u−tv, u−tv⟩ = ||u||² − 2t⟨u,v⟩ + t²||v||²

This quadratic in t is ≥ 0, so discriminant ≤ 0:
4⟨u,v⟩² − 4||u||²||v||² ≤ 0
⟨u,v⟩² ≤ ||u||²||v||²

Taking square roots: |⟨u,v⟩| ≤ ||u||·||v||. ∎

---

## Proof 5: Sylvester's Law of Inertia ⚡⚡

**Theorem:** The signature (p, q) of a real quadratic form is invariant under change of basis.

**Proof sketch:**
Suppose Q = x₁²+...+xₚ²−xₚ₊₁²−...−xᵣ² in one basis and Q = y₁²+...+yₛ²−yₛ₊₁²−...−yᵣ² in another.

Assume s > p. Let V⁺ = span{y₁,...,yₛ} and V⁻ = span{xₚ₊₁,...,xₙ}.
dim(V⁺) + dim(V⁻) = s + (n−p) > n, so V⁺ ∩ V⁻ ≠ {0}.

Take nonzero v ∈ V⁺ ∩ V⁻. Then Q(v) > 0 (from V⁺) and Q(v) ≤ 0 (from V⁻). Contradiction! So s = p. ∎

---

# EXTENDED EXAMPLES (5+ per critical topic)

## Eigenvalue Problems — Variations

**Ex 1:** A = [[3,1],[0,3]]. Char poly: (3−λ)² = 0. λ = 3 (double). Only one eigenvector (1,0). NOT diagonalizable. Jordan form: J₂(3).

**Ex 2:** A = [[0,−1],[1,0]]. Char poly: λ²+1 = 0. λ = ±i (no real eigenvalues). Over ℝ: not diagonalizable. Over ℂ: diagonalizable!

**Ex 3:** A = [[1,2,0],[0,1,0],[0,0,2]]. Char poly: (1−λ)²(2−λ). λ=1 (double), λ=2. For λ=1: rank(A−I) = 1, nullity = 2. Two independent eigenvectors → diagonalizable!

**Ex 4:** A³ = I (rotation by 120°). Eigenvalues must satisfy λ³ = 1. So λ = 1, e^(2πi/3), e^(4πi/3).

**Ex 5:** If A² = A (idempotent), eigenvalues satisfy λ² = λ, so λ = 0 or 1 only.

**Ex 6 (NET 2023):** A is 4×4 with eigenvalues 1,1,2,2 and rank(A−I) = rank(A−2I) = 2. Is A diagonalizable?
For λ=1: geometric mult = 4−rank(A−I) = 4−2 = 2 = algebraic mult. ✓
For λ=2: geometric mult = 4−rank(A−2I) = 4−2 = 2 = algebraic mult. ✓
YES, diagonalizable!

## Gram-Schmidt — Full Worked Examples

**Ex 1:** Orthogonalize {(1,1,1), (1,2,3), (1,4,9)} in ℝ³:

v₁ = (1,1,1), ||v₁|| = √3, e₁ = (1,1,1)/√3

⟨v₂,e₁⟩ = (1+2+3)/√3 = 6/√3 = 2√3
u₂ = (1,2,3) − 2√3·(1,1,1)/√3 = (1,2,3) − (2,2,2) = (−1,0,1)
||u₂|| = √2, e₂ = (−1,0,1)/√2

⟨v₃,e₁⟩ = (1+4+9)/√3 = 14/√3
⟨v₃,e₂⟩ = (−1+0+9)/√2 = 8/√2
u₃ = (1,4,9) − (14/√3)e₁ − (8/√2)e₂
= (1,4,9) − (14/3)(1,1,1) − 4(−1,0,1)
= (1−14/3+4, 4−14/3, 9−14/3−4) = (1/3, −2/3, 1/3)
e₃ = (1,−2,1)/√6

**Verify:** ⟨e₁,e₂⟩ = (−1+0+1)/√6 = 0 ✓, ⟨e₁,e₃⟩ = (1−2+1)/√18 = 0 ✓

## Jordan Form — Complete Examples

**Ex 1:** A with char poly (λ−2)³, minimal poly (λ−2)².
Possible Jordan forms: J₂(2) ⊕ J₁(2) (this is the ONLY option matching both).

**Ex 2:** A with char poly (λ−1)²(λ−3)², minimal poly (λ−1)(λ−3)².
For λ=1: minimal poly factor is (λ−1)¹, so the largest Jordan block for λ=1 has size 1. With algebraic multiplicity 2, we need two blocks of size 1: J₁(1) ⊕ J₁(1).
For λ=3: minimal poly factor is (λ−3)², so largest block has size 2. With algebraic multiplicity 2, we need exactly one J₂(3).
Jordan form: J₁(1) ⊕ J₁(1) ⊕ J₂(3) — total size 4. ✓

**Ex 3:** Nilpotent 4×4 with rank = 2, rank(A²) = 1, A³ = 0.
Jordan form: J₃(0) ⊕ J₁(0) (verify: rank of J₃(0) = 2 ✓, rank of J₃(0)² = 1 ✓)

---

# 30 ADDITIONAL PRACTICE PROBLEMS WITH SOLUTIONS

**P1.** True/False: If AB = I then BA = I (for square matrices).
**Answer:** TRUE (for square matrices). If A is n×n and AB = I, then A is invertible and B = A⁻¹, so BA = I.

**P2.** If A is 3×3 with eigenvalues 1, 2, 3, find det(A), tr(A), det(A⁻¹).
**Answer:** det(A) = 1·2·3 = 6. tr(A) = 1+2+3 = 6. det(A⁻¹) = 1/6.

**P3.** Rank of [[1,2,3],[4,5,6],[7,8,9]]?
**Answer:** R₂ → R₂−4R₁, R₃ → R₃−7R₁: [[1,2,3],[0,−3,−6],[0,−6,−12]]. R₃ → R₃−2R₂: [[1,2,3],[0,−3,−6],[0,0,0]]. Rank = **2**.

**P4.** A is real skew-symmetric (Aᵀ = −A). Show eigenvalues are pure imaginary or zero.
**Proof:** Let Av = λv with v ≠ 0 (over ℂ). Then v*Av = λ‖v‖². Take conjugate transpose:
  (v*Av)* = v*A*v = v*Aᵀv = v*(−A)v = −v*Av     (using A real and skew-symmetric: A* = Aᵀ = −A).
So v*Av is purely imaginary. Since v*Av = λ‖v‖² and ‖v‖² > 0 is real, λ must be purely imaginary (i.e., λ ∈ iℝ, possibly 0). ∎

**P5.** Dimension of the space of n×n symmetric matrices?
**Answer:** n(n+1)/2. For n=3: 6. For n=4: 10.

**P6.** If A² − 5A + 6I = 0, what are possible eigenvalues?
**Answer:** λ² − 5λ + 6 = 0 → (λ−2)(λ−3) = 0. Eigenvalues ∈ {2, 3}.

**P7.** T: P₂ → P₂ defined by T(p) = p' + p. Find matrix w.r.t. {1, x, x²}.
**Answer:** T(1)=1, T(x)=1+x, T(x²)=2x+x². Matrix: [[1,1,0],[0,1,2],[0,0,1]].

**P8.** Show that the trace is similarity-invariant.
**Proof:** tr(P⁻¹AP) = tr(APP⁻¹) = tr(A) (using tr(XY) = tr(YX)). ∎

**P9.** A is orthogonal, det(A) = −1. Show λ = −1 is an eigenvalue.
**Proof:** Eigenvalues of a real orthogonal matrix have |λ|=1. Complex eigenvalues come in conjugate pairs e^{±iθ}, each pair contributing a positive product e^{iθ}·e^{-iθ} = 1 to the determinant. Real eigenvalues are ±1.

For **odd n**: one real eigenvalue must exist (char poly has odd degree). Since the product of all eigenvalues = det(A) = −1, and each complex conjugate pair contributes +1, the single remaining real eigenvalue must be −1.

For **even n**: the real eigenvalues are some collection of ±1's and complex conjugate pairs. The product of all = −1. An even number of (−1)'s gives +1, so there must be an odd number of (−1) eigenvalues, meaning at least one is −1. ✓

**P10.** Find the quadratic form corresponding to A = [[2,−1],[−1,3]].
**Answer:** Q(x,y) = 2x² + 3y² − 2xy. Eigenvalues: (5±√5)/2, both > 0 → positive definite.

**P11.** A is nilpotent (Aᵏ=0). Show det(I+A) = 1.
**Proof:** Eigenvalues of A are all 0. Eigenvalues of I+A are all 1. det(I+A) = product = 1. ∎

**P12.** If A and B are similar, they have the same minimal polynomial.
**Proof:** B = P⁻¹AP. If m(A) = 0, then m(B) = m(P⁻¹AP) = P⁻¹m(A)P = 0. So minimal poly of B divides that of A. By symmetry (A = PBP⁻¹), minimal poly of A divides that of B. Hence equal. ∎

**P13-P15.** [Left as exercises — attempt before checking textbook]
P13: Find all 2×2 matrices that commute with [[1,1],[0,1]].
P14: Prove that the set of diagonalizable matrices is dense in M_n(ℂ).
P15: If T² = T, show V = ker(T) ⊕ Im(T).
