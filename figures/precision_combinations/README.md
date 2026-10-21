# Area of all supported precision-family combinations

This exhaustive companion to the measured implementation figure covers all **511 nonempty subsets of nine input-precision families**: TF32, FP16, BF16, FP8, FP6, FP4, INT8, INT4, and Binary (1-bit). FP8 E4M3/E5M2 and FP6 E3M2/E2M3 are coupled subformats in the released datapaths; they are not independently pruned. MX/NV scaling and arithmetic/LUT implementations are shown in the measured implementation figure rather than counted as new numeric precisions.

## Evidence contract

- **Source and target:** visual grammar adapted from the supplied grouped-bar/support-matrix screenshot; exact source venue and publication status unknown. Target venue unspecified; neutral hardware/architecture style.
- **Question:** what is the smallest **component-area sum** available in the released measured-unit catalogue for each exact supported-family union?
- **Population:** every nonempty union of the nine families, grouped by cardinality and sorted by area within each group. No subset is sampled or omitted.
- **Evidence:** canonical directly synthesized units at `dimK=16`, requested synthesis clock 1410 MHz, extracted from both released source tables. `components.json` preserves exact measurements and row-level provenance.
- **Transformation:** multi-unit area is the sum of full measured unit areas. Plot values divide μm² by 1000. No per-format discount, surrogate prediction, technology scaling, or internal pruning is applied.
- **Boundary:** composed configurations are **not separately synthesized integrated designs**. Integration, interconnect, mux, and control overhead are unavailable. The result does not establish equal throughput, timing closure, or global optimality outside this finite catalogue.
- **Excluded incomparable cases:** FP32 input appears only in array measurements and is plotted separately; asymmetric FP16×INT and expanded-FP8×INT datapaths do not implement selectable FP×FP/INT×INT unions and are also plotted separately.
- **Marks:** squares identify supported families; red outlines identify results consisting of one measured unit. Other bars are derived sums of two or more measured units. All bars start at zero.

## Outputs

- `area_all_combinations.png/pdf/svg`: overview with one panel for each family count, including every combination.
- `area_combinations_detail.pdf`: nine readable vector pages, one per family count, with exact column IDs and numeric area labels.
- `area_1_families.png/svg` through `area_9_families.png/svg`: individual detailed panels.
- `all_combinations.csv`: every area, supported-family set, constituent IDs, explicit sum, and original measurement provenance.
- `components.json`, `plot.py`: portable source inputs and standalone regeneration script.
- `provenance.json`, `qa.json`: selection/optimization boundary and actual validation results.

The overview is a large design-space atlas (28.8 × 15.3 inches); use the detail PDF for reading individual columns. Detail pages are 14.4 × 5.6 inches and should be viewed at that width rather than reduced to a single manuscript column.

All nine overview panels share the same area scale for direct comparison. Detail pages use individual, explicitly labeled ranges to make dense columns easier to read.

## Reproduce

Requires Python 3.10+ and matplotlib. From this directory:

```bash
python3 plot.py
```

The optimizer visits all 512 bitmask states. Each transition adds one measured whole datapath and its complete supported-family mask. A transition may overlap already supported families, but cannot remove any capability. This enumerates exact unions, including compositions with overlapping support; positive costs make redundant duplicate units unnecessary.

## Caption

**Area of all precision-family combinations realizable by composing released units.** All 511 nonempty subsets of TF32, FP16, BF16, FP8, FP6, FP4, INT8, INT4, and Binary are shown. Each bar is the minimum sum of full measured component areas over the finite released catalogue at `dimK=16` and a requested synthesis clock of 1410 MHz, subject to matching the supported-family union exactly. Squares indicate family membership. Red outlines identify single-unit results; all other results are derived multi-unit sums, excluding integration overhead. FP8 and FP6 each retain both released subformats. This comparison does not imply integrated synthesis, equal per-format throughput, or timing closure. FP32 arrays and asymmetric FP×INT datapaths appear in separate measured panels.
