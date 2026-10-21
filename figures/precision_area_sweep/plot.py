#!/usr/bin/env python3
"""Reproduce the measured TensorForge area/support figure with matplotlib.

The adjacent source_data.csv is a complete, portable snapshot. To refresh it,
pass --input ../../tensorforge_site_bundle/data/dp_training.csv.
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
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator


HERE = Path(__file__).resolve().parent
FORMATS = ("FP16", "BF16", "MXFP8", "MXFP6", "MXFP4", "INT8", "INT4")
SUPPORT = {
    "FP16": ("FP16",),
    "BF16": ("BF16",),
    "MXFP8": ("MXFP8",),
    "MXFP6": ("MXFP6",),
    "MXFP4": ("MXFP4",),
    "MXFP4LUT": ("MXFP4",),
    "INT8": ("INT8",),
    "INT4": ("INT4",),
    "INT8INT4": ("INT8", "INT4"),
    "FP16INT8INT4": ("FP16", "INT8", "INT4"),
    # The internal '2' is not a second numeric format.
    "MXFP8FP62FP4": ("MXFP8", "MXFP6", "MXFP4"),
    "FP16BF16INT8INT4": ("FP16", "BF16", "INT8", "INT4"),
    "MXBF16FP8FP6FP4": ("BF16", "MXFP8", "MXFP6", "MXFP4"),
    "MXFP16FP8FP6FP4": ("FP16", "MXFP8", "MXFP6", "MXFP4"),
    "MXFP16BF16FP8FP6FP4": FORMATS[:5],
    "MXFP16BF16FP8FP6FP4INT8INT4": FORMATS,
}
COLORS = {1: "#9BB8D5", 2: "#F4C28B", 3: "#EEABA3",
          4: "#AACDD0", 5: "#A9C69A", 7: "#C6BFDA"}
ACCENT = "#C4503D"
STEM = "precision_area_sweep"


def load_rows(path: Path, dim_k: int, clock_mhz: int) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"precision_set", "dimK", "clk_mhz", "area_value", "variant",
                    "design_name", "mx", "norm_kind", "acc_kind", "out_kind", "midMat"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing input fields: {sorted(missing)}")
        rows = []
        for line, row in enumerate(reader, 2):
            if float(row["dimK"]) != dim_k or float(row["clk_mhz"]) != clock_mhz:
                continue
            precision = row["precision_set"]
            if precision not in SUPPORT:
                raise ValueError(f"Unknown precision configuration: {precision}")
            value = float(row["area_value"])
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid area at input line {line}")
            if row.get("area_unit", "") not in ("", "um2", "µm²", "μm²"):
                raise ValueError(f"Unexpected area unit at input line {line}")
            row["source_row"] = row.get("source_row") or str(line)
            row["supported_formats"] = ";".join(SUPPORT[precision])
            row["format_count"] = str(len(SUPPORT[precision]))
            rows.append(row)
    counts = Counter(row["precision_set"] for row in rows)
    if counts != Counter({precision: 1 for precision in SUPPORT}):
        raise ValueError(f"Expected exactly one measurement for each of the 16 configurations; got {dict(counts)}")
    rows.sort(key=lambda row: (int(row["format_count"]), float(row["area_value"]), row["precision_set"]))
    for index, row in enumerate(rows, 1):
        row["column_id"] = f"U{index:02d}"
    return rows


def draw(rows: list[dict[str, str]], dim_k: int, clock_mhz: int, grayscale: bool = False):
    fig = plt.figure(figsize=(7.2, 4.25))
    grid = fig.add_gridspec(2, 1, height_ratios=(2.7, 1.3), hspace=0.055,
                           left=0.105, right=0.987, bottom=0.15, top=0.86)
    ax = fig.add_subplot(grid[0])
    matrix = fig.add_subplot(grid[1], sharex=ax)
    groups: dict[int, list[float]] = {}
    positions = []
    position = 0.0
    previous_count = None
    for row in rows:
        count = int(row["format_count"])
        if previous_count is not None and count != previous_count:
            position += 0.65
        positions.append(position)
        groups.setdefault(count, []).append(position)
        position += 1
        previous_count = count
    lower, upper = -0.65, positions[-1] + 0.65
    areas = [float(row["area_value"]) / 1000 for row in rows]
    max_y = math.ceil((max(areas) * 1.13) / 10) * 10
    ax.set(xlim=(lower, upper), ylim=(0, max_y), ylabel="Unit area (10³ μm²)")
    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="0.91", linewidth=0.45)
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", width=0.6, length=2.5, pad=3)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color("0.35")
        ax.spines[side].set_linewidth(0.65)

    fp_row = next(row for row in rows if row["precision_set"] == "MXFP16BF16FP8FP6FP4")
    baseline = float(fp_row["area_value"]) / 1000
    ax.axhline(baseline, color="0.45" if grayscale else ACCENT,
               linestyle=(0, (3, 2)), linewidth=0.75, alpha=0.85, zorder=1)
    ax.text(lower + 0.20, baseline + 1.25, f"All FP: {baseline:.1f}",
            color="0.25" if grayscale else ACCENT, fontsize=7, va="bottom")
    for x, row, value in zip(positions, rows, areas):
        count = int(row["format_count"])
        highlight = count == len(FORMATS)
        lut = row["precision_set"] == "MXFP4LUT"
        edge = ("0.15" if grayscale else ACCENT) if highlight else "0.40"
        ax.bar(x, value, width=0.68, color="0.77" if grayscale else COLORS[count],
               edgecolor=edge, linewidth=1.2 if highlight else 0.6,
               hatch="////" if lut else None, zorder=3)
        ax.text(x, value + 0.8, f"{value:.1f}", ha="center", va="bottom",
                fontsize=7, color=edge if highlight else "0.25",
                fontweight="bold" if highlight else "normal")
        if lut:
            ax.text(x, value + 5.4, "LUT", ha="center", va="bottom", fontsize=6.5, color="0.3")

    for count, xs in groups.items():
        heading = f"{count} format" if count == 1 else f"{count} formats"
        # Singleton groups use two lines to retain readable type at paper size.
        if len(xs) == 1:
            heading = heading.replace(" ", "\n", 1)
        ax.text((xs[0] + xs[-1]) / 2, 1.045, heading, transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=7.4, fontweight="bold", linespacing=1.0)
    group_values = list(groups.values())
    for left_group, right_group in zip(group_values[:-1], group_values[1:]):
        boundary = (left_group[-1] + right_group[0]) / 2
        for panel in (ax, matrix):
            panel.axvline(boundary, color="0.83", linewidth=0.5, linestyle=(0, (2, 2)), zorder=0)

    for y in range(len(FORMATS)):
        matrix.hlines(y, lower, upper, color="0.94", linewidth=4.4, zorder=0)
    for x, row in zip(positions, rows):
        ys = [i for i, fmt in enumerate(FORMATS) if fmt in SUPPORT[row["precision_set"]]]
        matrix.scatter([x] * len(ys), ys, marker="s", s=11,
                       color="0.18" if grayscale else "#286B3A", linewidths=0, zorder=3)
    matrix.set(ylim=(len(FORMATS) - 0.5, -0.5), yticks=range(len(FORMATS)),
               yticklabels=FORMATS, xticks=positions,
               xticklabels=[row["column_id"] for row in rows],
               xlabel="Precision configuration (one column = one synthesized unit)")
    matrix.tick_params(axis="both", length=0, pad=3)
    matrix.tick_params(axis="x", labelsize=6.3)
    for label in matrix.get_yticklabels():
        label.set_fontweight("bold")
        label.set_fontsize(7)
    for spine in matrix.spines.values():
        spine.set_visible(False)
    matrix.xaxis.label.set_size(7.5)
    matrix.xaxis.labelpad = 6
    fig.text(0.105, 0.974, f"dimK = {dim_k}  ·  Clock target = {clock_mhz} MHz", fontsize=8,
             ha="left", va="top")
    fig.text(0.987, 0.974, f"{len(rows)} measured units", fontsize=8, ha="right", va="top")
    handles = [Patch(facecolor="white", edgecolor="0.4", hatch="////", label="FP4 LUT"),
               Patch(facecolor="white", edgecolor="0.15" if grayscale else ACCENT,
                     linewidth=1.2, label="All 7 formats"),
               Line2D([0], [0], color="0.45" if grayscale else ACCENT,
                      linestyle=(0, (3, 2)), linewidth=0.75, label="All-FP area")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.55, 0.004),
               ncol=3, frameon=False, fontsize=7, handlelength=1.5, columnspacing=1.8)
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=HERE / "source_data.csv")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--dim-k", type=int, default=32)
    parser.add_argument("--clock-mhz", type=int, default=1410)
    args = parser.parse_args()
    rows = load_rows(args.input, args.dim_k, args.clock_mhz)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    input_sha256 = hashlib.sha256(args.input.read_bytes()).hexdigest()
    provenance_path = args.output_dir / "provenance.json"
    previous = json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
    # Preserve the original full-table hash when reproducing from the snapshot.
    from_snapshot = args.input.name == "source_data.csv"
    provenance = {
        "source_file": "tensorforge_site_bundle/data/dp_training.csv",
        "source_sha256": previous.get("source_sha256") if from_snapshot else input_sha256,
        "input_snapshot_sha256": input_sha256 if from_snapshot else None,
        "selection": {"dimK": args.dim_k, "clk_mhz": args.clock_mhz},
        "n_measurements": len(rows),
        "area_unit": "um2 (project convention; original CSV area_unit is blank)",
        "area_transform": "area_value / 1000",
        "order": "format_count ascending, then area_value ascending",
        "counts": dict(sorted(Counter(int(row["format_count"]) for row in rows).items())),
        "format_order": list(FORMATS),
        "evidence_type": "direct measured unit area; no prediction or composition",
        "reference_reuse": "grouped bars and aligned membership matrix; screenshot values not used",
        "physical_size_inches": [7.2, 4.25],
    }
    with (args.output_dir / "source_data.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    provenance["snapshot_sha256"] = hashlib.sha256((args.output_dir / "source_data.csv").read_bytes()).hexdigest()
    # The snapshot-input hash is redundant and would change between first export and rebuild.
    provenance.pop("input_snapshot_sha256")
    provenance_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 7.5,
                         "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
                         "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
                         "hatch.linewidth": 0.45, "savefig.facecolor": "white"}):
        fig = draw(rows, args.dim_k, args.clock_mhz)
        for suffix in ("png", "pdf", "svg"):
            fig.savefig(args.output_dir / f"{STEM}.{suffix}", dpi=300,
                        metadata={"Creator": "TensorForge matplotlib figure"} if suffix != "png" else None)
        plt.close(fig)
        gray = draw(rows, args.dim_k, args.clock_mhz, grayscale=True)
        gray.savefig(args.output_dir / f"{STEM}_grayscale.png", dpi=180)
        plt.close(gray)
    print(f"Rendered {len(rows)} measured units to {args.output_dir}")


if __name__ == "__main__":
    main()
