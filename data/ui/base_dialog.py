#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Base Dialog Class - Provides themed title bar functionality for all dialogs
"""

import platform
import ctypes
from PyQt5.QtWidgets import QDialog, QColorDialog, QApplication
from PyQt5.QtCore import Qt
from managers import ThemeManager


class ThemedDialogMixin:
    """Mixin class that adds themed title bar support to dialogs"""
    
    def set_windows_titlebar_theme(self, theme, has_focus=True):
        """Set Windows title bar to dark or light mode with custom colors
        
        Args:
            theme: Theme name ('Light', 'Medium', or 'Dark')
            has_focus: Whether the window currently has focus (True = lighter, False = darker)
        
        Note:
            Only works on Windows 10 (build 17763+) and Windows 11
            Custom titlebar colors only work on Windows 11 build 22000+
        """
        if platform.system() != 'Windows':
            return
        
        try:
            # Get the window handle
            hwnd = int(self.winId())
            
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (Windows 10 build 19041+)
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 19 (Windows 10 build 17763-19041)
            # DWMWA_CAPTION_COLOR = 35 (Windows 11 build 22000+)
            # DWMWA_TEXT_COLOR = 36 (Windows 11 build 22000+)
            DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            DWMWA_CAPTION_COLOR = 35
            DWMWA_TEXT_COLOR = 36
            
            # Set to dark mode if theme is Dark or Medium, light mode for Light
            use_dark_mode = 1 if theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM] else 0
            
            # Try the newer attribute first (Windows 10 20H1+)
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_USE_IMMERSIVE_DARK_MODE,
                    ctypes.byref(ctypes.c_int(use_dark_mode)),
                    ctypes.sizeof(ctypes.c_int)
                )
            except (OSError, AttributeError):
                # Fall back to the older attribute (Windows 10 1809-2004)
                try:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd,
                        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                        ctypes.byref(ctypes.c_int(use_dark_mode)),
                        ctypes.sizeof(ctypes.c_int)
                    )
                except (OSError, AttributeError):
                    pass
            
            # Set custom titlebar colors for Windows 11
            try:
                # Color format: 0x00BBGGRR (BGR order, not RGB)
                if theme == ThemeManager.THEME_DARK:
                    # Dark theme colors (same as defined in main window)
                    if has_focus:
                        titlebar_color = 0x002B2B2B  # #2B2B2B in BGR when focused
                    else:
                        titlebar_color = 0x00202020  # #202020 in BGR when not focused
                    text_color = 0x00FFFFFF  # White text
                elif theme == ThemeManager.THEME_MEDIUM:
                    # Medium theme colors
                    if has_focus:
                        titlebar_color = 0x006e6e6e  # #6e6e6e in BGR when focused
                    else:
                        titlebar_color = 0x005a5a5a  # #5a5a5a in BGR when not focused (matches BG_PRIMARY)
                    text_color = 0x00FFFFFF  # White text
                else:
                    # Light theme colors
                    if has_focus:
                        titlebar_color = 0x00FFFFFF  # White when focused
                    else:
                        titlebar_color = 0x00F3F3F3  # Light gray when not focused
                    
                    # Use default black text color in light mode (no need to set explicitly)
                    text_color = 0x00000000  # Black in BGR format
                
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_CAPTION_COLOR,
                    ctypes.byref(ctypes.c_int(titlebar_color)),
                    ctypes.sizeof(ctypes.c_int)
                )
                
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    DWMWA_TEXT_COLOR,
                    ctypes.byref(ctypes.c_int(text_color)),
                    ctypes.sizeof(ctypes.c_int)
                )
            except (OSError, AttributeError):
                # Windows 11 API not available (Windows 10 or older)
                pass
        except (OSError, AttributeError):
            # Silently fail if the API is not available
            pass
    
    def changeEvent(self, event):
        """Handle window state changes (focus gain/loss)"""
        if event.type() == event.ActivationChange:
            # Update titlebar color based on focus state (for both Dark and Light themes)
            if hasattr(self, 'current_theme'):
                self.set_windows_titlebar_theme(self.current_theme, self.isActiveWindow())
        super().changeEvent(event)
    
    def center_on_screen(self):
        """Center the dialog on the screen"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )


class ThemedColorDialog(ThemedDialogMixin, QColorDialog):
    """Custom QColorDialog with themed title bar support"""
    
    def __init__(self, initial_color, parent=None, title="Choose color"):
        """Initialize the themed color dialog
        
        Args:
            initial_color: QColor object for initial color
            parent: Parent widget
            title: Dialog title
        """
        super().__init__(initial_color, parent)
        
        self.setWindowTitle(title)
        
        # Get current theme from parent
        self.current_theme = 'Light'
        if parent and hasattr(parent, 'current_theme'):
            self.current_theme = parent.current_theme
        elif parent and hasattr(parent, 'data_manager'):
            self.current_theme = parent.data_manager.theme
        
        # Apply theme stylesheet to the color dialog
        self.setStyleSheet(ThemeManager.get_dialog_stylesheet(self.current_theme))
        
        # Set Windows titlebar theme with custom colors
        self.set_windows_titlebar_theme(self.current_theme)

