#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
PathManager - Centralized path management for emoji packages
"""

import os
import sys
import platform


class PathManager:
    """Centralized path management for emoji packages and resources"""
    
    def __init__(self):
        """Initialize base directories"""
        # Detect if running as PyInstaller executable
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            # Get the directory where the .exe is located
            exe_dir = os.path.dirname(sys.executable)
            # Check if data folder exists (our custom structure)
            data_dir = os.path.join(exe_dir, "data")
            if os.path.exists(data_dir):
                self.base_dir = data_dir
            else:
                # Fallback to PyInstaller's _MEIPASS if data doesn't exist
                self.base_dir = getattr(sys, '_MEIPASS', exe_dir)
        else:
            # Running as script
            self.base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Emoji packages are now stored in user directory (for extracted packages)
        self.packages_dir = self.get_user_packages_dir()
        
        # Source packages directory (for non-ZIP packages like Noto and Custom)
        self.source_packages_dir = os.path.join(self.base_dir, "emoji_packages")
    
    def get_user_packages_dir(self):
        """Get the user directory where packages are extracted
        
        Returns:
            str: Path to user emoji packages directory
        """
        system = platform.system()
        
        if system == "Windows":
            # %APPDATA%/PurrMoji/emoji_packages/
            base_dir = os.environ.get('APPDATA')
            if not base_dir:
                base_dir = os.path.expanduser('~\\AppData\\Roaming')
        elif system == "Darwin":  # macOS
            # ~/Library/Application Support/PurrMoji/emoji_packages/
            base_dir = os.path.expanduser('~/Library/Application Support')
        else:  # Linux and others
            # ~/.local/share/PurrMoji/emoji_packages/
            base_dir = os.environ.get('XDG_DATA_HOME')
            if not base_dir:
                base_dir = os.path.expanduser('~/.local/share')
        
        packages_dir = os.path.join(base_dir, 'PurrMoji', 'emoji_packages')
        os.makedirs(packages_dir, exist_ok=True)
        return packages_dir
    
    def join(self, *parts):
        """Helper to join paths from packages directory"""
        return os.path.join(self.packages_dir, *parts)
    
    # OpenMoji paths
    def get_openmoji_path(self, color_mode, format_type, size=None):
        """Get OpenMoji package path dynamically
        
        Args:
            color_mode: "color" or "black"
            format_type: "png", "svg", or "ttf"
            size: Optional size for PNG (72, 618)
        
        Returns:
            str: Path to the requested OpenMoji package
        """
        if format_type == "png":
            # PNG files are in openmoji-master/color/618x618 or openmoji-master/black/72x72
            size_folder = f"{size}x{size}" if size else "72x72"
            return self.join("OpenMoji", "openmoji-master", color_mode, size_folder)
        elif format_type == "svg":
            # SVG files are in openmoji-master/color/svg or openmoji-master/black/svg
            return self.join("OpenMoji", "openmoji-master", color_mode, "svg")
        elif format_type == "ttf":
            # TTF fonts are in openmoji-master/font/...
            if color_mode == "color":
                return self.join("OpenMoji", "openmoji-master", "font", "OpenMoji-color-glyf_colr_0")
            else:
                return self.join("OpenMoji", "openmoji-master", "font", "OpenMoji-black-glyf")
        return None
    
    # Noto paths
    def get_noto_path(self, color_mode):
        """Get Noto font file path
        
        Args:
            color_mode: "color" or "black"
        
        Returns:
            str: Path to the Noto font file
        """
        # Noto fonts are now copied to user directory
        if color_mode == "color":
            return self.join("Noto", "NotoColorEmoji-Regular.ttf")
        else:
            return self.join("Noto", "NotoEmoji-VariableFont_wght.ttf")
    
    # Twemoji paths
    def get_twemoji_path(self, format_type):
        """Get Twemoji package path
        
        Args:
            format_type: "png" or "svg"
        
        Returns:
            str: Path to the Twemoji package
        """
        if format_type == "png":
            return self.join("Twemoji", "twemoji-14.0.2", "assets", "72x72")
        else:
            return self.join("Twemoji", "twemoji-14.0.2", "assets", "svg")
    
    # EmojiTwo paths
    def get_emojitwo_path(self, color_mode, format_type, size=None):
        """Get EmojiTwo package path
        
        Args:
            color_mode: "color" or "black"
            format_type: "png" or "svg"
            size: Optional size for PNG (16, 32, 48, 64, 72, 96, 128, 512)
        
        Returns:
            str: Path to the EmojiTwo package
        """
        if format_type == "png":
            base_folder = "png" if color_mode == "color" else "png_bw"
            if size:
                return self.join("Emojitwo", "emojitwo-master", base_folder, str(size))
            else:
                return self.join("Emojitwo", "emojitwo-master", base_folder)
        else:  # SVG
            return self.join("Emojitwo", "emojitwo-master", "svg" if color_mode == "color" else "svg_bw")
    
    # Custom paths
    def get_custom_path(self):
        """Get custom emoji folder path
        
        Returns:
            str: Path to the custom emoji folder
        """
        # Custom folder remains in source directory
        return os.path.join(self.source_packages_dir, "custom")
    
    # Resource paths
    def get_emoji_data_file(self):
        """Get emoji data JSON file path
        
        Returns:
            str: Path to emoji_data.json
        """
        return os.path.join(self.base_dir, "emoji_data.json")
    
    def get_misc_file(self, filename):
        """Get misc file path
        
        Args:
            filename: Name of the file in misc folder
        
        Returns:
            str: Path to the requested misc file
        """
        return os.path.join(self.base_dir, "misc", filename)
    
    # Unified path getter
    def get_package_path(self, package_name, color_mode, format_type, size=None):
        """Unified method to get package path for any emoji package
        
        Args:
            package_name: Name of the package (e.g., "OpenMoji", "Noto", etc.)
            color_mode: "color" or "black"
            format_type: "png", "svg", or "ttf"
            size: Optional size for packages that support it
        
        Returns:
            str: Path to the requested package or None if invalid
        """
        package_name = package_name.lower()
        
        handlers = {
            "openmoji": lambda: self.get_openmoji_path(color_mode, format_type, size),
            "noto": lambda: self.get_noto_path(color_mode),
            "twemoji": lambda: self.get_twemoji_path(format_type),
            "emojitwo": lambda: self.get_emojitwo_path(color_mode, format_type, size),
            "custom": lambda: self.get_custom_path()
        }
        
        handler = handlers.get(package_name)
        return handler() if handler else None
    
    # Build complete folder structure (for backward compatibility)
    def build_all_paths(self):
        """Build complete emoji_folders dictionary for backward compatibility
        
        Returns:
            dict: Complete dictionary of all emoji folder paths
        """
        return {
            # OpenMoji PNG folders
            "color_72_png": self.get_openmoji_path("color", "png", 72),
            "black_72_png": self.get_openmoji_path("black", "png", 72),
            "color_618_png": self.get_openmoji_path("color", "png", 618),
            "black_618_png": self.get_openmoji_path("black", "png", 618),
            
            # OpenMoji SVG folders
            "color_svg": self.get_openmoji_path("color", "svg"),
            "black_svg": self.get_openmoji_path("black", "svg"),
            
            # OpenMoji TTF font folders
            "openmoji_color_ttf_folder": self.get_openmoji_path("color", "ttf"),
            "openmoji_black_ttf_folder": self.get_openmoji_path("black", "ttf"),
            
            # Noto TTF font files
            "google_noto_color_ttf": self.get_noto_path("color"),
            "google_noto_black_ttf": self.get_noto_path("black"),
            
            # Twemoji folders
            "twemoji_72_png": self.get_twemoji_path("png"),
            "twemoji_svg": self.get_twemoji_path("svg"),
            
            # Emojitwo PNG folders (with size subdirectories)
            "emojitwo_color_16_png": self.get_emojitwo_path("color", "png", 16),
            "emojitwo_color_32_png": self.get_emojitwo_path("color", "png", 32),
            "emojitwo_color_48_png": self.get_emojitwo_path("color", "png", 48),
            "emojitwo_color_64_png": self.get_emojitwo_path("color", "png", 64),
            "emojitwo_color_72_png": self.get_emojitwo_path("color", "png", 72),
            "emojitwo_color_96_png": self.get_emojitwo_path("color", "png", 96),
            "emojitwo_color_128_png": self.get_emojitwo_path("color", "png", 128),
            "emojitwo_color_512_png": self.get_emojitwo_path("color", "png", 512),
            "emojitwo_color_default_png": self.get_emojitwo_path("color", "png"),
            
            "emojitwo_black_16_png": self.get_emojitwo_path("black", "png", 16),
            "emojitwo_black_32_png": self.get_emojitwo_path("black", "png", 32),
            "emojitwo_black_48_png": self.get_emojitwo_path("black", "png", 48),
            "emojitwo_black_64_png": self.get_emojitwo_path("black", "png", 64),
            "emojitwo_black_72_png": self.get_emojitwo_path("black", "png", 72),
            "emojitwo_black_96_png": self.get_emojitwo_path("black", "png", 96),
            "emojitwo_black_128_png": self.get_emojitwo_path("black", "png", 128),
            "emojitwo_black_512_png": self.get_emojitwo_path("black", "png", 512),
            "emojitwo_black_default_png": self.get_emojitwo_path("black", "png"),
            
            # Emojitwo SVG folders
            "emojitwo_color_svg": self.get_emojitwo_path("color", "svg"),
            "emojitwo_black_svg": self.get_emojitwo_path("black", "svg"),
        }
    
    def get_path(self, key: str) -> str:
        """Get a path by its key from the paths dictionary
        
        Args:
            key: The path key (e.g., 'emojitwo_color_72_png', 'google_noto_color_ttf')
            
        Returns:
            The full path corresponding to the key
            
        Raises:
            KeyError: If the key doesn't exist in the paths dictionary
        """
        paths = self.build_all_paths()
        if key not in paths:
            raise KeyError(f"Path key '{key}' not found. Available keys: {list(paths.keys())}")
        return paths[key]

