"""Generate Ultra-Premium High-Resolution PNG App Icons for NIVA AI."""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import os

def create_niva_icon(size=512):
    # Create image with RGBA
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = int(size * 0.06)
    radius = int(size * 0.22)
    box = (margin, margin, size - margin, size - margin)

    # 1. Base squircle with deep titanium/dark charcoal gradient
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base_draw = ImageDraw.Draw(base)

    # Multi-layer rounded rectangle gradient simulation
    for i in range(margin, size - margin):
        ratio = (i - margin) / (size - 2 * margin)
        # Deep obsidian to cosmic navy
        r = int(12 + ratio * 15)
        g = int(15 + ratio * 18)
        b = int(24 + ratio * 35)
        color = (r, g, b, 255)
        # Horizontal gradient slice inside squircle
        # We draw the full squircle base first
    
    base_draw.rounded_rectangle(box, radius=radius, fill=(14, 18, 26, 255), outline=(42, 53, 74, 255), width=int(size * 0.015))

    # 2. Add glowing ambient lights in corners
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Cyan top-left ambient light
    glow_draw.ellipse(
        (int(size * 0.1), int(size * 0.1), int(size * 0.55), int(size * 0.55)),
        fill=(6, 182, 212, 60)
    )
    # Royal violet bottom-right ambient light
    glow_draw.ellipse(
        (int(size * 0.45), int(size * 0.45), int(size * 0.9), int(size * 0.9)),
        fill=(139, 92, 246, 50)
    )
    # Electric blue center core
    glow_draw.ellipse(
        (int(size * 0.25), int(size * 0.25), int(size * 0.75), int(size * 0.75)),
        fill=(37, 99, 235, 75)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(int(size * 0.12)))

    # Composite glow over squircle
    composite = Image.alpha_composite(base, glow)

    # 3. Outer border specular bevel
    spec_draw = ImageDraw.Draw(composite)
    spec_draw.rounded_rectangle(box, radius=radius, outline=(60, 130, 246, 140), width=int(size * 0.012))

    # Inner subtle rim
    inner_box = (margin + int(size * 0.02), margin + int(size * 0.02), size - margin - int(size * 0.02), size - margin - int(size * 0.02))
    spec_draw.rounded_rectangle(inner_box, radius=radius - int(size * 0.02), outline=(255, 255, 255, 30), width=1)

    # 4. Neural Network Geometry Lines (Hexagonal / Diamond Core)
    cx, cy = size // 2, size // 2
    r_core = int(size * 0.28)

    neural = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    n_draw = ImageDraw.Draw(neural)

    # Draw Hexagonal Outer Ring
    pts = []
    for deg in range(0, 360, 60):
        rad = math.radians(deg - 30)
        x = cx + r_core * math.cos(rad)
        y = cy + r_core * math.sin(rad)
        pts.append((x, y))

    n_draw.polygon(pts, outline=(59, 130, 246, 160), width=int(size * 0.01))

    # Connecting neural nodes
    for px, py in pts:
        n_draw.ellipse((px - size * 0.02, py - size * 0.02, px + size * 0.02, py + size * 0.02), fill=(6, 182, 212, 255))
        n_draw.line((cx, cy, px, py), fill=(59, 130, 246, 80), width=int(size * 0.005))

    # 5. Stylized Futuristic 'N' Glyph in Center
    glyph = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glyph)

    w = int(size * 0.075) # stroke width
    h = int(size * 0.26)  # half-height
    span = int(size * 0.16)

    # Left vertical leg
    p1 = (cx - span, cy - h)
    p2 = (cx - span, cy + h)
    # Right vertical leg
    p3 = (cx + span, cy - h)
    p4 = (cx + span, cy + h)

    # Diagonal bridge
    g_draw.line([p1, p2], fill=(255, 255, 255, 255), width=w)
    g_draw.line([p1, p4], fill=(6, 230, 255, 255), width=int(w * 1.15))
    g_draw.line([p3, p4], fill=(255, 255, 255, 255), width=w)

    # Glowing nodes on corners of 'N'
    for pt in [p1, p2, p3, p4]:
        g_draw.ellipse((pt[0] - w * 0.8, pt[1] - w * 0.8, pt[0] + w * 0.8, pt[1] + w * 0.8), fill=(255, 255, 255, 255))
        g_draw.ellipse((pt[0] - w * 1.2, pt[1] - w * 1.2, pt[0] + w * 1.2, pt[1] + w * 1.2), outline=(0, 240, 255, 200), width=3)

    # Center pulse star
    g_draw.ellipse((cx - w * 0.5, cy - w * 0.5, cx + w * 0.5, cy + w * 0.5), fill=(255, 255, 255, 255))

    # Glow filter for the glyph
    glyph_blur = glyph.filter(ImageFilter.GaussianBlur(int(size * 0.04)))
    glyph_glow = glyph.filter(ImageFilter.GaussianBlur(int(size * 0.08)))

    # Composite layers
    result = Image.alpha_composite(composite, neural)
    result = Image.alpha_composite(result, glyph_glow)
    result = Image.alpha_composite(result, glyph_blur)
    result = Image.alpha_composite(result, glyph)

    # Mask with rounded squircle to ensure clean transparent corners
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(box, radius=radius, fill=255)

    final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    final.paste(result, (0, 0), mask=mask)

    return final

if __name__ == "__main__":
    assets_dir = r"C:\Users\STUDENT\.gemini\antigravity\scratch\niva-ai\frontend\assets"
    os.makedirs(assets_dir, exist_ok=True)

    print("Generating ultra-premium NIVA AI app icons...")
    icon512 = create_niva_icon(512)
    icon512.save(os.path.join(assets_dir, "icon-512.png"), "PNG")
    print("[SAVED] 512x512 icon-512.png")

    icon192 = create_niva_icon(192)
    icon192.save(os.path.join(assets_dir, "icon-192.png"), "PNG")
    print("[SAVED] 192x192 icon-192.png")

    icon128 = create_niva_icon(128)
    icon128.save(os.path.join(assets_dir, "niva-logo.png"), "PNG")
    print("[SAVED] 128x128 niva-logo.png")

    icon64 = create_niva_icon(64)
    icon64.save(os.path.join(assets_dir, "favicon.png"), "PNG")
    icon64.save(os.path.join(assets_dir, "favicon.ico"), format="ICO", sizes=[(64, 64)])
    print("[SAVED] favicon.ico and favicon.png")

    print("\nAll premium icons created successfully!")
