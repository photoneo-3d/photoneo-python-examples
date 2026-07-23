# Read a PRAW or PMRAW file, extract the Texture matrix and normalize it to a
# displayable uint8 image using the same Auto Intensity normalization as PhoXi
# Control (percentile-clipping with 2 % tail clipping, works for grayscale and RGB).
#
# Prerequisites:
#   - PHOXI_CONTROL_PATH environment variable pointing to PhoXi Control installation directory
#   - phoxi_api Python package installed
#   - Pillow (pip install Pillow) — required only for saving the output PNG
#
# Usage:
#   python read_praw_texture.py <path>
#   python read_praw_texture.py <path> --frame <index>   # PMRAW only
#   python read_praw_texture.py <path> --out texture.png
#   python read_praw_texture.py <path> --percentile 1.0  # tighter clip

import argparse
import sys

from phoxi_api import PrawReader, normalize_texture

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("path", type=str, help="Path to a .praw or .pmraw file")
    arg_parser.add_argument(
        "--frame", type=int, default=0, help="Frame index to open (PMRAW only, default: 0)"
    )
    arg_parser.add_argument(
        "--out", type=str, default=None, metavar="FILE",
        help="Save normalized texture as PNG (requires Pillow)",
    )
    arg_parser.add_argument(
        "--percentile", type=float, default=2.0,
        help="Percentile tail clipping for normalization (default: 2.0)",
    )
    args = arg_parser.parse_args()

    with PrawReader(args.path, frame_index=args.frame) as reader:
        # Texture format depends on the device and scan settings: grayscale
        # (uint16, 12-bit range 0–4095) or 3-channel RGB for color cameras.
        texture = reader.read_matrix("Texture")
        if texture is None:
            print("No Texture matrix found in this file.")
            sys.exit(1)

        print(f"Raw texture  — shape: {texture.shape}, dtype: {texture.dtype}")
        print(f"  min: {texture.min():.1f}  max: {texture.max():.1f}  mean: {texture.mean():.1f}")

        # normalize_texture() clips outlier pixels using percentile-based min/max
        # and scales the result to uint8 [0, 255], identical to PhoXi Control output.
        normalized = normalize_texture(texture, percentile=args.percentile)

        print(f"\nNormalized   — shape: {normalized.shape}, dtype: {normalized.dtype}")
        print(f"  min: {normalized.min()}  max: {normalized.max()}  mean: {normalized.mean():.1f}")
        print(f"  (percentile clip: {args.percentile} %)")

        if args.out:
            try:
                from PIL import Image
            except ImportError:
                print("\nPillow is not installed — cannot save PNG. Run: pip install Pillow")
                sys.exit(1)

            # L = 8-bit grayscale, RGB = 8-bit colour (3 channels).
            mode = "RGB" if normalized.ndim == 3 else "L"
            Image.fromarray(normalized, mode=mode).save(args.out)
            print(f"\nSaved: {args.out}")
