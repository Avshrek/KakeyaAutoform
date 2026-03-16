/-
  Formalization of a δ-tube intersection volume bound from Hong Wang's
  work on the Kakeya conjecture in ℝ³.

  Statement (informal):
    Let δ ∈ (0,1). A δ-tube is the δ-neighborhood of a unit line segment
    in ℝ³. If two δ-tubes point in directions v₁, v₂ ∈ S² with
    ∠(v₁, v₂) ≥ θ > δ, then
      vol(T₁ ∩ T₂) ≤ C · δ³ / sin(∠(v₁, v₂)).
-/

import Mathlib.MeasureTheory.Measure.Lebesgue.Basic
import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.Geometry.Euclidean.Angle.Unoriented.Basic
import Mathlib.Topology.MetricSpace.Thickening
import Mathlib.Topology.MetricSpace.HausdorffDimension
import Mathlib.Analysis.InnerProductSpace.EuclideanDist
import Mathlib.Analysis.Convex.Segment
import Mathlib.Analysis.Normed.Lp.MeasurableSpace

open MeasureTheory Metric InnerProductGeometry Set

noncomputable section

/-! ### The ambient space: ℝ³ as `EuclideanSpace ℝ (Fin 3)` -/

/-- Notation for the ambient Euclidean 3-space. -/
abbrev E3 := EuclideanSpace ℝ (Fin 3)

/-! ### MeasureSpace instance for E3

`EuclideanSpace ℝ (Fin 3)` is definitionally `PiLp 2 (fun _ : Fin 3 => ℝ)`,
which is `WithLp 2 (Fin 3 → ℝ)`. Mathlib provides `MeasurableSpace` for
`WithLp` but not `MeasureSpace`. We pull back the Pi Lebesgue measure
(the product of the standard `volume` on each `ℝ` factor) through the
canonical measurable equivalence `MeasurableEquiv.toLp`. -/
instance : MeasureSpace E3 where
  volume := Measure.comap WithLp.ofLp volume

/-! ### The unit sphere S² -/

/-- The unit 2-sphere in ℝ³, i.e. `{v : E3 | ‖v‖ = 1}`. -/
abbrev S2 := Metric.sphere (0 : E3) 1

/-! ### δ-tube: closed δ-neighborhood of a unit line segment -/

/-- A **δ-tube** in ℝ³ centred at base point `p` pointing in direction `v`
    (where `v` is a unit vector).
    It is defined as the closed `δ`-thickening of the line segment from `p`
    to `p + v`, which has length 1 since `‖v‖ = 1`. -/
def deltaTube (p : E3) (v : E3) (δ : ℝ) : Set E3 :=
  Metric.cthickening δ (segment ℝ p (p + v))

/-! ### Tube intersection volume bound -/

/--
**Tube intersection volume bound (Hong Wang, Kakeya conjecture).**

Let `δ ∈ (0, 1)` be a small parameter.  Let `T₁` and `T₂` be two δ-tubes
in ℝ³, with base points `p₁, p₂` and unit-sphere directions `v₁, v₂ ∈ S²`.
Suppose the angle between their directions satisfies `∠(v₁, v₂) ≥ θ` for
some `θ > δ`.

Then the Lebesgue measure (volume) of the intersection `T₁ ∩ T₂` is
bounded above:

$$\operatorname{vol}(T_1 \cap T_2)
     \;\le\; C \,\frac{\delta^3}{\sin\!\bigl(\angle(v_1,v_2)\bigr)}$$

for some absolute constant `C > 0`.
-/
theorem tube_intersection_volume_bound :
    ∃ C : ℝ, C > 0 ∧
      ∀ (δ : ℝ) (hδ₀ : 0 < δ) (hδ₁ : δ < 1)
        (θ : ℝ) (hθδ : θ > δ)
        (p₁ p₂ : E3)
        (v₁ : E3) (hv₁ : v₁ ∈ S2)
        (v₂ : E3) (hv₂ : v₂ ∈ S2)
        (hangle : angle (v₁ : E3) (v₂ : E3) ≥ θ),
        volume (deltaTube p₁ v₁ δ ∩ deltaTube p₂ v₂ δ)
          ≤ ENNReal.ofReal (C * δ ^ 3 / Real.sin (angle (v₁ : E3) (v₂ : E3))) := by
  sorry

/-! ## ═══════════════════════════════════════════════════════════════════
    ## The Kakeya Conjecture in ℝ³
    ## ═══════════════════════════════════════════════════════════════════ -/

/-! ### Kakeya set: definition -/

/--
A **Kakeya set** in `E3 = ℝ³` is a compact set that contains a unit line
segment in every direction of the unit sphere `S²`.

Formally, `K` is Kakeya iff:
1. `K` is compact, and
2. for every direction `v ∈ S²` there exists a base point `x : E3` such
   that the closed segment `segment ℝ x (x + v)` (which has length 1
   since `‖v‖ = 1`) is entirely contained in `K`.
-/
def IsKakeyaSet (K : Set E3) : Prop :=
  IsCompact K ∧
    ∀ v ∈ S2, ∃ x : E3, segment ℝ x (x + v) ⊆ K

/-! ### The Kakeya Conjecture (now theorem, Hong Wang & Joshua Zahl 2025) -/

/--
**Kakeya Conjecture in ℝ³ (Wang–Zahl 2025).**

Every Kakeya set in `ℝ³` has Hausdorff dimension equal to 3.
-/
theorem kakeya_conjecture_3d (K : Set E3) (hK : IsKakeyaSet K) :
    dimH K = 3 := by
  sorry

end
