# 🔄 Dynamics of a Rigid Body — Deep Proofs & Solved Problems

> **Supplement to 06_Dynamics_of_Rigid_Body.md**

---

# CRITICAL PROOFS

## Proof 1: Parallel Axis Theorem ⚡⚡⚡

**Theorem:** I = I_cm + Md² where d = distance between parallel axes.

**Proof:**
Let axis through CM be the origin. Parallel axis at distance d.
I = Σ mᵢ(rᵢ + d)² = Σ mᵢrᵢ² + 2d·Σ mᵢrᵢ + d²·Σ mᵢ

- First term = I_cm
- Second term: Σ mᵢrᵢ = M·r̄ = 0 (rᵢ measured from CM, so r̄ = 0)
- Third term = Md²

Therefore I = I_cm + Md². ∎

---

## Proof 2: Perpendicular Axis Theorem ⚡⚡

**Theorem:** For a planar body in the xy-plane: I_z = I_x + I_y.

**Proof:**
I_x = Σ mᵢyᵢ², I_y = Σ mᵢxᵢ² (distances from x and y axes)
I_z = Σ mᵢ(xᵢ² + yᵢ²) = Σ mᵢxᵢ² + Σ mᵢyᵢ² = I_y + I_x. ∎

---

## Proof 3: König's Theorem (KE Decomposition) ⚡⚡⚡

**Theorem:** T = ½Mv_cm² + ½Σ mᵢv'ᵢ² where v'ᵢ = velocity relative to CM.

**Proof:**
vᵢ = v_cm + v'ᵢ

T = ½Σ mᵢ|vᵢ|² = ½Σ mᵢ|v_cm + v'ᵢ|²
= ½Σ mᵢv_cm² + Σ mᵢ(v_cm · v'ᵢ) + ½Σ mᵢv'ᵢ²
= ½Mv_cm² + v_cm · (Σ mᵢv'ᵢ) + ½Σ mᵢv'ᵢ²

But Σ mᵢv'ᵢ = d/dt(Σ mᵢr'ᵢ) = 0 (since CM is origin in body frame).

So T = ½Mv_cm² + T_rot. For rigid body: T_rot = ½I_cm·ω². ∎

---

## Proof 4: Euler-Lagrange Equations from D'Alembert ⚡⚡

**Derivation:**
D'Alembert: Σ(Fᵢ − mᵢr̈ᵢ)·δrᵢ = 0

Express rᵢ = rᵢ(q₁,...,qₙ,t). Then δrᵢ = Σⱼ (∂rᵢ/∂qⱼ)δqⱼ

After substitution and using:
- ∂ṙᵢ/∂q̇ⱼ = ∂rᵢ/∂qⱼ
- d/dt(∂rᵢ/∂qⱼ) = ∂ṙᵢ/∂qⱼ

We get: Σⱼ [d/dt(∂T/∂q̇ⱼ) − ∂T/∂qⱼ − Qⱼ]δqⱼ = 0

For independent δqⱼ: **d/dt(∂T/∂q̇ⱼ) − ∂T/∂qⱼ = Qⱼ**

For conservative Qⱼ = −∂V/∂qⱼ with L = T − V:

**d/dt(∂L/∂q̇ⱼ) − ∂L/∂qⱼ = 0** ∎

---

# 20 SOLVED PROBLEMS (Exam-Style)

**P1.** Find MI of a uniform disk (M, R) about a tangent in its plane.

**Solution:** I_diameter = MR²/4 (by perpendicular axis: I_z = 2I_d → I_d = MR²/4).
By parallel axis: I_tangent = MR²/4 + MR² = **5MR²/4**.

**P2.** A uniform rod (M=2kg, L=1m) rotates about one end. Torque = 6 N·m. Find angular acceleration.

**Solution:** I = ML²/3 = 2(1)/3 = 2/3 kg·m². α = τ/I = 6/(2/3) = **9 rad/s²**.

**P3.** Solid sphere vs solid cylinder race down incline (same M, R). Who wins?

**Solution:** a_sphere = 5g sinθ/7, a_cylinder = 2g sinθ/3. Ratio: (5/7)/(2/3) = 15/14 > 1. **Sphere wins** (higher acceleration).

**P4.** A rod (M, L) hangs from one end. It's displaced by angle θ₀ and released. Find period of small oscillations.

**Solution:** I_end = ML²/3, h = L/2 (CM distance from pivot).
T = 2π√(I/(Mgh)) = 2π√(ML²/3 / (MgL/2)) = 2π√(2L/3g).
Equivalent simple pendulum: l = 2L/3.

**P5.** A flywheel (I = 5 kg·m²) rotating at 60 rpm is brought to rest by friction in 30 s. Find frictional torque.

**Solution:** ω₀ = 60·2π/60 = 2π rad/s. α = −ω₀/t = −2π/30 = −π/15.
τ = Iα = 5·π/15 = **π/3 ≈ 1.05 N·m**.

**P6.** Find MI of a hollow sphere (M, R) about diameter using integration.

**Solution:** Use spherical shell element at angle φ: dm = M·sin φ dφ/2, distance from axis = R sinφ.
I = ∫₀π (R sinφ)² · M sinφ dφ/2 = MR²/2 · ∫₀π sin³φ dφ = MR²/2 · 4/3 = **2MR²/3**. ✓

**P7.** Billiard ball struck at height h = 7R/5 above table. Show it rolls without slipping immediately.

**Solution:** Impulse J at height h, contact at R from center.
Linear: Mv = J, Angular: (2MR²/5)ω = J(h−R) = J·2R/5.
So ω = J/(MR) = v/R. Rolling condition v = Rω satisfied. ✓

**P8.** A uniform square plate (side a, mass M). MI about diagonal?

**Solution:** I_x = I_y = Ma²/12 (about sides through center). I_z = Ma²/6 (perp axis).
By symmetry, I_diagonal = I_x = **Ma²/12** (diagonal is equivalent to side axis for square).

**P9.** Two particles of mass m at (a,0) and (0,a). Find products of inertia.

**Solution:** I_xy = −Σmᵢxᵢyᵢ = −[m·a·0 + m·0·a] = 0.
I_xx = Σmᵢ(yᵢ²+zᵢ²) = m(0+0) + m(a²+0) = ma².
I_yy = m(a²) + m(0) = ma². Inertia tensor: diag(ma², ma², 2ma²).

**P10.** A compound pendulum has minimum period when h = k (radius of gyration about CM). Prove.

**Solution:** T = 2π√((k²+h²)/(gh)). Minimize (k²+h²)/h = k²/h + h.
d/dh(k²/h + h) = −k²/h² + 1 = 0 → h = k.
T_min = 2π√(2k/g). ∎

**P11.** Centre of percussion: Rod pivoted at A, struck at distance x from A. Find x so no impulse at pivot.

**Solution:** Let impulse J at x from pivot. Linear: MΔv_cm = J − R (R = reaction at pivot).
Angular about A: I_A·Δω = Jx.
Kinematic constraint (rigid rotation about A): Δv_cm = (L/2)·Δω.

For R = 0: MΔv_cm = J and I_A·Δω = Jx, with M(L/2)Δω = J.
So x = I_A·Δω/J = I_A/(M·L/2) = (ML²/3)/(ML/2) = **2L/3**.

**P12.** Derive the acceleration of a body rolling down an incline using energy methods.

**Solution:** Energy: Mgh = ½Mv² + ½Iω² = ½v²(M + I/R²) where h = s sinθ.
Differentiate: Mg sinθ · v = v·(M + I/R²)·a.
So **a = g sinθ/(1 + I/(MR²))**. ∎

---

# KEY FORMULAS SUMMARY (For Quick Revision)

```
Parallel Axis:       I = I_cm + Md²
Perpendicular Axis:  I_z = I_x + I_y  (planar body only)
Euler-Lagrange:      d/dt(∂L/∂q̇) − ∂L/∂q = 0,  L = T − V
Euler's Equations:   I₁ω̇₁ = (I₂−I₃)ω₂ω₃ + N₁  (cyclic)
Rolling no-slip:     v = Rω,  a = Rα
KE:                  T = ½Mv_cm² + ½I_cm·ω²
Compound Pendulum:   T = 2π√((k²+h²)/(gh))
Precession:          Ω = Mgh/(I_spin·ω_spin)
Angular impulse:     I·Δω = ∫τ dt = moment of impulse
Centre of perc.:     x = I_pivot/(M·d_cm)  from pivot
Rolling accel.:      a = g sinθ/(1 + I_cm/(MR²))
```
