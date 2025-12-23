#!/usr/bin/env python3
"""
Optimised Logo Generator
Generates multiple sizes and formats of the logo for responsive loading.

Usage:
    python scripts/generate_logo_optimized.py
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: PIL (Pillow) library not installed.")
    print("Install it with: pip install Pillow")
    sys.exit(1)


def generate_optimised_logos(logo_path, output_dir):
    """
    Generates optimised logo versions in multiple sizes and formats.
    
    Args:
        logo_path: Path to the source logo image
        output_dir: Directory to save generated logos
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
    
    # Get original dimensions
    original_width, original_height = img.size
    print(f"Original size: {original_width}x{original_height}")
    
    # Define sizes based on CSS usage:
    # Desktop: 60px height, Mobile: 40px height
    # Generate 1x, 2x, and 3x versions for retina displays
    sizes = [
        # Mobile sizes (40px height)
        (40, "mobile-1x"),   # 1x for mobile
        (80, "mobile-2x"),   # 2x for mobile retina
        (120, "mobile-3x"),  # 3x for mobile high-DPI
        
        # Desktop sizes (60px height)
        (60, "desktop-1x"),  # 1x for desktop
        (120, "desktop-2x"), # 2x for desktop retina
        (180, "desktop-3x"), # 3x for desktop high-DPI
    ]
    
    # Calculate width maintaining aspect ratio
    aspect_ratio = original_width / original_height
    
    print("\nGenerating PNG logos...")
    for height, name in sizes:
        width = int(height * aspect_ratio)
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save PNG
        png_path = output_dir / f"EHRLogo-{name}.png"
        resized.save(png_path, format='PNG', optimize=True)
        file_size = png_path.stat().st_size
        print(f"  Created: {png_path} ({width}x{height}, {file_size/1024:.1f} KB)")
    
    # Generate WebP versions for better compression
    print("\nGenerating WebP logos...")
    try:
        for height, name in sizes:
            width = int(height * aspect_ratio)
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Save WebP with quality 85 (good balance between quality and size)
            webp_path = output_dir / f"EHRLogo-{name}.webp"
            resized.save(webp_path, format='WEBP', quality=85, method=6)
            file_size = webp_path.stat().st_size
            print(f"  Created: {webp_path} ({width}x{height}, {file_size/1024:.1f} KB)")
    except Exception as e:
        print(f"  Warning: WebP generation failed: {e}")
        print("  Continuing with PNG only...")
    
    print("\nLogo optimisation complete!")
    print(f"\nGenerated files are in: {output_dir}")
    print("\nNext steps:")
    print("1. Update index.html to use responsive images with srcset")
    print("2. Consider lazy loading for below-the-fold images")


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    logo_path = project_root / "assets" / "EHRLogo.png"
    output_dir = project_root / "assets" / "logos"
    
    generate_optimised_logos(logo_path, output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
