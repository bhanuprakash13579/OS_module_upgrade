# 🔷 Topology — Deep Proofs & Counterexamples

> **Supplement to 03_Topology.md — Counterexamples are GOLD for CSIR NET MCQs**

---

# CRITICAL PROOFS

## Proof 1: Heine-Borel Theorem ⚡⚡⚡

**Theorem:** A subset of ℝⁿ is compact iff it is closed and bounded.

**Proof (⟸ direction for ℝ, exam version):**
Let K ⊆ [a,b] (closed and bounded). Let {Uα} be an open cover.

Let S = {x ∈ [a,b] : [a,x] can be covered by finitely many Uα}.
S is nonempty (a ∈ S) and bounded above by b. Let c = sup S.

**Claim: c ∈ S.** Since c ∈ some Uα₀ (which is open), ∃δ: (c−δ,c+δ) ⊆ Uα₀. Since c = sup S, ∃x ∈ S with x > c−δ. So [a,x] has a finite subcover. Since x ∈ (c−δ, c] ⊆ Uα₀, the segment [x,c] ⊆ Uα₀. Adding Uα₀ to the finite cover of [a,x] gives a finite cover of [a,c]. So c ∈ S. ✓

**Claim: c = b.** If c < b, then [a,c+ε] can also be finitely covered (extend using Uα₀). This contradicts c = sup S. So c = b ∈ S. ✓

Therefore [a,b] is compact. Since K is closed subset of compact [a,b], K is compact. ∎

---

## Proof 2: Continuous Image of Compact is Compact ⚡⚡⚡

**Proof:**
Let f: X → Y be continuous, X compact. Let {Vα} be open cover of f(X).
Then {f⁻¹(Vα)} is open cover of X (by continuity). By compactness of X, ∃ finite subcover f⁻¹(Vα₁),...,f⁻¹(Vαₙ). Then Vα₁,...,Vαₙ covers f(X). ∎

---

## Proof 3: Continuous Image of Connected is Connected ⚡⚡⚡

**Proof (by contradiction):**
Let f: X → Y be continuous, X connected. Suppose f(X) = A ∪ B with A,B open in f(X), disjoint, nonempty.
Then X = f⁻¹(A) ∪ f⁻¹(B). These are open (continuity), disjoint, nonempty. This contradicts X connected. ∎

---

## Proof 4: Compact + Hausdorff ⟹ Normal ⚡⚡

**Proof sketch:**
Step 1: In Hausdorff space, compact sets are closed.
Step 2: Given disjoint closed sets A, B in compact Hausdorff X — both A, B are compact.
Step 3: For each a ∈ A, b ∈ B: separate by open sets (Hausdorff). Use compactness of B to get finite subcover → separate a from all of B.
Step 4: Use compactness of A to get finite subcover → separate all of A from all of B. ∎

---

## Proof 5: Connected Subsets of ℝ are Intervals ⚡⚡

**Proof:**
Let S ⊆ ℝ be connected. Suppose a, b ∈ S with a < c < b but c ∉ S.
Then S = (S ∩ (−∞,c)) ∪ (S ∩ (c,∞)) — two nonempty disjoint open (in S) sets. Contradicts connectedness. ∎

---

# COUNTEREXAMPLES BANK (CSIR NET GOLD MINE)

## The Big List

| Statement | True/False | Counterexample |
|-----------|-----------|----------------|
| Connected ⟹ Path connected | **FALSE** | Topologist's sine curve: {(x,sin(1/x)):x>0} ∪ {0}×[−1,1] |
| Compact ⟹ Closed | **FALSE** (in general) | {a} as a subset of ({a,b}, indiscrete) — compact (finite) but not closed (only ∅ and {a,b} are closed) |
| Compact ⟹ Closed | **TRUE in Hausdorff** | — |
| Closed + Bounded ⟹ Compact | **FALSE** (general metric) | ℚ ∩ [0,1] is closed and bounded in (ℚ, usual metric), but not compact (a sequence converging to an irrational has no subsequence converging in ℚ) |
| Closed + Bounded ⟹ Compact | **TRUE in ℝⁿ** | Heine-Borel |
| Product of compact = compact | **TRUE** | Tychonoff's theorem |
| Continuous bijection = homeomorphism | **FALSE** | f: [0,2π) → S¹ by f(t)=e^(it). Continuous bijection but f⁻¹ not continuous |
| Continuous bijection = homeomorphism | **TRUE** | If domain is compact, codomain Hausdorff |
| Hausdorff ⟹ Normal | **FALSE** | ℝ with the K-topology (basis: open intervals + $(a,b) \setminus K$, $K=\{1/n:n\in\mathbb{N}\}$) — Hausdorff but not regular, hence not normal. (Note: Sorgenfrey IS normal; Sorgenfrey *plane* is regular but not normal.) |
| Metric ⟹ Normal | **TRUE** | Every metric space is normal |
| Separable ⟹ Second countable | **FALSE** (general) | Sorgenfrey line |
| Separable ⟺ Second countable | **TRUE in metric spaces** | — |
| ℚ is connected | **FALSE** | Split at √2 |
| ℝ \ ℚ is connected | **FALSE** | Irrationals are totally disconnected: any rational r splits them into ℝ\ℚ ∩ (−∞,r) and ℝ\ℚ ∩ (r,∞), both open in the subspace topology |
| Subspace of Hausdorff is Hausdorff | **TRUE** | Subspace inherits separation |
| Subspace of compact is compact | **FALSE** | (0,1) ⊂ [0,1] — not compact |
| Closed subspace of compact = compact | **TRUE** | — |
| Finite × compact = compact | **TRUE** | — |

## 5 KEY Spaces to Know Cold

**1. Cofinite Topology on ℝ:** T₁, NOT T₂, connected, compact, every infinite set is dense.

**2. Discrete Topology on ℕ:** T₄, NOT compact (cover by singletons), NOT connected, second countable, separable.

**3. Sorgenfrey Line (Lower limit topology):** T₄, separable, NOT second countable, NOT connected ([0,∞) is clopen), Lindelöf but NOT compact.

**4. Topologist's Sine Curve:** Connected, NOT path connected, NOT locally connected.

**5. Long Line:** Connected, locally compact, NOT compact, NOT metrizable.

---

# 20 PRACTICE PROBLEMS

**P1.** Is [0,1] ∩ ℚ compact in ℝ? 
**Answer:** NO. Not closed in ℝ (limit point √2/2 ∉ set). Heine-Borel fails.

**P2.** Is {(x,y) : x²+y² ≤ 1} \ {(0,0)} compact?
**Answer:** NO. Closed? No — (0,0) is a limit point not in the set. Not closed → not compact.

**P3.** Is ℝ² \ {line} connected?
**Answer:** NO. ℝ² minus a line has two components.

**P4.** Is ℝ² \ {point} connected?
**Answer:** YES. Can connect any two points by a path avoiding one point.

**P5.** Is ℝ³ \ {line} connected?
**Answer:** YES. Can go "around" a line in 3D.

**P6.** In the cofinite topology on ℤ, is {even integers} open?
**Answer:** NO. Its complement (odd integers) is infinite, not finite. So not cofinite, so not open.

**P7.** True/False: Intersection of two compact sets is compact (in Hausdorff space).
**Answer:** TRUE. Compact sets are closed in Hausdorff. Intersection of closed sets is closed. Closed subset of compact is compact.

**P8.** Is the product topology on ℝ^ω (countable product) metrizable?
**Answer:** YES — use the metric d(x,y) = Σ min(|xₙ−yₙ|,1)/2ⁿ.

**P9.** Every second countable space is separable. Prove.
**Proof:** Let {Bₙ} be countable basis. Pick xₙ ∈ Bₙ for each n. Then {xₙ} is dense: for any open U ≠ ∅, U contains some Bₙ, which contains xₙ. ∎

**P10.** Is GL(n,ℝ) (invertible matrices) connected?
**Answer:** NO. GL(n,ℝ) = {det>0} ∪ {det<0}. Two components. But GL⁺(n,ℝ) = {det>0} IS connected.
