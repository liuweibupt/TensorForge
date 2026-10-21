# Precision support versus synthesized unit area

This figure adapts the supplied reference's grouped bars and aligned format-support matrix to TensorForge's released measurements. It uses **16 directly synthesized dot-product units**, all at `dimK=32` and a **requested** synthesis clock of **1410 MHz**. It is not a reconstruction of the screenshot's measurements.

## Figure contract

- **Question and role:** compare released unit areas across precision configurations, with a matrix identifying each unit's supported formats. This is a design-space comparison, not an isolated causal effect of format count.
- **Source reference:** user-supplied repository screenshot; publication type, exact venue, year, and publication status are unknown. Its subject is hardware arithmetic-unit area. Reuse is limited to the grouped-bar/support-matrix visual grammar.
- **Target:** unspecified venue and publication stage; neutral compact hardware/architecture figure. No Nature-specific styling or submission-compliance claim.
- **Evidence:** `tensorforge_site_bundle/data/dp_training.csv`, filtered to `dimK=32` and `clk_mhz=1410`. Every one of the 16 matching measurements is retained, without prediction, composition, averaging, or technology scaling.
- **Units:** original `area_value` in μm², following the repository's `normalize.py` and `reuse.py` conventions; the source CSV leaves `area_unit` blank. Displayed values divide by 1000, with no other area transformation.
- **Panels:** upper bars show area, grouped by supported-format count and sorted by ascending area within each group; lower square markers show the exact corresponding format membership.
- **Size and formats:** 7.2 × 4.25 inches; searchable vector PDF, editable SVG, and 300 dpi PNG.
- **Annotations:** the dashed line uses the measured five-format floating-point unit. The red outline identifies the seven-format unit. Hatching identifies the FP4 lookup-table implementation, which is not a separate numeric format.
- **Evidence boundary:** this is the released set of configurations, not an exhaustive format-subset sweep. There is no six-format measurement. Accumulation, normalization, output, MX configuration, intermediate width, and wrapper implementation vary with the released designs. Matching `dimK` does not establish equal throughput per format. The clock is a synthesis target; timing closure is not established by this CSV.

## Reproduce

Requires Python 3 and matplotlib. The plotting script and `source_data.csv` are sufficient to reproduce the figure outside this repository:

```bash
python3 plot.py
```

To refresh the snapshot from the released full table, from this directory:

```bash
python3 plot.py --input ../../tensorforge_site_bundle/data/dp_training.csv
```

`source_data.csv` preserves the original measurement fields, exact source CSV line numbers, column identifiers, and explicit format membership. `provenance.json` records the original source hash and selection, and `qa.json` records machine-checkable rendering and data checks. The script does not require a skill file or repository backend module.

## Caption

**Synthesized dot-product unit area across precision configurations.** Each bar is one of 16 released TensorForge units at `dimK=32` and a requested synthesis clock of 1410 MHz. Columns are grouped by the number of supported numeric formats and ordered by area within each group; the aligned squares indicate support. FP4 arithmetic and lookup-table (hatched) units implement the same numeric format. The dashed line marks the measured unit supporting all five floating-point formats; the red outline marks the seven-format unit. Areas are directly reported unit areas, not integrated compositions. Only released configurations are shown; other synthesis settings vary across designs, and equal per-format throughput or timing closure is not implied.

## Validation

See `qa.json` for the actual render's validation results. Inspect both the color PNG and the grayscale preview when revising the layout. Typography is checked at the 7.2-inch intended width with a 5 pt screening floor; no manuscript integration or venue-specific compliance check is in scope.
