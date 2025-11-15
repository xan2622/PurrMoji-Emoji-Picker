#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Managers package for PurrMoji Emoji Picker
Provides modular components for path management, data persistence, caching, and emoji operations.
"""

from .path_manager import PathManager
from .data_manager import DataManager
from .cache_manager import CacheManager
from .emoji_manager import EmojiManager
from .package_manager import PackageManager
from .package_initializer import PackageInitializer
from .theme_manager import ThemeManager
from .zip_extractor import ZipExtractor

__all__ = [
    'PathManager',
    'DataManager',
    'CacheManager',
    'EmojiManager',
    'PackageManager',
    'PackageInitializer',
    'ThemeManager',
    'ZipExtractor'
]

