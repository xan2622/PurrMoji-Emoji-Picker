#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
PackageManager - Centralized emoji package configuration management
"""


class PackageManager:
    """Manages emoji package configurations and capabilities"""
    
    def __init__(self, path_manager):
        """Initialize package manager
        
        Args:
            path_manager: PathManager instance for accessing paths
        """
        self.path_manager = path_manager
        self.packages = self.build_package_configs()
        
        # Display detected packages
        detected_packages = list(self.packages.keys())
        print(f"Detected emoji packages: {', '.join(detected_packages)}")
    
    def build_package_configs(self):
        """Build configuration for all emoji packages
        
        Returns:
            dict: Package configurations
        """
        emoji_folders = self.path_manager.build_all_paths()
        
        return {
            "Custom": {
                "type": "custom",
                "folder": self.path_manager.get_custom_path(),
                "supports_color": False,
                "supports_formats": ["png", "svg", "ttf"],  # Dynamic detection needed
                "supports_sizes": False
            },
            "EmojiTwo": {
                "type": "files",
                "folders": {
                    # PNG folders with different sizes
                    "color_16_png": emoji_folders["emojitwo_color_16_png"],
                    "color_32_png": emoji_folders["emojitwo_color_32_png"],
                    "color_48_png": emoji_folders["emojitwo_color_48_png"],
                    "color_64_png": emoji_folders["emojitwo_color_64_png"],
                    "color_72_png": emoji_folders["emojitwo_color_72_png"],
                    "color_96_png": emoji_folders["emojitwo_color_96_png"],
                    "color_128_png": emoji_folders["emojitwo_color_128_png"],
                    "color_512_png": emoji_folders["emojitwo_color_512_png"],
                    "color_default_png": emoji_folders["emojitwo_color_default_png"],
                    "black_16_png": emoji_folders["emojitwo_black_16_png"],
                    "black_32_png": emoji_folders["emojitwo_black_32_png"],
                    "black_48_png": emoji_folders["emojitwo_black_48_png"],
                    "black_64_png": emoji_folders["emojitwo_black_64_png"],
                    "black_72_png": emoji_folders["emojitwo_black_72_png"],
                    "black_96_png": emoji_folders["emojitwo_black_96_png"],
                    "black_128_png": emoji_folders["emojitwo_black_128_png"],
                    "black_512_png": emoji_folders["emojitwo_black_512_png"],
                    "black_default_png": emoji_folders["emojitwo_black_default_png"],
                    # SVG folders
                    "color_svg": emoji_folders["emojitwo_color_svg"],
                    "black_svg": emoji_folders["emojitwo_black_svg"]
                },
                "supports_color": True,
                "supports_formats": ["png", "svg"],
                "supports_sizes": False,  # Uses dynamic size folders
                "available_sizes": [16, 32, 48, 64, 72, 96, 128, 512]
            },
            "Noto": {
                "type": "ttf_font",
                "color_font": emoji_folders["google_noto_color_ttf"],
                "black_font": emoji_folders["google_noto_black_ttf"],
                "supports_color": True,
                "supports_formats": ["ttf"],
                "supports_sizes": False
            },
            "OpenMoji": {
                "type": "files",
                "folders": emoji_folders,
                "supports_color": True,
                "supports_formats": ["png", "svg", "ttf"],
                "supports_sizes": True,
                "available_sizes": [72, 618]
            },
            "Segoe UI Emoji": {
                "type": "system_font",
                "font_name": "Segoe UI Emoji",
                "supports_color": False,  # Only color mode available
                "supports_formats": ["ttf"],
                "supports_sizes": False
            },
            "Twemoji": {
                "type": "files",
                "folders": {
                    "png_72": emoji_folders["twemoji_72_png"],
                    "svg": emoji_folders["twemoji_svg"]
                },
                "supports_color": False,  # Always colored
                "supports_formats": ["png", "svg"],
                "supports_sizes": False,
                "available_sizes": [72]
            },
            "Kaomoji": {
                "type": "kaomoji",
                "supports_color": False,
                "supports_formats": [],
                "supports_sizes": False
            }
        }
    
    def get_package_config(self, package_name):
        """Get configuration for a specific package
        
        Args:
            package_name: Name of the package
        
        Returns:
            dict: Package configuration or None if not found
        """
        return self.packages.get(package_name)
    
    def get_package_type(self, package_name):
        """Get the type of a package
        
        Args:
            package_name: Name of the package
        
        Returns:
            str: Package type or None
        """
        config = self.get_package_config(package_name)
        return config.get("type") if config else None
    
    def supports_color_variants(self, package_name):
        """Check if package supports color/black variants
        
        Args:
            package_name: Name of the package
        
        Returns:
            bool: True if package supports color variants
        """
        config = self.get_package_config(package_name)
        return config.get("supports_color", False) if config else False
    
    def get_supported_formats(self, package_name):
        """Get supported formats for a package
        
        Args:
            package_name: Name of the package
        
        Returns:
            list: List of supported formats (e.g., ["png", "svg", "ttf"])
        """
        config = self.get_package_config(package_name)
        return config.get("supports_formats", []) if config else []
    
    def supports_size_selection(self, package_name):
        """Check if package supports size selection (72px/618px)
        
        Args:
            package_name: Name of the package
        
        Returns:
            bool: True if package supports size selection
        """
        config = self.get_package_config(package_name)
        return config.get("supports_sizes", False) if config else False
    
    def get_available_sizes(self, package_name):
        """Get available sizes for a package
        
        Args:
            package_name: Name of the package
        
        Returns:
            list: List of available sizes or empty list
        """
        config = self.get_package_config(package_name)
        return config.get("available_sizes", []) if config else []
    
    def get_package_folder(self, package_name, color_mode, format_type, size=None):
        """Get the appropriate folder for a package configuration
        
        Args:
            package_name: Name of the package
            color_mode: "color" or "black"
            format_type: "png", "svg", or "ttf"
            size: Optional size parameter
        
        Returns:
            str: Path to the package folder or None
        """
        config = self.get_package_config(package_name)
        if not config:
            return None
        
        package_type = config.get("type")
        
        if package_type == "custom":
            return config.get("folder")
        
        elif package_type == "system_font":
            return None  # System fonts don't have folders
        
        elif package_type == "ttf_font":
            # Return font file path based on color mode
            if color_mode == "color":
                return config.get("color_font")
            else:
                return config.get("black_font")
        
        elif package_type == "files":
            # Use PathManager to get the appropriate path
            return self.path_manager.get_package_path(
                package_name.lower(),
                color_mode,
                format_type,
                size
            )
        
        return None

