#!/usr/bin/env python3
"""
Favicon and PWA Icon Generator
Generates favicon.ico and various PNG sizes from the logo image.

Usage:
    python scripts/generate_favicon.py
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: PIL (Pillow) library not installed.")
    print("Install it with: pip install Pillow")
    sys.exit(1)


def generate_favicon(logo_path, output_dir):
    """
    Generates favicon.ico and various PNG sizes from the logo image.
    
    Args:
        logo_path: Path to the source logo image
        output_dir: Directory to save generated icons
    """
    logo_path = Path(logo_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not logo_path.exists():
        print(f"Error: Logo file not found: {logo_path}")
        sys.exit(1)
    
    print(f"Loading logo from: {logo_path}")
    try:
        img = Image.open(logo_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        sys.exit(1)
    
    # Convert RGBA to RGB if needed (for ICO format)
    if img.mode == 'RGBA':
        # Create a white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img_rgb = background
    else:
        img_rgb = img.convert('RGB')
    
    # Generate favicon.ico (16x16 and 32x32)
    print("Generating favicon.ico...")
    ico_sizes = [(16, 16), (32, 32)]
    ico_images = []
    for size in ico_sizes:
        resized = img_rgb.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(resized)
    
    ico_path = output_dir / "favicon.ico"
    ico_images[0].save(ico_path, format='ICO', sizes=[(s[0], s[1]) for s in ico_sizes])
    print(f"  Created: {ico_path}")
    
    # Generate PNG icons for PWA
    pwa_sizes = [
        (16, 16, "favicon-16x16.png"),
        (32, 32, "favicon-32x32.png"),
        (192, 192, "android-chrome-192x192.png"),
        (512, 512, "android-chrome-512x512.png"),
        (180, 180, "apple-touch-icon.png"),
    ]
    
    print("Generating PNG icons...")
    for width, height, filename in pwa_sizes:
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        output_path = output_dir / filename
        resized.save(output_path, format='PNG')
        print(f"  Created: {output_path}")
    
    print("\nFavicon generation complete!")


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    logo_path = project_root / "EHRHeater.png"
    output_dir = project_root
    
    generate_favicon(logo_path, output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())




