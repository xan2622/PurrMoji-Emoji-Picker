#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
UI package for PurrMoji Emoji Picker
Contains all user interface components (dialogs and main window).
"""

from .about_dialog import AboutDialog
from .hotkeys_dialog import HotkeysDialog
from .settings_dialog import SettingsDialog
from .mainwindow_dialog import EmojiPicker
from .event_handlers import DoubleClickButton, EmojiScrollArea
from .base_dialog import ThemedColorDialog, ThemedDialogMixin
from .extraction_dialog import ExtractionDialog

__all__ = [
    'AboutDialog',
    'HotkeysDialog',
    'SettingsDialog',
    'EmojiPicker',
    'DoubleClickButton',
    'EmojiScrollArea',
    'ThemedColorDialog',
    'ThemedDialogMixin',
    'ExtractionDialog',
]

