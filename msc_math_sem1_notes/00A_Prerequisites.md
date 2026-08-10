# 📖 Prerequisites — Class 12 Refresher & Mathematical Foundations

> **Read this chapter FIRST if it's been years since you studied Class 12 Maths.**
> **This covers everything you need before starting MSc Mathematics.**

---

# 1. SETS — The Language of Mathematics

A **set** is a well-defined collection of objects (called **elements**).

**Notation:**
- x ∈ A means "x belongs to set A"
- x ∉ A means "x does NOT belong to A"
- A ⊂ B means "A is a subset of B" (every element of A is in B)
- A ∪ B = union (elements in A OR B)
- A ∩ B = intersection (elements in A AND B)
- A \ B = difference (elements in A but NOT in B)
- ∅ = empty set (no elements)

**Important Number Sets:**
```
ℕ = {1, 2, 3, ...}           Natural numbers
ℤ = {..., -2, -1, 0, 1, 2, ...} Integers
ℚ = {p/q : p,q ∈ ℤ, q ≠ 0}   Rational numbers (fractions)
ℝ = all real numbers           (includes irrationals like √2, π)
ℂ = {a + bi : a,b ∈ ℝ}        Complex numbers (i² = -1)
```

**Relationship:** ℕ ⊂ ℤ ⊂ ℚ ⊂ ℝ ⊂ ℂ

---

# 2. FUNCTIONS

A **function** f: A → B assigns exactly one element f(x) ∈ B to each x ∈ A.

- **Domain** = set A (inputs)
- **Codomain** = set B (possible outputs)  
- **Range** = {f(x) : x ∈ A} (actual outputs) ⊆ B

**Types:**
- **Injective (one-to-one):** f(x₁) = f(x₂) ⟹ x₁ = x₂ (different inputs → different outputs)
- **Surjective (onto):** every b ∈ B has some a with f(a) = b
- **Bijective:** both injective AND surjective (perfect pairing)

**Example:** f(x) = x² on ℝ → ℝ is NOT injective (f(2) = f(-2) = 4) and NOT surjective (no x gives f(x) = -1).

---

# 3. MATRICES & DETERMINANTS

A **matrix** is a rectangular array of numbers. An n×n matrix is "square."

```
A = | a  b |      2×2 matrix
    | c  d |
```

**Operations:**
- **Addition:** add corresponding entries
- **Scalar multiplication:** multiply every entry by a number
- **Matrix multiplication:** (AB)ᵢⱼ = Σₖ aᵢₖbₖⱼ (row × column)

**Determinant** (2×2): det(A) = ad - bc

**Determinant** (3×3): expand along first row:
det = a₁₁(a₂₂a₃₃ - a₂₃a₃₂) - a₁₂(a₂₁a₃₃ - a₂₃a₃₁) + a₁₃(a₂₁a₃₂ - a₂₂a₃₁)

**Key facts:**
- det(A) ≠ 0 ⟺ A is invertible
- A⁻¹ exists only when det(A) ≠ 0
- (AB)⁻¹ = B⁻¹A⁻¹ (reverse order!)

**Identity matrix:** I = diag(1,1,...,1). AI = IA = A.

---

# 4. VECTORS

A **vector** in ℝⁿ is an ordered list of n real numbers: v = (v₁, v₂, ..., vₙ).

**Dot product:** u · v = u₁v₁ + u₂v₂ + ... + uₙvₙ (gives a NUMBER)

**Length (norm):** ||v|| = √(v · v) = √(v₁² + v₂² + ... + vₙ²)

**Orthogonal:** u ⊥ v means u · v = 0 (perpendicular)

**Linear combination:** c₁v₁ + c₂v₂ + ... + cₖvₖ (scalars × vectors, added up)

**Linearly independent:** no vector can be written as a combination of the others.

**Basis:** a set of linearly independent vectors that span the whole space.

ℝⁿ has dimension n. Standard basis for ℝ³: e₁ = (1,0,0), e₂ = (0,1,0), e₃ = (0,0,1).

---

# 5. CALCULUS ESSENTIALS

## Limits

lim(x→a) f(x) = L means f(x) gets arbitrarily close to L as x approaches a.

**Key limits to remember:**
- lim(x→0) sin(x)/x = 1
- lim(x→∞) (1 + 1/x)ˣ = e ≈ 2.718
- lim(x→0) (eˣ - 1)/x = 1

## Derivatives

f'(x) = lim(h→0) [f(x+h) - f(x)] / h

**Must-know derivatives:**
```
d/dx [xⁿ] = nxⁿ⁻¹           d/dx [eˣ] = eˣ
d/dx [sin x] = cos x         d/dx [cos x] = -sin x
d/dx [ln x] = 1/x            d/dx [tan x] = sec²x
```

**Chain rule:** d/dx [f(g(x))] = f'(g(x)) · g'(x)

**Product rule:** (fg)' = f'g + fg'

## Integration

∫ is the "reverse" of differentiation.

**Must-know integrals:**
```
∫ xⁿ dx = xⁿ⁺¹/(n+1) + C    (n ≠ -1)
∫ 1/x dx = ln|x| + C
∫ eˣ dx = eˣ + C
∫ sin x dx = -cos x + C
∫ cos x dx = sin x + C
```

**Fundamental Theorem:** ∫ₐᵇ f(x)dx = F(b) - F(a) where F' = f.

**Integration by parts:** ∫ u dv = uv - ∫ v du

---

# 6. SEQUENCES AND SERIES

**Sequence:** ordered list a₁, a₂, a₃, ... (one number for each n ∈ ℕ)

**Converges:** aₙ → L means aₙ gets arbitrarily close to L as n → ∞

**Series:** Σₙ₌₁^∞ aₙ = a₁ + a₂ + a₃ + ... (infinite sum)

**Converges** if the partial sums Sₙ = a₁ + ... + aₙ approach a finite limit.

**Key tests:**
- **Geometric:** Σ rⁿ converges iff |r| < 1, sum = 1/(1-r)
- **p-series:** Σ 1/nᵖ converges iff p > 1
- **Comparison:** if 0 ≤ aₙ ≤ bₙ and Σbₙ converges, then Σaₙ converges
- **Ratio test:** if lim |aₙ₊₁/aₙ| < 1, converges; > 1, diverges

---

# 7. COMPLEX NUMBERS

**i = √(-1)**, so i² = -1.

A complex number: z = a + bi where a = Re(z), b = Im(z).

**Conjugate:** z̄ = a - bi

**Modulus:** |z| = √(a² + b²)

**Polar form:** z = r(cosθ + i sinθ) = re^(iθ) where r = |z|, θ = arg(z)

**Euler's formula:** e^(iθ) = cosθ + i sinθ

**De Moivre:** (cosθ + i sinθ)ⁿ = cos(nθ) + i sin(nθ)

**Key:** Every polynomial of degree n has exactly n roots in ℂ (counting multiplicity).

---

# 8. PROOF TECHNIQUES

In MSc Maths, you'll write proofs constantly. Here are the main methods:

## Direct Proof
Assume P, derive Q step by step.
*Example:* "If n is even, then n² is even." Let n = 2k. Then n² = 4k² = 2(2k²), which is even. ∎

## Proof by Contradiction
Assume the statement is FALSE, derive a contradiction.
*Example:* "√2 is irrational." Assume √2 = p/q (fully reduced). Then 2q² = p², so p is even. Write p = 2k: 2q² = 4k², q² = 2k², so q is even. But p,q both even contradicts "fully reduced." ∎

## Proof by Induction
1. **Base case:** Prove for n = 1.
2. **Inductive step:** Assume true for n = k, prove for n = k+1.
*Example:* 1 + 2 + ... + n = n(n+1)/2. Base: n=1: 1 = 1·2/2 ✓. Step: Assume for k. Then 1+...+k+(k+1) = k(k+1)/2 + (k+1) = (k+1)(k+2)/2 ✓. ∎

## Proof by Contrapositive
Instead of "P ⟹ Q", prove "not Q ⟹ not P" (logically equivalent).
*Example:* "If n² is even, then n is even." Contrapositive: "If n is odd, then n² is odd." Let n = 2k+1. n² = 4k²+4k+1 = 2(2k²+2k)+1, which is odd. ✓ ∎

---

# 9. MATHEMATICAL NOTATION GLOSSARY

| Symbol | Meaning | Example |
|--------|---------|---------|
| ∀ | "for all" | ∀x ∈ ℝ means "for every real x" |
| ∃ | "there exists" | ∃x such that x² = 2 |
| ⟹ | "implies" | P ⟹ Q means "if P then Q" |
| ⟺ | "if and only if" | P ⟺ Q means P and Q are equivalent |
| ∎ or □ | "end of proof" | Written at end of every proof |
| := | "defined as" | f(x) := x² means "f is defined as x²" |
| Σ | summation | Σᵢ₌₁ⁿ i = 1+2+...+n |
| Π | product | Πᵢ₌₁ⁿ i = 1·2·...·n = n! |
| ∘ | composition | (f∘g)(x) = f(g(x)) |
| ≈ | approximately | π ≈ 3.14159 |
| dim | dimension | dim(ℝ³) = 3 |
| ker | kernel (null space) | ker(T) = {v : T(v) = 0} |
| Im | image (range) | Im(T) = {T(v) : v ∈ V} |
| sup | supremum (least upper bound) | sup{1/n : n ∈ ℕ} = 1 |
| inf | infimum (greatest lower bound) | inf{1/n : n ∈ ℕ} = 0 |

---

# 10. HOW TO STUDY THIS BOOKLET

1. **Read this prerequisites chapter first** — make sure you're comfortable with every concept
2. **For each unit:** Read the explanation → Study the example → Try to reproduce the proof without looking
3. **Don't skip proofs** — university exams will ask "State and Prove"
4. **Use pen and paper** — mathematics is NOT a spectator sport. Write as you read.
5. **If stuck on a concept:** Re-read the prerequisites section for that topic, then return.

> **Remember:** Every mathematician was once where you are. The difference between a student and a professor is simply years of consistent practice. You've got this! 💪
