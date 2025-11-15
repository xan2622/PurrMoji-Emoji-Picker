#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Settings Dialog for PurrMoji Emoji Picker
Allows users to configure which settings should persist between sessions.
"""

import sys
import os
import subprocess
import platform
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QCheckBox, QLabel, QApplication, QComboBox, QStyle, QStyleOptionButton, QFrame)
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter, QPen
from managers import ThemeManager, PathManager
from ui.base_dialog import ThemedColorDialog, ThemedDialogMixin


class CheckBoxWithCheckmark(QCheckBox):
    """Custom QCheckBox that draws a visible checkmark when checked with adaptive color"""
    
    def __init__(self, text, theme, background_color='#5555ff', parent=None):
        super().__init__(text, parent)
        self.current_theme = theme
        self.background_color = background_color
        self.update_checkmark_color()
    
    def update_checkmark_color(self):
        """Calculate optimal checkmark color based on background color"""
        self.checkmark_color = ThemeManager.get_text_color_for_background(self.background_color)
    
    def set_background_color(self, color):
        """Update background color and recalculate checkmark color"""
        self.background_color = color
        self.update_checkmark_color()
        self.update()
    
    def paintEvent(self, event):
        """Override paint event to draw checkmark manually with adaptive color"""
        # Call parent to draw the base checkbox
        super().paintEvent(event)
        
        # Draw custom checkmark when checked
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Get the checkbox indicator rectangle
            opt = QStyleOptionButton()
            self.initStyleOption(opt)
            indicator_rect = self.style().subElementRect(QStyle.SE_CheckBoxIndicator, opt, self)
            
            # Draw checkmark with adaptive color for optimal contrast
            checkmark_qcolor = QColor(self.checkmark_color)
            pen = QPen(checkmark_qcolor, 2)
            painter.setPen(pen)
            
            # Draw checkmark (✓) using lines
            center_x = indicator_rect.center().x()
            center_y = indicator_rect.center().y()
            
            # Short line (bottom left to middle)
            painter.drawLine(
                center_x - 4, center_y,
                center_x - 1, center_y + 3
            )
            # Long line (middle to top right)
            painter.drawLine(
                center_x - 1, center_y + 3,
                center_x + 5, center_y - 4
            )
            
            painter.end()
    
    def set_theme(self, theme):
        """Update theme and trigger repaint"""
        self.current_theme = theme
        self.update()


class SettingsDialog(ThemedDialogMixin, QDialog):
    """Settings dialog to configure which settings should be saved between sessions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Settings")
        
        # Get PathManager from parent or create new instance
        if parent and hasattr(parent, 'path_manager'):
            self.path_manager = parent.path_manager
        else:
            self.path_manager = PathManager()
        
        # Remove the "?" button from the title bar and set proper dialog flags
        self.setWindowFlags(
            self.windowFlags() & 
            ~Qt.WindowContextHelpButtonHint | 
            Qt.MSWindowsFixedSizeDialogHint
        )
        
        self.setFixedSize(900, 620)
        
        # Set window icon
        icon_path = self.path_manager.get_misc_file("Kitty-Head.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Get current theme and store initial theme for cancel operation
        self.current_theme = 'Light'
        if hasattr(self.parent_window, 'data_manager'):
            self.current_theme = self.parent_window.data_manager.theme
        self.initial_theme = self.current_theme  # Store initial theme
        
        # Get custom color for category/subcategory and initialize as instance variable
        self.category_subcategory_color = '#5555ff'
        if hasattr(self.parent_window, 'category_subcategory_color'):
            self.category_subcategory_color = self.parent_window.category_subcategory_color
        
        # Apply theme to this dialog
        self.setStyleSheet(ThemeManager.get_dialog_stylesheet(self.current_theme, self.category_subcategory_color))
        
        # Set Windows titlebar theme with custom colors
        self.set_windows_titlebar_theme(self.current_theme)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        self.setLayout(main_layout)
        
        # Create horizontal layout for two columns
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(15)
        
        # LEFT COLUMN: Save Preferences checkboxes
        left_column = QVBoxLayout()
        left_column.setSpacing(5)
        
        # Title label
        title_label = QLabel("Choose which settings should stay saved when you restart PurrMoji:")
        title_label.setWordWrap(True)
        title_label.setFont(QFont("Segoe UI", 9))
        title_label.setMinimumHeight(60)
        title_label.setStyleSheet(ThemeManager.get_settings_label_style(self.current_theme))
        left_column.addWidget(title_label)
        
        # Save Preferences section label
        save_preferences_label = QLabel("Save Preferences:")
        save_preferences_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        save_preferences_label.setStyleSheet("padding: 5px 10px;")
        left_column.addWidget(save_preferences_label)
        
        left_column.addSpacing(5)
        
        # Checkboxes
        self.checkboxes = {}
        
        checkbox_data = [
            ("last_selected_package", "Last selected package", True),
            ("emoji_variation_filter", "Emoji variation", False),
            ("color_black", "Color / Black", False),
            ("format_selection", "PNG / SVG / TTF", True),
            ("package_size", "Package Size (72 px / 618 px)", False),
            ("category_button", "Category button", True),
            ("subcategory_tab", "Sub-category tab", False),
            ("emoji_size", "Emoji size in grid", False),
            ("background_color", "Background color of grid elements", True)
        ]
        
        for key, label_text, default_checked in checkbox_data:
            checkbox = CheckBoxWithCheckmark(label_text, self.current_theme, self.category_subcategory_color)
            checkbox.setFont(QFont("Segoe UI", 9))
            checkbox.setStyleSheet("margin-left: 30px;")
            # Check if parent has save_preferences, otherwise use default
            if hasattr(self.parent_window, 'save_preferences'):
                checkbox.setChecked(self.parent_window.save_preferences.get(key, default_checked))
            else:
                checkbox.setChecked(default_checked)
            self.checkboxes[key] = checkbox
            left_column.addWidget(checkbox)
            
            # Add sub-checkboxes for background_color
            if key == "background_color":
                # Sub-checkbox for Light theme with color button
                light_layout = QHBoxLayout()
                light_layout.setSpacing(5)
                
                self.background_color_light_checkbox = CheckBoxWithCheckmark("for the Light theme", self.current_theme, self.category_subcategory_color)
                self.background_color_light_checkbox.setFont(QFont("Segoe UI", 9))
                self.background_color_light_checkbox.setStyleSheet("margin-left: 60px;")  # More indented
                if hasattr(self.parent_window, 'save_preferences'):
                    self.background_color_light_checkbox.setChecked(
                        self.parent_window.save_preferences.get('background_color_light', True)
                    )
                else:
                    self.background_color_light_checkbox.setChecked(True)
                self.background_color_light_checkbox.stateChanged.connect(self.on_background_sub_checkbox_changed)
                light_layout.addWidget(self.background_color_light_checkbox)
                
                light_layout.addStretch()
                
                # Color button for Light theme
                self.bg_color_light_button = QPushButton()
                self.bg_color_light_button.setFixedSize(25, 25)
                self.bg_color_light_button.setToolTip("Choose background color for Light theme")
                self.bg_color_light_button.clicked.connect(self.on_bg_color_light_change)
                light_layout.addWidget(self.bg_color_light_button)
                
                # Reset button for Light theme background color
                self.bg_color_light_reset_button = QPushButton("↩")
                self.bg_color_light_reset_button.setFixedSize(30, 25)
                self.bg_color_light_reset_button.setFont(QFont("Segoe UI", 12))
                self.bg_color_light_reset_button.setToolTip("Reset to default color (#ffffff)")
                self.bg_color_light_reset_button.clicked.connect(self.reset_bg_color_light)
                light_layout.addWidget(self.bg_color_light_reset_button)
                
                left_column.addLayout(light_layout)
                
                # Sub-checkbox for Medium theme with color button
                medium_layout = QHBoxLayout()
                medium_layout.setSpacing(5)
                
                self.background_color_medium_checkbox = CheckBoxWithCheckmark("for the Medium theme", self.current_theme, self.category_subcategory_color)
                self.background_color_medium_checkbox.setFont(QFont("Segoe UI", 9))
                self.background_color_medium_checkbox.setStyleSheet("margin-left: 60px;")  # More indented
                if hasattr(self.parent_window, 'save_preferences'):
                    self.background_color_medium_checkbox.setChecked(
                        self.parent_window.save_preferences.get('background_color_medium', True)
                    )
                else:
                    self.background_color_medium_checkbox.setChecked(True)
                self.background_color_medium_checkbox.stateChanged.connect(self.on_background_sub_checkbox_changed)
                medium_layout.addWidget(self.background_color_medium_checkbox)
                
                medium_layout.addStretch()
                
                # Color button for Medium theme
                self.bg_color_medium_button = QPushButton()
                self.bg_color_medium_button.setFixedSize(25, 25)
                self.bg_color_medium_button.setToolTip("Choose background color for Medium theme")
                self.bg_color_medium_button.clicked.connect(self.on_bg_color_medium_change)
                medium_layout.addWidget(self.bg_color_medium_button)
                
                # Reset button for Medium theme background color
                self.bg_color_medium_reset_button = QPushButton("↩")
                self.bg_color_medium_reset_button.setFixedSize(30, 25)
                self.bg_color_medium_reset_button.setFont(QFont("Segoe UI", 12))
                self.bg_color_medium_reset_button.setToolTip("Reset to default color (#4b4b4b)")
                self.bg_color_medium_reset_button.clicked.connect(self.reset_bg_color_medium)
                medium_layout.addWidget(self.bg_color_medium_reset_button)
                
                left_column.addLayout(medium_layout)
                
                # Sub-checkbox for Dark theme with color button
                dark_layout = QHBoxLayout()
                dark_layout.setSpacing(5)
                
                self.background_color_dark_checkbox = CheckBoxWithCheckmark("for the Dark theme", self.current_theme, self.category_subcategory_color)
                self.background_color_dark_checkbox.setFont(QFont("Segoe UI", 9))
                self.background_color_dark_checkbox.setStyleSheet("margin-left: 60px;")  # More indented
                if hasattr(self.parent_window, 'save_preferences'):
                    self.background_color_dark_checkbox.setChecked(
                        self.parent_window.save_preferences.get('background_color_dark', True)
                    )
                else:
                    self.background_color_dark_checkbox.setChecked(True)
                self.background_color_dark_checkbox.stateChanged.connect(self.on_background_sub_checkbox_changed)
                dark_layout.addWidget(self.background_color_dark_checkbox)
                
                dark_layout.addStretch()
                
                # Color button for Dark theme
                self.bg_color_dark_button = QPushButton()
                self.bg_color_dark_button.setFixedSize(25, 25)
                self.bg_color_dark_button.setToolTip("Choose background color for Dark theme")
                self.bg_color_dark_button.clicked.connect(self.on_bg_color_dark_change)
                dark_layout.addWidget(self.bg_color_dark_button)
                
                # Reset button for Dark theme background color
                self.bg_color_dark_reset_button = QPushButton("↩")
                self.bg_color_dark_reset_button.setFixedSize(30, 25)
                self.bg_color_dark_reset_button.setFont(QFont("Segoe UI", 12))
                self.bg_color_dark_reset_button.setToolTip("Reset to default color (#312829)")
                self.bg_color_dark_reset_button.clicked.connect(self.reset_bg_color_dark)
                dark_layout.addWidget(self.bg_color_dark_reset_button)
                
                left_column.addLayout(dark_layout)
                
                # Initialize color values
                if hasattr(self.parent_window, 'data_manager'):
                    self.bg_color_light = self.parent_window.data_manager.emoji_background_color_light
                    self.bg_color_medium = self.parent_window.data_manager.emoji_background_color_medium
                    self.bg_color_dark = self.parent_window.data_manager.emoji_background_color_dark
                else:
                    self.bg_color_light = '#ffffff'
                    self.bg_color_medium = '#4b4b4b'
                    self.bg_color_dark = '#312829'
                
                # Update button styles
                self.update_bg_color_button_styles()
                
                # Connect main checkbox to control sub-checkboxes
                checkbox.stateChanged.connect(self.on_background_main_checkbox_changed)
                
                # Update initial state of sub-checkboxes based on main checkbox
                self.update_background_sub_checkboxes_state()
        
        # Add stretch at the end of left column
        left_column.addStretch()
        
        # Add left column to columns layout
        columns_layout.addLayout(left_column)
        
        # VERTICAL SEPARATOR
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(2)
        separator.setStyleSheet("QFrame { color: #888888; }")
        columns_layout.addWidget(separator)
        
        # RIGHT COLUMN: Theme, Default Tab, Color Customization
        right_column = QVBoxLayout()
        right_column.setSpacing(5)
        
        # Theme selection section
        theme_section_label = QLabel("Theme:")
        theme_section_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        theme_section_label.setStyleSheet("padding: 5px 10px;")
        right_column.addWidget(theme_section_label)
        
        right_column.addSpacing(5)
        
        # Theme selection dropdown
        theme_layout = QHBoxLayout()
        theme_layout.setSpacing(5)
        
        theme_label = QLabel("Choose a theme:")
        theme_label.setFont(QFont("Segoe UI", 9))
        theme_label.setStyleSheet("margin-left: 30px;")
        theme_layout.addWidget(theme_label)
        
        theme_layout.addStretch()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(ThemeManager.AVAILABLE_THEMES)
        self.theme_combo.setFixedSize(150, 30)
        # Set same font as other dropdowns in main interface
        theme_combo_font = QFont("Segoe UI", 9)
        self.theme_combo.setFont(theme_combo_font)
        self.theme_combo.setCurrentText(self.current_theme)
        # Don't apply theme immediately - only on OK button click
        theme_layout.addWidget(self.theme_combo)
        
        right_column.addLayout(theme_layout)
        
        right_column.addSpacing(10)
        
        # Default Recent & Favorites tab section
        default_tab_section_label = QLabel("Default Tab for Recent & Favorites:")
        default_tab_section_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        default_tab_section_label.setStyleSheet("padding: 5px 10px;")
        right_column.addWidget(default_tab_section_label)
        
        right_column.addSpacing(5)
        
        # Checkbox for using last used tab
        self.use_last_used_tab_checkbox = CheckBoxWithCheckmark("Display the last used tab", self.current_theme, self.category_subcategory_color)
        self.use_last_used_tab_checkbox.setFont(QFont("Segoe UI", 9))
        self.use_last_used_tab_checkbox.setStyleSheet("margin-left: 30px;")
        if hasattr(self.parent_window, 'data_manager'):
            self.use_last_used_tab_checkbox.setChecked(self.parent_window.data_manager.use_last_used_tab)
        else:
            self.use_last_used_tab_checkbox.setChecked(True)
        self.use_last_used_tab_checkbox.stateChanged.connect(self.on_use_last_used_tab_changed)
        right_column.addWidget(self.use_last_used_tab_checkbox)
        
        right_column.addSpacing(5)
        
        # Default tab selection dropdown for Recent & Favorites category
        default_tab_layout = QHBoxLayout()
        default_tab_layout.setSpacing(5)
        
        self.default_tab_label = QLabel("Or always show this tab:")
        self.default_tab_label.setFont(QFont("Segoe UI", 9))
        self.default_tab_label.setStyleSheet("margin-left: 30px;")
        default_tab_layout.addWidget(self.default_tab_label)
        
        default_tab_layout.addStretch()
        
        self.default_tab_combo = QComboBox()
        self.default_tab_combo.addItems(["Recent", "Favorites", "Frequently used"])
        self.default_tab_combo.setFixedSize(150, 30)
        # Set same font as other dropdowns in main interface
        default_tab_combo_font = QFont("Segoe UI", 9)
        self.default_tab_combo.setFont(default_tab_combo_font)
        
        # Set current value from parent window
        if hasattr(self.parent_window, 'data_manager'):
            current_default_tab = self.parent_window.data_manager.default_recent_favorites_tab
            # Map internal values to display names
            tab_mapping = {
                'recent': 'Recent',
                'favorites': 'Favorites',
                'frequently_used': 'Frequently used'
            }
            display_name = tab_mapping.get(current_default_tab, 'Recent')
            self.default_tab_combo.setCurrentText(display_name)
        else:
            self.default_tab_combo.setCurrentText('Recent')
        
        default_tab_layout.addWidget(self.default_tab_combo)
        
        right_column.addLayout(default_tab_layout)
        
        # Update initial state of default_tab_combo based on use_last_used_tab_checkbox
        self.update_default_tab_combo_state()
        
        right_column.addSpacing(10)
        
        # Color customization section
        color_section_label = QLabel("Color Customization:")
        color_section_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        color_section_label.setStyleSheet("padding: 5px 10px;")
        right_column.addWidget(color_section_label)
        
        right_column.addSpacing(5)
        
        # Custom color for emoji selection
        emoji_selection_layout = QHBoxLayout()
        emoji_selection_layout.setSpacing(5)
        
        emoji_selection_label = QLabel("Custom color for emoji selection:")
        emoji_selection_label.setFont(QFont("Segoe UI", 9))
        emoji_selection_label.setStyleSheet("margin-left: 30px;")
        emoji_selection_layout.addWidget(emoji_selection_label)
        
        emoji_selection_layout.addStretch()
        
        self.emoji_selection_color_button = QPushButton()
        self.emoji_selection_color_button.setFixedSize(80, 25)
        self.emoji_selection_color_button.clicked.connect(self.choose_emoji_selection_color)
        emoji_selection_layout.addWidget(self.emoji_selection_color_button)
        
        # Reset button for emoji selection color
        self.emoji_selection_reset_button = QPushButton("↩")
        self.emoji_selection_reset_button.setFixedSize(30, 25)
        self.emoji_selection_reset_button.setFont(QFont("Segoe UI", 12))
        self.emoji_selection_reset_button.setToolTip("Reset to default color (#3699e7)")
        self.emoji_selection_reset_button.clicked.connect(self.reset_emoji_selection_color)
        emoji_selection_layout.addWidget(self.emoji_selection_reset_button)
        
        right_column.addLayout(emoji_selection_layout)
        
        right_column.addSpacing(5)
        
        # Custom color for category buttons, sub-category tabs, checkboxes, and dropdowns
        category_layout = QHBoxLayout()
        category_layout.setSpacing(5)
        
        category_label = QLabel("Background color for category buttons, sub-category tabs, active radio buttons, checkboxes in the Settings window, drop-down menus:")
        category_label.setFont(QFont("Segoe UI", 9))
        category_label.setWordWrap(True)
        category_label.setStyleSheet("margin-left: 30px;")
        category_label.setMaximumWidth(500)
        category_layout.addWidget(category_label)
        
        category_layout.addStretch()
        
        self.category_subcategory_color_button = QPushButton()
        self.category_subcategory_color_button.setFixedSize(80, 25)
        self.category_subcategory_color_button.clicked.connect(self.choose_category_subcategory_color)
        category_layout.addWidget(self.category_subcategory_color_button)
        
        # Reset button for category/subcategory color
        self.category_subcategory_reset_button = QPushButton("↩")
        self.category_subcategory_reset_button.setFixedSize(30, 25)
        self.category_subcategory_reset_button.setFont(QFont("Segoe UI", 12))
        self.category_subcategory_reset_button.setToolTip("Reset to default color (#5555ff)")
        self.category_subcategory_reset_button.clicked.connect(self.reset_category_subcategory_color)
        category_layout.addWidget(self.category_subcategory_reset_button)
        
        right_column.addLayout(category_layout)
        
        # Initialize emoji selection color (category_subcategory_color already initialized earlier)
        self.emoji_selection_color = '#3699e7'
        if hasattr(self.parent_window, 'emoji_selection_color'):
            self.emoji_selection_color = self.parent_window.emoji_selection_color
        
        self.update_color_button_styles()
        
        right_column.addSpacing(10)
        
        # Extracted packages folder section
        packages_folder_section_label = QLabel("Extracted packages folder:")
        packages_folder_section_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        packages_folder_section_label.setStyleSheet("padding: 5px 10px;")
        right_column.addWidget(packages_folder_section_label)
        
        right_column.addSpacing(5)
        
        # Open extracted packages folder button
        open_packages_folder_layout = QHBoxLayout()
        open_packages_folder_layout.setSpacing(5)
        
        open_packages_folder_label = QLabel("Open the folder where emoji packages are extracted:")
        open_packages_folder_label.setFont(QFont("Segoe UI", 9))
        open_packages_folder_label.setWordWrap(True)
        open_packages_folder_label.setStyleSheet("margin-left: 30px;")
        open_packages_folder_label.setMaximumWidth(500)
        open_packages_folder_layout.addWidget(open_packages_folder_label)
        
        open_packages_folder_layout.addStretch()
        
        self.open_packages_folder_button = QPushButton("Open folder")
        self.open_packages_folder_button.setFixedSize(110, 30)
        self.open_packages_folder_button.setFont(QFont("Segoe UI", 9))
        self.open_packages_folder_button.setToolTip("Open extracted packages folder in file explorer")
        self.open_packages_folder_button.clicked.connect(self.open_packages_folder)
        open_packages_folder_layout.addWidget(self.open_packages_folder_button)
        
        right_column.addLayout(open_packages_folder_layout)
        
        # Add stretch at the end of right column
        right_column.addStretch()
        
        # Add right column to columns layout
        columns_layout.addLayout(right_column)
        
        # Add columns layout to main layout
        main_layout.addLayout(columns_layout)
        
        main_layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(80, 30)
        cancel_button.clicked.connect(self.reject_settings)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Center the dialog on screen
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def reject_settings(self):
        """Cancel and restore initial theme if it was changed"""
        # Restore initial theme to parent window if user changed it
        selected_theme = self.theme_combo.currentText()
        if selected_theme != self.initial_theme:
            # Theme was changed but user cancelled, don't apply it
            pass
        
        self.reject()
    
    def on_use_last_used_tab_changed(self):
        """Handle use_last_used_tab checkbox state change"""
        self.update_default_tab_combo_state()
    
    def update_default_tab_combo_state(self):
        """Update the enabled state of default_tab_combo based on use_last_used_tab_checkbox"""
        use_last_used = self.use_last_used_tab_checkbox.isChecked()
        
        # When "Display the last used tab" is checked, disable the default tab combo
        self.default_tab_combo.setEnabled(not use_last_used)
        self.default_tab_label.setEnabled(not use_last_used)
    
    def update_background_sub_checkboxes_state(self):
        """Update the enabled state of sub-checkboxes based on main checkbox"""
        main_checked = self.checkboxes['background_color'].isChecked()
        
        if main_checked:
            # Enable sub-checkboxes
            self.background_color_light_checkbox.setEnabled(True)
            self.background_color_medium_checkbox.setEnabled(True)
            self.background_color_dark_checkbox.setEnabled(True)
        else:
            # Disable and uncheck sub-checkboxes
            self.background_color_light_checkbox.setEnabled(False)
            self.background_color_medium_checkbox.setEnabled(False)
            self.background_color_dark_checkbox.setEnabled(False)
    
    def on_background_main_checkbox_changed(self, state):
        """Handle main background_color checkbox state change"""
        if state == Qt.Checked:
            # When main checkbox is checked, check all sub-checkboxes
            self.background_color_light_checkbox.setChecked(True)
            self.background_color_medium_checkbox.setChecked(True)
            self.background_color_dark_checkbox.setChecked(True)
            self.background_color_light_checkbox.setEnabled(True)
            self.background_color_medium_checkbox.setEnabled(True)
            self.background_color_dark_checkbox.setEnabled(True)
        else:
            # When main checkbox is unchecked, disable sub-checkboxes
            self.background_color_light_checkbox.setEnabled(False)
            self.background_color_medium_checkbox.setEnabled(False)
            self.background_color_dark_checkbox.setEnabled(False)
    
    def on_background_sub_checkbox_changed(self):
        """Handle sub-checkbox state changes"""
        # Check if at least one sub-checkbox is checked
        light_checked = self.background_color_light_checkbox.isChecked()
        medium_checked = self.background_color_medium_checkbox.isChecked()
        dark_checked = self.background_color_dark_checkbox.isChecked()
        
        # Block signals temporarily to avoid recursive calls
        self.checkboxes['background_color'].blockSignals(True)
        
        if not light_checked and not medium_checked and not dark_checked:
            # If all are unchecked, uncheck main checkbox and disable sub-checkboxes
            self.checkboxes['background_color'].setChecked(False)
            self.background_color_light_checkbox.setEnabled(False)
            self.background_color_medium_checkbox.setEnabled(False)
            self.background_color_dark_checkbox.setEnabled(False)
        else:
            # If at least one is checked, ensure main checkbox is checked
            if not self.checkboxes['background_color'].isChecked():
                self.checkboxes['background_color'].setChecked(True)
        
        # Restore signals
        self.checkboxes['background_color'].blockSignals(False)
    
    def on_bg_color_light_change(self):
        """Open color picker dialog to change background color for Light theme"""
        initial_color = QColor(self.bg_color_light)
        color_dialog = ThemedColorDialog(initial_color, self, "Choose background color for Light theme")
        
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            if color.isValid():
                self.bg_color_light = color.name()
                self.update_bg_color_button_styles()
    
    def on_bg_color_medium_change(self):
        """Open color picker dialog to change background color for Medium theme"""
        initial_color = QColor(self.bg_color_medium)
        color_dialog = ThemedColorDialog(initial_color, self, "Choose background color for Medium theme")
        
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            if color.isValid():
                self.bg_color_medium = color.name()
                self.update_bg_color_button_styles()
    
    def on_bg_color_dark_change(self):
        """Open color picker dialog to change background color for Dark theme"""
        initial_color = QColor(self.bg_color_dark)
        color_dialog = ThemedColorDialog(initial_color, self, "Choose background color for Dark theme")
        
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            if color.isValid():
                self.bg_color_dark = color.name()
                self.update_bg_color_button_styles()
    
    def update_bg_color_button_styles(self):
        """Update the background color buttons to display the current colors"""
        # Use darker border for Dark/Medium themes, lighter for Light theme
        if self.current_theme == ThemeManager.THEME_DARK:
            border_color = '#555555'
        elif self.current_theme == ThemeManager.THEME_MEDIUM:
            border_color = '#777777'
        else:
            border_color = '#999'
        
        self.bg_color_light_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_color_light};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid {border_color};
            }}
        """)
        
        self.bg_color_medium_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_color_medium};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid {border_color};
            }}
        """)
        
        self.bg_color_dark_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.bg_color_dark};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid {border_color};
            }}
        """)
    
    def reset_bg_color_light(self):
        """Reset background color for Light theme to default"""
        self.bg_color_light = '#ffffff'
        self.update_bg_color_button_styles()
    
    def reset_bg_color_medium(self):
        """Reset background color for Medium theme to default"""
        self.bg_color_medium = '#4b4b4b'
        self.update_bg_color_button_styles()
    
    def reset_bg_color_dark(self):
        """Reset background color for Dark theme to default"""
        self.bg_color_dark = '#312829'
        self.update_bg_color_button_styles()
    
    def choose_emoji_selection_color(self):
        """Open color picker for emoji selection color"""
        initial_color = QColor(self.emoji_selection_color)
        color_dialog = ThemedColorDialog(initial_color, self, "Choose emoji selection color")
        
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            if color.isValid():
                self.emoji_selection_color = color.name()
                self.update_color_button_styles()
    
    def reset_emoji_selection_color(self):
        """Reset emoji selection color to default"""
        self.emoji_selection_color = '#3699e7'
        self.update_color_button_styles()
    
    def choose_category_subcategory_color(self):
        """Open color picker for category/subcategory color"""
        initial_color = QColor(self.category_subcategory_color)
        color_dialog = ThemedColorDialog(initial_color, self, "Choose category/subcategory color")
        
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            if color.isValid():
                self.category_subcategory_color = color.name()
                self.update_color_button_styles()
                self.update_checkboxes_color()
                # Reapply dialog stylesheet with new color
                self.setStyleSheet(ThemeManager.get_dialog_stylesheet(self.current_theme, self.category_subcategory_color))
    
    def reset_category_subcategory_color(self):
        """Reset category/subcategory color to default"""
        self.category_subcategory_color = '#5555ff'
        self.update_color_button_styles()
        self.update_checkboxes_color()
        # Reapply dialog stylesheet with default color
        self.setStyleSheet(ThemeManager.get_dialog_stylesheet(self.current_theme, self.category_subcategory_color))
    
    def update_checkboxes_color(self):
        """Update checkmark colors for all checkboxes based on current category/subcategory color"""
        # Update main checkboxes
        for checkbox in self.checkboxes.values():
            checkbox.set_background_color(self.category_subcategory_color)
        
        # Update sub-checkboxes for background color
        if hasattr(self, 'background_color_light_checkbox'):
            self.background_color_light_checkbox.set_background_color(self.category_subcategory_color)
        if hasattr(self, 'background_color_medium_checkbox'):
            self.background_color_medium_checkbox.set_background_color(self.category_subcategory_color)
        if hasattr(self, 'background_color_dark_checkbox'):
            self.background_color_dark_checkbox.set_background_color(self.category_subcategory_color)
        
        # Update use last used tab checkbox
        if hasattr(self, 'use_last_used_tab_checkbox'):
            self.use_last_used_tab_checkbox.set_background_color(self.category_subcategory_color)
    
    def update_color_button_styles(self):
        """Update the color buttons to display the current colors"""
        self.emoji_selection_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.emoji_selection_color};
                border: 1px solid #999;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #333;
            }}
        """)
        
        self.category_subcategory_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.category_subcategory_color};
                border: 1px solid #999;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #333;
            }}
        """)
    
    def accept_settings(self):
        """Save the checkbox states and colors to parent window"""
        if hasattr(self.parent_window, 'save_preferences'):
            for key, checkbox in self.checkboxes.items():
                self.parent_window.save_preferences[key] = checkbox.isChecked()
            
            # Save sub-checkboxes states for background color
            self.parent_window.save_preferences['background_color_light'] = self.background_color_light_checkbox.isChecked()
            self.parent_window.save_preferences['background_color_medium'] = self.background_color_medium_checkbox.isChecked()
            self.parent_window.save_preferences['background_color_dark'] = self.background_color_dark_checkbox.isChecked()
        
        # Save custom colors
        if hasattr(self.parent_window, 'emoji_selection_color'):
            self.parent_window.emoji_selection_color = self.emoji_selection_color
            self.parent_window.data_manager.emoji_selection_color = self.emoji_selection_color
            self.parent_window.data_manager.save_data('emoji_selection_color', self.emoji_selection_color)
        
        if hasattr(self.parent_window, 'category_subcategory_color'):
            self.parent_window.category_subcategory_color = self.category_subcategory_color
            self.parent_window.data_manager.category_subcategory_color = self.category_subcategory_color
            self.parent_window.data_manager.save_data('category_subcategory_color', self.category_subcategory_color)
        
        # Save background colors for Light, Medium, and Dark themes
        if hasattr(self.parent_window, 'data_manager'):
            self.parent_window.data_manager.emoji_background_color_light = self.bg_color_light
            self.parent_window.data_manager.emoji_background_color_medium = self.bg_color_medium
            self.parent_window.data_manager.emoji_background_color_dark = self.bg_color_dark
            self.parent_window.data_manager.save_data('background_color_light', self.bg_color_light)
            self.parent_window.data_manager.save_data('background_color_medium', self.bg_color_medium)
            self.parent_window.data_manager.save_data('background_color_dark', self.bg_color_dark)
            
            # Save default Recent & Favorites tab preference
            # Map display names to internal values
            tab_reverse_mapping = {
                'Recent': 'recent',
                'Favorites': 'favorites',
                'Frequently used': 'frequently_used'
            }
            selected_tab = tab_reverse_mapping.get(self.default_tab_combo.currentText(), 'recent')
            self.parent_window.data_manager.default_recent_favorites_tab = selected_tab
            self.parent_window.data_manager.save_data('default_recent_favorites_tab', selected_tab)
            
            # Save use_last_used_tab preference
            use_last_used = self.use_last_used_tab_checkbox.isChecked()
            self.parent_window.data_manager.use_last_used_tab = use_last_used
            self.parent_window.data_manager.save_data('use_last_used_tab', use_last_used)
            
            # Update background color button style in main window
            if hasattr(self.parent_window, 'update_bg_color_button_style'):
                self.parent_window.update_bg_color_button_style()
            
            # Refresh emoji display to apply new background color
            if hasattr(self.parent_window, 'refresh_emoji_display'):
                self.parent_window.refresh_emoji_display()
        
        # Get selected theme from combo box (may have changed)
        selected_theme = self.theme_combo.currentText()
        
        # Save and apply theme only if OK is clicked
        if hasattr(self.parent_window, 'data_manager'):
            self.parent_window.data_manager.theme = selected_theme
            self.parent_window.data_manager.save_data('theme', selected_theme)
            
            # Apply theme to parent window
            if hasattr(self.parent_window, 'apply_theme'):
                self.parent_window.apply_theme(selected_theme)
        
        # Update stylesheets in parent window
        if hasattr(self.parent_window, 'update_selection_color_stylesheets'):
            self.parent_window.update_selection_color_stylesheets()
        
        self.accept()
    
    def open_packages_folder(self):
        """Open the extracted packages folder in file explorer"""
        try:
            packages_dir = self.path_manager.get_user_packages_dir()
            
            # Ensure the directory exists
            os.makedirs(packages_dir, exist_ok=True)
            
            # Open the folder in the appropriate file explorer
            system = platform.system()
            if system == "Windows":
                os.startfile(packages_dir)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", packages_dir])
            else:  # Linux and others
                subprocess.run(["xdg-open", packages_dir])
        except Exception as e:
            print(f"[ERROR] Failed to open packages folder: {e}", file=sys.stderr)

