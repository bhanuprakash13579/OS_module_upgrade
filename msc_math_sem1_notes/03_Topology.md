# 🔷 Topology-1 — Complete Study Notes

> **CSIR NET Priority: ⭐⭐⭐⭐ | Topology questions appear regularly in Part B and C**

---

## 🗺️ Subject Mind Map

```
                         TOPOLOGY
                           │
         ┌─────────┬───────┴────────┬──────────┐
         │         │                │          │
    Foundations  Structure       Properties   Axioms
         │         │                │          │
    ┌────┴────┐  ┌─┴──┐        ┌───┴───┐   ┌──┴──┐
    Open/Closed  Basis         Connected  T0,T1,T2
    Boundary   Subbasis       Compact    Regular
    Interior   Nbhd bases     Path-conn  Normal
```

---

# UNIT 1: Basic Concepts

> 📋 **Quick Refresher Before Starting:**
>
> **Open interval** (a,b) = {x ∈ ℝ : a < x < b}. Does NOT include endpoints.
> **Closed interval** [a,b] = {x ∈ ℝ : a ≤ x ≤ b}. INCLUDES endpoints.
>
> **Why (0,1) is "open":** Every point has wiggle room. Pick any x ∈ (0,1), say x = 0.3. Then (0.2, 0.4) ⊂ (0,1) is a small interval around x entirely inside (0,1). ✓
> **Why [0,1] is NOT open:** The point 0 has no wiggle room to the left — any interval around 0 escapes [0,1].
>
> **Topology** abstracts this: we declare which sets are "open" (have wiggle room) via axioms, WITHOUT needing distances or coordinates.



## What is Topology?

**In plain English:** Topology studies properties of spaces that don't change when you stretch, bend, or deform them (but NOT tear or glue). It's "rubber sheet geometry."

A coffee mug and a donut are "the same" topologically — each has exactly one hole!

## Definition of a Topological Space

A **topology** τ on a set X is a collection of subsets of X satisfying:

1. **∅ ∈ τ and X ∈ τ** (empty set and whole space are open)
2. **Finite intersections:** If U₁,...,Uₙ ∈ τ, then U₁ ∩ ... ∩ Uₙ ∈ τ
3. **Arbitrary unions:** If {Uα} ⊆ τ, then ∪α Uα ∈ τ

The pair (X, τ) is called a **topological space**. Members of τ are called **open sets**.

### 💡 Memory Aid: "FInite Intersections, Arbitrary Unions" → Think "FIAU"

### Example 1: The Real Line ℝ
Standard topology: τ = all sets that are unions of open intervals (a,b).
This is what you're used to from calculus!

### Example 2: Discrete Topology
τ = P(X) (power set — ALL subsets are open). This is the "finest" topology.

### Example 3: Indiscrete (Trivial) Topology
τ = {∅, X} (only the empty set and X are open). This is the "coarsest" topology.

### Example 4: Cofinite Topology
On X, τ = {∅} ∪ {U ⊆ X : X \ U is finite}. Open sets are those whose complement is finite.

**Verify:** ∅ ∈ τ ✓, X ∈ τ (X \ X = ∅ is finite) ✓
Finite intersection of cofinite sets is cofinite ✓ (complement of intersection is union of finite sets = finite)
Arbitrary union of cofinite sets is cofinite ✓ (complement of union is intersection, subset of a finite set) ✓

---

# UNIT 2: Open and Closed Sets

> 📋 **Quick Refresher Before Starting:**
>
> **Set operations you need:**
> - A ∪ B (union) = elements in A OR B
> - A ∩ B (intersection) = elements in A AND B
> - Aᶜ (complement) = everything NOT in A
> - **De Morgan:** (A ∪ B)ᶜ = Aᶜ ∩ Bᶜ and (A ∩ B)ᶜ = Aᶜ ∪ Bᶜ
>
> **Key rule in topology:** A set is CLOSED if its complement is open.
> So [0,1] is closed in ℝ because ℝ\[0,1] = (-∞,0) ∪ (1,∞) is open (union of open intervals).


## Closed Sets
A set F ⊆ X is **closed** if X \ F is open (i.e., X \ F ∈ τ).

> **⚠️ COMMON MISCONCEPTION:** "Open" and "closed" are NOT opposites! A set can be:
> - Both open and closed (called **clopen**): ∅ and X always are
> - Neither open nor closed: [0,1) in ℝ with standard topology
> - Open but not closed: (0,1)
> - Closed but not open: [0,1]

## Interior, Closure, Limit Points

### Interior
**Int(A) = A°** = largest open set contained in A = ∪{U ∈ τ : U ⊆ A}

### Closure
**Cl(A) = Ā** = smallest closed set containing A = ∩{F : F is closed, A ⊆ F}

### Limit Point (Accumulation Point)
x is a **limit point** of A if every open set containing x intersects A in a point other than x itself.

**A' = set of all limit points of A** (derived set)

### Key Formula: **Ā = A ∪ A'**

### Example
In ℝ (standard topology), A = (0,1) ∪ {2}:
- Int(A) = (0,1) — the isolated point 2 has no open set around it inside A
- A' = [0,1] — every point of [0,1] is a limit point (including 0 and 1, which are not in (0,1)); the isolated point 2 is NOT a limit point
- Ā = [0,1] ∪ {2}

## Dense Sets
A is **dense** in X if Ā = X. Example: ℚ is dense in ℝ.

### 🎯 CSIR NET Frequent Question
**Q:** In the cofinite topology on ℝ, what is the closure of any infinite set A?
**A:** Ā = ℝ. The closed sets in cofinite topology are exactly ∅, ℝ, and the finite subsets. An infinite set A is not contained in any finite set, so the only closed set containing A is ℝ. Hence Ā = ℝ.

---

# UNIT 3: Boundary of a Set

> 📋 **Quick Refresher Before Starting:**
>
> **Boundary intuition:** A boundary point is "on the edge" — every neighborhood contains points both INSIDE and OUTSIDE the set.
> Example: For (0,1) in ℝ, the boundary is {0, 1}. Around 0, any interval (-ε, ε) contains points both in (0,1) (like ε/2) and outside (like -ε/2).
> Example: For ℚ (rationals) in ℝ, EVERY real number is a boundary point! Because every interval contains both rationals and irrationals.


## Definition
**Bd(A) = ∂A = Cl(A) ∩ Cl(X\A) = Ā \ Int(A)**

**In English:** The boundary consists of points that are "on the edge" — every neighborhood intersects both A and its complement.

### Example
In ℝ: A = (0,1]
- Ā = [0,1], Int(A) = (0,1)
- ∂A = [0,1] \ (0,1) = {0, 1}

### Key Relationships
```
X = Int(A) ∪ Bd(A) ∪ Int(X\A)   (disjoint union!)

Equivalently:
- x ∈ Int(A) ⟺ some neighborhood of x lies entirely in A
- x ∈ Int(X\A) ⟺ some neighborhood of x lies entirely outside A  
- x ∈ Bd(A) ⟺ every neighborhood of x meets both A and X\A
```

### Properties
1. ∂A is always closed
2. A is open ⟺ A ∩ ∂A = ∅ (A doesn't contain any of its boundary)
3. A is closed ⟺ ∂A ⊆ A (A contains all its boundary)
4. ∂A = ∂(X\A)

---

# UNIT 4: Constructing Topologies

> 📋 **Quick Refresher Before Starting:**
>
> **Basis for a topology** works like a basis for a vector space — a smaller collection that generates all open sets.
> Example: Open intervals (a,b) form a basis for the usual topology on ℝ. Every open set is a union of open intervals.
>
> **Product topology on X × Y:** Open sets are unions of "boxes" U × V where U is open in X and V is open in Y.
> Think of it as: the plane ℝ² gets its topology from open rectangles (a,b) × (c,d).


## Basis for a Topology 🎯

A **basis** B for a topology on X is a collection of subsets such that:
1. For each x ∈ X, ∃B ∈ B with x ∈ B
2. If x ∈ B₁ ∩ B₂ (with B₁, B₂ ∈ B), ∃B₃ ∈ B with x ∈ B₃ ⊆ B₁ ∩ B₂

The topology **generated** by B: U is open iff for every x ∈ U, ∃B ∈ B with x ∈ B ⊆ U.

### Examples of Bases
| Space | Basis |
|-------|-------|
| ℝ (standard) | {(a,b) : a < b} — open intervals |
| ℝ² (standard) | {open disks} or {open rectangles} |
| ℝ (lower limit) | {[a,b) : a < b} — half-open intervals |

## Subbasis
A **subbasis** S is any collection of subsets whose union is X. The topology generated by S has as basis all finite intersections of members of S.

## Product Topology 🎯
On X × Y, the **product topology** has basis: {U × V : U open in X, V open in Y}

### Example
ℝ² = ℝ × ℝ with product of standard topologies gives the standard topology on ℝ².
Basis: open rectangles (a,b) × (c,d).

## Subspace Topology
If (X,τ) is a topological space and Y ⊆ X, the **subspace topology** on Y is:
τ_Y = {U ∩ Y : U ∈ τ}

### Example
[0,1] with subspace topology from ℝ. The set [0, 1/2) is open in [0,1] because [0,1/2) = (-1, 1/2) ∩ [0,1].

---

# UNIT 5: Topological Maps, Neighbourhood Bases, Connectedness

> 📋 **Quick Refresher Before Starting:**
>
> **Continuous function** (Class 12): No jumps, no breaks. f is continuous at a if lim(x→a) f(x) = f(a).
> **Topological definition:** f: X → Y is continuous if the preimage of every open set is open.
> f⁻¹(V) = {x ∈ X : f(x) ∈ V}. This must be open in X whenever V is open in Y.
>
> **Homeomorphism:** A continuous bijection whose inverse is also continuous. If X ≅ Y (homeomorphic), they are "topologically the same."
> Example: (0,1) ≅ ℝ via f(x) = tan(π(x - 1/2)). They look different but are topologically identical!


## Continuous Functions (Topological Definition) 🎯

f: X → Y is **continuous** iff for every open set V in Y, f⁻¹(V) is open in X.

**This generalizes the ε-δ definition from calculus!**

## Homeomorphism
f: X → Y is a **homeomorphism** if f is bijective, continuous, and f⁻¹ is continuous.

Homeomorphic spaces are "topologically identical." We write X ≅ Y.

### Example
f: (0,1) → ℝ given by f(x) = tan(π(x − 1/2)) is a homeomorphism.
So (0,1) ≅ ℝ — the open unit interval and the entire real line are topologically the same!

## Neighbourhood Bases
A **neighbourhood base** at x is a collection Bₓ of neighborhoods of x such that every neighborhood of x contains some member of Bₓ.

### First Countable Space
X is **first countable** if every point has a countable neighbourhood base.

All metric spaces are first countable (use balls B(x, 1/n)).

---

# UNIT 6: Connected Spaces 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Connected** = "one piece." A space X is connected if you CANNOT write X = A ∪ B where A,B are both open, both nonempty, and disjoint.
> **Example:** ℝ is connected. (0,1) ∪ (2,3) is NOT connected (two separate pieces).
> **Example:** ℚ is NOT connected! For any irrational r, ℚ = (-∞,r)∩ℚ ∪ (r,∞)∩ℚ splits it.
>
> **Path connected:** Any two points can be joined by a continuous curve. Path connected ⟹ connected (but not always vice versa).


## Definition of Connectedness

X is **connected** if it cannot be written as X = U ∪ V where U, V are non-empty, disjoint, open sets.

Equivalently: X is connected iff the only clopen subsets are ∅ and X.

### 💡 Memory Aid: A connected space is "one piece" — you can't split it into two open chunks.

### Examples
- ℝ is connected ✓
- ℚ is NOT connected (e.g., split at √2: U = ℚ ∩ (−∞,√2), V = ℚ ∩ (√2,∞). Both are open in the subspace topology of ℚ, they are disjoint, and U ∪ V = ℚ because √2 ∉ ℚ.)
- [0,1] is connected ✓
- {0} ∪ {1} is NOT connected (discrete)

## Key Theorems 🎯

### Intermediate Value Theorem (Topological Version)
If f: X → Y is continuous and X is connected, then f(X) is connected.

**Corollary (IVT from calculus):** If f: [a,b] → ℝ is continuous with f(a) < 0 < f(b), then ∃c with f(c) = 0.

### Connected Subsets of ℝ
A subset of ℝ is connected iff it is an interval (possibly infinite, open, closed, or half-open).

### Properties
1. Continuous image of connected space is connected
2. If A is connected and A ⊆ B ⊆ Ā, then B is connected
3. Union of connected sets with common point is connected
4. Product of connected spaces is connected

## Path Connectedness
X is **path connected** if for any x,y ∈ X, there exists a continuous f: [0,1] → X with f(0) = x, f(1) = y.

**Path connected ⟹ Connected** (but NOT the converse!)

### 🎯 CSIR NET: Topologist's Sine Curve
The set A = {(x, sin(1/x)) : x > 0} ∪ {(0,y) : −1 ≤ y ≤ 1} is connected but NOT path connected.

---

# UNIT 7: Compactness 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Open cover:** A collection of open sets whose union contains X. Example: {(-n,n) : n = 1,2,...} covers ℝ.
> **Finite subcover:** Choosing finitely many sets from the cover that still cover X.
>
> **Compact:** Every open cover has a finite subcover. Intuitively: compact sets behave like finite sets.
> **In ℝⁿ (Heine-Borel):** Compact ⟺ closed AND bounded.
> Example: [0,1] is compact ✓ (closed + bounded). (0,1) is NOT compact ✗ (not closed). ℝ is NOT compact ✗ (not bounded).


## Open Cover Definition

An **open cover** of X is a collection {Uα} of open sets with X = ∪α Uα.

X is **compact** if every open cover has a **finite subcover**.

### 💡 Memory Aid: "You can always find a finite team to do the whole job."

### Example: [0,1] is compact
Take any open cover. By the Heine-Borel theorem (proven using completeness), we can extract a finite subcover.

### Example: (0,1) is NOT compact
Cover: {(1/n, 1) : n ≥ 2}. This covers (0,1) but no finite subcollection does (always misses points near 0).

## Heine-Borel Theorem 🎯 (CRITICAL for CSIR NET)

A subset of ℝⁿ is compact **if and only if** it is **closed and bounded**.

### Quick Classification
| Set | Compact? | Why? |
|-----|----------|------|
| [0,1] | Yes | Closed + bounded |
| (0,1) | No | Not closed |
| [0,∞) | No | Not bounded |
| {1/n : n ∈ ℕ} | No | Not closed (0 is a limit point not in the set) |
| {0} ∪ {1/n : n ∈ ℕ} | Yes | Closed + bounded |
| Sⁿ (n-sphere) | Yes | Closed + bounded in ℝⁿ⁺¹ |

---

# UNIT 8: Compact Spaces — Properties 🎯

> 📋 **Quick Refresher Before Starting:**
>
> **Why compactness matters** — it guarantees things that can fail in non-compact spaces:
> - Continuous functions on compact sets are bounded and attain their max/min (Extreme Value Theorem)
> - Continuous functions on compact sets are uniformly continuous
> - In Hausdorff spaces: compact sets are closed
> - A continuous bijection from compact to Hausdorff is automatically a homeomorphism!


## Key Theorems

1. **Closed subset of compact space is compact**
2. **Compact subset of Hausdorff space is closed**
3. **Continuous image of compact space is compact**
4. **Continuous bijection from compact to Hausdorff is homeomorphism**
5. **Extreme Value Theorem:** Continuous real-valued function on compact space attains max and min

### 🎯 CSIR NET Application
**Q:** f: [0,1] → ℝ is continuous. Must f be bounded?
**A:** Yes! [0,1] is compact, so f([0,1]) is compact in ℝ, hence closed and bounded.

## Tychonoff's Theorem
Product of compact spaces is compact (in the product topology). This is one of the most powerful theorems in topology.

## Sequential Compactness
In metric spaces: X is compact ⟺ every sequence has a convergent subsequence.

## Bolzano-Weierstrass Property
Every infinite subset of a compact space has a limit point.

---

# UNIT 9: Separation Axioms

> 📋 **Quick Refresher Before Starting:**
>
> **Separation axioms** describe how well a topology can "separate" points and sets:
> - **T₁:** For any two distinct points, each has a neighborhood not containing the other.
> - **T₂ (Hausdorff):** Any two distinct points have DISJOINT neighborhoods. Most "nice" spaces are Hausdorff.
> - **T₃ (Regular):** Points and closed sets can be separated by open sets.
> - **T₄ (Normal):** Any two disjoint closed sets can be separated by open sets.
>
> **Hierarchy:** T₄ ⟹ T₃ ⟹ T₂ ⟹ T₁. Every metric space is T₄.
>
> **Note (Munkres' convention):** T₃ and T₄ as defined here INCLUDE T₁. Without T₁, regular/normal does NOT imply Hausdorff.


## The Hierarchy 🎯

```
T0 ──▶ T1 ──▶ T2 (Hausdorff) ──▶ T3 (Regular) ──▶ T4 (Normal)
                                    (each implies the previous)
```

| Axiom | Name | Condition |
|-------|------|-----------|
| T₀ | Kolmogorov | For any two distinct points, at least one has an open set not containing the other |
| T₁ | Fréchet | For any two distinct points, each has an open set not containing the other |
| T₂ | Hausdorff | Any two distinct points have disjoint open neighborhoods |
| T₃ | Regular | T₁ + point and closed set can be separated by open sets |
| T₃½ | Tychonoff | T₁ + point and closed set can be separated by continuous function |
| T₄ | Normal | T₁ + two disjoint closed sets can be separated by open sets |

### 💡 Memory Aid
**T₂ (Hausdorff):** "Two points can be *housed* apart" — put each in its own open house (neighborhood).

### Examples
| Space | Highest Separation Axiom |
|-------|-------------------------|
| ℝ (standard) | T₄ (Normal) — all metric spaces are normal |
| ℝ (cofinite) | T₁ but NOT T₂ |
| ℝ (indiscrete) | None — fails even T₀ (only nonempty open set is ℝ itself, which contains both points) |
| Any metric space | T₄ |

### 🎯 Urysohn's Lemma
If X is normal and A, B are disjoint closed sets, then there exists a continuous function f: X → [0,1] with f(A) = {0} and f(B) = {1}.

---

# UNIT 10: Separable and Second Countable Spaces

> 📋 **Quick Refresher Before Starting:**
>
> **Countable set:** Can be listed as a sequence: a₁, a₂, a₃, ... Examples: ℕ, ℤ, ℚ are countable. ℝ is UNcountable.
> **Dense set:** A ⊂ X is dense if every open set contains a point of A. Example: ℚ is dense in ℝ (every interval contains a rational).
> **Separable:** X has a countable dense subset. ℝ is separable (ℚ is countable and dense).
> **Second countable:** X has a countable basis. Example: ℝ has basis {(a,b) : a,b ∈ ℚ} which is countable.


## Separable Spaces
X is **separable** if it has a countable dense subset.

### Examples
- ℝ is separable (ℚ is countable and dense)
- ℓ² (separable Hilbert space) is separable
- ℓ^∞ with sup norm is NOT separable

## Second Countable Spaces
X is **second countable** if it has a countable basis for its topology.

### Examples
- ℝ is second countable (basis: intervals with rational endpoints)
- ℝⁿ is second countable
- Any uncountable set with discrete topology is NOT second countable

### Key Relationships 🎯
```
Second Countable ──▶ First Countable
       │                    
       ▼                    
   Separable               
       │                    
       ▼                    
   Lindelöf
```

**In metric spaces:** Separable ⟺ Second Countable ⟺ Lindelöf

### Lindelöf's Theorem
Every second countable space is Lindelöf (every open cover has a countable subcover).

---

# 📝 CSIR NET Practice Problems — Topology

**Q1.** In the cofinite topology on an infinite set X, is X compact?
**Answer:** YES. Any open cover {Uα} — pick one Uα₀. Its complement X\Uα₀ is finite = {x₁,...,xₙ}. For each xᵢ, pick Uαᵢ containing xᵢ. Then {Uα₀, Uα₁,...,Uαₙ} is a finite subcover.

**Q2.** Is ℝ with the lower limit topology (basis = {[a,b)}) connected?
**Answer:** NO. [0,∞) is both open (union of [0,n)) and closed (complement = ∪ₙ[−n,0) is open). So ℝ splits as [0,∞) ∪ (−∞,0).

**Q3.** Product of [0,1] with itself uncountably many times — is it compact?
**Answer:** YES — by Tychonoff's theorem!

**Q4.** Give an example of a space that is T₁ but not T₂.
**Answer:** ℝ with cofinite topology. Singletons are closed (T₁), but you can't separate two points by disjoint open sets (any two non-empty open sets intersect, since their complements are finite).

---

> **📖 Recommended Reading:** Munkres "Topology", Simmons "Introduction to Topology and Modern Analysis"
> **Next Subject:** [Advanced Complex Analysis →](./04_Advanced_Complex_Analysis.md)
