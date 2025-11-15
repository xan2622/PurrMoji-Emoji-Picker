#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Hotkeys Dialog for PurrMoji Emoji Picker
Displays keyboard shortcuts available in the application.
"""

import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from managers import ThemeManager, PathManager
from ui.base_dialog import ThemedDialogMixin


class HotkeysDialog(ThemedDialogMixin, QDialog):
    """Custom Hotkeys dialog with native Qt widgets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys")
        self.setFixedSize(650, 385)
        
        # Get PathManager from parent or create new instance
        if parent and hasattr(parent, 'path_manager'):
            self.path_manager = parent.path_manager
        else:
            self.path_manager = PathManager()
        
        # Set window icon
        icon_path = self.path_manager.get_misc_file("Kitty-Head.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Remove the "?" help button from the title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Get current theme from parent
        self.current_theme = 'Light'
        if parent and hasattr(parent, 'data_manager'):
            self.current_theme = parent.data_manager.theme
        
        # Get custom color for category/subcategory
        category_subcategory_color = '#5555ff'
        if parent and hasattr(parent, 'category_subcategory_color'):
            category_subcategory_color = parent.category_subcategory_color
        
        # Apply theme to this dialog
        self.setStyleSheet(ThemeManager.get_dialog_stylesheet(self.current_theme, category_subcategory_color))
        
        # Set Windows titlebar theme with custom colors
        self.set_windows_titlebar_theme(self.current_theme)
        
        # Center the dialog on the screen
        self.center_on_screen()
        
        # Get optimal link color based on theme for readability
        link_color = ThemeManager.get_link_color(self.current_theme)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Keyboard Shortcuts")
        title_font = QFont("Segoe UI", 12, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {link_color}; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Shortcuts list
        shortcuts = [
            ("Double-click on emoji", "Copy emoji to clipboard"),
            ("Shift + Left Click on emoji", "Add/Remove emoji to/from favorites"),
            ("Ctrl + Wheel Up/Down", "Increase/Decrease emoji size in grid"),
            ("Numpad +", "Increase emoji size in grid"),
            ("Numpad -", "Decrease emoji size in grid"),
            ("Page Up", "Navigate to previous package in the dropdown"),
            ("Page Down", "Navigate to next package in the dropdown"),
            ("T", "Cycle through themes (Light → Medium → Dark)")
        ]
        
        # Calculate maximum width needed for shortcuts column to align all colons
        font = QFont("Segoe UI", 10, QFont.Bold)
        font_metrics = QFontMetrics(font)
        max_shortcut_width = 0
        for key_combo, _ in shortcuts:
            # Measure text width without HTML tags (bold doesn't change width)
            width = font_metrics.horizontalAdvance(key_combo)
            if width > max_shortcut_width:
                max_shortcut_width = width
        
        # Add some padding for the colon and spacing
        shortcut_column_width = max_shortcut_width + 20
        
        for key_combo, description in shortcuts:
            shortcut_layout = QHBoxLayout()
            shortcut_layout.setSpacing(0)
            
            key_label = QLabel(f"<b>{key_combo}</b>")
            key_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            key_label.setFixedWidth(shortcut_column_width)
            key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            shortcut_layout.addWidget(key_label)
            
            desc_label = QLabel(f" : {description}")  # Extra space after colon
            desc_label.setFont(QFont("Segoe UI", 10))
            shortcut_layout.addWidget(desc_label)
            
            shortcut_layout.addStretch()
            
            layout.addLayout(shortcut_layout)
        
        layout.addStretch()
        
        # Add OK button
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

