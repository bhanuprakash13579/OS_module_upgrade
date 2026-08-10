# 🔄 Dynamics of a Rigid Body — Complete Study Notes

> **CSIR NET Priority: ⭐⭐⭐ | Classical Mechanics appears in CSIR NET (Lagrangian/Hamiltonian overlap)**

---

## 🗺️ Subject Mind Map

```
                DYNAMICS OF A RIGID BODY
                         │
       ┌─────────┬───────┴───────┬──────────┐
       │         │               │          │
   Inertia    Principles     Motion      Impulsive
       │         │               │          │
   ┌───┴───┐  ┌──┴──┐      ┌───┴───┐  ┌───┴───┐
   Moments D'Alembert Fixed  2D      Conservation
   Products Angular   Axis  Motion   Initial
   Theorems Momentum  Rotation       Motion
```

---

# UNIT 1: Moments and Products of Inertia

> 📋 **Quick Refresher Before Starting:**
>
> **Moment of inertia I** = resistance to rotation (like mass is resistance to linear motion).
> For a point mass m at distance r from axis: I = mr².
> For a continuous body: I = ∫r²dm (integrate over the body).
>
> **Common results you'll derive:**
> - Thin rod about center: I = ML²/12
> - Thin rod about end: I = ML²/3
> - Solid disk about center: I = MR²/2
> - Solid sphere about diameter: I = 2MR²/5



## What is a Rigid Body?

A **rigid body** is a system of particles where the distance between any two particles remains constant during motion. Unlike a single particle, a rigid body can **rotate**.

## Moment of Inertia

The **moment of inertia** about an axis is the rotational equivalent of mass:

**I = Σ mᵢrᵢ²** (discrete) or **I = ∫ r² dm** (continuous)

where rᵢ is the perpendicular distance from particle i to the axis.

### 💡 Memory Aid
Mass tells you how hard it is to push something (linear). Moment of inertia tells you how hard it is to SPIN something (rotational).

### Standard Results (MEMORIZE THESE)

| Body | Axis | Moment of Inertia |
|------|------|-------------------|
| Thin rod (mass M, length L) | Through center, ⊥ to rod | ML²/12 |
| Thin rod | Through end, ⊥ to rod | ML²/3 |
| Circular ring (M, radius R) | Through center, ⊥ to plane | MR² |
| Circular disk (M, radius R) | Through center, ⊥ to plane | MR²/2 |
| Solid sphere (M, radius R) | Through center | 2MR²/5 |
| Hollow sphere (M, radius R) | Through center | 2MR²/3 |
| Rectangular plate (M, a×b) | Through center, ⊥ to plate | M(a²+b²)/12 |

### Worked Example
Find the moment of inertia of a uniform rod of mass M, length L about its center.

```
Take the rod along x-axis from −L/2 to L/2.
Linear density: λ = M/L

I = ∫_{-L/2}^{L/2} x² · λ dx = (M/L) · [x³/3]_{-L/2}^{L/2}
  = (M/L) · (L³/24 + L³/24) = (M/L) · (L³/12) = ML²/12 ✓
```

## Products of Inertia

**I_{xy} = Σ mᵢxᵢyᵢ** (or ∫ xy dm)

Similarly I_{xz} = Σ mᵢxᵢzᵢ and I_{yz} = Σ mᵢyᵢzᵢ. These measure the "asymmetry" of mass distribution. (Convention: products of inertia are defined **without** a leading minus sign; the minus sign appears in the inertia-tensor matrix below — see Goldstein, Symon, Greenwood.)

## Inertia Tensor

The full picture is captured by the **inertia tensor** (3×3 symmetric matrix):

```
[I] = | I_{xx}   -I_{xy}  -I_{xz} |
      | -I_{xy}   I_{yy}  -I_{yz} |
      | -I_{xz}  -I_{yz}   I_{zz} |
```

where I_{xx} = Σ mᵢ(yᵢ²+zᵢ²), etc.

---

# UNIT 2: Special Cases and Theorems

> 📋 **Quick Refresher Before Starting:**
>
> **Parallel axis theorem:** I = I_cm + Md² (shift axis by distance d from center of mass).
> Example: Rod about center: ML²/12. Rod about end (d = L/2): ML²/12 + M(L/2)² = ML²/3.
>
> **Perpendicular axis theorem** (flat bodies only): I_z = I_x + I_y
> Example: Disk: I_x = I_y = MR²/4 (by symmetry), so I_z = MR²/2 ✓


## Parallel Axis Theorem (Steiner's Theorem) 🎯

**I = I_cm + Md²**

where I_cm = moment about axis through center of mass, d = distance between parallel axes.

### Example
Moment of inertia of a rod about one end:
I_end = I_cm + M(L/2)² = ML²/12 + ML²/4 = ML²/3 ✓

## Perpendicular Axis Theorem

For a **planar body** (lying in xy-plane):

**I_z = I_x + I_y**

### Example
For a circular disk: I_x = I_y (by symmetry) and I_z = MR²/2.
So I_x = I_y = MR²/4.

## Principal Axes

Since the inertia tensor is real and symmetric, it can be diagonalized. The eigenvectors are the **principal axes**, and the eigenvalues are the **principal moments of inertia** I₁, I₂, I₃.

About principal axes, all products of inertia vanish: I_{xy} = I_{xz} = I_{yz} = 0.

### Example
For a rectangular plate (a×b, mass M) with sides along x,y axes:
- I₁ = Ma²/12 (about x-axis)
- I₂ = Mb²/12 (about y-axis)  
- I₃ = M(a²+b²)/12 (about z-axis)
- All products of inertia = 0 (symmetry)

These are already principal axes.

## Ellipsoid of Inertia

The set of points satisfying I_{xx}x² + I_{yy}y² + I_{zz}z² − 2I_{xy}xy − 2I_{xz}xz − 2I_{yz}yz = 1 forms an ellipsoid. Its principal axes are the principal axes of inertia.

---

# UNIT 3: D'Alembert's Principle

> 📋 **Quick Refresher Before Starting:**
>
> **Newton's second law:** F = ma (force = mass × acceleration).
> **D'Alembert's principle:** Rewrite as F - ma = 0, treating -ma as a "fictitious force." Now it looks like a statics problem!
> **Virtual work:** If we imagine a small displacement δr, the work done by all forces (including -ma) is zero: Σ(Fᵢ - mᵢaᵢ)·δrᵢ = 0.
> This powerful idea leads directly to Lagrangian mechanics.


## From Newton to D'Alembert

Newton's law: **F = ma** → rearrange as **F − ma = 0**

D'Alembert's idea: treat **−ma** as a fictitious "inertial force." Then the system is in "equilibrium":

**F + (−ma) = 0** → Apply methods of statics!

### D'Alembert's Principle (General Form) 🎯

For a system of particles with constraints:

**Σ (Fᵢ − mᵢaᵢ) · δrᵢ = 0**

where δrᵢ are virtual displacements consistent with constraints.

### 💡 Why is this useful?
Constraint forces (like normal forces, tension) do no virtual work for ideal constraints, so they DROP OUT of the equation!

### Example: Particle on Inclined Plane
Mass m on a frictionless plane inclined at angle θ.

Virtual displacement δr along the plane:
(mg sin θ − ma) · δs = 0 → a = g sin θ ✓

The normal force N never appeared — it does no work along the allowed motion.

## Connection to Lagrangian Mechanics 🎯

D'Alembert's principle leads directly to the **Euler-Lagrange equations**:

**d/dt(∂L/∂q̇ᵢ) − ∂L/∂qᵢ = 0**

where L = T − V (Lagrangian = Kinetic − Potential energy).

### Example: Simple Pendulum
q = θ (angle from vertical), length l.

T = ½ml²θ̇², V = −mgl cos θ, L = ½ml²θ̇² + mgl cos θ

∂L/∂θ̇ = ml²θ̇, d/dt(ml²θ̇) = ml²θ̈
∂L/∂θ = −mgl sin θ

Euler-Lagrange: ml²θ̈ + mgl sin θ = 0 → **θ̈ + (g/l) sin θ = 0** ✓

---

# UNIT 4: Angular Momentum and Equations of Motion

> 📋 **Quick Refresher Before Starting:**
>
> **Angular momentum** L = Iω (analogous to linear momentum p = mv).
> **Torque** τ = Iα = dL/dt (analogous to F = dp/dt).
> **Cross product** (Class 12): a × b is perpendicular to both a and b. |a × b| = |a||b|sinθ.
> **Euler's equations:** Govern rotation of a 3D rigid body about its center of mass. They couple the three components of angular velocity.


## Angular Momentum 🎯

For a rigid body rotating with angular velocity **ω**:

**L = [I] · ω** (angular momentum = inertia tensor × angular velocity)

For rotation about a principal axis: L = Iω (scalar form).

## Euler's Equations of Motion 🎯

In the body-fixed frame (rotating with the body), for principal axes:

```
I₁ω̇₁ + (I₃ − I₂)ω₂ω₃ = N₁
I₂ω̇₂ + (I₁ − I₃)ω₃ω₁ = N₂
I₃ω̇₃ + (I₂ − I₁)ω₁ω₂ = N₃
```

where Nᵢ are the components of external torque.

### 💡 Memory Aid for Signs
Each equation has the pattern: I_i · ω̇_i + (I_k − I_j) · ω_j · ω_k = N_i, with cyclic indices (1→2→3→1). Equivalent form: I_i ω̇_i − (I_j − I_k) ω_j ω_k = N_i (same equation, sign distributed differently).

### Example: Torque-Free Motion of Symmetric Top
I₁ = I₂ ≠ I₃, N = 0:

  ω̇₃ = 0 → ω₃ = constant.

Define Ω := ((I₃ − I₁)/I₁) ω₃. Then with I₁ = I₂:

  ω̇₁ = ((I₂ − I₃)/I₁) ω₂ ω₃ = ((I₁ − I₃)/I₁) ω₃ ω₂ = −Ω ω₂
  ω̇₂ = ((I₃ − I₁)/I₂) ω₃ ω₁ = ((I₃ − I₁)/I₁) ω₃ ω₁ = +Ω ω₁

So the system is ω̇₁ = −Ω ω₂, ω̇₂ = +Ω ω₁. Solution:

  ω₁(t) = A cos(Ω t + φ),  ω₂(t) = A sin(Ω t + φ).

(Verification: ω̇₁ = −AΩ sin(Ωt+φ) = −Ω·A sin(Ωt+φ) = −Ω ω₂ ✓, and ω̇₂ = AΩ cos(Ωt+φ) = +Ω·A cos(Ωt+φ) = +Ω ω₁ ✓. The constant A and phase φ are fixed by initial conditions.)

The transverse angular velocity (ω₁, ω₂) **precesses** around the body's symmetry axis at rate |Ω| = |(I₃ − I₁)/I₁| · |ω₃|.

## Kinetic Energy of Rotation

**T = ½ω · L = ½ωᵀ[I]ω = ½(I₁ω₁² + I₂ω₂² + I₃ω₃²)**

---

# UNIT 5: Motion Under Impulsive Forces

> 📋 **Quick Refresher Before Starting:**
>
> **Impulse** (Class 12): J = FΔt = change in momentum (Δp).
> For very short time (like a bat hitting a ball), force is huge but time is tiny. The product is finite.
> **For rigid bodies:** Impulsive force → sudden change in velocity.
> Impulsive torque → sudden change in angular velocity. τΔt = ΔL = I·Δω.


## What is an Impulse?

An **impulse** is a very large force acting for a very short time:

**J = ∫₀^Δt F dt = Δp** (change in momentum)

During an impulse, positions don't change (Δt ≈ 0), but velocities change instantaneously.

## Impulsive Motion of Rigid Bodies

### Principle
**Change in angular momentum = Impulsive torque**

[I]·(ω₊ − ω₋) = Impulsive moment

where ω₋ = angular velocity just before, ω₊ = just after.

### Example: Striking a Rod
A rod of mass M, length L, is at rest. An impulse J is applied perpendicular to the rod at distance d from center.

Change in linear momentum: Mv_cm = J → v_cm = J/M
Change in angular momentum: I_cm · ω = J·d → (ML²/12)ω = Jd → ω = 12Jd/(ML²)

### Centre of Percussion
The point where you can strike without producing a reaction at the pivot. For a rod pivoted at one end, the center of percussion is at distance 2L/3 from the pivot.

**Condition:** The impulse at the striking point produces zero impulse at the pivot.

---

# UNIT 6: Motion About a Fixed Axis

> 📋 **Quick Refresher Before Starting:**
>
> **Fixed axis rotation:** Body can ONLY rotate about one fixed line (like a door on hinges).
> **Key equation:** τ = Iα where I is moment of inertia about the fixed axis, α = angular acceleration.
> **Compound pendulum:** A rigid body swinging about a fixed point (not just a point mass on a string).
> Period: T = 2π√(I/(Mgh)) where h = distance from pivot to center of mass.


## The Equation

For rotation about a fixed axis (say z-axis):

**I_z · θ̈ = N_z** (moment of inertia × angular acceleration = torque)

This is the rotational analogue of F = ma.

### Example 1: Compound Pendulum 🎯
A rigid body pivoted at point O, center of mass at distance h from O.

I_O · θ̈ = −Mgh sin θ

For small oscillations (sin θ ≈ θ):

**Period T = 2π√(I_O/(Mgh)) = 2π√((k²+h²)/(gh))**

where k = radius of gyration about center of mass (I_cm = Mk²).

### Equivalent Simple Pendulum Length
l_eq = I_O/(Mh) = (k²+h²)/h = k²/h + h

### Example 2: Flywheel
A flywheel (I = 2 kg·m²) has a torque of 10 N·m applied. Find angular acceleration.

θ̈ = N/I = 10/2 = 5 rad/s²

After 4 seconds from rest: ω = θ̈·t = 20 rad/s, KE = ½Iω² = ½(2)(400) = 400 J.

## Reactions at the Axis

For rotation about a fixed axis, the pivot must supply forces to maintain the constraint. These are found from:

Ma_cm = F_external + R (where R = reaction)

---

# UNIT 7: Rotational Dynamics

> 📋 **Quick Refresher Before Starting:**
>
> **Kinetic energy of rolling:** T = ½mv² + ½Iω² (translational + rotational).
> **Rolling without slipping:** v = Rω (the contact point has zero velocity).
> **Energy conservation:** For a body rolling down an incline: mgh = ½mv² + ½Iω².
> Substituting v = Rω: v = √(2gh/(1 + I/mR²)). Higher I → slower rolling!


## General Motion = Translation + Rotation

Any rigid body motion can be decomposed as:

**v_P = v_cm + ω × r_{P/cm}**

(velocity of any point = velocity of center of mass + rotation about center of mass)

## Rolling Motion 🎯

For a body rolling without slipping: **v_cm = Rω** (no slip condition)

### Example: Disk Rolling Down Incline
For a uniform disk (I_cm = MR²/2) on a plane inclined at θ:

Energy method: Mgh = ½Mv² + ½Iω² = ½Mv² + ½(MR²/2)(v/R)² = ¾Mv²

So v = √(4gh/3) — slower than a sliding block (v = √(2gh)) because energy goes into rotation!

### Acceleration on incline
a = g sin θ / (1 + I_cm/(MR²))

| Body | I_cm/(MR²) | a |
|------|------------|---|
| Hollow cylinder | 1 | g sin θ / 2 (slowest) |
| Solid cylinder | 1/2 | 2g sin θ / 3 |
| Solid sphere | 2/5 | 5g sin θ / 7 |
| Hollow sphere | 2/3 | 3g sin θ / 5 |

The solid sphere reaches the bottom first!

## Gyroscopic Precession

A spinning top (gyroscope) precesses about the vertical at rate:

**Ω_precession = Mgh/(I_spin · ω_spin)**

Faster spin → slower precession (counterintuitive!).

---

# UNIT 8: Motion in Two Dimensions

> 📋 **Quick Refresher Before Starting:**
>
> **2D rigid body motion = translation + rotation.** Three equations govern it:
> M·ẍ = ΣFₓ (horizontal forces)
> M·ÿ = ΣF_y (vertical forces)
> I·θ̈ = ΣN (torques about center of mass)
> Plus constraint equations (e.g., rolling: ẍ = Rθ̈).


## Equations of Motion (2D) 🎯

For a rigid body moving in a plane:

```
M·ẍ = ΣF_x      (translation of CM in x)
M·ÿ = ΣF_y      (translation of CM in y)
I_cm·θ̈ = ΣN_cm  (rotation about CM)
```

Three equations for three unknowns (x_cm, y_cm, θ).

### Example: Cylinder Rolling on Rough Surface
A solid cylinder (M, R) rolls without slipping on a horizontal surface under force F applied at center.

```
Mẍ = F − f        (translation)
Iθ̈ = fR           (rotation about center)
ẍ = Rθ̈             (rolling condition)

From rotation: f = Iθ̈/R = (MR/2)θ̈ = (M/2)ẍ
Substituting: Mẍ = F − (M/2)ẍ → (3M/2)ẍ = F → ẍ = 2F/(3M)
And f = F/3
```

## Energy Methods

**Total KE = ½Mv_cm² + ½I_cm·ω²** (König's theorem)

Work-energy theorem: W_net = ΔKE

These often provide the easiest route to solving problems.

---

# UNIT 9: Impulsive Forces in Two Dimensions

> 📋 **Quick Refresher Before Starting:**
>
> **Combining impulsive forces with 2D motion:**
> Linear impulse: J = M·Δv (change in linear velocity of CM)
> Angular impulse: Moment of J about CM = I·Δω (change in angular velocity)
> **Centre of percussion:** The point where a blow produces NO reaction at the pivot.


## General Equations

For an impulse applied to a rigid body in 2D:

```
M·Δv_x = J_x        (change in x-momentum)
M·Δv_y = J_y        (change in y-momentum)
I_cm·Δω = moment of impulse about CM
```

### Example: Billiard Ball
A billiard ball (solid sphere, mass M, radius R) is struck horizontally at height h above the table surface. Find h for pure rolling immediately after the strike.

Impulse J applied horizontally at height h above surface (center at height R):

```
M·v = J              (translation)
I_cm·ω = J·(h − R)   (rotation about center)
```

For pure rolling: v = Rω

So MRω = J and (2MR²/5)ω = J(h−R)

Dividing: (2R/5) = (h−R) → h = R + 2R/5 = **7R/5**

Strike at height 7R/5 above the table for immediate rolling!

---

# UNIT 10: Conservation Principles and Initial Motion

> 📋 **Quick Refresher Before Starting:**
>
> **Conservation laws** (from Class 12 physics):
> - **Energy:** T + V = constant (if no non-conservative forces)
> - **Linear momentum:** If no external force, p = constant
> - **Angular momentum:** If no external torque, L = constant
>
> **Initial motion problems:** At t = 0, find the initial accelerations and reactions just as motion begins from rest.


## Conservation Laws 🎯

### Conservation of Energy
If all forces are conservative: **T + V = constant**

### Conservation of Linear Momentum
If no external forces: **Mv_cm = constant**

### Conservation of Angular Momentum
If no external torque about an axis: **L = Iω = constant**

### Example: Figure Skater
Skater pulls arms in: I decreases → ω increases (since L = Iω = const).

If I₁ = 4 kg·m² at ω₁ = 2 rad/s, and arms pulled to I₂ = 1 kg·m²:
ω₂ = I₁ω₁/I₂ = 4(2)/1 = 8 rad/s (spins 4× faster!)

## Initial Motion Problems

These involve finding accelerations at the instant a system is released from rest.

**Method:**
1. Set up equations of motion
2. Substitute initial conditions (velocities = 0 at start)
3. Solve the resulting algebraic equations for accelerations

### Example
A uniform rod of length 2a and mass M is held horizontally with one end hinged. It is released. Find initial angular acceleration.

At the instant of release (ω = 0):
I_O · θ̈ = Mga (torque about hinge)

I_O = M(2a)²/3 = 4Ma²/3

θ̈ = Mga/(4Ma²/3) = **3g/(4a)**

Acceleration of the free end: a_end = 2a · θ̈ = 3g/2 > g!

The free end accelerates faster than free fall initially! (Surprising but true.)

---

# 📝 Practice Problems — Dynamics

**Q1.** A solid sphere and a hollow sphere, both of same mass and radius, roll down an incline from the same height. Which reaches the bottom first?

**Answer:** Solid sphere. a_solid = 5g sinθ/7 > a_hollow = 3g sinθ/5.

**Q2.** A rod of mass M, length L is free to rotate about one end. A bullet of mass m hits the other end with velocity v and embeds. Find the angular velocity after impact.

**Solution:** Conservation of angular momentum about pivot:
mvL = (ML²/3 + mL²)ω → ω = 3mv/((M+3m)L)

**Q3.** Find the principal moments of inertia of a uniform cube of mass M, side a, about axes through the center parallel to edges.

**Answer:** By symmetry, I₁ = I₂ = I₃ = Ma²/6.

**Q4.** A compound pendulum has period 2π√(5/3g). If the body is a uniform rod of length L pivoted at one end, find L.

**Solution:** T = 2π√(I/(Mgh)) where I = ML²/3, h = L/2.
T = 2π√(2L/(3g)). Setting equal: 2L/(3g) = 5/(3g) → L = 5/2 = 2.5 m.

---

> **📖 Recommended Reading:** Goldstein "Classical Mechanics", S.L. Loney "Dynamics of a Particle and Rigid Bodies"
> **← Back to [Master Index](./00_MASTER_INDEX.md)**
