# Open two PRAW or PMRAW files simultaneously and compare their common matrices.
# Demonstrates that multiple files can be held open at the same time.
# For PointCloud, per-point Euclidean distances are reported with a text histogram.
#
# Prerequisites:
#   - PHOXI_CONTROL_PATH environment variable pointing to PhoXi Control installation directory
#   - phoxi_api Python package installed
#
# Usage:
#   python read_praw_two_files.py <path1> <path2>

import argparse

import numpy as np

from phoxi_api import PrawReader


def _text_histogram(values: np.ndarray, bins: int = 10, width: int = 40) -> str:
    counts, edges = np.histogram(values, bins=bins)
    peak = counts.max()
    lines = []
    for i, count in enumerate(counts):
        bar = "#" * int(count / peak * width)
        lo, hi = edges[i], edges[i + 1]
        lines.append(f"  {lo:8.3f} – {hi:8.3f} | {bar:<{width}} {count}")
    return "\n".join(lines)


def _compare_point_cloud(m1: np.ndarray, m2: np.ndarray) -> None:
    # Point cloud shape is (H, W, 3) — X, Y, Z coordinates in millimetres.
    # Points where the scanner had no measurement are stored as (0, 0, 0).
    # Exclude them from statistics so they don't skew the distance distribution.
    valid = ~(
        np.all(m1 == 0, axis=-1) |
        np.all(m2 == 0, axis=-1)
    )
    if not valid.any():
        print("  no valid point pairs to compare")
        return

    dist = np.linalg.norm(m1[valid].astype(float) - m2[valid].astype(float), axis=-1)

    print(f"  valid point pairs : {valid.sum()} / {valid.size}")
    print(f"  distance (mm)")
    print(f"    mean   : {dist.mean():.4f}")
    print(f"    median : {np.median(dist):.4f}")
    print(f"    max    : {dist.max():.4f}")
    print(f"    p95    : {np.percentile(dist, 95):.4f}")
    print(f"    p99    : {np.percentile(dist, 99):.4f}")
    print(f"  distribution:")
    print(_text_histogram(dist))


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("path1", type=str, help="Path to the first .praw or .pmraw file")
    arg_parser.add_argument("path2", type=str, help="Path to the second .praw or .pmraw file")
    args = arg_parser.parse_args()

    # Both readers are opened inside a single with statement — they stay open
    # concurrently for the duration of the block and are closed automatically on exit.
    with PrawReader(args.path1) as r1, PrawReader(args.path2) as r2:
        info1 = r1.info()
        info2 = r2.info()

        print(f"File 1: {args.path1}")
        print(f"  Device : {info1.name} ({info1.variant})")
        print(f"  Frames : {info1.frames_count}")
        print(f"  Matrices: {r1.list_matrices()}")

        print(f"\nFile 2: {args.path2}")
        print(f"  Device : {info2.name} ({info2.variant})")
        print(f"  Frames : {info2.frames_count}")
        print(f"  Matrices: {r2.list_matrices()}")

        matrices1 = r1.list_matrices()
        matrices2 = r2.list_matrices()
        # Find matrices available in both files — only these can be compared.
        common = sorted(set(matrices1) & set(matrices2))
        print(f"\nMatrices present in both files: {common}")

        for name in common:
            m1 = r1.read_matrix(name)
            m2 = r2.read_matrix(name)
            if m1 is None or m2 is None:
                continue
            # Shapes may differ when files come from different camera resolutions.
            if m1.shape != m2.shape:
                print(f"\n{name}: shapes differ ({m1.shape} vs {m2.shape}), skipping comparison")
                continue

            print(f"\n{name} (shape {m1.shape}, dtype {m1.dtype}):")

            if name == "PointCloud":
                _compare_point_cloud(m1, m2)
            else:
                diff = np.abs(m1.astype(float) - m2.astype(float))
                print(f"  max absolute difference: {diff.max():.4f}")
                print(f"  mean absolute difference: {diff.mean():.4f}")
