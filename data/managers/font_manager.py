#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Font Manager for PurrMoji Emoji Picker
Provides cross-platform font handling with OS-specific adjustments.
"""

import platform
from PyQt5.QtGui import QFont


class FontManager:
    """Manages fonts with cross-platform adjustments for consistent UI appearance"""
    
    # OS detection
    _platform = platform.system()
    IS_WINDOWS = _platform == 'Windows'
    IS_LINUX = _platform == 'Linux'
    IS_MACOS = _platform == 'Darwin'
    
    # Font size adjustments for different platforms
    # Linux fonts tend to render smaller, so we increase by 2 points
    _LINUX_SIZE_ADJUSTMENT = 2
    
    # Universal font family available on all major operating systems
    _DEFAULT_FONT = "Arial"
    
    @classmethod
    def get_font_family(cls):
        """
        Get Arial as the font family - available on Windows, macOS, and most Linux distributions.
        
        Returns:
            str: "Arial" - universal font family
        """
        return cls._DEFAULT_FONT
    
    @classmethod
    def adjust_font_size(cls, base_size):
        """
        Adjust font size for the current platform to ensure consistent visual appearance.
        
        Args:
            base_size (int): Base font size in points (designed for Windows)
            
        Returns:
            int: Adjusted font size for the current platform
        """
        if cls.IS_LINUX:
            return base_size + cls._LINUX_SIZE_ADJUSTMENT
        else:
            return base_size
    
    @classmethod
    def get_font(cls, base_size, weight=QFont.Normal):
        """
        Create a QFont with platform-specific adjustments.
        
        Args:
            base_size (int): Base font size in points (designed for Windows)
            weight (QFont.Weight): Font weight (QFont.Normal, QFont.Bold, etc.)
            
        Returns:
            QFont: Configured font with platform adjustments
        """
        family = cls.get_font_family()
        size = cls.adjust_font_size(base_size)
        return QFont(family, size, weight)
    
    @classmethod
    def get_font_family_and_size(cls, base_size):
        """
        Get font family and adjusted size as a tuple.
        Useful for code that manually creates QFont objects.
        
        Args:
            base_size (int): Base font size in points (designed for Windows)
            
        Returns:
            tuple: (font_family, adjusted_size)
        """
        return cls.get_font_family(), cls.adjust_font_size(base_size)

