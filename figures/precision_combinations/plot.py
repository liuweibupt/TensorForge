#!/usr/bin/env python3
"""Enumerate all nonempty precision-family unions using measured whole units.

Requires only matplotlib and the adjacent components.json snapshot. Areas of
multi-unit configurations are derived component sums, not integrated synthesis.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator


HERE = Path(__file__).resolve().parent
FAMILIES = ("TF32", "FP16", "BF16", "FP8", "FP6", "FP4", "INT8", "INT4", "Binary")
LABELS = ("TF32", "FP16", "BF16", "FP8 (E4M3/E5M2)", "FP6 (E3M2/E2M3)",
          "FP4 (E2M1)", "INT8", "INT4", "Binary (1-bit)")
COLORS = ("#9BB8D5", "#F4C28B", "#EEABA3", "#AACDD0", "#A9C69A",
          "#C6BFDA", "#D7C39E", "#A5BECD", "#CCB7C7")
ACCENT = "#BC4D3B"


def family_mask(families):
    families = tuple(families)
    unknown = set(families).difference(FAMILIES)
    if unknown:
        raise ValueError(f"Unknown numeric families: {sorted(unknown)}")
    return sum(1 << FAMILIES.index(name) for name in set(families))


def clean_svg(path):
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


def optimize(components):
    """Exact minimum-area OR-union dynamic program, including overlap.

    A shared unit's full supported-family mask must fit the requested union.
    No internal pruning or proportional area discount is possible. The state
    graph is acyclic because adding a new family strictly increases the mask.
    """
    units = []
    seen_ids = set()
    for index, raw in enumerate(components, 1):
        unit = dict(raw)
        unit["id"] = str(unit.get("id") or f"U{index:02d}")
        if unit["id"] in seen_ids:
            raise ValueError(f"Duplicate unit id: {unit['id']}")
        seen_ids.add(unit["id"])
        families = unit["supported_families"]
        if isinstance(families, str):
            families = families.split(";")
        unit["mask"] = family_mask(families)
        unit["area_um2"] = float(unit["area_um2"])
        if not unit["mask"] or not math.isfinite(unit["area_um2"]) or unit["area_um2"] <= 0:
            raise ValueError(f"Invalid component: {unit['id']}")
        if int(float(unit["dimK"])) != 16 or float(unit["clk_mhz"]) != 1410:
            raise ValueError("Every component must use dimK=16 and clock target=1410 MHz")
        if "WrapperFP16INT" in unit.get("variant", "") or "WrapperFP16INT" in unit.get("design_name", ""):
            raise ValueError("Mixed FP×INT datapaths cannot represent selectable precision unions")
        units.append(unit)
    units.sort(key=lambda unit: unit["id"])
    limit = 1 << len(FAMILIES)
    costs = [math.inf] * limit
    paths = [None] * limit
    costs[0], paths[0] = 0.0, ()
    for mask in range(limit):
        if paths[mask] is None:
            continue
        for index, unit in enumerate(units):
            union = mask | unit["mask"]
            if union == mask:
                continue
            candidate = costs[mask] + unit["area_um2"]
            path = tuple(sorted((*paths[mask], index)))
            if candidate < costs[union] - 1e-7 or (abs(candidate - costs[union]) <= 1e-7 and
                                                     (paths[union] is None or path < paths[union])):
                costs[union], paths[union] = candidate, path
    records = []
    for mask in range(1, limit):
        if paths[mask] is None:
            raise ValueError(f"Missing measured-component coverage for mask {mask}")
        chosen = [units[index] for index in paths[mask]]
        assert family_mask(name for unit in chosen for name in FAMILIES if unit["mask"] & (1 << FAMILIES.index(name))) == mask
        records.append({"mask": mask, "family_count": mask.bit_count(),
                        "families": [name for bit, name in enumerate(FAMILIES) if mask & (1 << bit)],
                        "area_um2": sum(unit["area_um2"] for unit in chosen),
                        "component_count": len(chosen), "components": chosen})
    records.sort(key=lambda row: (row["family_count"], row["area_um2"], row["mask"]))
    for index, row in enumerate(records, 1):
        row["id"] = f"C{index:03d}"
    return units, records


def panel(fig, spec, records, *, detailed=False, gray=False, common_ymax=None):
    grid = spec.subgridspec(2, 1, height_ratios=(2.3, 1.25), hspace=0.065)
    ax = fig.add_subplot(grid[0])
    matrix = fig.add_subplot(grid[1], sharex=ax)
    n = len(records)
    count = records[0]["family_count"]
    values = [row["area_um2"] / 1000 for row in records]
    color = "0.77" if gray else COLORS[count - 1]
    ax.set(xlim=(-0.8, n - 0.2), ylim=(0, common_ymax or max(values) * 1.20 + 0.2))
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="0.91", linewidth=0.5)
    ax.yaxis.set_major_locator(MaxNLocator(4 if not detailed else 6))
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", length=2.5, width=0.5, labelsize=9 if not detailed else 8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.6)
        ax.spines[side].set_color("0.4")
    for index, (row, value) in enumerate(zip(records, values)):
        direct = row["component_count"] == 1
        edge = ("0.15" if gray else ACCENT) if direct else "0.4"
        ax.bar(index, value, width=0.74 if n >= 9 else 0.34, color=color, edgecolor=edge,
               linewidth=1.0 if direct else 0.35, zorder=3)
        if detailed:
            ax.text(index, value + max(values) * 0.015, f"{value:.1f}", ha="center", va="bottom",
                    fontsize=7, rotation=90 if n > 36 else 0,
                    color=edge if direct else "0.25")
    family_word = "family" if count == 1 else "families"
    combination_word = "combination" if n == 1 else "combinations"
    ax.set_title(f"{count} {family_word}  ·  {n} {combination_word}", loc="left", pad=9,
                 fontsize=11 if not detailed else 12, fontweight="bold")
    ax.set_ylabel("Area (10³ μm²)", fontsize=9 if not detailed else 10)
    for bit in range(len(FAMILIES)):
        matrix.axhline(bit, color="0.94", linewidth=5 if detailed else 4.5, zorder=0)
    for index, row in enumerate(records):
        ys = [bit for bit in range(len(FAMILIES)) if row["mask"] & (1 << bit)]
        matrix.scatter([index] * len(ys), ys, marker="s",
                       s=7 if detailed else 4, color="0.18" if gray else "#286B3A", linewidths=0, zorder=2)
    matrix.set(ylim=(len(FAMILIES) - 0.5, -0.5), yticks=range(len(FAMILIES)),
               yticklabels=LABELS)
    matrix.tick_params(axis="y", length=0, pad=4, labelsize=8 if detailed else 8.5)
    if detailed:
        matrix.set_xticks(range(n), [row["id"] for row in records],
                          rotation=90 if n > 18 else 0, fontsize=7)
        matrix.tick_params(axis="x", length=0, pad=3)
    else:
        matrix.set_xticks([])
    for spine in matrix.spines.values():
        spine.set_visible(False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE / "components.json")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    components = data if isinstance(data, list) else data["units"]
    units, records = optimize(components)
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    groups = [[row for row in records if row["family_count"] == count] for count in range(1, 10)]
    overview_ymax = math.ceil(max(row["area_um2"] for row in records) / 1000 * 1.15 / 10) * 10
    with (out / "all_combinations.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["id", "family_count", "families", "area_um2", "component_count", "evidence_type", "component_ids", "area_formula", "component_sources"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in records:
            writer.writerow({"id": row["id"], "family_count": row["family_count"],
                             "families": ";".join(row["families"]), "area_um2": f"{row['area_um2']:.9f}",
                             "component_count": row["component_count"],
                             "evidence_type": "one_measured_unit" if row["component_count"] == 1 else "derived_component_sum",
                             "component_ids": ";".join(unit["id"] for unit in row["components"]),
                             "area_formula": " + ".join(str(unit["area_um2"]) for unit in row["components"]),
                             "component_sources": json.dumps(row["components"], ensure_ascii=False)})
    with plt.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "svg.fonttype": "none",
                         "font.size": 9, "savefig.facecolor": "white"}):
        for gray in (False, True):
            fig = plt.figure(figsize=(28.8, 15.3))
            outer = fig.add_gridspec(3, 3, left=0.065, right=0.992, bottom=0.05, top=0.89,
                                     wspace=0.30, hspace=0.30)
            for index, rows in enumerate(groups):
                panel(fig, outer[index // 3, index % 3], rows, gray=gray, common_ymax=overview_ymax)
            fig.text(0.065, 0.977, "All 511 nonempty precision-family combinations", fontsize=19, weight="bold", va="top")
            fig.text(0.065, 0.948, "Minimum sum of available whole-unit areas · dimK = 16 · synthesis target = 1410 MHz", fontsize=13, va="top")
            fig.text(0.065, 0.017, "Derived compositions exclude integration overhead. FP8 and FP6 subformats stay coupled; FP32 arrays and asymmetric FP×INT units are shown separately.", fontsize=11)
            handles = [Patch(facecolor="white", edgecolor="0.15" if gray else ACCENT, linewidth=1.1, label="One measured unit"),
                       Patch(facecolor="0.8", edgecolor="0.4", label="Sum of ≥2 measured units")]
            fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.985), frameon=False, fontsize=12)
            stem = "area_all_combinations_grayscale" if gray else "area_all_combinations"
            fig.savefig(out / f"{stem}.png", dpi=150)
            if not gray:
                fig.savefig(out / f"{stem}.pdf")
                fig.savefig(out / f"{stem}.svg")
                clean_svg(out / f"{stem}.svg")
            plt.close(fig)
        with PdfPages(out / "area_combinations_detail.pdf") as pdf:
            for count, rows in enumerate(groups, 1):
                fig = plt.figure(figsize=(14.4, 5.6))
                spec = fig.add_gridspec(1, 1, left=0.135, right=0.989, bottom=0.19, top=0.86)
                panel(fig, spec[0], rows, detailed=True)
                fig.text(0.135, 0.96, "Whole-unit area sum · dimK = 16 · clock target = 1410 MHz", fontsize=11, va="top")
                fig.text(0.135, 0.035, "Red outline: one measured unit. Other bars: derived component sums, excluding integration overhead. All configurations are listed in all_combinations.csv.", fontsize=8)
                pdf.savefig(fig)
                fig.savefig(out / f"area_{count}_families.png", dpi=180)
                fig.savefig(out / f"area_{count}_families.svg")
                clean_svg(out / f"area_{count}_families.svg")
                plt.close(fig)
    provenance = {
        "component_snapshot_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "families": list(FAMILIES), "component_count": len(units),
        "number_nonempty_unions": len(records),
        "cardinality_counts": {str(count): len(rows) for count, rows in enumerate(groups, 1)},
        "component_count_distribution": dict(sorted(Counter(row["component_count"] for row in records).items())),
        "objective": "Minimum sum of measured component areas subject to exact supported-family union",
        "algorithm": "Acyclic dynamic program over all 512 OR-mask states; overlapping supported families allowed",
        "tie_break": "Lexicographic tuple of unit indices ordered by component id; tolerance 1e-7 um2",
        "constraints": ["Only whole measured units at dimK16 / 1410MHz", "No internal pruning or proportional discount", "No unsupported extra numeric families", "No asymmetric FPxINT units", "No FP32 array-to-unit extrapolation"],
        "not_measured": ["Integrated composition area", "Interconnect/mux/control overhead", "Timing closure", "Equal per-format throughput", "Integrated power"],
        "scope": "Finite released unit catalogue, not global RTL optimality or newly synthesized combinations",
        "detail_pdf_inches": [14.4, 5.6], "overview_inches": [28.8, 15.3],
        "overview_y_axis": f"All nine panels share 0–{overview_ymax} × 1000 um2; detail pages use individual labeled ranges",
    }
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    print(f"Rendered all {len(records)} combinations from {len(units)} measured unit implementations")


if __name__ == "__main__":
    main()
