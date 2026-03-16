# Kakeya Auto-Formalization Engine

An experimental AI-driven pipeline for auto-formalizing the **Wang–Zahl 2025 Kakeya Conjecture** results in **Lean 4** with Mathlib4.

## What This Contains

### Lean 4 Formalization (`KakeyaAutoform/Basic.lean`)

Type-checking Lean 4 definitions and theorem statements for:

- **δ-tube intersection volume bound** — a foundational geometric lemma from Hong Wang's work:  
  `vol(T₁ ∩ T₂) ≤ C · δ³ / sin(∠(v₁, v₂))`
- **Kakeya Conjecture in ℝ³** — the main theorem (Wang–Zahl 2025):  
  `dimH K = 3` for every Kakeya set `K ⊂ ℝ³`

All proofs are deferred with `sorry` — only the **statements** are formalized.

### Diagnostic Bridge (`Automation/`)

A Python-based diagnostic engine that intercepts `lake build` compiler errors and provides semantic fixes for common LLM hallucinations against Mathlib's typeclass hierarchies.

| Script | Purpose |
|--------|---------|
| `compiler_interface.py` | Runs `lake build`, parses errors into classified JSON |
| `diagnostic_engine.py` | Matches errors against a known-fix database |
| `run_diagnostics.py` | Single-command runner |

**Usage:**
```bash
python Automation/run_diagnostics.py
```

## Key Technical Achievement

`EuclideanSpace ℝ (Fin 3)` is `WithLp 2 (Fin 3 → ℝ)` — a structure wrapper that does **not** inherit `MeasureSpace` from the underlying Pi type. The LLM hallucinated that `volume` would work directly on `E3`. The diagnostic bridge caught this and injected:

```lean
instance : MeasureSpace E3 where
  volume := Measure.comap WithLp.ofLp volume
```

## Environment

- **Lean 4:** v4.28.0
- **Mathlib4:** v4.28.0

## Building

```bash
lake build
```
