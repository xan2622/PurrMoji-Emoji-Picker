#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Skia-Python renderer for PurrMoji Emoji Picker
Universal renderer for all emoji formats (PNG, SVG, TTF).
"""

import os
from PyQt5.QtGui import QPixmap, QIcon

# Check if skia-python is available
SKIA_AVAILABLE = False
try:
    import skia
    SKIA_AVAILABLE = True
except ImportError:
    SKIA_AVAILABLE = False
    print("[WARNING] skia-python not available. Please install it with: pip install skia-python")


class SkiaRenderer:
    """Universal Skia-Python renderer for all emoji formats (PNG, SVG, TTF) - direct memory rendering"""
    
    def __init__(self):
        """Initialize universal Skia renderer"""
        if not SKIA_AVAILABLE:
            self.initialized = False
            return
        
        try:
            import skia  # type: ignore
            self.skia = skia
            
            self.initialized = True
        except Exception:
            self.initialized = False
    
    def get_package_info_from_font_path(self, font_path):
        """Extract package information from font path"""
        font_name = os.path.basename(font_path).lower()
        font_full_path = font_path.lower()
        
        if "openmoji" in font_name:
            color_type = "Color" if ("color" in font_name or "color" in font_full_path) else "Black"
            return "OpenMoji", "TTF", color_type
        elif "noto" in font_name:
            # For Noto, check both filename and full path
            # NotoColorEmoji contains "color" in filename
            # NotoEmoji (monochrome) doesn't, but path contains "Noto Emoji" (not "Noto Color Emoji")
            color_type = "Color" if ("color" in font_name or "noto color emoji" in font_full_path) else "Black"
            return "GoogleNoto", "TTF", color_type
        
        return "Unknown", "TTF", "Unknown"
    
    def create_pixmap_from_data(self, png_data):
        """Helper to create QPixmap from PNG data
        
        Args:
            png_data: Skia PNG data bytes
        
        Returns:
            QPixmap or None if creation failed
        """
        if not png_data:
            return None
        
        pixmap = QPixmap()
        pixmap.loadFromData(png_data.bytes())
        
        if pixmap.isNull():
            return None
        
        return pixmap
    
    def render_image_file(self, image_path, size):
        """Render PNG/JPEG/WEBP image file using Skia"""
        if not self.initialized:
            return None
        
        if not os.path.exists(image_path):
            print(f"[ERROR] Image file not found: {image_path}")
            return None
        
        try:
            # Load image file
            image = self.skia.Image.open(image_path)
            if not image:
                print(f"[ERROR] Failed to load image file: {image_path}")
                return None
            
            # Create surface for rendering
            surface = self.skia.Surface(size, size)
            canvas = surface.getCanvas()
            canvas.clear(self.skia.Color4f(0, 0, 0, 0))
            
            # Calculate scaling to fit in container
            img_width = image.width()
            img_height = image.height()
            scale = min(size / img_width, size / img_height)
            
            # Calculate position to center
            scaled_width = img_width * scale
            scaled_height = img_height * scale
            x = (size - scaled_width) / 2
            y = (size - scaled_height) / 2
            
            # Draw image
            dest_rect = self.skia.Rect.MakeXYWH(x, y, scaled_width, scaled_height)
            canvas.drawImageRect(image, dest_rect, self.skia.SamplingOptions(), self.skia.Paint())
            
            # Get result as PNG data and convert to QPixmap
            snapshot = surface.makeImageSnapshot()
            png_data = snapshot.encodeToData()
            pixmap = self.create_pixmap_from_data(png_data)
            
            if not pixmap:
                return None
            
            return QIcon(pixmap)
            
        except Exception:
            return None
    
    def render_svg_file(self, svg_path, size):
        """Render SVG file using Skia"""
        if not self.initialized:
            return None
        
        if not os.path.exists(svg_path):
            print(f"[ERROR] SVG file not found: {svg_path}")
            return None
        
        try:
            # Load SVG
            svg_stream = self.skia.FILEStream.Make(svg_path)
            if not svg_stream:
                print(f"[ERROR] Failed to open SVG file: {svg_path}")
                return None
            
            svg_dom = self.skia.SVGDOM.MakeFromStream(svg_stream)
            if not svg_dom:
                print(f"[ERROR] Failed to parse SVG file: {svg_path}")
                return None
            
            # Set container size for SVG
            svg_dom.setContainerSize(self.skia.Size(size, size))
            
            # Create surface
            surface = self.skia.Surface(size, size)
            canvas = surface.getCanvas()
            canvas.clear(self.skia.Color4f(0, 0, 0, 0))
            
            # Render SVG
            svg_dom.render(canvas)
            
            # Get result as PNG data and convert to QPixmap
            snapshot = surface.makeImageSnapshot()
            png_data = snapshot.encodeToData()
            pixmap = self.create_pixmap_from_data(png_data)
            
            if not pixmap:
                return None
            
            return QIcon(pixmap)
            
        except Exception:
            return None
    
    def render_emoji_to_pixmap(self, emoji, font_path, size, is_monochrome=False, monochrome_color=(0, 0, 0, 255)):
        """Render emoji using Skia directly in memory (supports both COLR and monochrome TTF)
        
        Args:
            emoji: The emoji character to render
            font_path: Path to the font file
            size: Size of the output image
            is_monochrome: If True, render with a solid color (for monochrome TTF fonts)
            monochrome_color: RGBA tuple for monochrome rendering (default: black)
        """
        if not self.initialized:
            return None
        
        if not os.path.exists(font_path):
            print(f"[ERROR] Font file not found: {font_path}")
            return None
        
        try:
            # Load the font
            typeface = self.skia.Typeface.MakeFromFile(font_path)
            if not typeface:
                print(f"[ERROR] Failed to load font file: {font_path}")
                return None
            
            # Create a font with the desired size (slightly larger for better rendering)
            font_size = int(size * 0.9)
            font = self.skia.Font(typeface, font_size)
            font.setEdging(self.skia.Font.Edging.kAntiAlias)
            font.setSubpixel(True)
            
            # Create a surface for rendering
            surface = self.skia.Surface(size, size)
            canvas = surface.getCanvas()
            
            # Clear with transparent background
            canvas.clear(self.skia.Color4f(0, 0, 0, 0))
            
            # Measure text to center it
            text_width = font.measureText(emoji)
            
            # Get font metrics for vertical positioning
            metrics = font.getMetrics()
            
            # Calculate position to center the emoji horizontally
            x = (size - text_width) / 2
            
            # Calculate position to center the emoji vertically
            # The baseline should be positioned so the visual center is at size/2
            text_height = metrics.fDescent - metrics.fAscent  # Total height of the font
            y = size / 2 - metrics.fAscent - text_height / 2
            
            # Create paint for text
            paint = self.skia.Paint()
            paint.setAntiAlias(True)
            
            if is_monochrome:
                # For monochrome fonts, use the specified color
                r, g, b, a = monochrome_color
                paint.setColor(self.skia.Color4f(r/255.0, g/255.0, b/255.0, a/255.0))
            else:
                # For COLR fonts, use white (will be overridden by COLR data)
                paint.setColor(self.skia.Color4f(1, 1, 1, 1))
            
            # Draw the text
            canvas.drawSimpleText(emoji, x, y, font, paint)
            
            # Get the image from surface and convert to QPixmap
            image = surface.makeImageSnapshot()
            png_data = image.encodeToData()
            pixmap = self.create_pixmap_from_data(png_data)
            
            if not pixmap:
                return None
            
            return QIcon(pixmap)
            
        except Exception:
            return None


# Global Skia renderer instance (singleton pattern)
skia_renderer_instance = None


def get_skia_renderer():
    """Get the global Skia renderer instance (singleton)"""
    global skia_renderer_instance
    
    if skia_renderer_instance is None and SKIA_AVAILABLE:
        try:
            skia_renderer_instance = SkiaRenderer()
        except Exception as e:
            skia_renderer_instance = None
            print(f"[ERROR] Failed to initialize Skia renderer: {e}")
    
    return skia_renderer_instance

