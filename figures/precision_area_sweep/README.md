# Precision support and measured area catalogue

This catalogue expands the original 16-point figure to **31 released selectable-mode implementations**, **4 asymmetric FP × INT units**, **2 K=32-only units**, and **4 outer-product arrays**. It follows the supplied screenshot's grouped bars and aligned support matrix. Every area is a reported synthesis measurement; no composed or predicted area appears here.

## Figure contract

- **Source reference:** user-supplied repository screenshot. Publication type, exact venue, year, and publication status are unknown; the subject is arithmetic hardware area. Only its grouped-bar/support-matrix layout is reused.
- **Target:** unspecified hardware/architecture venue and publication stage; a landscape supplemental catalogue. No venue-specific or Nature styling is assumed.
- **Claim:** expose every released input-precision implementation family, including plain, MX, NV, LUT, packed FP4, integer, and binary variants, while retaining the boundary between selectable numeric modes, asymmetric operand types, and complete arrays.
- **Evidence population:** the union of `dp_training.csv` and `area_power_measurements.csv`; one canonical implementation for every released precision token at `dimK=16`, target `clk_mhz=1410`. K=16 replaces the original figure's K=32 to provide the broadest matched catalogue; two configurations released only at K=32 appear in a separate panel.
- **Panel a:** 31 units, grouped by numeric-mode count and ordered by ascending measured area within groups. FP8 E4M3/E5M2 and FP6 E3M2/E2M3 have separate matrix rows. TF32, FP16, BF16, FP4 E2M1, INT8, INT4, and Binary1bit are also explicit. Diamonds show orthogonal MX/NV scaling, LUT implementation, and packed 2×FP4 support.
- **Panel b:** four asymmetric FP16/FP8 × INT4/INT8 units. These configurations name different left/right operand types; they are not treated as units that can independently select FP and INT modes. FP8 here is the expanded nine-bit interface of `DotProductWrapperFP16INT`; this panel does not claim both FP8 subencodings.
- **Panel c:** two extra implementations released only at K=32: FP8/FP6/packed 2×FP4 and MX FP8/FP6/FP4. Their actual K=32 measurements are shown separately; they are not rescaled to K=16 or added to the canonical K=16 composition pool.
- **Panel d:** FP32, TF32, FP16, and BF16 **complete** OuterProductArray areas at matched `M=N=8, K=1` and the same target clock. FP32 input support is measured only at array scope in the source data and is not fabricated as a K=16 dot-product unit.
- **Units:** μm² by repository convention; original `area_unit` cells are blank. Plotted values are `area_value / 1000`. Every bar begins at zero; array and dot-product axes are separate.
- **Annotations:** the dashed line is the measured MX FP16/BF16/FP8/FP6/FP4 combined unit (seven numeric modes); red outlines mark the two combined FP16/BF16/FP8/FP6/FP4/INT8/INT4 units (nine numeric modes). “Combined FP” does not include TF32 or FP32. Hatching identifies LUT implementations.
- **Size and exports:** 14.4 × 8.8 inches, intended for full-size landscape supplemental viewing. Searchable vector PDF, editable SVG, color PNG, and grayscale PNG. It should not be reduced to an ordinary 7.2-inch two-column width without rearranging panels; that would halve its 7 pt minimum text size.

## Canonical source selection

The 16 curated `dp_training.csv` configurations retain their exact released selectors, now at K=16. Additional configurations come from the complete area table, using explicit intermediate widths: BF16/TF32 and high-format shared units use `midMat26`; plain FP8 and FP8/FP6/FP4 use `midMat22`; FP6 uses `midMat17`; FP4/LUT/MX/NV variants use `midMat9`; integer and binary implementations use `midMat0`. Floating-point additions use FP32 normalization, accumulation, and output. The curated FP16 uses the released FP16/FP32 output selector. Intermediate-width sweeps are not counted as new precision combinations, and minimum-area selection is not used.

Repeated source rows and equivalent `noMX`/`noMXnoNV` aliases are deduplicated. When an explicit `noNV` spelling exists it is preferred; remaining ties use source order. Exact originating CSV filenames and line numbers are retained. `equivalent_source_rows` records matching extra full-table rows where applicable. Legacy `DotProduct_baseline` wrappers are omitted from the main comparison. Binary `norm4` and `norm8` are distinct measured configurations of **one-bit input arithmetic**, not INT4/INT8. The source uses precision tokens `4` and `8` for these rows; `display_label` and `supported_families` repair the interpretation without altering the original fields.

There are 35 distinct released precision tokens at the common dot-product setting, covering the 31 main units plus four asymmetric units. Alternative normalization/output/intermediate-width settings and repeated aliases remain in the original tables; they are not additional precision-support subsets. All precision tokens at the common setting are retained. Two additional precision tokens, `FP8FP62FP4` and `MXFP8FP6FP4`, are released only at K=32 and appear in panel c. Together the main, asymmetric, and K=32 panels retain all **37 distinct dot-product precision tokens across both entire source tables**. The separate array panel covers FP32 input support.

The two K=32-only measurements are `FP8FP62FP4` (19.404 ×10³ μm²; full-table line 3642) and `MXFP8FP6FP4` (16.414 ×10³ μm²; full-table line 3680), both at the 1410 MHz target. Exact aliases are recorded in `additional_data.csv`.

## Evidence boundaries

This is an implementation catalogue, not an exhaustive synthesis of every possible precision subset. The separate `../precision_combinations/` artefact enumerates compositions and distinguishes their estimated component-area sums from these measured unit areas. Other implementation settings vary; matching K and target clock does not establish equal throughput per mode or timing closure. Areas across panels do not describe interchangeable hardware scopes. The measurements contain no repeat-based uncertainty estimate, so none is invented.

## Reproduce

Python 3 and matplotlib are required. The script and four adjacent snapshots are sufficient for an offline rebuild:

```bash
python3 plot.py
```

To repeat canonical selection from this repository's full tables:

```bash
python3 plot.py --refresh --repo-root ../..
```

`source_data.csv` contains the 31 main bars. `mixed_data.csv`, `additional_data.csv`, and `array_data.csv` contain the separate lower panels. `canonical_units.json` exposes only the main 31-unit component pool to the composition enumerator. `provenance.json` contains source and snapshot hashes. `qa.json` records the performed source, data, PDF, grayscale, and reproduction checks. Every export is generated by the same `plot.py`.

## Column lookup

| Column | Released configuration | Numeric modes | Area (10³ μm²) | Source CSV:line |
|---|---|---:|---:|---|
| U01 | Binary1bit (norm4) | 1 | 0.184 | area_power_measurements.csv:4063 |
| U02 | Binary1bit (norm8) | 1 | 0.184 | area_power_measurements.csv:4070 |
| U03 | INT4 | 1 | 2.014 | dp_training.csv:459 |
| U04 | INT8 | 1 | 4.023 | dp_training.csv:465 |
| U05 | FP4LUT | 1 | 4.717 | area_power_measurements.csv:3750 |
| U06 | MXFP4LUT | 1 | 4.873 | dp_training.csv:553 |
| U07 | NVFP4LUT | 1 | 5.530 | area_power_measurements.csv:3818 |
| U08 | MXNVFP4LUT | 1 | 5.798 | area_power_measurements.csv:3804 |
| U09 | FP4 | 1 | 6.233 | area_power_measurements.csv:3764 |
| U10 | MXFP4 | 1 | 6.540 | dp_training.csv:474 |
| U11 | NVFP4 | 1 | 7.033 | area_power_measurements.csv:3825 |
| U12 | MXNVFP4 | 1 | 7.312 | area_power_measurements.csv:3811 |
| U13 | BF16 | 1 | 12.770 | dp_training.csv:482 |
| U14 | FP16 | 1 | 14.521 | dp_training.csv:478 |
| U15 | TF32 | 1 | 14.636 | area_power_measurements.csv:3688 |
| U16 | INT8INT4 | 2 | 5.318 | dp_training.csv:470 |
| U17 | FP6 | 2 | 8.432 | area_power_measurements.csv:4033 |
| U18 | MXFP6 | 2 | 8.576 | dp_training.csv:488 |
| U19 | FP8 | 2 | 9.658 | area_power_measurements.csv:4036 |
| U20 | MXFP8 | 2 | 9.951 | dp_training.csv:489 |
| U21 | FP16INT8INT4 | 3 | 20.027 | dp_training.csv:448 |
| U22 | FP16BF16INT8INT4 | 4 | 20.532 | dp_training.csv:447 |
| U23 | FP8FP6FP4 | 5 | 9.735 | area_power_measurements.csv:4038 |
| U24 | MXFP8FP62FP4 | 5 | 12.329 | dp_training.csv:518 |
| U25 | BF16FP8FP6FP4 | 6 | 20.589 | area_power_measurements.csv:3494 |
| U26 | MXBF16FP8FP6FP4 | 6 | 20.680 | dp_training.csv:453 |
| U27 | MXFP16FP8FP6FP4 | 6 | 23.211 | dp_training.csv:456 |
| U28 | FP16BF16FP8FP6FP4 | 7 | 23.633 | area_power_measurements.csv:3542 |
| U29 | MXFP16BF16FP8FP6FP4 | 7 | 23.869 | dp_training.csv:455 |
| U30 | FP16BF16FP8FP6FP4INT8INT4 | 9 | 28.587 | area_power_measurements.csv:3541 |
| U31 | MXFP16BF16FP8FP6FP4INT8INT4 | 9 | 29.066 | dp_training.csv:454 |

## Caption

**Released precision implementations and their measured areas.** (a) Thirty-one selectable-mode arithmetic implementations at K=16 and a 1410 MHz synthesis target, grouped by supported numeric-mode count and sorted by area within each group. Squares denote numeric modes; diamonds denote scaling and implementation features. FP8 and FP6 encodings are shown separately. Binary norm4/norm8 label distinct normalization settings for one-bit inputs. Hatching denotes LUT implementations. The dashed line marks the combined MX floating-point implementation; red outlines identify the two nine-mode combined units. (b) Four asymmetric FP × INT implementations, whose operand-pair support is distinct from selectable numeric modes. (c) Two additional K=32 implementations whose precision configurations have no K=16 row in the released tables. (d) Complete 8×8 outer-product arrays at K=1 and the same target clock, including FP32 input arithmetic. All areas are reported synthesis measurements. Canonical rows are selected by explicit implementation settings rather than minimum area. This is the released implementation catalogue, not all possible integrated subsets; synthesis target clock does not establish timing closure.
