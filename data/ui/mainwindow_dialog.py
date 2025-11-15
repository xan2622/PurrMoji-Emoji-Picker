#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Main Window for PurrMoji Emoji Picker
Contains the EmojiPicker class with all UI and business logic.
"""

import sys
import os
import json
import unicodedata
import io
import platform
import ctypes
from typing import Dict, List, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLineEdit, QScrollArea, QLabel, QRadioButton, QButtonGroup,
    QMenu, QAction, QMessageBox, QComboBox, QDialog, QCheckBox, QSizePolicy,
    QShortcut
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QIODevice
from PyQt5.QtGui import (
    QFont, QPixmap, QPainter, QIcon, QFontMetrics, QFontDatabase, QColor,
    QPalette, QKeySequence
)
from PyQt5.QtSvg import QSvgRenderer

# Import managers for modular architecture
from managers import (
    PathManager, DataManager, CacheManager, EmojiManager, PackageManager,
    PackageInitializer, ThemeManager
)

# Import UI components
from ui.base_dialog import ThemedColorDialog

# Import renderers
from renderers import SKIA_AVAILABLE, get_skia_renderer

# Import UI dialogs
from .about_dialog import AboutDialog
from .hotkeys_dialog import HotkeysDialog
from .settings_dialog import SettingsDialog

# Import custom event handlers
from .event_handlers import DoubleClickButton, EmojiScrollArea

# Get global Skia renderer instance
skia_renderer = get_skia_renderer()


class EmojiPicker(QMainWindow):
    """Main Emoji Picker application class"""
    
    # Configuration table for radio buttons per package type
    # Structure: {package_type: {button_name: (visible, enabled, checked, style)}}
    # - visible: boolean, whether button should be visible
    # - enabled: boolean, whether button should be enabled
    # - checked: boolean or None (None = keep current state)
    # - style: "" (normal) or "disabled" stylesheet
    PACKAGE_BUTTON_CONFIG = {
        "custom": {
            "color": (False, False, None, "disabled"),
            "black": (False, False, None, "disabled"),
            "size_72": (False, False, None, "disabled"),
            "size_618": (False, False, None, "disabled"),
            "open_folder": (True, True, None, ""),
            "refresh": (True, True, None, ""),
            # PNG/SVG/TTF handled dynamically based on custom_emoji_formats_available
        },
        "kaomoji": {
            "color": (False, False, None, "disabled"),
            "black": (False, False, None, "disabled"),
            "png": (False, False, None, "disabled"),
            "svg": (False, False, None, "disabled"),
            "ttf": (False, False, None, "disabled"),
            "size_72": (False, False, None, "disabled"),
            "size_618": (False, False, None, "disabled"),
            "open_folder": (False, False, None, ""),
            "refresh": (False, False, None, ""),
        },
        "system_font": {
            "color": (True, True, True, ""),
            "black": (True, False, None, "disabled"),
            "png": (True, False, None, "disabled"),
            "svg": (True, False, None, "disabled"),
            "ttf": (True, True, True, ""),
            "size_72": (True, False, None, "disabled"),
            "size_618": (True, False, None, "disabled"),
            "open_folder": (False, False, None, ""),
            "refresh": (False, False, None, ""),
        },
        "ttf_font": {
            "color": (True, True, None, ""),
            "black": (True, True, None, ""),
            "png": (True, False, None, "disabled"),
            "svg": (True, False, None, "disabled"),
            "ttf": (True, True, True, ""),
            "size_72": (True, False, None, "disabled"),
            "size_618": (True, False, None, "disabled"),
            "open_folder": (False, False, None, ""),
            "refresh": (False, False, None, ""),
        },
    }
    
    def __init__(self):
        super().__init__()
        
        # Initialize managers for modular architecture
        self.path_manager = PathManager()
        self.data_manager = DataManager(self.path_manager.get_emoji_data_file())
        self.cache_manager = CacheManager(max_size=1000)
        self.emoji_manager = EmojiManager()
        self.package_manager = PackageManager(self.path_manager)
        self.package_initializer = PackageInitializer(self)
        
        # Build emoji folders dictionary (for backward compatibility)
        self.emoji_folders = self.path_manager.build_all_paths()
        
        # Emoji Unicode codes for category buttons (used for dynamic icon loading)
        self.category_emoji_codes = {
            "activities": "26BD",  # Soccer Ball
            "animals-nature": "1F436",  # Dog Face
            "component": "1F3FD",  # Medium skin tone
            "flags": "1F6A9",  # Triangular Flag On Post
            "food-drink": "1F34E",  # Red Apple
            "objects": "1F4F1",  # Mobile Phone
            "people-body": "1F464",  # Bust in silhouette
            "smileys-emotion": "1F603",  # Smiling Face With Open Mouth
            "symbols": "267B",  # Black Universal Recycling Symbol
            "travel-places": "2708"  # Airplane
        }
        
        # Get emoji packages configuration from PackageManager
        self.emoji_packages = self.package_manager.packages
        
        # Load data from DataManager
        self.data_manager.load_data()
        
        # Check system font availability and filter unavailable packages
        self.filter_unavailable_system_fonts()
        
        # Keep reference to emoji_data_file for backward compatibility
        self.emoji_data_file = self.data_manager.data_file
        
        # Initialize UI state variables
        # Only restore last selected package if preference is enabled
        if self.data_manager.get_preference('last_selected_package'):
            self.current_emoji_package = self.data_manager.preferred_emoji_package
        else:
            self.current_emoji_package = "EmojiTwo"  # Default package
        
        # Default to EmojiTwo color 72px PNG
        self.emoji_folder = self.path_manager.get_path("emojitwo_color_72_png")
        
        # Only restore category if preference is enabled
        if self.data_manager.get_preference('category_button'):
            self.current_category = self.data_manager.get_saved_setting(
                'category_button', 'Recent & Favorites'
            )
        else:
            self.current_category = 'Recent & Favorites'
        
        # Only restore subcategory if preference is enabled
        if self.data_manager.get_preference('subcategory_tab'):
            self.current_subcategory = self.data_manager.get_saved_setting(
                'subcategory_tab', self.get_recent_favorites_tab_to_display()
            )
        else:
            # Use user's preferred default tab for Recent & Favorites
            self.current_subcategory = self.get_recent_favorites_tab_to_display()
        
        self.current_emojis = []
        
        # Kaomoji data structures
        self.kaomoji_categories = {}  # Stores kaomoji data by category
        self.kaomoji_tab_buttons = {}  # Stores tab buttons for kaomoji subcategories
        
        # Only restore emoji size if preference is enabled
        if self.data_manager.get_preference('emoji_size'):
            self.emoji_size = self.data_manager.get_saved_setting('emoji_size', 48)
        else:
            self.emoji_size = 48
        
        self.emojis_per_row = 13  # Default emojis per row (calculated dynamically)
        
        # Only restore variation filter if preference is enabled
        if self.data_manager.get_preference('emoji_variation_filter'):
            self.variation_filter = self.data_manager.get_saved_setting('variation_filter', 'all')
        else:
            self.variation_filter = 'all'
        self.selected_emoji_button = None  # Track currently selected emoji button
        self.selected_emoji = None  # Track currently selected emoji character
        
        # Load custom selection colors
        if self.data_manager.get_preference('emoji_selection_color'):
            self.emoji_selection_color = self.data_manager.emoji_selection_color
        else:
            self.emoji_selection_color = '#3699e7'  # Default blue
        
        if self.data_manager.get_preference('category_subcategory_color'):
            self.category_subcategory_color = self.data_manager.category_subcategory_color
        else:
            self.category_subcategory_color = '#5555ff'  # Default blue
        
        # Store current theme
        self.current_theme = self.data_manager.theme
        
        # Contrast mode state (inverts emoji colors in Black + Dark theme)
        self.contrast_enabled = False
        
        # Copy save preferences from DataManager
        self.save_preferences = self.data_manager.save_preferences
        
        # Copy emoji data from DataManager
        self.emoji_data = self.data_manager.emoji_data
        self.emoji_names = self.data_manager.emoji_names
        self.emoji_subcategories = self.data_manager.emoji_subcategories
        self.recent_emojis = self.data_manager.recent_emojis
        self.favorite_emojis = self.data_manager.favorite_emojis
        self.frequently_used_emojis = self.data_manager.frequently_used_emojis
        
        # Store saved settings as attributes for apply_saved_ui_settings()
        if self.save_preferences.get('color_black', False):
            self.saved_color_mode = self.data_manager.get_saved_setting('color_mode', 'color')
        
        if self.save_preferences.get('format_selection', False):
            self.saved_format = self.data_manager.get_saved_setting('format', 'png')
        
        if self.save_preferences.get('package_size', False):
            self.saved_package_size = self.data_manager.get_saved_setting('package_size', '72')
        
        # Predefined emoji sizes for +/- buttons
        self.predefined_sizes = [16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]
        
        # Cache for OpenMoji TTF font names (key: "color" or "black")
        self.openmoji_ttf_fonts = {}
        
        # Cache for Noto TTF font names (key: "color" or "black")
        self.google_noto_ttf_fonts = {}
        
        # Cache for registered font families (font_path -> font_family_name)
        # Only used for Noto Black (Qt native rendering)
        self.registered_font_families = {}
        
        # Custom emoji formats available in the custom folder
        self.custom_emoji_formats_available = {"png": False, "svg": False, "ttf": False}
        
        # Initialize emoji mapping dictionaries (will be populated by create_emoji_mapping)
        self.emoji_to_filename = {}
        self.compound_emoji_variations = {}
        
        
        # Setup UI first (creates radio buttons and other UI elements)
        self.init_ui()
        
        # Apply theme
        self.apply_theme(self.data_manager.theme)
        
        # Apply saved UI settings (color/black, format, package size, variation filter)
        self.apply_saved_ui_settings()
        
        # Register external TTF fonts (Noto Black only) for fast Qt rendering
        self.register_external_fonts()
        
        # Apply package-specific initialization using PackageInitializer
        # Special pre-initialization for Custom package (detect formats)
        if self.current_emoji_package == "Custom":
            self.detect_custom_emoji_formats()
        
        # Delegate to PackageInitializer for clean, strategy-based initialization
        self.package_initializer.initialize_package(self.current_emoji_package)
        
        # Update displayed emoji source label (for all packages)
        self.update_displayed_emoji_source_label()
        
        # Force UI update to ensure proper rendering at startup
        QApplication.processEvents()
        
        # Re-adjust grid height after UI is fully rendered (fixes startup layout issue)
        if self.current_emoji_package != "Custom":
            num_rows = self.get_current_subcategory_rows_count()
            self.adjust_grid_height_for_subcategories(num_rows)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    @property
    def emoji_background_color(self):
        """Get the current emoji background color based on active theme"""
        if self.current_theme == ThemeManager.THEME_LIGHT:
            return self.data_manager.emoji_background_color_light
        elif self.current_theme == ThemeManager.THEME_MEDIUM:
            return self.data_manager.emoji_background_color_medium
        else:
            return self.data_manager.emoji_background_color_dark
    
    def setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts"""
        # Page Up: Navigate to previous package
        shortcut_page_up = QShortcut(QKeySequence(Qt.Key_PageUp), self)
        shortcut_page_up.activated.connect(self.navigate_to_previous_package)
        shortcut_page_up.setContext(Qt.ApplicationShortcut)
        
        # Page Down: Navigate to next package
        shortcut_page_down = QShortcut(QKeySequence(Qt.Key_PageDown), self)
        shortcut_page_down.activated.connect(self.navigate_to_next_package)
        shortcut_page_down.setContext(Qt.ApplicationShortcut)
        
        # Numpad Minus: Decrease emoji size
        shortcut_numpad_minus = QShortcut(QKeySequence(Qt.Key_Minus), self)
        shortcut_numpad_minus.activated.connect(self.on_decrease_size)
        shortcut_numpad_minus.setContext(Qt.ApplicationShortcut)
        
        # Numpad Plus: Increase emoji size
        shortcut_numpad_plus = QShortcut(QKeySequence(Qt.Key_Plus), self)
        shortcut_numpad_plus.activated.connect(self.on_increase_size)
        shortcut_numpad_plus.setContext(Qt.ApplicationShortcut)
        
        # T: Cycle through themes (Light -> Medium -> Dark -> Light)
        shortcut_theme_toggle = QShortcut(QKeySequence(Qt.Key_T), self)
        shortcut_theme_toggle.activated.connect(self.cycle_theme)
        shortcut_theme_toggle.setContext(Qt.WindowShortcut)
        
        # Install event filter on widgets to prevent them from handling Page Up/Down
        self.emoji_package_combo.installEventFilter(self)
        self.emoji_scroll_area.installEventFilter(self)
        self.search_edit.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Event filter to intercept keyboard shortcuts on various widgets"""
        from PyQt5.QtCore import QEvent
        
        # Block Page Up/Down and +/- from being processed by child widgets
        # so our global shortcuts can handle them
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Plus, Qt.Key_Minus):
                # Check if it's from one of our filtered widgets
                if obj in (self.emoji_package_combo, self.emoji_scroll_area, self.search_edit):
                    # Let our shortcuts handle it instead
                    return True  # Event is handled, don't propagate to widget
        
        # Let other events pass through
        return super().eventFilter(obj, event)
    
    def navigate_to_previous_package(self):
        """Navigate to the previous package in the dropdown"""
        current_index = self.emoji_package_combo.currentIndex()
        new_index = current_index - 1
        
        # Wrap around to the last package if at the beginning
        if new_index < 0:
            new_index = self.emoji_package_combo.count() - 1
        
        self.emoji_package_combo.setCurrentIndex(new_index)
    
    def navigate_to_next_package(self):
        """Navigate to the next package in the dropdown"""
        current_index = self.emoji_package_combo.currentIndex()
        new_index = current_index + 1
        
        # Wrap around to the first package if at the end
        if new_index >= self.emoji_package_combo.count():
            new_index = 0
        
        self.emoji_package_combo.setCurrentIndex(new_index)
    
    def filter_unavailable_system_fonts(self):
        """Filter out system font packages that are not available on the current platform
        
        This method checks if system fonts like 'Segoe UI Emoji' are available
        and removes them from the packages dictionary if not found.
        """
        font_database = QFontDatabase()
        packages_to_remove = []
        
        for package_name, package_config in self.emoji_packages.items():
            if package_config.get("type") == "system_font":
                font_name = package_config.get("font_name")
                if font_name:
                    # Check if font is available on the system
                    available_families = font_database.families()
                    if font_name not in available_families:
                        packages_to_remove.append(package_name)
                        # If current package is unavailable, switch to default
                        if self.current_emoji_package == package_name:
                            self.current_emoji_package = "EmojiTwo"
        
        # Remove unavailable packages from the dictionary
        for package_name in packages_to_remove:
            del self.emoji_packages[package_name]
    
    def register_external_fonts(self):
        """Register external TTF fonts with Qt for fast native rendering
        
        Only Noto Black is registered here. Other fonts use Skia rendering:
        - OpenMoji: Color and Black variants share the same family name "OpenMoji", 
          so Qt cannot differentiate them. Skia is used with font file paths.
        - Noto Color: Uses COLR v1 format which Qt doesn't support. Also, Windows 
          may have Noto Color Emoji as a system font which would take priority over 
          a registered font, causing conflicts.
        """
        noto_black_font = self.path_manager.get_path("google_noto_black_ttf")
        if os.path.exists(noto_black_font):
            font_id = QFontDatabase.addApplicationFont(noto_black_font)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    self.registered_font_families[noto_black_font] = families[0]
    
    def generate_active_stylesheet(
        self, base_color, border_width=1, border_radius=3, padding='5px', text_color='white'
    ):
        """Generate stylesheet for active/selected elements
        
        Args:
            base_color: Base color for the element
            border_width: Border width in pixels
            border_radius: Border radius in pixels
            padding: CSS padding value
            text_color: Text color (None to omit color property)
            
        Returns:
            Complete stylesheet string
        """
        hover_color = self.darken_color(base_color, 0.1)
        pressed_color = self.darken_color(base_color, 0.2)
        
        color_property = f"color: {text_color};" if text_color else ""
        
        return f"""
        QPushButton {{
            border: {border_width}px solid {base_color};
            border-radius: {border_radius}px;
            background-color: {base_color};
            {color_property}
            padding: {padding};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
            border: {border_width}px solid {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        """
        
    def darken_color(self, hex_color, factor=0.1):
        """Darken a hex color by a factor (0.0 to 1.0)
        
        Args:
            hex_color: Hex color string (e.g., "#3699e7")
            factor: Darkening factor (0.0 = no change, 1.0 = black)
        
        Returns:
            Darkened hex color string
        """
        # Remove '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert hex to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Darken by factor
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_selection_color_stylesheets(self):
        """Update all UI elements with the new custom colors"""
        # Update selected emoji button if any
        if self.selected_emoji_button:
            self.selected_emoji_button.setStyleSheet(self.get_button_selected_stylesheet())
        
        # Update category buttons
        if hasattr(self, 'category_buttons'):
            for cat_name, cat_button in self.category_buttons.items():
                if cat_name == self.current_category:
                    cat_button.setStyleSheet(self.get_active_category_stylesheet())
        
        # Update subcategory buttons
        if hasattr(self, 'subcategory_buttons_widget') and self.subcategory_buttons_widget:
            for i in range(self.subcategory_buttons_widget.layout().count()):
                widget = self.subcategory_buttons_widget.layout().itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    # Check if this is the active button
                    if hasattr(widget, 'objectName') and widget.objectName():
                        subcategory_name = widget.objectName()
                        if subcategory_name == self.current_subcategory:
                            widget.setStyleSheet(self.get_active_button_stylesheet())
        
        # Update background color button hover style
        self.update_bg_color_button_style()
    
    def apply_theme(self, theme):
        """Apply theme (Light/Medium/Dark) to the main window
        
        Args:
            theme: Theme name ('Light', 'Medium', or 'Dark')
        """
        self.current_theme = theme
        self.setStyleSheet(
            ThemeManager.get_mainwindow_stylesheet(
                theme, self.category_subcategory_color
            )
        )
        
        # Update background color button style and refresh emoji display
        if self.data_manager.get_preference('background_color'):
            self.update_bg_color_button_style()
            self.refresh_emoji_display()
        
        # Apply theme to Windows title bar (dark mode for Dark/Medium, light mode for Light)
        # Only works on Windows 10 (build 17763+) and Windows 11
        self.set_windows_titlebar_theme(theme)
        
        # Update search field style
        if hasattr(self, 'search_edit'):
            self.search_edit.setStyleSheet(ThemeManager.get_search_edit_stylesheet(theme))
            # Set placeholder text color based on theme
            palette = self.search_edit.palette()
            if theme == ThemeManager.THEME_LIGHT:
                palette.setColor(QPalette.PlaceholderText, QColor("#999999"))
            else:  # Medium or Dark
                palette.setColor(QPalette.PlaceholderText, QColor("#888888"))
            self.search_edit.setPalette(palette)
        
        # Update size input field style
        if hasattr(self, 'size_input'):
            self.size_input.setStyleSheet(ThemeManager.get_size_input_stylesheet(theme))
        
        # Update category button icons (for extras SVG icons color inversion in Dark and Medium themes)
        if hasattr(self, 'category_buttons'):
            self.update_category_icons_for_theme(theme)
        
        # Update all buttons with new theme
        self.update_all_button_styles()
        
        # Update Contrast button style to adapt tooltip to new theme
        if hasattr(self, 'contrast_button'):
            self.update_contrast_button_state()
    
    def cycle_theme(self):
        """Cycle through themes: Light -> Medium -> Dark -> Light
        
        This method is triggered by the T keyboard shortcut.
        """
        # Define theme cycle order
        theme_order = [ThemeManager.THEME_LIGHT, ThemeManager.THEME_MEDIUM, ThemeManager.THEME_DARK]
        
        # Find current theme index
        try:
            current_index = theme_order.index(self.current_theme)
        except ValueError:
            # If current theme is not in the list, default to Light
            current_index = 0
        
        # Get next theme (cycle back to start if at the end)
        next_index = (current_index + 1) % len(theme_order)
        next_theme = theme_order[next_index]
        
        # Apply the new theme
        self.current_theme = next_theme
        self.apply_theme(next_theme)
        
        # Save theme preference
        self.data_manager.theme = next_theme
        self.data_manager.save_data('theme', next_theme)
    
    def load_svg_icon_with_theme(self, svg_path, size=32):
        """Load SVG icon and adapt colors based on current theme
        
        Args:
            svg_path: Path to SVG file
            size: Icon size in pixels (default: 32)
            
        Returns:
            QIcon or None if loading failed
        """
        if not os.path.exists(svg_path):
            return None
        
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Invert colors for Dark and Medium themes (black -> white)
            if self.current_theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM]:
                svg_content = svg_content.replace('fill: #000000', 'fill: #ffffff')
                svg_content = svg_content.replace('fill:#000000', 'fill:#ffffff')
            
            svg_bytes = svg_content.encode('utf-8')
            svg_renderer = QSvgRenderer(svg_bytes)
            
            if svg_renderer.isValid():
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                svg_renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
        except Exception:
            pass
        
        return None
    
    def update_category_icons_for_theme(self, theme):
        """Update category button icons based on theme (invert colors for Dark and Medium themes)
        
        Args:
            theme: Theme name ('Light', 'Medium', or 'Dark')
        """
        # Update extras SVG icons (Recent & Favorites, extras-openmoji, extras-unicode)
        category_svg_icons = {
            "Recent & Favorites": self.path_manager.get_misc_file("Recent_Favorites.svg"),
            "extras-openmoji": self.path_manager.get_misc_file("extras_OpenMoji.svg"),
            "extras-unicode": self.path_manager.get_misc_file("extras_Unicode.svg")
        }
        
        for category, svg_path in category_svg_icons.items():
            if category in self.category_buttons:
                btn = self.category_buttons[category]
                icon = self.load_svg_icon_with_theme(svg_path, 32)
                if icon:
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(32, 32))
        
        # Update emoji-based category icons (for Black mode + Dark theme automatic inversion)
        # Only regenerate if we're in Black mode, as Color mode doesn't need theme-based inversion
        if hasattr(self, 'black_radio') and self.black_radio.isChecked():
            for category, emoji_code in self.category_emoji_codes.items():
                if category in self.category_buttons:
                    btn = self.category_buttons[category]
                    # Regenerate icon with new theme (create_category_icon uses self.current_theme in cache key)
                    icon = self.create_category_icon(emoji_code, 32)
                    if icon:
                        btn.setIcon(icon)
                        btn.setIconSize(QSize(32, 32))
    
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
                    # Dark theme colors
                    # Active (focused): #3c3c3c = RGB(60, 60, 60) = lighter
                    # Inactive (unfocused): #202020 = RGB(32, 32, 32) = same as interface background
                    if has_focus:
                        titlebar_color = 0x003c3c3c  # Lighter when focused
                    else:
                        titlebar_color = 0x00202020  # Same as interface background when not focused
                    
                    # Force text color to white (0xFFFFFF) in dark mode
                    text_color = 0x00FFFFFF  # White in BGR format
                elif theme == ThemeManager.THEME_MEDIUM:
                    # Medium theme colors
                    # Active (focused): #707070 = RGB(112, 112, 112) = lighter medium
                    # Inactive (unfocused): #5a5a5a = RGB(90, 90, 90) = same as interface background
                    if has_focus:
                        titlebar_color = 0x00707070  # Lighter when focused
                    else:
                        titlebar_color = 0x005a5a5a  # Same as interface background when not focused
                    
                    # Force text color to white (0xFFFFFF) in medium mode
                    text_color = 0x00FFFFFF  # White in BGR format
                else:
                    # Light theme colors - Windows 11 official colors
                    # Active (focused): #FFFFFF = RGB(255, 255, 255) = white
                    # Inactive (unfocused): #F3F3F3 = RGB(243, 243, 243) = light gray
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
            self.set_windows_titlebar_theme(self.current_theme, self.isActiveWindow())
        super().changeEvent(event)
    
    def get_emoji_button_stylesheet(self):
        """Get stylesheet for emoji buttons based on current theme"""
        return ThemeManager.get_emoji_button_stylesheet(
            self.current_theme, self.emoji_background_color
        )
    
    def get_button_selected_stylesheet(self):
        """Get stylesheet for selected emoji button based on current theme"""
        return ThemeManager.get_emoji_button_selected_stylesheet(
            self.current_theme, self.emoji_selection_color
        )
    
    def get_active_button_stylesheet(self):
        """Get stylesheet for active subcategory buttons based on current theme"""
        return ThemeManager.get_active_button_stylesheet(
            self.current_theme, self.category_subcategory_color
        )
    
    def get_inactive_button_stylesheet(self):
        """Get stylesheet for inactive subcategory buttons based on current theme"""
        return ThemeManager.get_inactive_button_stylesheet(self.current_theme)
    
    def get_active_category_stylesheet(self):
        """Get stylesheet for active category buttons based on current theme"""
        return ThemeManager.get_active_category_stylesheet(
            self.current_theme, self.category_subcategory_color
        )
    
    def get_inactive_category_stylesheet(self):
        """Get stylesheet for inactive category buttons based on current theme"""
        return ThemeManager.get_inactive_category_stylesheet(self.current_theme)
    
    def get_disabled_radio_stylesheet(self):
        """Get stylesheet for disabled radio buttons based on current theme"""
        return ThemeManager.get_disabled_radio_stylesheet(self.current_theme)
    
    def update_all_button_styles(self):
        """Update all button styles when theme changes"""
        # Update category buttons
        if hasattr(self, 'category_buttons'):
            for cat_name, cat_button in self.category_buttons.items():
                if cat_name == self.current_category:
                    cat_button.setStyleSheet(self.get_active_category_stylesheet())
                else:
                    cat_button.setStyleSheet(self.get_inactive_category_stylesheet())
        
        # Update subcategory buttons
        if hasattr(self, 'subcategory_buttons'):
            for subcat_name, subcat_button in self.subcategory_buttons.items():
                if subcat_name == self.current_subcategory:
                    subcat_button.setStyleSheet(self.get_active_button_stylesheet())
                else:
                    subcat_button.setStyleSheet(self.get_inactive_button_stylesheet())
        
        # Update Kaomoji tab buttons
        if hasattr(self, 'kaomoji_tab_buttons') and self.kaomoji_tab_buttons:
            self.update_kaomoji_tab_styles()
        
        # Update emoji buttons in grid
        if hasattr(self, 'emoji_scroll_area'):
            emoji_content = self.emoji_scroll_area.widget()
            if emoji_content and emoji_content.layout():
                for i in range(emoji_content.layout().count()):
                    item = emoji_content.layout().itemAt(i)
                    if item and item.widget():
                        btn = item.widget()
                        if isinstance(btn, QPushButton):
                            if self.selected_emoji_button and btn == self.selected_emoji_button:
                                btn.setStyleSheet(self.get_button_selected_stylesheet())
                            else:
                                btn.setStyleSheet(self.get_emoji_button_stylesheet())
        
        # Update disabled radio buttons
        if hasattr(self, 'color_radio'):
            radio_buttons = [
                self.color_radio, self.black_radio, self.png_radio,
                self.svg_radio, self.ttf_radio, self.size_72_radio,
                self.size_618_radio
            ]
            for radio_button in radio_buttons:
                if not radio_button.isEnabled():
                    radio_button.setStyleSheet(self.get_disabled_radio_stylesheet())
                else:
                    radio_button.setStyleSheet("")
    
    def apply_saved_ui_settings(self):
        """Apply saved UI settings (color/black, format, package size, variation filter) after UI is initialized"""
        # Apply saved color mode
        if hasattr(self, 'saved_color_mode'):
            if self.saved_color_mode == "black":
                self.black_radio.setChecked(True)
            else:
                self.color_radio.setChecked(True)
        
        # Apply saved format selection
        if hasattr(self, 'saved_format'):
            if self.saved_format == "svg":
                self.svg_radio.setChecked(True)
            elif self.saved_format == "ttf":
                self.ttf_radio.setChecked(True)
            else:
                self.png_radio.setChecked(True)
        
        # Apply saved package size
        if hasattr(self, 'saved_package_size'):
            if self.saved_package_size == "618":
                self.size_618_radio.setChecked(True)
            else:
                self.size_72_radio.setChecked(True)
        
        # Apply saved variation filter
        if hasattr(self, 'variation_filter'):
            if self.variation_filter == "with_variations":
                self.variation_filter_combo.setCurrentIndex(1)
            elif self.variation_filter == "without_variations":
                self.variation_filter_combo.setCurrentIndex(2)
            else:
                self.variation_filter_combo.setCurrentIndex(0)
        
        # Apply saved emoji size
        if hasattr(self, 'emoji_size'):
            self.size_input.setText(str(self.emoji_size))
        
        # Update Contrast button state based on Color/Black mode
        self.update_contrast_button_state()
    
    
    def get_emoji_image_path(self, emoji):
        """Get the PNG/SVG file path for an emoji character"""
        if emoji in self.emoji_to_filename:
            filename = self.emoji_to_filename[emoji]
            image_path = os.path.join(self.emoji_folder, filename)
            
            # Check if file exists in current folder
            if os.path.exists(image_path):
                return image_path
            
            # Special handling for EmojiTwo: if file doesn't exist in size-specific folder,
            # try to find it in the default folder
            if self.current_emoji_package == "EmojiTwo":
                import re
                folder_name = os.path.basename(self.emoji_folder)
                if re.match(r'^\d+$', folder_name):  # Folder name is just a number (size)
                    # Determine the default folder path based on current color/black selection
                    # This ensures we load the correct variant (color or black)
                    # Check if radio buttons exist (they might not during initialization)
                    if hasattr(self, 'black_radio') and self.black_radio.isChecked():
                        default_folder = self.path_manager.get_path("emojitwo_black_default_png")
                    else:
                        default_folder = self.path_manager.get_path("emojitwo_color_default_png")
                    
                    # Try to find the file in the default folder
                    default_path = os.path.join(default_folder, filename)
                    if os.path.exists(default_path):
                        return default_path
        
        return None
    
    def create_emoji_button(self, emoji, row, col):
        """Create an emoji button and add it to the grid (utility method to avoid duplication)"""
        # Create emoji button
        btn = DoubleClickButton()
        btn.setFixedSize(self.emoji_size, self.emoji_size)
        btn.setMinimumSize(self.emoji_size, self.emoji_size)
        btn.setMaximumSize(self.emoji_size, self.emoji_size)
        
        # Load PNG/SVG image for emoji
        icon = self.create_emoji_icon(emoji, self.emoji_size)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(QSize(self.emoji_size, self.emoji_size))
        else:
            # For EmojiTwo, if emoji doesn't exist, just leave button empty
            if self.current_emoji_package != "EmojiTwo":
                # Fallback to text for other packages (font size proportional to emoji_size)
                btn.setText(emoji)
                # Calculate font size proportional to emoji_size (16pt for 48px = 0.333 ratio)
                font_size = max(8, int(self.emoji_size * 0.333))
                emoji_font = QFont("Segoe UI Emoji", font_size)
                btn.setFont(emoji_font)
        
        # Apply appropriate stylesheet based on selection state
        if emoji == self.selected_emoji:
            btn.setStyleSheet(self.get_button_selected_stylesheet())
            self.selected_emoji_button = btn
        else:
            btn.setStyleSheet(self.get_emoji_button_stylesheet())
        
        btn.clicked.connect(
            lambda checked=False, e=emoji, b=btn: self.on_emoji_click(e, b)
        )
        btn.doubleClicked.connect(
            lambda checked=False, e=emoji, b=btn: self.on_emoji_double_click(e, b)
        )
        
        # Add context menu for compound emojis
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(
            lambda pos, e=emoji, button=btn: self.show_emoji_context_menu(
                pos, e, button
            )
        )
        
        # Add tooltip
        emoji_name = self.get_emoji_name(emoji)
        btn.setToolTip(emoji_name)
        
        # Add to grid with explicit positioning
        self.emoji_layout.addWidget(btn, row, col)
        
        return btn
    
    def update_emoji_preview_display(self, icon, text):
        """Update the status widget with emoji preview
        
        Args:
            icon: QIcon or QPixmap to display (can be None)
            text: Text to display next to the icon
        """
        if icon:
            if isinstance(icon, QIcon):
                pixmap = icon.pixmap(24, 24)
            else:
                pixmap = icon
            self.status_emoji_label.setPixmap(pixmap)
            self.status_emoji_label.show()
        else:
            self.status_emoji_label.clear()
            self.status_emoji_label.hide()
        
        self.status_text_label.setText(text)
    
    def update_emoji_preview(self, emoji=None, emoji_name=None, unicode_code=None, button_icon=None):
        """Update emoji preview using the current emoji package
        
        Args:
            emoji: Emoji character (optional, uses self.selected_emoji if not provided)
            emoji_name: Name of the emoji (optional, computed if not provided)
            unicode_code: Unicode code point(s) (optional, computed if not provided)
            button_icon: Optional QIcon from button to avoid re-rendering
        """
        # If no emoji provided, use selected emoji
        if emoji is None:
            if not self.selected_emoji:
                return
            
            emoji = self.selected_emoji
            
            # Get icon from selected button to avoid re-rendering
            if button_icon is None:
                button_icon = self.selected_emoji_button.icon() if self.selected_emoji_button else None
            
            # Handle different package types
            if self.current_emoji_package == "Custom":
                self.update_custom_emoji_preview(emoji, button_icon)
                return
            elif self.current_emoji_package == "Kaomoji" and self.is_kaomoji_text(emoji):
                # This is a kaomoji text (not an emoji), use kaomoji preview (no icon)
                self.update_kaomoji_preview(emoji)
                return
            
            # Compute emoji_name and unicode_code if not provided
            if emoji_name is None:
                emoji_name = self.get_emoji_name(emoji)
            if unicode_code is None:
                unicode_code = self.emoji_manager.emoji_to_unicode(emoji)
        
        # Standard emoji preview update
        if button_icon:
            # Reuse button icon and scale it down for preview
            icon = button_icon
        else:
            # Create new icon if not provided
            icon = self.create_emoji_icon(emoji, 24)
        
        text = f"{emoji_name} ({unicode_code})"
        self.update_emoji_preview_display(icon, text)
    
    def update_custom_emoji_preview(self, filename, button_icon=None):
        """Update custom emoji preview with image display
        
        Args:
            filename: Name of the custom emoji file
            button_icon: Optional QIcon from button to avoid re-rendering
        """
        if button_icon:
            # Reuse button icon and scale it down for preview
            self.update_emoji_preview_display(button_icon, filename)
        else:
            # Create new icon if not provided
            file_path = os.path.join(self.emoji_folder, filename)
            file_ext = os.path.splitext(filename)[1].lower()
            preview_size = 24
            
            if os.path.exists(file_path):
                icon = self.create_custom_emoji_icon(file_path, preview_size)
                self.update_emoji_preview_display(icon, filename)
            else:
                # Show format indicator if file doesn't exist
                self.status_emoji_label.clear()
                self.status_emoji_label.hide()
                self.status_text_label.setText(f"[{file_ext.upper().lstrip('.')}] {filename}")
    
    def update_kaomoji_preview(self, kaomoji):
        """Update kaomoji preview
        
        Args:
            kaomoji: Kaomoji text string
        """
        char_count = len(kaomoji)
        text = f"{kaomoji} - Kaomoji ({char_count} characters)"
        
        # For kaomoji, we can optionally show it in a larger font
        # But since we're using native widgets, we'll just show the text
        self.status_emoji_label.clear()
        self.status_emoji_label.hide()
        self.status_text_label.setText(text)
    
    def copy_emoji_to_clipboard(self, emoji):
        """Copy emoji to clipboard and add to recent list (utility method to avoid duplication)"""
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(emoji)
        
        # Show visual feedback - change button text to checkmark
        self.copy_button.setText("✔")
        
        # Reset button text after 500ms
        QTimer.singleShot(500, lambda: self.copy_button.setText("Copy to clipboard"))
        
        # Add to recent emojis (avoid duplicates)
        if emoji not in self.recent_emojis:
            self.recent_emojis.insert(0, emoji)
            # Keep only last 50 recent emojis
            if len(self.recent_emojis) > 50:
                self.recent_emojis = self.recent_emojis[:50]
        
        # Save recent emojis
        self.save_recent_emojis()
        
        # Update emoji usage count and frequently used list
        self.data_manager.update_emoji_usage(emoji)
        self.frequently_used_emojis = self.data_manager.frequently_used_emojis
        
        # Update counter for all categories
        self.update_emoji_counter()
        
        # Update action buttons state
        self.update_action_buttons_state()
    
    def reconnect_signal(self, signal, new_handler):
        """Safely disconnect and reconnect a signal (utility method to avoid duplication)"""
        try:
            signal.disconnect()
        except TypeError:
            pass  # No connections to disconnect
        signal.connect(new_handler)
    
    def show_emoji_context_menu(self, pos, emoji, button):
        """Show context menu for emoji variations"""
        # Find the base emoji (first character) to get variations
        base_emoji = emoji[0] if emoji else emoji
        
        if base_emoji in self.compound_emoji_variations:
            menu = QMenu(self)
            
            # Add main emoji option
            main_icon = self.create_emoji_icon(base_emoji, 16)
            unicode_code = self.emoji_manager.emoji_to_unicode(base_emoji)
            main_action = QAction(
                f"Main: {base_emoji} ({unicode_code})", self
            )
            if main_icon:
                main_action.setIcon(main_icon)
            variation_data = {
                'full_emoji': base_emoji,
                'codes': [self.emoji_manager.emoji_to_unicode(base_emoji)]
            }
            main_action.triggered.connect(
                lambda checked=False, btn=button: self.on_variation_click(
                    variation_data, btn
                )
            )
            menu.addAction(main_action)
            
            menu.addSeparator()
            
            # Add variation options
            for variation in self.compound_emoji_variations[base_emoji]:
                variation_codes = '-'.join(variation['codes'])
                variation_icon = self.create_emoji_icon(variation['full_emoji'], 16)
                variation_action = QAction(
                    f"{variation['full_emoji']} ({variation_codes})", self
                )
                if variation_icon:
                    variation_action.setIcon(variation_icon)
                # Capture variation by value using default parameter to avoid closure issue
                variation_action.triggered.connect(
                    lambda checked=False, v=variation, btn=button: self.on_variation_click(v, btn)
                )
                menu.addAction(variation_action)
            
            # Show menu at the button's position (center of emoji)
            menu.exec_(button.mapToGlobal(pos))
    
    def on_variation_click(self, variation, button):
        """Handle variation emoji click"""
        variation_emoji = variation['full_emoji']
        
        # Update the button with the variation emoji
        icon = self.create_emoji_icon(variation_emoji, self.emoji_size)
        if icon:
            button.setIcon(icon)
            button.setIconSize(QSize(self.emoji_size, self.emoji_size))
        else:
            # Fallback to text if image not found
            button.setText(variation_emoji)
            emoji_font = QFont("Segoe UI Emoji", 16)
            button.setFont(emoji_font)
        
        # Update the button's click handler to use the variation
        self.reconnect_signal(button.clicked, lambda checked=False, e=variation_emoji, b=button: self.on_emoji_click(e, b))
        
        # Update the button's double-click handler to use the variation
        self.reconnect_signal(button.doubleClicked, lambda checked=False, e=variation_emoji, b=button: self.on_emoji_double_click(e, b))
        
        # Update the context menu handler to use the variation
        self.reconnect_signal(button.customContextMenuRequested, lambda pos, e=variation_emoji, btn=button: self.show_emoji_context_menu(pos, e, btn))
        
        # Update tooltip
        emoji_name = self.get_emoji_name(variation_emoji)
        button.setToolTip(emoji_name)
        
        # Show variation emoji in status widget
        unicode_code = '-'.join(variation['codes'])
        self.update_emoji_preview(variation_emoji, emoji_name, unicode_code)
        
        # Update selected emoji reference
        self.selected_emoji = variation_emoji
        self.selected_emoji_button = button
        button.setStyleSheet(self.get_button_selected_stylesheet())
    
    def create_emoji_icon(self, emoji, size, is_category_icon=False):
        """Create an icon for an emoji, handling PNG, SVG, and system font formats with caching
        
        Args:
            emoji: Emoji character to render
            size: Target size for the icon
            is_category_icon: If True, don't apply Contrast button inversion (only for grid emojis)
        """
        # Create cache key based on emoji, size, and current folder/package
        # For file-based packages, use the folder path to differentiate between different sizes
        # For system fonts, use the package name
        package_info = self.emoji_packages.get(self.current_emoji_package, {})
        package_type = package_info.get("type", "files")
        
        # Special handling for Kaomoji package with real emojis - use system font
        if self.current_emoji_package == "Kaomoji":
            package_type = "system_font"
        
        # Special handling for OpenMoji TTF
        if self.current_emoji_package == "OpenMoji" and self.ttf_radio.isChecked():
            package_type = "system_font"
        
        # Special handling for Noto (TTF font package)
        if self.current_emoji_package == "Noto":
            package_type = "system_font"
        
        if package_type == "system_font":
            # Include color/black mode and contrast state in cache key to differentiate variants
            # But only include contrast_enabled for grid emojis, not for category icons
            color_mode = "color" if self.color_radio.isChecked() else "black"
            contrast_key = False if is_category_icon else self.contrast_enabled
            cache_key = (emoji, size, self.current_emoji_package, color_mode, contrast_key)
        else:
            contrast_key = False if is_category_icon else self.contrast_enabled
            cache_key = (emoji, size, self.emoji_folder, contrast_key)
        
        # Check if icon is already in cache
        cached_icon = self.cache_manager.get(cache_key)
        if cached_icon:
            return cached_icon
        
        icon = None
        
        # Handle system font rendering
        if package_type == "system_font":
            # Determine which font to use
            if self.current_emoji_package == "OpenMoji" and self.ttf_radio.isChecked():
                # OpenMoji TTF: Color & Black have same family name, Qt cannot differentiate them
                font_name = self.get_openmoji_ttf_font_name()
                font_path = self.get_openmoji_ttf_font_path()
            elif self.current_emoji_package == "Noto":
                # Noto: Use Skia for both variants for consistency and to avoid Qt font conflicts
                # Windows may have Noto Color Emoji as system font which takes priority over registered Noto Black
                font_name = self.get_google_noto_ttf_font_name()
                font_path = self.get_google_noto_ttf_font_path()
            else:
                font_name = package_info.get("font_name", "Segoe UI Emoji")
                font_path = None
            
            # Render emoji using Skia if available and we have a font path
            # (OpenMoji Color/Black, Noto Color, and monochrome fonts)
            if SKIA_AVAILABLE and font_path and os.path.exists(font_path):
                icon = self.render_emoji_with_skia(emoji, size, font_path)
            
            # Fallback to Qt rendering if Skia not available or rendering failed
            if not icon:
                # Determine appropriate font size based on emoji type
                # Use 0.5 ratio for all system fonts to ensure emojis fit properly in their containers
                font_size = int(size * 0.5)
                
                font = QFont(font_name, font_size)
                
                # Create pixmap and render emoji
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                painter.setFont(font)
                painter.drawText(0, 0, size, size, Qt.AlignCenter, emoji)
                painter.end()
                
                icon = QIcon(pixmap)
        else:
            # Handle file-based rendering (PNG/SVG)
            image_path = self.get_emoji_image_path(emoji)
            if not image_path or not os.path.exists(image_path):
                return None
            
            # Try Skia first for better performance and quality
            if SKIA_AVAILABLE and skia_renderer and skia_renderer.initialized:
                if image_path.endswith('.svg'):
                    icon = skia_renderer.render_svg_file(image_path, size)
                else:
                    icon = skia_renderer.render_image_file(image_path, size)
            
            # Fallback to Qt if Skia is not available or failed
            if not icon:
                if image_path.endswith('.svg'):
                    # Handle SVG files with QSvgRenderer
                    svg_renderer = QSvgRenderer(image_path)
                    if svg_renderer.isValid():
                        pixmap = QPixmap(size, size)
                        pixmap.fill(Qt.transparent)
                        painter = QPainter(pixmap)
                        svg_renderer.render(painter)
                        painter.end()
                        icon = QIcon(pixmap)
                else:
                    # Handle PNG files with QPixmap - scale to exact size
                    source_pixmap = QPixmap(image_path)
                    if not source_pixmap.isNull():
                        # Create a target pixmap of exact size
                        pixmap = QPixmap(size, size)
                        pixmap.fill(Qt.transparent)
                        
                        # Scale source to fit within target size
                        scaled_source = source_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        
                        # Draw scaled source centered on target pixmap
                        painter = QPainter(pixmap)
                        x = (size - scaled_source.width()) // 2
                        y = (size - scaled_source.height()) // 2
                        painter.drawPixmap(x, y, scaled_source)
                        painter.end()
                        
                        icon = QIcon(pixmap)
        
        # Apply color inversion if contrast mode is enabled and conditions are met
        # (Black mode + user explicitly enabled Contrast button)
        # Note: Category icons have their own automatic inversion in create_category_icon()
        if icon and self.contrast_enabled and not self.color_radio.isChecked() and not is_category_icon:
            icon = self.invert_icon_colors(icon, size)
        
        # Store in cache before returning
        if icon:
            self.cache_manager.set(cache_key, icon)
        
        return icon
    
    def invert_icon_colors(self, icon, size):
        """Invert colors of an icon (used for Black + Dark theme)
        
        Args:
            icon: QIcon to invert
            size: Size of the icon
            
        Returns:
            QIcon with inverted colors
        """
        # Get pixmap from icon
        pixmap = icon.pixmap(size, size)
        
        # Create inverted image
        image = pixmap.toImage()
        image.invertPixels()
        
        # Convert back to icon
        inverted_pixmap = QPixmap.fromImage(image)
        return QIcon(inverted_pixmap)
    
    def get_ttf_font_property(self, font_type, property_name, default_value="NOT_FOUND"):
        """Generic method to get TTF font properties (name or path) with caching
        
        Args:
            font_type: "openmoji" or "noto"
            property_name: "font_name" or "font_path"
            default_value: Default value if property not found
            
        Returns:
            Font property value (name or path)
        """
        color_mode = "color" if self.color_radio.isChecked() else "black"
        cache_key = f"{property_name}_{color_mode}"
        cache_dict = self.openmoji_ttf_fonts if font_type == "openmoji" else self.google_noto_ttf_fonts
        
        # Check cache
        if cache_key in cache_dict:
            cached_value = cache_dict[cache_key]
            # For paths, validate existence
            if property_name == "font_path" and cached_value != "NOT_FOUND":
                return cached_value if os.path.exists(cached_value) else None
            return None if cached_value == "NOT_FOUND" else cached_value
        
        # Compute value based on font type and property
        if font_type == "openmoji":
            if property_name == "font_name":
                value = "OpenMoji"
            else:  # font_path
                value = self.find_openmoji_ttf_path(color_mode)
        else:  # noto
            if property_name == "font_name":
                value = self.get_noto_font_name(color_mode)
            else:  # font_path
                value = self.find_noto_ttf_path(color_mode)
        
        # Cache and return
        cache_dict[cache_key] = value if value else "NOT_FOUND"
        return value
    
    def find_openmoji_ttf_path(self, color_mode):
        """Find OpenMoji TTF font file path"""
        if color_mode == "color":
            # Try COLR v1, then COLR v0, then COLR v0 with SVG
            font_variants = [
                "OpenMoji-color-glyf_colr_1",
                "OpenMoji-color-glyf_colr_0",
                "OpenMoji-color-colr0_svg",
            ]
            for variant in font_variants:
                candidate_path = os.path.join(self.path_manager.packages_dir, "OpenMoji", "openmoji-font", variant)
                if os.path.exists(candidate_path):
                    font_folder = candidate_path
                    break
            else:
                font_folder = self.path_manager.get_path("openmoji_color_ttf_folder")
        else:
            font_folder = self.path_manager.get_path("openmoji_black_ttf_folder")
        
        # Find TTF file in folder
        if os.path.exists(font_folder):
            for filename in os.listdir(font_folder):
                if filename.endswith('.ttf'):
                    return os.path.join(font_folder, filename)
        return None
    
    def get_noto_font_name(self, color_mode):
        """Get Noto font name (from registered fonts for Black, placeholder for Color)"""
        if color_mode == "black":
            font_path = self.find_noto_ttf_path(color_mode)
            if font_path and font_path in self.registered_font_families:
                return self.registered_font_families[font_path]
            return "Segoe UI Emoji"  # Fallback
        return "Noto Color Emoji"
    
    def find_noto_ttf_path(self, color_mode):
        """Find Noto TTF font file path"""
        package_info = self.emoji_packages.get("Noto", {})
        font_path = package_info.get("color_font" if color_mode == "color" else "black_font")
        return font_path if font_path and os.path.exists(font_path) else None
    
    def get_openmoji_ttf_font_name(self):
        """Get the OpenMoji TTF font name (not used for rendering, only for fallback)"""
        return self.get_ttf_font_property("openmoji", "font_name", "OpenMoji")
    
    def get_openmoji_ttf_font_path(self):
        """Get the OpenMoji TTF font file path"""
        return self.get_ttf_font_property("openmoji", "font_path")
    
    def get_google_noto_ttf_font_name(self):
        """Get the Noto TTF font name from registered fonts cache (Black) or placeholder (Color)"""
        return self.get_ttf_font_property("noto", "font_name", "Segoe UI Emoji")
    
    def get_google_noto_ttf_font_path(self):
        """Get the Noto TTF font file path"""
        return self.get_ttf_font_property("noto", "font_path")
    
    def render_emoji_with_skia(self, emoji, size, font_path):
        """Render emoji using Skia for all TTF fonts (COLR and monochrome)"""
        if not SKIA_AVAILABLE or not skia_renderer:
            return None
        
        try:
            # Determine the font type from the path
            is_color_font = "color" in font_path.lower()
            is_noto = "noto" in font_path.lower()
            
            # Determine if this is a black/monochrome font
            # For Noto: check radio button state since filenames don't contain "black"
            # For OpenMoji: check if "black" is in filename
            if is_noto:
                is_black_font = not self.color_radio.isChecked()
            else:
                is_black_font = "black" in font_path.lower()
            
            # Determine if this is a monochrome font
            is_monochrome = is_black_font and not is_color_font
            
            # Render with Skia
            if is_monochrome:
                icon = skia_renderer.render_emoji_to_pixmap(
                    emoji, 
                    font_path, 
                    size, 
                    is_monochrome=True, 
                    monochrome_color=(0, 0, 0, 255)  # Black
                )
                if icon:
                    return icon
            else:
                icon = skia_renderer.render_emoji_to_pixmap(emoji, font_path, size)
                if icon:
                    return icon
            
            return None
            
        except Exception:
            return None
    
    def render_image_to_icon(self, image_path, size):
        """Render an image file (PNG/SVG) to QIcon with Skia or Qt fallback
        
        Args:
            image_path: Path to image file
            size: Target size for icon
            
        Returns:
            QIcon or None if rendering failed
        """
        if not os.path.exists(image_path):
            return None
        
        icon = None
        is_svg = image_path.endswith('.svg')
        
        # Try Skia first
        if SKIA_AVAILABLE and skia_renderer and skia_renderer.initialized:
            icon = skia_renderer.render_svg_file(image_path, size) if is_svg else skia_renderer.render_image_file(image_path, size)
        
        # Fallback to Qt
        if not icon:
            if is_svg:
                svg_renderer = QSvgRenderer(image_path)
                if svg_renderer.isValid():
                    pixmap = QPixmap(size, size)
                    pixmap.fill(Qt.transparent)
                    painter = QPainter(pixmap)
                    svg_renderer.render(painter)
                    painter.end()
                    icon = QIcon(pixmap)
            else:
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon = QIcon(pixmap)
        
        return icon
    
    def create_emojitwo_component_icon(self, emoji_code, size):
        """Create icon for EmojiTwo component category (1F3FD emoji)
        
        Args:
            emoji_code: Unicode emoji code
            size: Target size for icon
            
        Returns:
            QIcon or None
        """
        if self.black_radio.isChecked():
            # Use special icon from misc folder since EmojiTwo Black doesn't have this emoji
            misc_icon_path = self.path_manager.get_misc_file("Emojitwo_component_1f3fd.png")
            return self.render_image_to_icon(misc_icon_path, size)
        
        # Color mode - load from EmojiTwo Color folder
        if self.png_radio.isChecked():
            emoji_path = os.path.join(self.emoji_folder, f"{emoji_code.lower()}.png")
            
            # Fallback to default folder if not found
            if not os.path.exists(emoji_path):
                try:
                    default_folder = self.path_manager.get_path("emojitwo_color_default_png")
                    emoji_path = os.path.join(default_folder, f"{emoji_code.lower()}.png")
                except KeyError:
                    pass
            
            return self.render_image_to_icon(emoji_path, size)
        
        elif self.svg_radio.isChecked():
            try:
                svg_folder = self.path_manager.get_path("emojitwo_color_svg")
                emoji_path = os.path.join(svg_folder, f"{emoji_code.lower()}.svg")
                return self.render_image_to_icon(emoji_path, size)
            except KeyError:
                return None
        
        return None
    
    def create_category_icon(self, emoji_code, size=32):
        """Create an icon for a category using emoji code with system font fallback"""
        # Convert emoji code to emoji character
        emoji = self.emoji_manager.unicode_to_emoji(emoji_code + ".png")  # unicode_to_emoji handles .png extension
        if not emoji:
            return None
        
        package_info = self.emoji_packages.get(self.current_emoji_package, {})
        package_type = package_info.get("type", "files")
        
        # Create cache key that includes color/black variant and theme for automatic inversion
        color_mode = "color" if self.color_radio.isChecked() else "black"
        cache_key = (f"category_{emoji_code}", size, self.emoji_folder if package_type == "files" else self.current_emoji_package, color_mode if package_type != "files" else None, self.current_theme)
        
        # Check cache
        cached_icon = self.cache_manager.get(cache_key)
        if cached_icon:
            return cached_icon
        
        # Special handling for EmojiTwo component category (1F3FD emoji)
        icon = None
        if self.current_emoji_package == "EmojiTwo" and emoji_code == "1F3FD":
            icon = self.create_emojitwo_component_icon(emoji_code, size)
        
        # Try standard loading if special handling didn't apply or failed
        if not icon:
            icon = self.create_emoji_icon(emoji, size, is_category_icon=True)
        
        # Final fallback: system font rendering
        if not icon:
            font_name = package_info.get("font_name", "Segoe UI Emoji") if package_type == "system_font" else "Segoe UI Emoji"
            font_size = max(8, size // 2)
            font = QFont(font_name, font_size)
            
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setFont(font)
            painter.drawText(0, 0, size, size, Qt.AlignCenter, emoji)
            painter.end()
            
            icon = QIcon(pixmap)
        
        # Automatic color inversion for category icons when Dark/Medium theme + Black mode
        # This is independent of the Contrast button (which only affects grid emojis)
        if icon and self.current_theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM] and not self.color_radio.isChecked():
            icon = self.invert_icon_colors(icon, size)
        
        # Store in cache
        if icon:
            self.cache_manager.set(cache_key, icon)
        
        return icon
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PurrMoji Emoji Picker")
        self.setFixedSize(800, 1000)  # Increased height to accommodate all footer elements
        
        # Set window icon
        icon_path = self.path_manager.get_misc_file("Kitty-Head.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Set default font for the application
        default_font = QFont("Segoe UI", 10)
        self.setFont(default_font)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)  # Standard margins for all categories
        self.main_layout.setSpacing(11)  # Default spacing between elements
        
        # Create search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(6)  # Explicit spacing between search bar elements
        
        # Emoji package dropdown
        self.emoji_package_combo = QComboBox()
        # Get available package names from emoji_packages (already filtered by filter_unavailable_system_fonts)
        package_names = list(self.emoji_packages.keys())
        # Ensure consistent order: EmojiTwo, Noto, OpenMoji, Segoe UI Emoji (if available), Twemoji, Kaomoji, Custom
        preferred_order = ["EmojiTwo", "Noto", "OpenMoji", "Segoe UI Emoji", "Twemoji", "Kaomoji", "Custom"]
        ordered_package_names = []
        for preferred_name in preferred_order:
            if preferred_name in package_names:
                ordered_package_names.append(preferred_name)
        # Add any remaining packages not in preferred order
        for package_name in package_names:
            if package_name not in ordered_package_names:
                ordered_package_names.append(package_name)
        
        self.emoji_package_combo.addItems(ordered_package_names)
        
        # Set the package dropdown to match current_emoji_package (already set in __init__ according to preferences)
        try:
            current_index = ordered_package_names.index(self.current_emoji_package)
            self.emoji_package_combo.setCurrentIndex(current_index)
        except (ValueError, AttributeError):
            # If current package not found, default to EmojiTwo (index 0)
            self.emoji_package_combo.setCurrentIndex(0)
            self.current_emoji_package = ordered_package_names[0] if ordered_package_names else "EmojiTwo"
        
        self.emoji_package_combo.setFixedWidth(200)
        package_font = QFont("Segoe UI", 9)
        self.emoji_package_combo.setFont(package_font)
        self.emoji_package_combo.setToolTip("Select emoji package/font to display")
        self.emoji_package_combo.currentIndexChanged.connect(self.on_emoji_package_change)
        search_layout.addWidget(self.emoji_package_combo)
        
        # Variation filter dropdown
        self.variation_filter_combo = QComboBox()
        self.variation_filter_combo.addItems(["All emojis", "Only the ones with variations", "Only the ones without variations"])
        self.variation_filter_combo.setFixedWidth(250)  # Increased from 220 to 250
        variation_font = QFont("Segoe UI", 9)
        self.variation_filter_combo.setFont(variation_font)
        self.variation_filter_combo.setToolTip("Filter emojis by variation availability")
        self.variation_filter_combo.currentIndexChanged.connect(self.on_variation_filter_change)
        search_layout.addWidget(self.variation_filter_combo)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search emojis...")
        # Set smaller font for search
        search_font = QFont("Segoe UI", 10)
        self.search_edit.setFont(search_font)
        self.search_edit.textChanged.connect(self.on_search_change)
        # Apply theme-specific stylesheet
        self.search_edit.setStyleSheet(ThemeManager.get_search_edit_stylesheet(self.current_theme))
        # Set placeholder text color based on theme
        palette = self.search_edit.palette()
        if self.current_theme == ThemeManager.THEME_LIGHT:
            palette.setColor(QPalette.PlaceholderText, QColor("#999999"))
        else:  # Medium or Dark
            palette.setColor(QPalette.PlaceholderText, QColor("#888888"))
        self.search_edit.setPalette(palette)
        search_layout.addWidget(self.search_edit)
        
        # Clear button
        self.clear_button = QPushButton("✕")
        self.clear_button.setFixedSize(25, 30)
        clear_font = QFont("Segoe UI", 9)
        self.clear_button.setFont(clear_font)
        self.clear_button.setToolTip("Clear search field")
        self.clear_button.clicked.connect(self.clear_search)
        # No custom stylesheet - use default style like other buttons (adapts to theme automatically)
        search_layout.addWidget(self.clear_button)
        
        self.main_layout.addLayout(search_layout)
        
        # Create radio buttons container widget
        self.radio_buttons_container = QWidget()
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(0)  # No default spacing, use explicit addSpacing() instead
        radio_layout.setContentsMargins(0, 0, 0, 0)
        
        # Color/Black radio buttons
        self.color_radio = QRadioButton("Color")
        self.black_radio = QRadioButton("Black")
        radio_font = QFont("Segoe UI", 9)
        self.color_radio.setFont(radio_font)
        self.black_radio.setFont(radio_font)
        self.color_radio.setChecked(True)  # Default to Color
        
        # Open Custom Folder button
        self.open_custom_folder_button = QPushButton("Open custom folder")
        self.open_custom_folder_button.setFont(radio_font)
        self.open_custom_folder_button.setFixedWidth(160)  # Widened by 10px
        self.open_custom_folder_button.setVisible(False)  # Hidden by default
        self.open_custom_folder_button.clicked.connect(self.open_custom_emoji_folder)
        
        # Refresh custom emojis button
        self.refresh_custom_button = QPushButton("🔄")
        self.refresh_custom_button.setFont(radio_font)
        self.refresh_custom_button.setFixedWidth(32)  # Small button for emoji icon
        self.refresh_custom_button.setVisible(False)  # Hidden by default
        self.refresh_custom_button.setToolTip("Refresh custom emojis folder")
        self.refresh_custom_button.clicked.connect(self.refresh_custom_emojis)
        
        # Create button group for Color/Black
        self.color_black_group = QButtonGroup()
        self.color_black_group.addButton(self.color_radio, 0)
        self.color_black_group.addButton(self.black_radio, 1)
        self.color_black_group.buttonClicked.connect(self.on_color_black_change)
        
        # Size radio buttons
        self.size_72_radio = QRadioButton("72 px")
        self.size_618_radio = QRadioButton("618 px")
        self.size_72_radio.setFont(radio_font)
        self.size_618_radio.setFont(radio_font)
        self.size_72_radio.setChecked(True)  # Default to 72px
        
        # Format radio buttons (PNG/SVG/TTF)
        self.png_radio = QRadioButton("PNG")
        self.svg_radio = QRadioButton("SVG")
        self.ttf_radio = QRadioButton("TTF")
        self.png_radio.setFont(radio_font)
        self.svg_radio.setFont(radio_font)
        self.ttf_radio.setFont(radio_font)
        self.png_radio.setChecked(True)  # Default to PNG
        
        # Create button group for Size
        self.size_group = QButtonGroup()
        self.size_group.addButton(self.size_72_radio, 0)
        self.size_group.addButton(self.size_618_radio, 1)
        self.size_group.buttonClicked.connect(self.on_size_radio_change)
        
        # Create button group for Format
        self.format_group = QButtonGroup()
        self.format_group.addButton(self.png_radio, 0)
        self.format_group.addButton(self.svg_radio, 1)
        self.format_group.addButton(self.ttf_radio, 2)
        self.format_group.buttonClicked.connect(self.on_format_radio_change)
        
        # Add radio buttons to layout - Color/Black, PNG/SVG/TTF, 72px/618px
        radio_layout.addWidget(self.color_radio)
        radio_layout.addSpacing(5)  # Small spacing between Color and Black
        radio_layout.addWidget(self.black_radio)
        radio_layout.addWidget(self.open_custom_folder_button)
        radio_layout.addWidget(self.refresh_custom_button)
        radio_layout.addStretch()  # Push center buttons to center
        radio_layout.addWidget(self.png_radio)
        radio_layout.addSpacing(5)  # Small spacing between PNG and SVG
        radio_layout.addWidget(self.svg_radio)
        radio_layout.addSpacing(5)  # Small spacing between SVG and TTF
        radio_layout.addWidget(self.ttf_radio)
        radio_layout.addStretch()  # Push size buttons to the right
        radio_layout.addWidget(self.size_72_radio)
        radio_layout.addSpacing(5)  # Small spacing between 72px and 618px
        radio_layout.addWidget(self.size_618_radio)
        
        self.radio_buttons_container.setLayout(radio_layout)
        self.main_layout.addWidget(self.radio_buttons_container)
        
        # Update size radio buttons state based on format selection (initially PNG is selected)
        self.update_size_radio_buttons_state()
        
        # Create category tabs
        self.create_category_tabs(self.main_layout)
        
        # Create subcategory tabs (initially hidden)
        self.create_subcategory_tabs(self.main_layout)
        
        # Create emoji grid container
        self.emoji_scroll_area = EmojiScrollArea()
        self.base_grid_height = 680  # Base height when no subcategories
        self.subcategory_row_height = 35  # Height of one subcategory row (30px button + 5px margin)
        self.emoji_scroll_area.setFixedSize(780, self.base_grid_height)
        self.emoji_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.emoji_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.emoji_scroll_area.setWidgetResizable(True)
        
        self.emoji_widget = QWidget()
        self.emoji_layout = QGridLayout(self.emoji_widget)
        self.emoji_layout.setSpacing(1)  # Minimal spacing for tight grid
        self.emoji_layout.setContentsMargins(0, 0, 0, 0)  # No margins for top-left alignment
        self.emoji_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Force top-left alignment
        self.emoji_scroll_area.setWidget(self.emoji_widget)
        
        # Connect wheel event with Ctrl modifier to size adjustment handler
        self.emoji_scroll_area.wheelEventWithCtrl.connect(self.on_wheel_event_with_ctrl)
        
        self.main_layout.addWidget(self.emoji_scroll_area)
        
        # Status widget with emoji preview (empty by default, filled when emoji is selected)
        self.status_widget = QWidget()
        self.status_layout = QHBoxLayout(self.status_widget)
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setSpacing(4)
        
        # Emoji preview label (for icon/pixmap)
        self.status_emoji_label = QLabel()
        self.status_emoji_label.setFixedSize(24, 24)
        self.status_emoji_label.setAlignment(Qt.AlignCenter)
        self.status_emoji_label.setScaledContents(True)
        self.status_layout.addWidget(self.status_emoji_label)
        
        # Text label (for emoji name/info)
        self.status_text_label = QLabel("")
        self.status_text_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        status_font = QFont("Segoe UI", 9)
        self.status_text_label.setFont(status_font)
        self.status_layout.addWidget(self.status_text_label)
        
        self.status_widget.setMinimumHeight(32)
        
        # Displayed emojis label (shows current folder or TTF file name)
        self.displayed_emoji_source_label = QLabel("Displayed emojis: EmojiTwo Color PNG 72px")
        self.displayed_emoji_source_label.setMinimumWidth(200)
        self.displayed_emoji_source_label.setFixedHeight(30)
        # Set smaller font for source label
        source_font = QFont("Segoe UI", 9)
        self.displayed_emoji_source_label.setFont(source_font)
        
        # Displayed emojis counter label (always visible)
        self.displayed_emojis_counter = QLabel("Displayed emojis: 0")
        self.displayed_emojis_counter.setMinimumWidth(150)  # Changed to minimum width instead of fixed
        self.displayed_emojis_counter.setFixedHeight(30)
        # Set smaller font for counter label
        counter_font = QFont("Segoe UI", 9)
        self.displayed_emojis_counter.setFont(counter_font)        
        
        # Size controls with input field and +/- buttons
        self.size_label = QLabel("Size:")
        size_font = QFont("Segoe UI", 9)
        self.size_label.setFont(size_font)

        # Contrast button (inverts emoji colors in Black + Dark theme)
        self.contrast_button = QPushButton()
        self.contrast_button.setFixedSize(25, 25)
        self.contrast_button.setToolTip("Invert emoji colors (useful in Black + Dark theme)")
        self.contrast_button.clicked.connect(self.on_contrast_toggle)
        # Load contrast icon SVG
        contrast_icon_path = self.path_manager.get_misc_file("mono-contrast.svg")
        if os.path.exists(contrast_icon_path):
            contrast_icon = QIcon(contrast_icon_path)
            self.contrast_button.setIcon(contrast_icon)
            self.contrast_button.setIconSize(QSize(20, 20))
                
        # Background color button (displays current color)
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedSize(25, 25)
        self.bg_color_button.setToolTip("Change emoji background color")
        self.bg_color_button.clicked.connect(self.on_background_color_change)
        self.update_bg_color_button_style()        

        # Decrease size button (-)
        self.decrease_size_button = QPushButton("-")
        self.decrease_size_button.setFixedSize(25, 25)
        self.decrease_size_button.setFont(size_font)
        self.decrease_size_button.setToolTip("Decrease emoji size to nearest predefined size")
        self.decrease_size_button.clicked.connect(self.on_decrease_size)
        
        # Size input field
        self.size_input = QLineEdit()
        self.size_input.setText(str(self.emoji_size))
        self.size_input.setFixedSize(60, 15)
        self.size_input.setFont(size_font)
        self.size_input.setAlignment(Qt.AlignCenter)
        self.size_input.setToolTip("Enter emoji size in pixels (from 1 to 618)")
        self.size_input.returnPressed.connect(self.on_size_input_change)
        self.size_input.editingFinished.connect(self.on_size_input_change)
        # Apply theme-specific stylesheet for size input
        self.size_input.setStyleSheet(ThemeManager.get_size_input_stylesheet(self.current_theme))
        
        # Increase size button (+)
        self.increase_size_button = QPushButton("+")
        self.increase_size_button.setFixedSize(25, 25)
        self.increase_size_button.setFont(size_font)
        self.increase_size_button.setToolTip("Increase emoji size to nearest predefined size")
        self.increase_size_button.clicked.connect(self.on_increase_size)
        
        # Separator between background color button and size controls
        self.separator_label_3 = QLabel('🔹')
        self.separator_label_3.setFont(counter_font)
        self.separator_label_3.setFixedHeight(30)
        
        # Clear recent button (initially hidden)
        self.clear_recent_button = QPushButton("Clear")
        self.clear_recent_button.setFixedSize(60, 30)
        # Set smaller font for clear recent button
        clear_recent_font = QFont("Segoe UI", 9)
        self.clear_recent_button.setFont(clear_recent_font)
        self.clear_recent_button.setToolTip("Clear all recent emojis")
        self.clear_recent_button.clicked.connect(self.clear_recent_emojis)
        self.clear_recent_button.hide()
        
        # Add to favorites button (always visible)
        self.add_favorite_button = QPushButton("Add to favorites")
        self.add_favorite_button.setFixedSize(130, 30)
        favorite_font = QFont("Segoe UI", 9)
        self.add_favorite_button.setFont(favorite_font)
        self.add_favorite_button.setToolTip("Add/Remove selected emoji to/from favorites (or use Shift + Click to toggle)")
        self.add_favorite_button.clicked.connect(self.add_to_favorites)
        
        # Copy button (always visible)
        self.copy_button = QPushButton("Copy to clipboard")
        self.copy_button.setFixedSize(140, 30)
        copy_font = QFont("Segoe UI", 9)
        self.copy_button.setFont(copy_font)
        self.copy_button.setToolTip("Copy selected emoji to clipboard")
        self.copy_button.clicked.connect(self.copy_selected_emoji)
        
        # Footer container with fixed height to stay at bottom
        self.footer_widget = QWidget()
        self.footer_widget.setFixedHeight(110)  # Increased height to accommodate spacing
        self.footer_layout = QVBoxLayout(self.footer_widget)
        self.footer_layout.setContentsMargins(0, 0, 0, 15)  # Add bottom margin for spacing
        self.footer_layout.setSpacing(13)  # Reduced from 15 to 13px to move Size field up by 2px
        self.footer_layout.setAlignment(Qt.AlignTop)  # Align all content to the top
        
        # First row: emoji preview and size controls
        first_row_layout = QHBoxLayout()
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        first_row_layout.setSpacing(5)  # 5px spacing between size controls
        first_row_layout.addWidget(self.status_widget, 0, Qt.AlignLeft)
        first_row_layout.addStretch()
        first_row_layout.addWidget(self.contrast_button)
        first_row_layout.addWidget(self.bg_color_button)
        first_row_layout.addWidget(self.separator_label_3)
        first_row_layout.addWidget(self.size_label)
        first_row_layout.addWidget(self.size_input)
        first_row_layout.addWidget(self.decrease_size_button)
        first_row_layout.addWidget(self.increase_size_button)
        
        # Second row: counters, clear button, add to favorites button, copy button
        second_row_layout = QHBoxLayout()
        second_row_layout.setContentsMargins(0, 0, 0, 0)
        second_row_layout.setSpacing(5)  # 5px spacing between action buttons
        second_row_layout.addWidget(self.displayed_emojis_counter, 0, Qt.AlignLeft)
        second_row_layout.addStretch()
        second_row_layout.addWidget(self.clear_recent_button)
        second_row_layout.addWidget(self.add_favorite_button)
        second_row_layout.addWidget(self.copy_button)
        
        # Hotkeys button (will be added to third row)
        self.hotkeys_button = QPushButton("Hotkeys")
        self.hotkeys_button.setFixedSize(80, 30)
        self.hotkeys_button.clicked.connect(self.show_hotkeys_dialog)
        self.hotkeys_button.setFont(counter_font)
        self.hotkeys_button.setToolTip("View keyboard shortcuts")
        
        # Settings button (will be added to third row)
        self.settings_button = QPushButton("Settings")
        self.settings_button.setFixedSize(80, 30)
        self.settings_button.clicked.connect(self.show_settings_dialog)
        self.settings_button.setFont(counter_font)
        self.settings_button.setToolTip("Configure which settings to save")
        
        # About button (will be added to third row)
        self.about_button = QPushButton("About")
        self.about_button.setFixedSize(80, 30)
        self.about_button.clicked.connect(self.show_about_dialog)
        self.about_button.setFont(counter_font)
        self.about_button.setToolTip("About PurrMoji Emoji Picker")
        
        # Third row: displayed emoji source on left, hotkeys/settings/about buttons on right
        third_row_layout = QHBoxLayout()
        third_row_layout.setSpacing(5)  # Same spacing as between action buttons (Add to favorites, Copy to clipboard)
        third_row_layout.addWidget(self.displayed_emoji_source_label, 0, Qt.AlignLeft)
        third_row_layout.addStretch()
        third_row_layout.addWidget(self.hotkeys_button)
        third_row_layout.addWidget(self.settings_button)
        third_row_layout.addWidget(self.about_button)
        
        self.footer_layout.addLayout(first_row_layout)
        self.footer_layout.addLayout(second_row_layout)
        self.footer_layout.addLayout(third_row_layout)
        
        # Add footer to main layout - this will keep it at the bottom
        # Add stretch before footer to absorb extra space and prevent spacing expansion
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.footer_widget)
    
    def create_category_tabs(self, parent_layout):
        """Create category tab buttons"""
        categories = ["Recent & Favorites", "activities", "animals-nature", "component", "flags", 
                     "food-drink", "objects", "people-body", "smileys-emotion", 
                     "symbols", "travel-places", "extras-openmoji", "extras-unicode"]
        # SVG icons for special categories (Recent & Favorites, extras)
        category_svg_icons = {
            "Recent & Favorites": self.path_manager.get_misc_file("Recent_Favorites.svg"),
            "extras-openmoji": self.path_manager.get_misc_file("extras_OpenMoji.svg"),
            "extras-unicode": self.path_manager.get_misc_file("extras_Unicode.svg")
        }
        category_names = {
            "Recent & Favorites": "Recent & Favorites",
            "activities": "Activities",
            "animals-nature": "Animals & Nature",
            "component": "Component",
            "flags": "Flags",
            "food-drink": "Food & Drink",
            "objects": "Objects",
            "people-body": "People & Body",
            "smileys-emotion": "Smileys & Emotion",
            "symbols": "Symbols",
            "travel-places": "Travel & Places",
            "extras-openmoji": "Extras OpenMoji",
            "extras-unicode": "Extras Unicode"
        }
        
        # Create container widget for category buttons
        self.category_buttons_container = QWidget()
        tabs_layout = QHBoxLayout(self.category_buttons_container)
        tabs_layout.setSpacing(0)  # No spacing between category buttons
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        self.category_buttons = {}  # Store category buttons for visual feedback
        
        for category in categories:
            btn = QPushButton()
            btn.setFixedSize(60, 40)
            
            # Load icon - use emoji for 10 dynamic categories, SVG for special ones
            if category in category_svg_icons:
                # Load static SVG icon for special categories
                svg_path = category_svg_icons[category]
                icon = self.load_svg_icon_with_theme(svg_path, 32)
                if icon:
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(32, 32))
            elif category in self.category_emoji_codes:
                # Load dynamic emoji icon for 10 main categories
                emoji_code = self.category_emoji_codes[category]
                icon = self.create_category_icon(emoji_code, 32)
                if icon:
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(32, 32))
            
            # Style for inactive buttons
            btn.setStyleSheet(self.get_inactive_category_stylesheet())
            
            btn.clicked.connect(lambda checked, cat=category: self.on_category_click(cat))
            btn.setToolTip(category_names[category])  # Add tooltip with category name
            tabs_layout.addWidget(btn)
            self.category_buttons[category] = btn
        
        parent_layout.addWidget(self.category_buttons_container)
    
    def create_kaomoji_category_tabs(self):
        """Create category tab buttons specifically for Kaomoji package"""
        # Clear existing category buttons
        for button in list(self.category_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass
        self.category_buttons.clear()
        
        # Kaomoji categories with their emoji icons (using Segoe UI Emoji)
        # Use OrderedDict-like list to maintain order, with Recent & Favorites first
        kaomoji_categories = [
            ("recent_favorites", {"name": "Recent & Favorites", "emoji": "❤️", "use_svg": True}),
            ("happy", {"name": "Happy", "emoji": "😊", "use_svg": False}),
            ("sad", {"name": "Sad", "emoji": "😢", "use_svg": False}),
            ("angry", {"name": "Angry", "emoji": "😠", "use_svg": False}),
            ("surprised", {"name": "Surprised", "emoji": "😲", "use_svg": False}),
            ("confused", {"name": "Confused", "emoji": "😕", "use_svg": False}),
            ("sleepy", {"name": "Sleepy", "emoji": "😴", "use_svg": False}),
            ("greetings", {"name": "Greetings", "emoji": "👋", "use_svg": False}),
            ("animals", {"name": "Animals", "emoji": "🐾", "use_svg": False}),
            ("actions", {"name": "Actions", "emoji": "🏃", "use_svg": False}),
            ("objects", {"name": "Misc", "emoji": "🎵", "use_svg": False}),
            ("special", {"name": "Special", "emoji": "⭐", "use_svg": False})
        ]
        
        # Get existing layout or create error
        tabs_layout = self.category_buttons_container.layout()
        if tabs_layout is None:
            print("[ERROR] category_buttons_container has no layout! This should not happen.", file=sys.stderr)
            return
        
        # Clear existing layout content
        while tabs_layout.count():
            item = tabs_layout.takeAt(0)
            if item.widget():
                try:
                    item.widget().deleteLater()
                except RuntimeError:
                    pass
        
        # Get project root for SVG icons
        recent_favorites_svg = self.path_manager.get_misc_file("Recent_Favorites.svg")
        
        # Add Kaomoji category buttons to existing layout
        for category_key, category_info in kaomoji_categories:
            btn = QPushButton()
            btn.setFixedSize(60, 40)
            
            # Check if we should use SVG icon
            if category_info.get("use_svg", False) and category_key == "recent_favorites":
                # Use SVG icon for Recent & Favorites (same as other packages)
                icon = self.load_svg_icon_with_theme(recent_favorites_svg, 32)
                if icon:
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(32, 32))
            else:
                # Create icon from emoji using system font rendering
                emoji_code = category_info["emoji"]
                emoji_pixmap = QPixmap(32, 32)
                emoji_pixmap.fill(Qt.transparent)
                painter = QPainter(emoji_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.TextAntialiasing)
                
                # Use Segoe UI Emoji font with smaller size to prevent clipping
                emoji_font = QFont("Segoe UI Emoji", 16)
                painter.setFont(emoji_font)
                painter.drawText(emoji_pixmap.rect(), Qt.AlignCenter, emoji_code)
                painter.end()
                
                icon = QIcon(emoji_pixmap)
                btn.setIcon(icon)
                btn.setIconSize(QSize(32, 32))
            
            # Style for inactive buttons
            btn.setStyleSheet(self.get_inactive_category_stylesheet())
            
            btn.clicked.connect(lambda checked, cat=category_key: self.on_kaomoji_category_click(cat))
            btn.setToolTip(category_info["name"])
            tabs_layout.addWidget(btn)
            self.category_buttons[category_key] = btn
        
        # Show the container
        self.category_buttons_container.show()
        
        # Show Clear button if in Recent/Favorites, hide for other categories
        if self.current_category == "recent_favorites":
            self.clear_recent_button.show()
        else:
            self.clear_recent_button.hide()
    
    def restore_standard_category_tabs(self):
        """Restore standard emoji category tab buttons after Kaomoji"""
        # Clear existing category buttons
        for button in list(self.category_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass
        self.category_buttons.clear()
        
        # Get existing layout
        tabs_layout = self.category_buttons_container.layout()
        if tabs_layout is None:
            print("[ERROR] category_buttons_container has no layout! This should not happen.", file=sys.stderr)
            return
        
        # Clear existing layout content
        while tabs_layout.count():
            item = tabs_layout.takeAt(0)
            if item.widget():
                try:
                    item.widget().deleteLater()
                except RuntimeError:
                    pass
        
        # Standard categories
        categories = ["Recent & Favorites", "activities", "animals-nature", "component", "flags", 
                     "food-drink", "objects", "people-body", "smileys-emotion", 
                     "symbols", "travel-places", "extras-openmoji", "extras-unicode"]
        
        # SVG icons for special categories
        category_svg_icons = {
            "Recent & Favorites": self.path_manager.get_misc_file("Recent_Favorites.svg"),
            "extras-openmoji": self.path_manager.get_misc_file("extras_OpenMoji.svg"),
            "extras-unicode": self.path_manager.get_misc_file("extras_Unicode.svg")
        }
        category_names = {
            "Recent & Favorites": "Recent & Favorites",
            "activities": "Activities",
            "animals-nature": "Animals & Nature",
            "component": "Component",
            "flags": "Flags",
            "food-drink": "Food & Drink",
            "objects": "Objects",
            "people-body": "People & Body",
            "smileys-emotion": "Smileys & Emotion",
            "symbols": "Symbols",
            "travel-places": "Travel & Places",
            "extras-openmoji": "Extras OpenMoji",
            "extras-unicode": "Extras Unicode"
        }
        
        # Create standard category buttons
        for category in categories:
            btn = QPushButton()
            btn.setFixedSize(60, 40)
            
            # Load icon - use emoji for 10 dynamic categories, SVG for special ones
            if category in category_svg_icons:
                svg_path = category_svg_icons[category]
                icon = self.load_svg_icon_with_theme(svg_path, 32)
                if icon:
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(32, 32))
            elif category in self.category_emoji_codes:
                emoji_code = self.category_emoji_codes[category]
                icon = self.create_category_icon(emoji_code, 32)
                if icon:
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(32, 32))
            
            # Style for inactive buttons
            btn.setStyleSheet(self.get_inactive_category_stylesheet())
            
            btn.clicked.connect(lambda checked, cat=category: self.on_category_click(cat))
            btn.setToolTip(category_names[category])
            tabs_layout.addWidget(btn)
            self.category_buttons[category] = btn
        
        # Update category button styles to show current category
        if hasattr(self, 'current_category') and self.current_category in self.category_buttons:
            self.update_category_button_styles(self.current_category)
        
        # Show the container
        self.category_buttons_container.show()
        
        # Show/hide the clear recent button based on current category
        # Restore proper state after switching from another package
        if self.current_category in ["Recent & Favorites", "recent_favorites"]:
            self.clear_recent_button.show()
        else:
            self.clear_recent_button.hide()
    
    def create_subcategory_tabs(self, parent_layout):
        """Create subcategory tab buttons (initially hidden)"""
        self.subcategory_container = QWidget()
        self.subcategory_container.setMinimumHeight(10)  # Minimum height to maintain spacing consistency
        self.subcategory_main_layout = QVBoxLayout(self.subcategory_container)
        self.subcategory_main_layout.setSpacing(3)
        self.subcategory_main_layout.setContentsMargins(0, 5, 0, 5)
        
        # Create up to three rows for subcategory buttons (will be added dynamically)
        self.subcategory_row_layouts = []
        
        self.subcategory_buttons = {}  # Store subcategory buttons
        
        parent_layout.addWidget(self.subcategory_container)
    
    def calculate_button_width(self, text):
        """Calculate precise width needed for a button based on actual text rendering"""
        # Create QFontMetrics for the exact font used in subcategory buttons
        font = QFont("Segoe UI", 9)
        font_metrics = QFontMetrics(font)
        
        # Get the actual pixel width of the text
        text_width = font_metrics.horizontalAdvance(text)
        
        # Add padding (5px left + 5px right = 10px), borders (2px), and extra margin for safety
        padding_and_border = 16
        min_width = 60
        
        calculated_width = text_width + padding_and_border
        return max(min_width, calculated_width)
    
    def create_recent_favorites_subcategories(self):
        """Create Recent, Favorites and Frequently used subcategory buttons for Recent & Favorites category"""
        # Clear existing subcategory buttons safely
        for button in list(self.subcategory_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass
        self.subcategory_buttons.clear()
        
        # Clear existing Kaomoji tab buttons safely
        for button in list(self.kaomoji_tab_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass
        self.kaomoji_tab_buttons.clear()
        
        # Remove all existing row layouts safely
        for row_layout in self.subcategory_row_layouts:
            while row_layout.count():
                item = row_layout.takeAt(0)
                if item.widget():
                    try:
                        item.widget().deleteLater()
                    except RuntimeError:
                        pass
            try:
                self.subcategory_main_layout.removeItem(row_layout)
            except RuntimeError:
                pass
        self.subcategory_row_layouts.clear()
        
        # Create one row layout for the three buttons
        row_layout = QHBoxLayout()
        row_layout.setSpacing(2)
        self.subcategory_row_layouts.append(row_layout)
        self.subcategory_main_layout.addLayout(row_layout)
        
        subcategory_font = QFont("Segoe UI", 9)
        
        # Create "Recent" button
        recent_btn = QPushButton("Recent")
        recent_btn.setFixedHeight(30)
        recent_btn.setMinimumWidth(60)
        recent_btn.setFont(subcategory_font)
        recent_btn.setToolTip("Show recently copied emojis")
        
        # Style based on current selection
        if self.current_subcategory == "recent":
            recent_btn.setStyleSheet(self.get_active_button_stylesheet())
        else:
            recent_btn.setStyleSheet(self.get_inactive_button_stylesheet())
        
        recent_btn.clicked.connect(lambda: self.on_subcategory_click(self.current_category, "recent"))
        self.subcategory_buttons["recent"] = recent_btn
        row_layout.addWidget(recent_btn)
        
        # Create "Favorites" button
        favorites_btn = QPushButton("Favorites")
        favorites_btn.setFixedHeight(30)
        favorites_btn.setMinimumWidth(60)
        favorites_btn.setFont(subcategory_font)
        favorites_btn.setToolTip("Show favorite emojis")
        
        # Style based on current selection
        if self.current_subcategory == "favorites":
            favorites_btn.setStyleSheet(self.get_active_button_stylesheet())
        else:
            favorites_btn.setStyleSheet(self.get_inactive_button_stylesheet())
        
        favorites_btn.clicked.connect(lambda: self.on_subcategory_click(self.current_category, "favorites"))
        self.subcategory_buttons["favorites"] = favorites_btn
        row_layout.addWidget(favorites_btn)
        
        # Create "Frequently used" button
        frequently_used_btn = QPushButton("Frequently used")
        frequently_used_btn.setFixedHeight(30)
        frequently_used_btn.setMinimumWidth(60)
        frequently_used_btn.setFont(subcategory_font)
        frequently_used_btn.setToolTip("Show most frequently used emojis (automatically updated based on usage)")
        
        # Style based on current selection
        if self.current_subcategory == "frequently_used":
            frequently_used_btn.setStyleSheet(self.get_active_button_stylesheet())
        else:
            frequently_used_btn.setStyleSheet(self.get_inactive_button_stylesheet())
        
        frequently_used_btn.clicked.connect(lambda: self.on_subcategory_click(self.current_category, "frequently_used"))
        self.subcategory_buttons["frequently_used"] = frequently_used_btn
        row_layout.addWidget(frequently_used_btn)
        
        # Add stretch to push buttons to the left
        row_layout.addStretch()
        
        # Adjust grid height (1 row of subcategories)
        self.adjust_grid_height_for_subcategories(1)
    
    def get_current_subcategory_rows_count(self):
        """Get the current number of subcategory rows displayed"""
        return len(self.subcategory_row_layouts)
    
    def adjust_grid_height_for_subcategories(self, num_subcategory_rows):
        """Adjust the emoji grid height and subcategory container based on the number of subcategory rows"""
        # Apply 10px reduction for non-Custom/Kaomoji packages to prevent overlap with size buttons
        height_reduction = 10 if self.current_emoji_package not in ["Custom", "Kaomoji"] else 0
        
        # Add 21px extra height specifically for Kaomoji package (only for grid, not window)
        kaomoji_height_bonus = 21 if self.current_emoji_package == "Kaomoji" else 0
        
        # Theme correction: Only Light theme needs +7px to compensate for rendering differences
        # Medium and Dark themes have consistent rendering
        # theme_correction = 7 if self.current_theme == ThemeManager.THEME_LIGHT else 0
        theme_correction = 0  # No longer needed - search bar now has consistent styling across all themes
        
        base_height = self.base_grid_height
        
        if num_subcategory_rows == 0:
            # No subcategories, use base height and minimal container height
            new_height = base_height - height_reduction + kaomoji_height_bonus + theme_correction
            self.subcategory_container.setFixedHeight(10)  # Minimal height to maintain spacing
        elif num_subcategory_rows == 1:
            # 1 row of subcategories, keep base height
            new_height = base_height - height_reduction + kaomoji_height_bonus + theme_correction
            self.subcategory_container.setFixedHeight(40)  # 30px button + 10px margins
        elif num_subcategory_rows == 2:
            # 2 rows of subcategories, reduce height by one row height
            new_height = base_height - self.subcategory_row_height - height_reduction + kaomoji_height_bonus + theme_correction
            self.subcategory_container.setFixedHeight(75)  # 2 rows: (30px + 5px) * 2 + margins
        elif num_subcategory_rows == 3:
            # 3 rows of subcategories, reduce height by two row heights
            new_height = base_height - (self.subcategory_row_height * 2) - height_reduction + kaomoji_height_bonus + theme_correction
            self.subcategory_container.setFixedHeight(110)  # 3 rows: (30px + 5px) * 3 + margins
        else:
            # 4+ rows of subcategories (for Kaomoji), reduce height proportionally
            # Each additional row after the first reduces grid height by subcategory_row_height
            rows_to_subtract = num_subcategory_rows - 1
            new_height = base_height - (self.subcategory_row_height * rows_to_subtract) - height_reduction + kaomoji_height_bonus + theme_correction
            # Calculate container height: (30px button height + 5px spacing) * num_rows + 10px margins
            container_height = (35 * num_subcategory_rows) + 10
            self.subcategory_container.setFixedHeight(container_height)
        
        self.emoji_scroll_area.setFixedSize(780, new_height)
    
    def update_subcategory_buttons(self, category):
        """Update subcategory buttons based on selected category"""
        # Clear existing buttons safely
        for button in list(self.subcategory_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass  # Button already deleted
        self.subcategory_buttons.clear()
        
        # Remove all existing row layouts safely
        for row_layout in self.subcategory_row_layouts:
            while row_layout.count():
                item = row_layout.takeAt(0)
                if item.widget():
                    try:
                        item.widget().deleteLater()
                    except RuntimeError:
                        pass  # Widget already deleted
            # Remove the layout from parent
            try:
                self.subcategory_main_layout.removeItem(row_layout)
            except RuntimeError:
                pass  # Layout already removed
        self.subcategory_row_layouts.clear()
        
        # Special handling for Recent & Favorites category
        if category == "Recent & Favorites":
            # Create Recent and Favorites subcategory buttons
            self.create_recent_favorites_subcategories()
            return
        
        # Check if category has subcategories
        if category not in self.emoji_subcategories:
            self.adjust_grid_height_for_subcategories(0)
            return
        
        subcategories = self.emoji_subcategories.get(category, {})
        if not subcategories:
            self.adjust_grid_height_for_subcategories(0)
            return
        
        subcategory_font = QFont("Segoe UI", 9)
        
        # Calculate button widths and collect button info
        button_info = []
        
        # Add "All" button info
        all_text = "All"
        all_width = self.calculate_button_width(all_text)
        button_info.append({"text": all_text, "width": all_width, "subcat_name": None})
        
        # Add subcategory button info
        for subcat_name in sorted(subcategories.keys()):
            display_name = subcat_name.replace('-', ' ').title()
            btn_width = self.calculate_button_width(display_name)
            button_info.append({"text": display_name, "width": btn_width, "subcat_name": subcat_name})
        
        # Calculate how many rows we need
        available_width = 760  # Approximate usable width (800 - margins - spacing)
        button_spacing = 2
        total_width = sum(info["width"] for info in button_info) + (len(button_info) - 1) * button_spacing
        
        # Determine number of rows needed (1, 2, or 3)
        if total_width <= available_width:
            num_rows = 1
        elif total_width <= available_width * 2:
            num_rows = 2
        else:
            num_rows = 3
        
        # Create the necessary number of row layouts
        for _ in range(num_rows):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            self.subcategory_row_layouts.append(row_layout)
            self.subcategory_main_layout.addLayout(row_layout)
        
        # Distribute buttons across rows - fill each row maximally before moving to next
        rows = [[] for _ in range(num_rows)]
        
        button_index = 0
        for row_idx in range(num_rows):
            current_row_width = 0
            
            # Fill current row with as many buttons as possible
            while button_index < len(button_info):
                button_width = button_info[button_index]["width"]
                
                # Calculate what the width would be if we add this button
                if len(rows[row_idx]) == 0:
                    new_width = button_width
                else:
                    new_width = current_row_width + button_spacing + button_width
                
                # Check if button fits in available width
                # For last row, add all remaining buttons regardless of width
                if row_idx == num_rows - 1 or new_width <= available_width:
                    rows[row_idx].append(button_info[button_index])
                    current_row_width = new_width
                    button_index += 1
                else:
                    # Button doesn't fit, move to next row
                    break
        
        # Create actual buttons and add them to rows
        for row_idx, row_buttons in enumerate(rows):
            for info in row_buttons:
                btn = QPushButton(info["text"])
                btn.setFixedHeight(30)
                btn.setMinimumWidth(60)
                btn.setFont(subcategory_font)
                
                # Special styling for "All" button
                if info["subcat_name"] is None:
                    btn.setStyleSheet(self.get_active_button_stylesheet())
                    btn.clicked.connect(lambda checked=False, cat=category: self.on_subcategory_click(cat, None))
                    btn.setToolTip("Show all emojis in this category")
                    self.subcategory_buttons["All"] = btn
                else:
                    btn.setStyleSheet(self.get_inactive_button_stylesheet())
                    subcat_name = info["subcat_name"]
                    btn.clicked.connect(lambda checked=False, cat=category, sub=subcat_name: self.on_subcategory_click(cat, sub))
                    btn.setToolTip(f"Filter by {info['text']}")
                    self.subcategory_buttons[subcat_name] = btn
                
                self.subcategory_row_layouts[row_idx].addWidget(btn)
            
            # Add stretch to each row
            self.subcategory_row_layouts[row_idx].addStretch()
        
        # Adjust grid height based on number of subcategory rows
        self.adjust_grid_height_for_subcategories(num_rows)
    
    def update_button_group_styles(self, buttons_dict, active_item, active_style, inactive_style, special_case=None):
        """Generic method to update button group styles
        
        Args:
            buttons_dict: Dictionary of {item_name: button_widget}
            active_item: The item name that should be styled as active
            active_style: Stylesheet for active button
            inactive_style: Stylesheet for inactive button
            special_case: Optional function(item_name, active_item) -> bool for custom logic
        """
        for item_name, btn in buttons_dict.items():
            # Use special case logic if provided, otherwise simple equality check
            is_active = special_case(item_name, active_item) if special_case else (item_name == active_item)
            btn.setStyleSheet(active_style if is_active else inactive_style)
    
    def update_subcategory_button_styles(self, active_subcategory):
        """Update visual styles for subcategory buttons"""
        # Special case: "All" is active when active_subcategory is None
        def subcategory_special_case(subcat_name, active):
            return (active is None and subcat_name == "All") or (subcat_name == active)
        
        self.update_button_group_styles(
            self.subcategory_buttons,
            active_subcategory,
            self.get_active_button_stylesheet(),
            self.get_inactive_button_stylesheet(),
            subcategory_special_case
        )
    
    def load_kaomoji_data(self):
        """Load kaomoji data from JSON file"""
        kaomoji_file = os.path.join(os.path.dirname(self.emoji_data_file), 'kaomoji_data.json')
        
        try:
            with open(kaomoji_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.kaomoji_categories = data.get('categories', {})
        except FileNotFoundError:
            print(f"[ERROR] Kaomoji data file not found: {kaomoji_file}", file=sys.stderr)
            self.kaomoji_categories = {}
        except Exception as e:
            print(f"[ERROR] Failed to load kaomoji data: {e}", file=sys.stderr)
            self.kaomoji_categories = {}
    
    def create_kaomoji_subcategory_tabs_for_category(self, category):
        """Create tab buttons for kaomoji subcategories of a specific category"""
        # Clear existing subcategory buttons safely
        for button in list(self.subcategory_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass
        self.subcategory_buttons.clear()
        
        for button in list(self.kaomoji_tab_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass
        self.kaomoji_tab_buttons.clear()
        
        # Remove all existing row layouts safely
        for row_layout in self.subcategory_row_layouts:
            while row_layout.count():
                item = row_layout.takeAt(0)
                if item.widget():
                    try:
                        item.widget().deleteLater()
                    except RuntimeError:
                        pass
            try:
                self.subcategory_main_layout.removeItem(row_layout)
            except RuntimeError:
                pass
        self.subcategory_row_layouts.clear()
        
        if not self.kaomoji_categories or category not in self.kaomoji_categories:
            return
        
        # Get subcategories for this specific category
        category_data = self.kaomoji_categories[category]
        category_name = category_data.get('name', category)
        subcategories = category_data.get('subcategories', {})
        
        if not subcategories:
            return
        
        # Create button info for subcategories
        button_info = []
        subcategory_font = QFont("Segoe UI", 9)
        font_metrics = QFontMetrics(subcategory_font)
        
        for subcat_key, subcat_data in subcategories.items():
            subcat_name = subcat_data.get('name', subcat_key)
            display_text = subcat_name
            
            # Calculate actual width needed for this button
            text_width = font_metrics.horizontalAdvance(display_text)
            button_width = max(60, text_width + 30)
            
            button_info.append({
                "text": display_text,
                "width": button_width,
                "category_key": category,
                "subcat_key": subcat_key
            })
        
        # Distribute buttons across rows based on actual width
        available_width = 750
        button_spacing = 2
        
        rows = []
        current_row_buttons = []
        current_row_width = 0
        
        for info in button_info:
            button_width = info["width"]
            
            if len(current_row_buttons) == 0:
                needed_width = button_width
            else:
                needed_width = current_row_width + button_spacing + button_width
            
            if needed_width <= available_width:
                current_row_buttons.append(info)
                current_row_width = needed_width
            else:
                if current_row_buttons:
                    rows.append(current_row_buttons)
                current_row_buttons = [info]
                current_row_width = button_width
        
        if current_row_buttons:
            rows.append(current_row_buttons)
        
        # Create row layouts and buttons
        for row_buttons in rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            self.subcategory_row_layouts.append(row_layout)
            self.subcategory_main_layout.addLayout(row_layout)
            
            for info in row_buttons:
                btn = QPushButton(info["text"])
                btn.setFont(subcategory_font)
                btn.setFixedWidth(info["width"])
                btn.setFixedHeight(30)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.setCursor(Qt.PointingHandCursor)
                
                if self.current_category == info["category_key"] and self.current_subcategory == info["subcat_key"]:
                    btn.setStyleSheet(self.get_active_button_stylesheet())
                else:
                    btn.setStyleSheet(self.get_inactive_button_stylesheet())
                
                category_key = info["category_key"]
                subcat_key = info["subcat_key"]
                btn.clicked.connect(lambda checked=False, cat=category_key, sub=subcat_key: self.on_kaomoji_tab_click(cat, sub))
                btn.setToolTip(info["text"])
                
                tab_key = f"{category_key}_{subcat_key}"
                self.kaomoji_tab_buttons[tab_key] = btn
                
                row_layout.addWidget(btn)
            
            row_layout.addStretch()
        
        # Adjust grid height
        num_rows = len(rows)
        self.adjust_grid_height_for_subcategories(num_rows)
    
    def create_kaomoji_subcategory_tabs(self):
        """Create tab buttons for kaomoji subcategories (all categories)"""
        # Clear existing subcategory buttons safely
        for button in list(self.subcategory_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass  # Button already deleted
        self.subcategory_buttons.clear()
        
        for button in list(self.kaomoji_tab_buttons.values()):
            try:
                if button is not None:
                    button.deleteLater()
            except RuntimeError:
                pass  # Button already deleted
        self.kaomoji_tab_buttons.clear()
        
        # Remove all existing row layouts safely
        for row_layout in self.subcategory_row_layouts:
            while row_layout.count():
                item = row_layout.takeAt(0)
                if item.widget():
                    try:
                        item.widget().deleteLater()
                    except RuntimeError:
                        pass  # Widget already deleted
            try:
                self.subcategory_main_layout.removeItem(row_layout)
            except RuntimeError:
                pass  # Layout already removed
        self.subcategory_row_layouts.clear()
        
        if not self.kaomoji_categories:
            return
        
        # Create button info for all categories and subcategories
        button_info = []
        subcategory_font = QFont("Segoe UI", 9)
        font_metrics = QFontMetrics(subcategory_font)
        
        for category_key, category_data in self.kaomoji_categories.items():
            category_name = category_data.get('name', category_key)
            subcategories = category_data.get('subcategories', {})
            
            for subcat_key, subcat_data in subcategories.items():
                subcat_name = subcat_data.get('name', subcat_key)
                display_text = f"{category_name} › {subcat_name}"
                
                # Calculate actual width needed for this button
                text_width = font_metrics.horizontalAdvance(display_text)
                # Add padding for button (left/right padding + borders + margin + safety)
                button_width = max(60, text_width + 30)
                
                button_info.append({
                    "text": display_text,
                    "width": button_width,
                    "category_key": category_key,
                    "subcat_key": subcat_key
                })
        
        # Distribute buttons across rows based on actual width
        available_width = 750  # Conservative container width (accounting for margins and scrollbar)
        button_spacing = 2
        
        rows = []
        current_row_buttons = []
        current_row_width = 0
        
        for info in button_info:
            button_width = info["width"]
            
            # Calculate width if we add this button to current row
            if len(current_row_buttons) == 0:
                needed_width = button_width
            else:
                needed_width = current_row_width + button_spacing + button_width
            
            # Check if button fits in current row
            if needed_width <= available_width:
                current_row_buttons.append(info)
                current_row_width = needed_width
            else:
                # Current row is full, start a new row
                if current_row_buttons:
                    rows.append(current_row_buttons)
                current_row_buttons = [info]
                current_row_width = button_width
        
        # Add last row if not empty
        if current_row_buttons:
            rows.append(current_row_buttons)
        
        # Create row layouts and buttons
        for row_buttons in rows:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)
            self.subcategory_row_layouts.append(row_layout)
            self.subcategory_main_layout.addLayout(row_layout)
            
            for info in row_buttons:
                # Create button with fixed width
                btn = QPushButton(info["text"])
                btn.setFont(subcategory_font)
                btn.setFixedWidth(info["width"])
                btn.setFixedHeight(30)
                btn.setFocusPolicy(Qt.NoFocus)
                btn.setCursor(Qt.PointingHandCursor)
                
                # Set initial style
                if self.current_category == info["category_key"] and self.current_subcategory == info["subcat_key"]:
                    btn.setStyleSheet(self.get_active_button_stylesheet())
                else:
                    btn.setStyleSheet(self.get_inactive_button_stylesheet())
                
                # Connect click handler
                category_key = info["category_key"]
                subcat_key = info["subcat_key"]
                btn.clicked.connect(lambda checked=False, cat=category_key, sub=subcat_key: self.on_kaomoji_tab_click(cat, sub))
                btn.setToolTip(info["text"])
                
                # Store button
                tab_key = f"{category_key}_{subcat_key}"
                self.kaomoji_tab_buttons[tab_key] = btn
                
                # Add button to row
                row_layout.addWidget(btn)
            
            # Add stretch to fill remaining space
            row_layout.addStretch()
        
        # Adjust grid height
        num_rows = len(rows)
        self.adjust_grid_height_for_subcategories(num_rows)
    
    def on_kaomoji_category_click(self, category):
        """Handle kaomoji category button click"""
        # Save previous category to check if we're switching
        previous_category = self.current_category
        self.current_category = category
        
        # Special handling for Recent & Favorites category
        if category == "recent_favorites":
            # Keep current subcategory if already on Recent & Favorites, otherwise use user preference
            if previous_category != "recent_favorites":
                # Use user's preferred default tab
                self.current_subcategory = self.get_recent_favorites_tab_to_display()
            # Update category button styles
            self.update_category_button_styles(category)
            # Create Recent/Favorites subcategory tabs
            self.create_recent_favorites_subcategories()
            # Show Clear button for Recent/Favorites in Kaomoji package
            self.clear_recent_button.show()
            # Refresh display
            self.populate_emojis()
            # Update counter
            self.update_emoji_counter()
            # Save preferences
            if self.save_preferences.get('category_button', False):
                self.data_manager.save_data('category_button', category)
            if self.save_preferences.get('subcategory_tab', False):
                self.data_manager.save_data('subcategory_tab', self.current_subcategory)
            return
        
        # Get first subcategory of this category
        if category in self.kaomoji_categories:
            category_data = self.kaomoji_categories[category]
            subcategories = category_data.get('subcategories', {})
            if subcategories:
                first_subcategory = list(subcategories.keys())[0]
                self.current_subcategory = first_subcategory
            else:
                self.current_subcategory = None
        
        # Update category button styles
        self.update_category_button_styles(category)
        
        # Recreate subcategory tabs for this category
        self.create_kaomoji_subcategory_tabs_for_category(category)
        
        # Refresh display
        self.populate_emojis()
        
        # Update counter
        self.update_emoji_counter()
        
        # Save preferences
        if self.save_preferences.get('category_button', False):
            self.data_manager.save_data('category_button', category)
        if self.save_preferences.get('subcategory_tab', False):
            self.data_manager.save_data('subcategory_tab', self.current_subcategory)
    
    def on_kaomoji_tab_click(self, category, subcategory):
        """Handle kaomoji tab button click"""
        self.current_category = category
        self.current_subcategory = subcategory
        
        # Update button styles
        self.update_kaomoji_tab_styles()
        
        # Refresh display
        self.populate_emojis()
        
        # Update counter
        self.update_emoji_counter()
        
        # Save preferences
        if self.save_preferences.get('category_button', False):
            self.data_manager.save_data('category_button', category)
        if self.save_preferences.get('subcategory_tab', False):
            self.data_manager.save_data('subcategory_tab', subcategory)
    
    def update_kaomoji_tab_styles(self):
        """Update visual styles for kaomoji tab buttons"""
        active_style = self.get_active_button_stylesheet()
        inactive_style = self.get_inactive_button_stylesheet()
        
        for tab_key, btn in self.kaomoji_tab_buttons.items():
            cat_key, sub_key = tab_key.split('_', 1)
            is_active = (cat_key == self.current_category and sub_key == self.current_subcategory)
            btn.setStyleSheet(active_style if is_active else inactive_style)
    
    def get_recent_favorites_tab_to_display(self):
        """Get the tab to display for Recent & Favorites category
        
        Returns the last used tab if use_last_used_tab is enabled,
        otherwise returns the default tab preference.
        """
        if self.data_manager.use_last_used_tab:
            return self.data_manager.last_used_recent_favorites_tab
        else:
            return self.data_manager.default_recent_favorites_tab
    
    def on_subcategory_click(self, category, subcategory):
        """Handle subcategory button click"""
        self.current_category = category
        self.current_subcategory = subcategory
        
        # Save last used tab if we're in Recent & Favorites and use_last_used_tab is enabled
        if (category in ["Recent & Favorites", "recent_favorites"] and 
            subcategory in ["recent", "favorites", "frequently_used"] and 
            self.data_manager.use_last_used_tab):
            self.data_manager.last_used_recent_favorites_tab = subcategory
            self.data_manager.save_data('last_used_recent_favorites_tab', subcategory)
        
        # Update visual feedback for subcategory buttons
        self.update_subcategory_button_styles(subcategory)
        
        # Show Clear button for Recent/Favorites subcategories in Kaomoji package
        if self.current_emoji_package == "Kaomoji" and self.current_category == "recent_favorites":
            self.clear_recent_button.show()
        elif self.current_emoji_package == "Kaomoji":
            self.clear_recent_button.hide()
        
        # Update Add to favorites button text and functionality based on subcategory
        self.update_favorite_button_for_subcategory()
        
        # Update counter and populate emojis (also updates action buttons state)
        self.update_emoji_counter()
        
        # Save current subcategory preference
        self.data_manager.save_data('subcategory_tab', self.current_subcategory)
        
        self.populate_emojis()
    
    def on_category_click(self, category):
        """Handle category button click"""
        # Save previous category to check if we're switching
        previous_category = self.current_category
        self.current_category = category
        
        # Set default subcategory for Recent & Favorites
        if category == "Recent & Favorites":
            # Keep current subcategory if already on Recent & Favorites, otherwise use user preference
            if previous_category not in ["Recent & Favorites", "recent_favorites"]:
                # Use user's preferred default tab
                self.current_subcategory = self.get_recent_favorites_tab_to_display()
        else:
            self.current_subcategory = None  # Reset subcategory when changing category
        
        # Update visual feedback for category buttons
        self.update_category_button_styles(category)
        
        # Update subcategory buttons based on selected category
        self.update_subcategory_buttons(category)
        
        # Show/hide Clear button based on category and package, counter always visible
        if category == "Recent & Favorites":
            # Show Clear button for Recent & Favorites in all packages including Kaomoji
            self.clear_recent_button.show()
        else:
            # Hide Clear button for other categories
            self.clear_recent_button.hide()
        
        # Update favorite button for the active category/subcategory
        self.update_favorite_button_for_subcategory()
        
        # Always update counter for current category
        self.update_emoji_counter()
        
        # Save current category preference
        self.data_manager.save_data('category_button', self.current_category)
        
        # Populate emojis (also updates action buttons state)
        self.populate_emojis()
    
    def update_category_button_styles(self, active_category):
        """Update visual styles for category buttons"""
        self.update_button_group_styles(
            self.category_buttons,
            active_category,
            self.get_active_category_stylesheet(),
            self.get_inactive_category_stylesheet()
        )
    
    def update_emoji_counter(self):
        """Update the emoji counter display"""
        # Update displayed emojis counter
        if self.current_category in ["Recent & Favorites", "recent_favorites"]:
            if self.current_subcategory == "recent":
                displayed_count = len(self.recent_emojis)
            elif self.current_subcategory == "favorites":
                displayed_count = len(self.favorite_emojis)
            elif self.current_subcategory == "frequently_used":
                displayed_count = len(self.frequently_used_emojis)
            else:
                displayed_count = 0
        elif self.current_category in self.emoji_data:
            emojis = self.emoji_data[self.current_category]
            
            # Filter by subcategory if one is selected
            if self.current_subcategory is not None and self.current_category in self.emoji_subcategories:
                subcategories_data = self.emoji_subcategories[self.current_category]
                if self.current_subcategory in subcategories_data:
                    # Get emojis from the selected subcategory
                    subcategory_emojis = subcategories_data[self.current_subcategory]
                    # Filter main category emojis to only include those in the subcategory
                    emojis = [emoji for emoji in emojis if emoji in subcategory_emojis]
            
            displayed_count = len(emojis)
        else:
            displayed_count = 0
        
        self.displayed_emojis_counter.setText(f"Number of emojis: {displayed_count}")
    
    def update_action_buttons_state(self):
        """Enable or disable action buttons (Clear, Add to favorites, Copy to clipboard) based on emoji presence in grid"""
        # For Custom package, hide Clear and Add to favorites buttons, only show Copy button
        if self.current_emoji_package == "Custom":
            self.clear_recent_button.hide()
            self.add_favorite_button.hide()
            self.copy_button.setEnabled(True)
        elif self.current_category in ["Recent & Favorites", "recent_favorites"]:
            # Check if current subcategory has emojis
            if self.current_subcategory == "recent":
                has_emojis = len(self.recent_emojis) > 0
            elif self.current_subcategory == "favorites":
                has_emojis = len(self.favorite_emojis) > 0
            elif self.current_subcategory == "frequently_used":
                has_emojis = len(self.frequently_used_emojis) > 0
            else:
                has_emojis = False
            
            # Show and enable/disable all action buttons based on emoji presence
            self.clear_recent_button.show()
            self.clear_recent_button.setEnabled(has_emojis)
            self.add_favorite_button.show()
            self.add_favorite_button.setEnabled(has_emojis)
            self.copy_button.setEnabled(has_emojis)
        else:
            # In other categories, hide Clear button and always enable Add to favorites and Copy buttons
            self.clear_recent_button.hide()
            self.add_favorite_button.show()
            self.add_favorite_button.setEnabled(True)
            self.copy_button.setEnabled(True)
    
    def populate_emojis(self):
        """Populate the emoji grid with current category emojis"""
        # Clear existing buttons
        self.clear_emoji_grid()
        
        self.current_emojis = []
        
        # Special handling for Custom package - load files directly from folder
        if self.current_emoji_package == "Custom":
            # For Custom package, get files from the custom folder
            if os.path.exists(self.emoji_folder):
                # Determine file extension based on selected format
                if self.svg_radio.isChecked():
                    file_extension = '.svg'
                elif self.ttf_radio.isChecked():
                    file_extension = '.ttf'
                else:
                    file_extension = '.png'
                
                # Get all files with the selected extension
                custom_files = []
                for filename in os.listdir(self.emoji_folder):
                    if filename.lower().endswith(file_extension):
                        custom_files.append(filename)
                
                # Sort files for consistent display
                custom_files.sort()
                
                # Create emoji buttons for each file
                self.calculate_emojis_per_row()
                row = 0
                col = 0
                
                for filename in custom_files:
                    self.current_emojis.append(filename)
                    
                    # Create emoji button for custom file
                    btn = DoubleClickButton()
                    btn.setFixedSize(self.emoji_size, self.emoji_size)
                    btn.setMinimumSize(self.emoji_size, self.emoji_size)
                    btn.setMaximumSize(self.emoji_size, self.emoji_size)
                    
                    # Load image for custom emoji
                    image_path = os.path.join(self.emoji_folder, filename)
                    icon = self.create_custom_emoji_icon(image_path, self.emoji_size)
                    if icon:
                        btn.setIcon(icon)
                        btn.setIconSize(QSize(self.emoji_size, self.emoji_size))
                    
                    # Set button styling
                    btn.setStyleSheet(self.get_emoji_button_stylesheet())
                    btn.setFocusPolicy(Qt.NoFocus)
                    
                    # Connect click handlers
                    btn.clicked.connect(lambda checked, f=filename, b=btn: self.on_custom_emoji_click(f, b))
                    btn.doubleClicked.connect(lambda f=filename, b=btn: self.on_custom_emoji_double_click(f, b))
                    btn.shiftClicked.connect(lambda f=filename, b=btn: self.on_custom_emoji_shift_click(f, b))
                    
                    # Add to grid
                    self.emoji_layout.addWidget(btn, row, col)
                    
                    # Move to next position
                    col += 1
                    if col >= self.emojis_per_row:
                        col = 0
                        row += 1
            
            # Update widget size
            self.update_emoji_widget_size()
            self.update_action_buttons_state()
            
            # Update displayed emojis counter for Custom category
            self.displayed_emojis_counter.setText(f"Displayed emojis: {len(self.current_emojis)}")
            return
        
        # Special handling for Kaomoji package - display text-based emoticons
        if self.current_emoji_package == "Kaomoji":
            kaomojis = []
            
            # Special case: Recent & Favorites category should use shared data
            if self.current_category == "recent_favorites":
                # Use shared recent/favorites/frequently used data (emojis + kaomojis)
                if self.current_subcategory == "recent":
                    kaomojis = self.recent_emojis
                elif self.current_subcategory == "favorites":
                    kaomojis = self.favorite_emojis
                elif self.current_subcategory == "frequently_used":
                    kaomojis = self.frequently_used_emojis
                else:
                    kaomojis = []
            # Get kaomojis from current category and subcategory
            elif self.current_category in self.kaomoji_categories:
                category_data = self.kaomoji_categories[self.current_category]
                subcategories = category_data.get('subcategories', {})
                
                if self.current_subcategory and self.current_subcategory in subcategories:
                    subcat_data = subcategories[self.current_subcategory]
                    kaomojis = subcat_data.get('kaomojis', [])
            
            # Calculate grid layout
            self.calculate_emojis_per_row()
            row = 0
            col = 0
            
            for item in kaomojis:
                # Check if this item is an emoji or a kaomoji
                if not self.is_kaomoji_text(item):
                    # This is a real emoji, use standard emoji button (48x48)
                    self.current_emojis.append(item)
                    btn = self.create_emoji_button(item, row, col)
                    btn.shiftClicked.connect(lambda e=item, b=btn: self.on_emoji_shift_click(e, b))
                    
                    # Move to next position (emoji takes 1 column)
                    col += 1
                    if col >= self.emojis_per_row:
                        col = 0
                        row += 1
                    continue
                
                # This is a kaomoji text, create kaomoji button with fixed size tiers
                self.current_emojis.append(item)
                
                # Create kaomoji button using utility method
                btn, colspan = self.create_kaomoji_button(item, row, col)
                
                # Check if button fits in current row, otherwise move to next row
                if col + colspan > self.emojis_per_row:
                    col = 0
                    row += 1
                
                # Add to grid with colspan
                self.emoji_layout.addWidget(btn, row, col, 1, colspan)
                
                # Move to next position (kaomoji takes colspan columns)
                col += colspan
                if col >= self.emojis_per_row:
                    col = 0
                    row += 1
            
            # Update widget size
            self.update_emoji_widget_size()
            self.update_action_buttons_state()
            
            # Update displayed emojis counter
            self.displayed_emojis_counter.setText(f"Displayed emojis: {len(self.current_emojis)}")
            return
        
        # Original code for non-Custom packages
        # Get emojis for current category
        if self.current_category in ["Recent & Favorites", "recent_favorites"]:
            # Handle Recent & Favorites with subcategories
            if self.current_subcategory == "recent":
                emojis = self.recent_emojis
            elif self.current_subcategory == "favorites":
                emojis = self.favorite_emojis
            elif self.current_subcategory == "frequently_used":
                emojis = self.frequently_used_emojis
            else:
                emojis = []
        elif self.current_category in self.emoji_data:
            emojis = self.emoji_data[self.current_category]
        else:
            emojis = []
        
        # Filter by subcategory if one is selected (for other categories)
        if self.current_subcategory is not None and self.current_category not in ["Recent & Favorites", "recent_favorites"] and self.current_category in self.emoji_subcategories:
            subcategories_data = self.emoji_subcategories[self.current_category]
            if self.current_subcategory in subcategories_data:
                # Get emojis from the selected subcategory
                subcategory_emojis = subcategories_data[self.current_subcategory]
                # Filter main category emojis to only include those in the subcategory
                emojis = [emoji for emoji in emojis if emoji in subcategory_emojis]
        
        # Calculate grid layout - use dynamic calculation
        self.calculate_emojis_per_row()
        row = 0
        col = 0
        
        for emoji_code in emojis:
            # Check if this is already a kaomoji text or emoji character
            # Kaomoji texts and emoji characters don't need conversion
            is_emoji_code = all(c in '0123456789ABCDEFabcdef-' for c in emoji_code)
            
            if is_emoji_code:
                # This is a hex code, convert to emoji character
                emoji = self.emoji_manager.convert_emoji_code_to_character(emoji_code)
            else:
                # This is already a kaomoji text or emoji character, use as-is
                emoji = emoji_code
            
            # Apply variation filter
            base_emoji = emoji[0] if emoji else emoji
            has_variations = base_emoji in self.compound_emoji_variations
            
            if self.variation_filter == "with_variations" and not has_variations:
                continue  # Skip emojis without variations
            elif self.variation_filter == "without_variations" and has_variations:
                continue  # Skip emojis with variations
            
            self.current_emojis.append(emoji)
            
            # Check if this is a kaomoji text (display as kaomoji in all packages)
            if self.is_kaomoji_text(emoji):
                # This is a kaomoji text, create kaomoji button with fixed size tiers (works in all packages)
                btn, colspan = self.create_kaomoji_button(emoji, row, col)
                
                # Check if button fits in current row, otherwise move to next row
                if col + colspan > self.emojis_per_row:
                    col = 0
                    row += 1
                
                # Add to grid with colspan
                self.emoji_layout.addWidget(btn, row, col, 1, colspan)
                
                # Move to next position (kaomoji with colspan)
                col += colspan
                if col >= self.emojis_per_row:
                    col = 0
                    row += 1
            else:
                # Create emoji button using utility method
                btn = self.create_emoji_button(emoji, row, col)
                
                # Add shift click handler (not in create_emoji_button to avoid duplication in search)
                btn.shiftClicked.connect(lambda e=emoji, b=btn: self.on_emoji_shift_click(e, b))
                
                # Move to next position (regular emoji, 1 column)
                col += 1
                if col >= self.emojis_per_row:
                    col = 0
                    row += 1
        
        # Update the widget size to accommodate all emojis
        self.update_emoji_widget_size()
        
        # Update action buttons state based on emoji presence
        self.update_action_buttons_state()
    
    def on_search_change(self, text):
        """Handle search text change"""
        if text == "":
            self.populate_emojis()
            return
        
        # Clear existing buttons
        self.clear_emoji_grid()
        
        self.current_emojis = []
        
        # Search through all emojis
        search_text = text.lower()
        self.calculate_emojis_per_row()
        row = 0
        col = 0
        
        for category, emojis in self.emoji_data.items():
            for emoji_code in emojis:
                # Convert Unicode code to emoji character if needed
                emoji = self.emoji_manager.convert_emoji_code_to_character(emoji_code)
                
                # Apply variation filter
                base_emoji = emoji[0] if emoji else emoji
                has_variations = base_emoji in self.compound_emoji_variations
                
                if self.variation_filter == "with_variations" and not has_variations:
                    continue  # Skip emojis without variations
                elif self.variation_filter == "without_variations" and has_variations:
                    continue  # Skip emojis with variations
                
                emoji_name = self.get_emoji_name(emoji).lower()
                if search_text in emoji_name or search_text in emoji or search_text in emoji_code.lower():
                    self.current_emojis.append(emoji)
                    
                    # Create emoji button using utility method
                    self.create_emoji_button(emoji, row, col)
                    
                    # Move to next position
                    col += 1
                    if col >= self.emojis_per_row:
                        col = 0
                        row += 1
        
        # Update the widget size to accommodate all emojis
        self.update_emoji_widget_size()
        
        # Update action buttons state based on emoji presence
        self.update_action_buttons_state()
        
        # Update emoji counter after search
        self.displayed_emojis_counter.setText(f"Number of emojis: {len(self.current_emojis)}")
    
    def clear_emoji_grid(self):
        """Clear all emoji buttons from the grid"""
        # Reset selected button reference as all buttons will be destroyed
        self.selected_emoji_button = None
        
        for i in reversed(range(self.emoji_layout.count())):
            child = self.emoji_layout.itemAt(i).widget()
            if child:
                try:
                    child.deleteLater()
                except RuntimeError:
                    pass  # Widget already deleted
    
    def update_emoji_widget_size(self):
        """Update the emoji widget size to accommodate all emojis"""
        # Calculate the required size based on the number of emojis
        if not self.current_emojis:
            return
        
        num_rows = (len(self.current_emojis) + self.emojis_per_row - 1) // self.emojis_per_row
        
        # Calculate widget size: (button_size + spacing) * count + margins
        button_size = self.emoji_size
        spacing = 1  # Minimal spacing
        margins = 0  # No margins for tight alignment
        
        widget_width = (button_size + spacing) * self.emojis_per_row - spacing + margins
        widget_height = (button_size + spacing) * num_rows - spacing + margins
        
        self.emoji_widget.setMinimumSize(widget_width, widget_height)
        self.emoji_widget.resize(widget_width, widget_height)
    
    def clear_search(self):
        """Clear search and reset to current category"""
        self.search_edit.clear()
        self.search_edit.setFocus()
    
    def on_variation_filter_change(self, index):
        """Handle variation filter change"""
        if index == 0:
            self.variation_filter = "all"
        elif index == 1:
            self.variation_filter = "with_variations"
        elif index == 2:
            self.variation_filter = "without_variations"
        
        # Save variation filter preference
        self.data_manager.save_data('emoji_variation_filter', self.variation_filter)
        
        # Refresh display with new filter
        if self.search_edit.text():
            self.on_search_change(self.search_edit.text())
        else:
            self.populate_emojis()
    
    def on_emoji_package_change(self, index):
        """Handle emoji package change from dropdown"""
        package_names = [
            "EmojiTwo",
            "Noto",
            "OpenMoji",
            "Segoe UI Emoji",
            "Twemoji",
            "Kaomoji",
            "Custom"
        ]
        
        if 0 <= index < len(package_names):
            selected_package = package_names[index]
            
            # Map display name to internal package name
            self.current_emoji_package = selected_package
            
            # Reset selected emoji and preview when changing packages
            self.selected_emoji = None
            self.selected_emoji_button = None
            self.status_emoji_label.clear()
            self.status_emoji_label.hide()
            self.status_text_label.setText("")
            
            # Clear icon cache for the previous package
            self.cache_manager.clear()
            
            # Also clear OpenMoji TTF font cache
            self.openmoji_ttf_fonts.clear()
            
            # Also clear Noto TTF font cache
            self.google_noto_ttf_fonts.clear()
            
            # Update radio buttons state based on package type
            self.update_radio_buttons_for_package()
            
            # If switching to Kaomoji package, use PackageInitializer
            if self.current_emoji_package == "Kaomoji":
                self.package_initializer.initialize_package("Kaomoji")
            else:
                # Show radio buttons for all other packages
                self.radio_buttons_container.show()
                # Restore standard category tabs (in case coming from Kaomoji)
                self.restore_standard_category_tabs()
                # Reset to default category if coming from Kaomoji
                if not hasattr(self, 'current_category') or self.current_category not in ["Recent & Favorites", "activities", "animals-nature", "component", "flags", "food-drink", "objects", "people-body", "smileys-emotion", "symbols", "travel-places", "extras-openmoji", "extras-unicode"]:
                    self.current_category = "Recent & Favorites"
                
                # Apply user's preferred default tab when on Recent & Favorites
                if self.current_category == "Recent & Favorites":
                    self.current_subcategory = self.get_recent_favorites_tab_to_display()
                
            if self.current_emoji_package == "Custom":
                # For Custom package, detect available formats
                self.detect_custom_emoji_formats()
                # Custom uses file-based formats without categories
                self.emoji_folder = self.emoji_packages["Custom"]["folder"]
                
                # Ensure custom folder exists
                import os as os_module
                os_module.makedirs(self.emoji_folder, exist_ok=True)
                
                self.update_category_visibility(False)  # Hide categories for Custom
                self.update_search_filter_ui_state(True)  # Enable search for Custom
                # But gray out variation filter for Custom since it doesn't apply to custom files
                self.variation_filter_combo.setEnabled(False)
                
                # Update radio buttons to set the correct format (before refresh)
                self.update_radio_buttons_for_package()
                
                # Now refresh display (which calls populate_emojis internally)
                self.refresh_emoji_display()
            elif self.current_emoji_package == "Segoe UI Emoji":
                # No file mapping needed for system fonts, just refresh
                self.update_category_visibility(True)  # Show categories
                self.update_search_filter_ui_state(True)  # Enable search and filters
                # Update size radio buttons state for system font
                self.update_size_radio_buttons_state()
                self.refresh_emoji_display()
            elif self.current_emoji_package == "Noto":
                # For Noto TTF fonts, no file mapping needed
                # TTF is already enabled by update_radio_buttons_for_package()
                self.ttf_radio.setChecked(True)
                # Reset to Color mode as default
                self.color_radio.setChecked(True)
                # Update Contrast button state
                self.update_contrast_button_state()
                # Update size radio buttons state after setting TTF
                self.update_size_radio_buttons_state()
                self.update_category_visibility(True)  # Show categories
                self.update_search_filter_ui_state(True)  # Enable search and filters
                self.refresh_emoji_display()
            elif self.current_emoji_package in ["OpenMoji", "Twemoji", "EmojiTwo"]:
                # Reset to default format (PNG) and size (72px) for file-based packages
                # Ensure PNG is selected if TTF is not available (e.g., for EmojiTwo)
                if not self.ttf_radio.isEnabled():
                    self.png_radio.setChecked(True)
                else:
                    # For packages that support TTF, keep current selection or default to PNG
                    if not self.png_radio.isChecked() and not self.svg_radio.isChecked():
                        self.png_radio.setChecked(True)
                self.size_72_radio.setChecked(True)
                
                # Reset to Color mode for OpenMoji and EmojiTwo (Twemoji doesn't use color/black)
                if self.current_emoji_package in ["OpenMoji", "EmojiTwo"]:
                    self.color_radio.setChecked(True)
                    # Update Contrast button state
                    self.update_contrast_button_state()
                
                # Update size radio buttons state after format has been set
                self.update_size_radio_buttons_state()
                
                # Update emoji folder, recreate mapping and refresh display
                # This will set the correct emoji_folder path based on package and radio buttons
                self.update_category_visibility(True)  # Show categories
                self.update_search_filter_ui_state(True)  # Enable search and filters
                self.update_emoji_folder()
                self.refresh_emoji_display()
            elif self.current_emoji_package == "Kaomoji":
                # Kaomoji is already handled by PackageInitializer above, do nothing here
                pass
            else:
                # For other packages not yet implemented
                # Just refresh to show that we tried to switch
                self.update_category_visibility(True)  # Show categories
                self.update_search_filter_ui_state(True)  # Enable search and filters
                self.refresh_emoji_display()
            
            # Update category button icons AFTER emoji_folder has been properly set
            # Skip for Kaomoji which doesn't use category buttons
            if self.current_emoji_package != "Kaomoji":
                self.update_category_button_icons()
            
            # Update subcategory buttons for the current category (for packages with categories)
            # Skip for Custom and Kaomoji which handle subcategories differently
            if self.current_emoji_package not in ["Custom", "Kaomoji"]:
                self.update_subcategory_buttons(self.current_category)
                # Restore subcategory button selection visually
                self.update_subcategory_button_styles(self.current_subcategory)
            
            # Update displayed emoji source label
            self.update_displayed_emoji_source_label()
            
            # Adjust grid height based on current subcategory layout for non-Custom packages
            # For Custom package, update_category_visibility() already handles the grid height adjustment
            if self.current_emoji_package != "Custom":
                num_rows = self.get_current_subcategory_rows_count()
                self.adjust_grid_height_for_subcategories(num_rows)
            
            # Save the selected package as the preferred package
            self.data_manager.save_data('last_selected_package', selected_package)
    
    def update_category_button_icons(self):
        """Update category button icons based on the current emoji package"""
        for category, btn in self.category_buttons.items():
            if category in self.category_emoji_codes:
                # Update emoji icon for 10 main categories
                emoji_code = self.category_emoji_codes[category]
                icon = self.create_category_icon(emoji_code, 32)
                if icon:
                    btn.setIcon(icon)
                    btn.setIconSize(QSize(32, 32))
    
    def create_kaomoji_button(self, kaomoji_text, row, col):
        """Create a kaomoji button with appropriate sizing and handlers
        
        Args:
            kaomoji_text: The kaomoji text to display
            row: Grid row position
            col: Grid column position
            
        Returns:
            tuple: (button, colspan) - The created button and its column span
        """
        btn = DoubleClickButton()
        
        # Calculate font size proportional to emoji_size (10pt for 48px = 0.208 ratio)
        font_size = max(8, int(self.emoji_size * 0.208))
        kaomoji_font = QFont("Segoe UI", font_size)
        btn.setFont(kaomoji_font)
        btn.setText(kaomoji_text)
        
        # Calculate button width using size tiers proportional to emoji_size
        font_metrics = QFontMetrics(kaomoji_font)
        text_rect = font_metrics.boundingRect(kaomoji_text)
        text_width = text_rect.width()
        
        # Add margin for comfortable text display (proportional to emoji_size)
        margin = int(self.emoji_size * 0.83)  # 40px at size 48
        text_width_with_margin = text_width + margin
        
        # Determine button width based on text width with size tiers
        # Tiers are proportional to emoji_size (2x, 3x, 4x the base size)
        tier_medium = int(self.emoji_size * 3.04)  # 146px at size 48
        tier_large = int(self.emoji_size * 4.06)   # 195px at size 48
        tier_small = int(self.emoji_size * 2.02)   # 97px at size 48
        
        if text_width_with_margin > tier_medium:
            button_width = tier_large
        elif text_width_with_margin > tier_small:
            button_width = tier_medium
        else:
            button_width = tier_small
        
        button_height = self.emoji_size
        
        btn.setFixedSize(button_width, button_height)
        btn.setMinimumSize(button_width, button_height)
        btn.setMaximumSize(button_width, button_height)
        btn.setStyleSheet(self.get_emoji_button_stylesheet())
        btn.setFocusPolicy(Qt.NoFocus)
        
        # Add tooltip with kaomoji
        btn.setToolTip(kaomoji_text)
        
        # Connect kaomoji click handlers
        btn.clicked.connect(lambda checked, k=kaomoji_text, b=btn: self.on_kaomoji_click(k, b))
        btn.doubleClicked.connect(lambda k=kaomoji_text, b=btn: self.on_kaomoji_double_click(k, b))
        btn.shiftClicked.connect(lambda k=kaomoji_text, b=btn: self.on_kaomoji_shift_click(k, b))
        
        # Calculate colspan based on button width (each emoji cell = emoji_size width)
        # 97px button = 2 columns, 146px = 3 columns, 195px = 4 columns
        colspan = max(1, round(button_width / self.emoji_size))
        
        return btn, colspan
    
    def is_kaomoji_text(self, text):
        """Check if the given text is a kaomoji (ASCII art) rather than a Unicode emoji
        
        Args:
            text: String to check
            
        Returns:
            bool: True if text is a kaomoji, False if it's a modern Unicode emoji
        """
        if not text:
            return False
        
        # Modern emoji Unicode ranges (excludes old symbols U+2600-U+27BF that kaomojis use)
        EMOJI_RANGES = [
            (0x1F300, 0x1F5FF), (0x1F600, 0x1F64F), (0x1F680, 0x1F6FF),
            (0x1F700, 0x1F77F), (0x1F780, 0x1F7FF), (0x1F800, 0x1F8FF),
            (0x1F900, 0x1F9FF), (0x1FA00, 0x1FA6F), (0x1FA70, 0x1FAFF),
            (0x1F1E6, 0x1F1FF), (0x1F3FB, 0x1F3FF), (0xFE00, 0xFE0F),
            (0x23E9, 0x23F3), (0x23F8, 0x23FA), (0x25AA, 0x25AB),
            (0x25FB, 0x25FE)
        ]
        
        EMOJI_SINGLES = {0x200D, 0x2328, 0x23CF, 0x25B6, 0x25C0}
        
        # Check if text contains modern emoji Unicode characters
        for char in text:
            code_point = ord(char)
            
            # Check ranges
            if any(start <= code_point <= end for start, end in EMOJI_RANGES):
                return False
            
            # Check single codepoints
            if code_point in EMOJI_SINGLES:
                return False
        
        # Check length: modern emojis are typically very short (1-10 chars with modifiers)
        # Kaomojis are usually longer ASCII art expressions
        if len(text) <= 2:
            kaomoji_chars = set('()[]{}^_-~*\\/|`\'",;:')
            if not any(c in kaomoji_chars for c in text):
                return False
        
        return True
    
    
    def select_emoji_button(self, emoji, button):
        """Select an emoji button and update UI state
        
        Args:
            emoji: Emoji character or filename (for custom)
            button: QPushButton to select
        """
        if not button:
            return
        
        # Reset previously selected button to normal style
        if self.selected_emoji_button and self.selected_emoji_button != button:
            self.selected_emoji_button.setStyleSheet(self.get_emoji_button_stylesheet())
        
        # Set new selected button to selected style
        button.setStyleSheet(self.get_button_selected_stylesheet())
        self.selected_emoji_button = button
        self.selected_emoji = emoji
        
        # Update favorite button based on whether this emoji is already in favorites
        self.update_favorite_button_for_subcategory()
    
    def handle_item_click(self, item, button, click_type='single'):
        """Generic handler for emoji/kaomoji/custom item clicks
        
        Args:
            item: Item to handle (emoji char, kaomoji text, or custom filename)
            button: QPushButton that was clicked
            click_type: 'single', 'double', or 'shift'
        """
        # Always select and update preview for all click types
        self.select_emoji_button(item, button)
        self.update_emoji_preview()
        
        if click_type == 'double':
            # Double-click: copy to clipboard
            if self.current_emoji_package == "Custom":
                self.copy_selected_emoji()
            else:
                self.copy_emoji_to_clipboard(item)
        
        elif click_type == 'shift':
            # Shift+click: toggle favorites (skip for custom package)
            if self.current_emoji_package != "Custom":
                if item in self.favorite_emojis:
                    self.remove_from_favorites()
                else:
                    self.add_to_favorites()
    
    def on_emoji_click(self, emoji, button=None):
        """Handle emoji button single click - select and display preview only"""
        self.handle_item_click(emoji, button, 'single')
    
    def on_emoji_double_click(self, emoji, button=None):
        """Handle emoji button double click - copy to clipboard"""
        self.handle_item_click(emoji, button, 'double')
    
    def on_emoji_shift_click(self, emoji, button=None):
        """Handle emoji button Shift+Click - toggle favorites (add/remove)"""
        self.handle_item_click(emoji, button, 'shift')
    
    def get_emoji_name(self, emoji):
        """Get the name of an emoji"""
        return self.emoji_names.get(emoji, "Emoji")
    
    
    def save_recent_emojis(self):
        """Save recent emojis to JSON file"""
        self.data_manager.save_data('recent', self.recent_emojis)
    
    def update_emoji_folder(self):
        """Update emoji folder based on current radio button selections"""
        # Check if TTF is selected - TTF doesn't use folders
        if self.ttf_radio.isChecked():
            # For TTF format, just clear cache and refresh display
            self.cache_manager.clear()
            self.refresh_emoji_display()
            return
        
        # Handle Custom package - uses the custom folder directly
        if self.current_emoji_package == "Custom":
            # For Custom, emoji_folder is already set to the custom folder
            # Just clear cache and recreate mapping
            self.cache_manager.clear()
            self.refresh_emoji_display()
            return
        
        # Handle Twemoji package which has different folder structure (no color/black variants)
        if self.current_emoji_package == "Twemoji":
            format_mode = "png" if self.png_radio.isChecked() else "svg"
            if format_mode == "svg":
                folder_key = "twemoji_svg"
            else:
                folder_key = "twemoji_72_png"
        elif self.current_emoji_package == "EmojiTwo":
            # Handle EmojiTwo package with specific size folders
            color_mode = "color" if self.color_radio.isChecked() else "black"
            format_mode = "png" if self.png_radio.isChecked() else "svg"
            
            if format_mode == "svg":
                folder_key = f"emojitwo_{color_mode}_svg"
            else:
                # For PNG, handle color and black differently
                # Color has size-specific folders (16, 32, 48, 64, 72, 96, 128, 512)
                # Black only has a default folder without size subdirectories
                if color_mode == "color":
                    # Available sizes: 16, 32, 48, 64, 72, 96, 128, 512
                    available_sizes = [16, 32, 48, 64, 72, 96, 128, 512]
                    closest_size = min(available_sizes, key=lambda x: abs(x - self.emoji_size))
                    folder_key = f"emojitwo_{color_mode}_{closest_size}_png"
                else:
                    # Black only has a default folder (no size subdirectories)
                    folder_key = f"emojitwo_{color_mode}_default_png"
        else:
            # Handle OpenMoji and other file-based packages
            color_mode = "color" if self.color_radio.isChecked() else "black"
            size_mode = "72" if self.size_72_radio.isChecked() else "618"
            format_mode = "png" if self.png_radio.isChecked() else "svg"
            
            # For SVG format, size doesn't matter, so we use a different key structure
            if format_mode == "svg":
                folder_key = f"{color_mode}_svg"
            else:
                folder_key = f"{color_mode}_{size_mode}_png"
        
        # Check if the path key exists using path_manager
        try:
            old_folder = self.emoji_folder
            self.emoji_folder = self.path_manager.get_path(folder_key)
            
            # Clear cache entries for old folder to free memory
            if old_folder != self.emoji_folder:
                self.cache_manager.clear(lambda k: k[2] == old_folder)
            
            # Recreate emoji mapping with new folder
            self.emoji_to_filename, self.compound_emoji_variations = self.emoji_manager.create_emoji_mapping(self.emoji_folder)
            # Note: refresh_emoji_display() is called by the caller, not here to avoid recursion
        except KeyError as e:
            print(f"[ERROR] Invalid folder key '{folder_key}': {e}", file=sys.stderr)
            # Keep the old folder and don't change anything
            return
    
    def get_displayed_emoji_source_name(self):
        """Get the name of the currently displayed emoji source (folder name or TTF font name)"""
        if self.ttf_radio.isChecked() and self.current_emoji_package == "OpenMoji":
            # For OpenMoji TTF
            if self.color_radio.isChecked():
                # Use OpenMoji Color with the best suitable color TTF variant
                # Based on available folders: OpenMoji-color-glyf_colr_1 is the best modern format
                return "OpenMoji Color TTF"
            else:
                # Use OpenMoji Black
                return "OpenMoji Black TTF"
        elif self.current_emoji_package == "Noto":
            # For Noto TTF
            if self.color_radio.isChecked():
                return "Noto Color Emoji TTF"
            else:
                return "Noto Black Emoji TTF"
        elif self.current_emoji_package == "Segoe UI Emoji":
            # For system font
            return "Segoe UI Emoji TTF"
        elif self.current_emoji_package == "Custom":
            # For Custom package
            if self.ttf_radio.isChecked():
                return "Custom TTF"
            elif self.svg_radio.isChecked():
                return "Custom SVG"
            else:
                return "Custom PNG"
        elif self.ttf_radio.isChecked():
            # For any other TTF package
            return f"{self.current_emoji_package} TTF"
        elif self.current_emoji_package == "Twemoji":
            # For Twemoji package
            if self.svg_radio.isChecked():
                return "Twemoji SVG"
            else:
                return "Twemoji PNG 72px"
        elif self.current_emoji_package == "EmojiTwo":
            # For EmojiTwo package
            color_mode = "Color" if self.color_radio.isChecked() else "Black"
            if self.svg_radio.isChecked():
                return f"EmojiTwo {color_mode} SVG"
            else:
                # For PNG, show the actual size being used
                folder_name = os.path.basename(self.emoji_folder)
                return f"EmojiTwo {color_mode} PNG {folder_name}px"
        else:
            # For file-based packages (PNG/SVG)
            folder_name = os.path.basename(self.emoji_folder)
            return folder_name
    
    def update_displayed_emoji_source_label(self):
        """Update the displayed emoji source label"""
        source_name = self.get_displayed_emoji_source_name()
        self.displayed_emoji_source_label.setText(f"Displayed emojis: {source_name}")
    
    def on_color_black_change(self, button):
        """Handle color/black radio button change"""
        # Clear OpenMoji TTF font cache to force reloading the correct variant
        self.openmoji_ttf_fonts.clear()
        
        # Also clear Noto TTF font cache to force reloading the correct variant
        self.google_noto_ttf_fonts.clear()
        
        # Clear icon cache to force regeneration of category button icons with new color/black variant
        self.cache_manager.clear()
        
        # Save color/black mode preference
        color_mode = "color" if self.color_radio.isChecked() else "black"
        self.data_manager.save_data('color_black', color_mode)
        
        # Update Contrast button state: enabled only in Black mode
        self.update_contrast_button_state()
        
        self.update_emoji_folder()
        self.refresh_emoji_display()
        self.update_displayed_emoji_source_label()
        # Update category button icons to reflect the color change (for category buttons displaying category emojis)
        self.update_category_button_icons()
        
        # Update preview if an emoji is currently selected
        self.update_emoji_preview()
    
    def on_format_radio_change(self, button):
        """Handle PNG/SVG radio button change"""
        # First, update the UI state of size radio buttons
        self.update_size_radio_buttons_state()
        
        # Save format selection preference
        if self.png_radio.isChecked():
            format_mode = "png"
        elif self.svg_radio.isChecked():
            format_mode = "svg"
        else:
            format_mode = "ttf"
        self.data_manager.save_data('format_selection', format_mode)
        
        # Force UI update before the heavy loading operation
        QApplication.processEvents()
        
        # Then update emoji folder (which triggers heavy loading)
        self.update_emoji_folder()
        self.refresh_emoji_display()
        self.update_displayed_emoji_source_label()
        # Update category button icons to reflect the format change
        self.update_category_button_icons()
        
        # Handle preview based on package type
        if self.current_emoji_package == "Custom":
            # For Custom package, clear selection when changing format
            # because file list changes and previous selection is no longer valid
            self.selected_emoji = None
            self.selected_emoji_button = None
            self.status_emoji_label.clear()
            self.status_emoji_label.hide()
            self.status_text_label.setText("")
        else:
            # For standard packages, update preview if an emoji is currently selected
            self.update_emoji_preview()
    
    def update_size_radio_buttons_state(self):
        """Enable or disable size radio buttons based on format selection and package"""
        is_svg_selected = self.svg_radio.isChecked()
        is_ttf_selected = self.ttf_radio.isChecked()
        is_png_selected = self.png_radio.isChecked()
        is_twemoji = self.current_emoji_package == "Twemoji"
        is_emojitwo = self.current_emoji_package == "EmojiTwo"
        
        # For Twemoji: only 72px is clickable when PNG is selected, 618px is never clickable
        if is_twemoji:
            if is_png_selected:
                self.size_72_radio.setEnabled(True)
                self.size_618_radio.setEnabled(False)
                # If 618px was selected, switch to 72px
                if self.size_618_radio.isChecked():
                    self.size_72_radio.setChecked(True)
            else:
                # For SVG, both size buttons are disabled
                self.size_72_radio.setEnabled(False)
                self.size_618_radio.setEnabled(False)
        else:
            # 72px button: enabled for PNG (disabled for SVG/TTF/EmojiTwo)
            self.size_72_radio.setEnabled(not is_svg_selected and not is_ttf_selected and not is_emojitwo)
            
            # 618px button: enabled for PNG except for Twemoji and EmojiTwo
            self.size_618_radio.setEnabled(not is_svg_selected and not is_ttf_selected and not is_twemoji and not is_emojitwo)
    
    def apply_radio_button_config(self, button_name, visible, enabled, checked, style):
        """Helper method to apply configuration to a radio button
        
        Args:
            button_name: Name of the button (color, black, png, svg, ttf, size_72, size_618, open_folder, refresh)
            visible: Whether button should be visible
            enabled: Whether button should be enabled
            checked: Whether button should be checked (None = keep current state)
            style: Stylesheet to apply ("" or "disabled")
        """
        # Map button names to actual widget attributes
        button_map = {
            "color": self.color_radio,
            "black": self.black_radio,
            "png": self.png_radio,
            "svg": self.svg_radio,
            "ttf": self.ttf_radio,
            "size_72": self.size_72_radio,
            "size_618": self.size_618_radio,
            "open_folder": self.open_custom_folder_button,
            "refresh": self.refresh_custom_button,
        }
        
        button = button_map.get(button_name)
        if button:
            button.setVisible(visible)
            button.setEnabled(enabled)
            if checked is not None:
                button.setChecked(checked)
            button.setStyleSheet(self.get_disabled_radio_stylesheet() if style == "disabled" else "")
    
    
    def update_radio_buttons_for_package(self):
        """Update radio button states based on selected emoji package"""
        package_info = self.emoji_packages.get(self.current_emoji_package, {})
        package_type = package_info.get("type", "files")
        
        # Get configuration from table
        config = self.PACKAGE_BUTTON_CONFIG.get(package_type)
        
        if config and package_type in ["system_font", "ttf_font"]:
            # Apply configuration from table for system_font and ttf_font
            for button_name, (visible, enabled, checked, style) in config.items():
                self.apply_radio_button_config(button_name, visible, enabled, checked, style)
        elif package_type == "custom":
            # Apply basic config from table
            for button_name, (visible, enabled, checked, style) in config.items():
                if button_name not in ["png", "svg", "ttf"]:  # These are handled dynamically
                    self.apply_radio_button_config(button_name, visible, enabled, checked, style)
            
            # Detect currently selected format before updating
            current_format = None
            if self.png_radio.isChecked():
                current_format = "png"
            elif self.svg_radio.isChecked():
                current_format = "svg"
            elif self.ttf_radio.isChecked():
                current_format = "ttf"
            
            # Enable only available format buttons based on detected formats
            for format_name in ["png", "svg", "ttf"]:
                is_available = self.custom_emoji_formats_available.get(format_name, False)
                self.apply_radio_button_config(format_name, True, is_available, None, "" if is_available else "disabled")
            
            # Set format: preserve current selection if still available, otherwise respect saved preference, otherwise use first available
            format_set = False
            
            # First priority: preserve current format if still available
            if current_format and self.custom_emoji_formats_available.get(current_format, False):
                self.apply_radio_button_config(current_format, True, True, True, "")
                format_set = True
            # Second priority: respect saved preference if available
            elif self.save_preferences.get('format_selection', False) and hasattr(self, 'saved_format'):
                if self.custom_emoji_formats_available.get(self.saved_format, False):
                    self.apply_radio_button_config(self.saved_format, True, True, True, "")
                    format_set = True
            
            # Third priority: use first available format
            if not format_set:
                for fmt in ["png", "svg", "ttf"]:
                    if self.custom_emoji_formats_available.get(fmt, False):
                        self.apply_radio_button_config(fmt, True, True, True, "")
                        break
        else:
            # For file-based packages (Twemoji, EmojiTwo, OpenMoji)
            # Show Color/Black, hide Custom buttons
            self.apply_radio_button_config("open_folder", False, False, None, "")
            self.apply_radio_button_config("refresh", False, False, None, "")
            self.apply_radio_button_config("color", True, True, None, "")
            self.apply_radio_button_config("black", True, True, None, "")
            
            if self.current_emoji_package == "Twemoji":
                # Twemoji: PNG/SVG only, always colored
                self.apply_radio_button_config("color", True, True, True, "")
                self.apply_radio_button_config("black", True, False, None, "disabled")
                self.apply_radio_button_config("png", True, True, None, "")
                self.apply_radio_button_config("svg", True, True, None, "")
                self.apply_radio_button_config("ttf", True, False, None, "disabled")
                self.apply_radio_button_config("size_618", True, False, None, "disabled")
                self.update_size_radio_buttons_state()  # Manage 72px for PNG
            elif self.current_emoji_package == "EmojiTwo":
                # EmojiTwo: PNG/SVG with color/black, no size selection
                self.apply_radio_button_config("png", True, True, None, "")
                self.apply_radio_button_config("svg", True, True, None, "")
                self.apply_radio_button_config("ttf", True, False, None, "disabled")
                self.apply_radio_button_config("size_72", True, False, None, "disabled")
                self.apply_radio_button_config("size_618", True, False, None, "disabled")
                self.update_size_radio_buttons_state()
            else:
                # OpenMoji and others: all formats available
                for btn in ["png", "svg", "ttf", "size_72", "size_618"]:
                    self.apply_radio_button_config(btn, True, True, None, "")
                self.update_size_radio_buttons_state()
    
    def on_size_radio_change(self, button):
        """Handle size radio button change - only update emoji folder, not display size"""
        # Save package size preference
        package_size = "72" if self.size_72_radio.isChecked() else "618"
        self.data_manager.save_data('package_size', package_size)
        
        # Update folder based on selected size option
        self.update_emoji_folder()
        self.refresh_emoji_display()
        self.update_displayed_emoji_source_label()
        # Update category button icons to reflect the size change
        self.update_category_button_icons()
        
        # Update preview if an emoji is currently selected
        self.update_emoji_preview()
    
    def on_size_input_change(self):
        """Handle size input field change"""
        try:
            new_size = int(self.size_input.text())
            # Validate size range
            if new_size < 1:
                new_size = 1
            elif new_size > 618:
                new_size = 618
            
            # Update size and refresh
            self.emoji_size = new_size
            self.size_input.setText(str(new_size))
            
            # Save emoji size preference
            self.data_manager.save_data('emoji_size', self.emoji_size)
            
            self.refresh_emoji_display()
        except ValueError:
            # Invalid input, reset to current size
            self.size_input.setText(str(self.emoji_size))
    
    def adjust_emoji_size(self, direction):
        """Adjust emoji size to nearest predefined size in the given direction
        
        Args:
            direction: 1 for increase, -1 for decrease
        """
        current_size = self.emoji_size
        sizes = self.predefined_sizes if direction > 0 else reversed(self.predefined_sizes)
        
        # Find the nearest size in the given direction
        for size in sizes:
            if (direction > 0 and size > current_size) or (direction < 0 and size < current_size):
                self.emoji_size = size
                self.size_input.setText(str(size))
                self.data_manager.save_data('emoji_size', self.emoji_size)
                self.refresh_emoji_display()
                return
        
        # No size found in direction, use boundary size
        boundary_size = self.predefined_sizes[-1 if direction > 0 else 0]
        if current_size != boundary_size:
            self.emoji_size = boundary_size
            self.size_input.setText(str(boundary_size))
            self.data_manager.save_data('emoji_size', self.emoji_size)
            self.refresh_emoji_display()
    
    def on_decrease_size(self):
        """Decrease emoji size to nearest lower predefined size"""
        self.adjust_emoji_size(-1)
    
    def on_increase_size(self):
        """Increase emoji size to nearest higher predefined size"""
        self.adjust_emoji_size(1)
    
    def update_bg_color_button_style(self):
        """Update the background color button to display the current color"""
        # Use darker border for Dark/Medium themes, lighter for Light theme
        if self.current_theme == ThemeManager.THEME_DARK:
            border_color = '#555555'
        elif self.current_theme == ThemeManager.THEME_MEDIUM:
            border_color = '#777777'
        else:
            border_color = '#999'
        self.bg_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.emoji_background_color};
                border: 1px solid {border_color};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid {self.emoji_selection_color};
            }}
        """)
    
    def on_background_color_change(self):
        """Open color picker dialog to change emoji background color"""
        # Open color dialog with current color
        initial_color = QColor(self.emoji_background_color)
        color_dialog = ThemedColorDialog(initial_color, self, "Choose emoji background color")
        
        # Execute dialog and get result
        if color_dialog.exec_():
            color = color_dialog.selectedColor()
            if color.isValid():
                # Save to appropriate theme-specific color
                if self.current_theme == ThemeManager.THEME_LIGHT:
                    self.data_manager.emoji_background_color_light = color.name()
                    self.data_manager.save_data('background_color_light', color.name())
                elif self.current_theme == ThemeManager.THEME_MEDIUM:
                    self.data_manager.emoji_background_color_medium = color.name()
                    self.data_manager.save_data('background_color_medium', color.name())
                else:
                    self.data_manager.emoji_background_color_dark = color.name()
                    self.data_manager.save_data('background_color_dark', color.name())
                
                self.update_bg_color_button_style()
                self.refresh_emoji_display()
    
    def get_contrast_button_tooltip_style(self):
        """Get tooltip style for Contrast button based on current theme
        
        Returns:
            str: Tooltip stylesheet adapted to current theme
        """
        if self.current_theme == ThemeManager.THEME_DARK:
            return "QToolTip { color: #ffffff; background-color: #2b2b2b; border: 1px solid #555555; }"
        elif self.current_theme == ThemeManager.THEME_MEDIUM:
            return "QToolTip { color: #ffffff; background-color: #4a4a4a; border: 1px solid #6e6e6e; }"
        else:  # Light theme
            return "QToolTip { color: #000000; background-color: #f3f3f3; border: 1px solid #cccccc; }"
    
    def on_contrast_toggle(self):
        """Toggle contrast mode (inverts emoji colors in Black + Dark theme)"""
        self.contrast_enabled = not self.contrast_enabled
        # Update contrast button visual state with same blue as links
        tooltip_style = self.get_contrast_button_tooltip_style()
        if self.contrast_enabled:
            self.contrast_button.setStyleSheet(
                f"QPushButton {{ background-color: #3699e7; border: 1px solid #3699e7; }}"
                f"{tooltip_style}"
            )
        else:
            self.contrast_button.setStyleSheet(tooltip_style)
        # Clear cache to force reload of emojis with new color inversion
        self.cache_manager.clear()
        # Refresh display with inverted colors
        self.refresh_emoji_display()
    
    def update_contrast_button_state(self):
        """Update Contrast button state based on Color/Black mode
        
        Contrast button is only enabled in Black mode
        """
        is_black_mode = self.black_radio.isChecked()
        self.contrast_button.setEnabled(is_black_mode)
        
        tooltip_style = self.get_contrast_button_tooltip_style()
        
        # If switching to Color mode while Contrast was enabled, disable it
        if not is_black_mode and self.contrast_enabled:
            self.contrast_enabled = False
            self.contrast_button.setStyleSheet(
                f"QPushButton:disabled {{ opacity: 0.15; }}"
                f"{tooltip_style}"
            )
        elif not is_black_mode:
            # Apply disabled style with opacity 0.15 (same as disabled radio buttons) for all themes
            self.contrast_button.setStyleSheet(
                f"QPushButton:disabled {{ opacity: 0.15; }}"
                f"{tooltip_style}"
            )
        else:
            # Button is enabled, reset to default style (unless Contrast is active)
            if not self.contrast_enabled:
                self.contrast_button.setStyleSheet(tooltip_style)
    
    def on_wheel_event_with_ctrl(self, angle_delta):
        """Handle Ctrl+Wheel event for size adjustment"""
        # Determine if wheel went up or down
        # angleDelta().y() returns positive for wheel up, negative for wheel down
        if angle_delta > 0:
            # Wheel up -> increase size
            self.on_increase_size()
        else:
            # Wheel down -> decrease size
            self.on_decrease_size()
    
    def refresh_emoji_display(self):
        """Refresh emoji display with new size and recalculate grid"""
        # For EmojiTwo, update the emoji folder to use the closest size
        if self.current_emoji_package == "EmojiTwo" and self.png_radio.isChecked():
            self.update_emoji_folder()
        
        # Clear existing buttons
        self.clear_emoji_grid()
        
        # Recalculate emojis per row based on current emoji size
        self.calculate_emojis_per_row()
        
        # Repopulate with new size
        self.populate_emojis()
        
        # Update the displayed emoji source label
        self.update_displayed_emoji_source_label()
    
    def calculate_emojis_per_row(self):
        """Calculate number of emojis per row based on current emoji size"""
        # Get the width of the scroll area
        scroll_width = self.emoji_scroll_area.width() - 20  # Account for scrollbar
        
        # Calculate how many emojis fit per row
        # Each emoji takes: emoji_size + spacing (1px)
        emoji_with_spacing = self.emoji_size + 1
        
        # Calculate emojis per row, but limit to reasonable values for very large emojis
        self.emojis_per_row = max(1, scroll_width // emoji_with_spacing)
    
    def clear_recent_emojis(self):
        """Clear recent emojis, favorites or frequently used depending on active subcategory"""
        if self.current_category in ["Recent & Favorites", "recent_favorites"]:
            if self.current_subcategory == "recent":
                # Clear recent emojis
                self.recent_emojis = []
                self.save_recent_emojis()
            elif self.current_subcategory == "favorites":
                # Clear favorites
                self.favorite_emojis = []
                self.save_favorites()
            elif self.current_subcategory == "frequently_used":
                # Clear frequently used emojis and reset usage counts
                self.frequently_used_emojis = []
                self.data_manager.emoji_usage_count = {}
                self.data_manager.frequently_used_emojis = []
                self.data_manager.save_data('emoji_usage_count', {})
                self.data_manager.save_data('frequently_used', [])
        
        self.update_emoji_counter()
        # Populate emojis (also updates action buttons state - buttons will be disabled now)
        self.populate_emojis()
        # Reset selected emoji
        self.selected_emoji = None
        self.selected_emoji_button = None
        # Reset the preview widget (clear emoji preview)
        self.status_emoji_label.clear()
        self.status_emoji_label.hide()
        self.status_text_label.setText("")
    
    def copy_selected_emoji(self):
        """Copy the currently selected emoji to clipboard"""
        if self.selected_emoji:
            # For Kaomoji package, copy the text to clipboard and add to recent
            if self.current_emoji_package == "Kaomoji":
                self.copy_emoji_to_clipboard(self.selected_emoji)
                return
            
            # For Custom package, copy the image itself to clipboard
            if self.current_emoji_package == "Custom":
                file_path = os.path.join(self.emoji_folder, self.selected_emoji)
                file_ext = os.path.splitext(file_path)[1].lower()
                
                clipboard = QApplication.clipboard()
                pixmap = None
                
                # Load image based on file type
                if file_ext == '.png' and os.path.exists(file_path):
                    # Load PNG directly
                    pixmap = QPixmap(file_path)
                elif file_ext == '.svg' and os.path.exists(file_path):
                    # Render SVG to pixmap
                    svg_renderer = QSvgRenderer(file_path)
                    if svg_renderer.isValid():
                        # Use a good size for clipboard (e.g., 256x256)
                        size = 256
                        pixmap = QPixmap(size, size)
                        pixmap.fill(Qt.transparent)
                        painter = QPainter(pixmap)
                        svg_renderer.render(painter)
                        painter.end()
                
                # Copy image to clipboard
                if pixmap and not pixmap.isNull():
                    clipboard.setPixmap(pixmap)
                    
                    # Show visual feedback
                    self.copy_button.setText("✔")
                    QTimer.singleShot(500, lambda: self.copy_button.setText("Copy to clipboard"))
            else:
                # For regular emoji packages, copy the emoji character
                self.copy_emoji_to_clipboard(self.selected_emoji)
    
    def add_to_favorites(self):
        """Add the currently selected emoji to favorites"""
        if self.selected_emoji and self.selected_emoji not in self.favorite_emojis:
            self.favorite_emojis.append(self.selected_emoji)
            
            # Save favorites
            self.save_favorites()
            
            # Update counter
            self.update_emoji_counter()
            
            # Update action buttons state
            self.update_action_buttons_state()
            
            # Show visual feedback - change button text temporarily
            self.add_favorite_button.setText("✔")
            
            # Update button text after 500ms to reflect new favorite status
            QTimer.singleShot(500, self.update_favorite_button_for_subcategory)
    
    def save_favorites(self):
        """Save favorite emojis to JSON file"""
        self.data_manager.save_data('favorites', self.favorite_emojis)
    
    def remove_from_favorites(self):
        """Remove the currently selected emoji from favorites"""
        if self.selected_emoji and self.selected_emoji in self.favorite_emojis:
            # Remove from favorites
            self.favorite_emojis.remove(self.selected_emoji)
            
            # Save favorites
            self.save_favorites()
            
            # Update counter
            self.update_emoji_counter()
            
            # Refresh the grid to remove the emoji from display (also updates action buttons state)
            self.populate_emojis()
            
            # Show visual feedback
            self.add_favorite_button.setText("✔")
            
            # Update button text after 500ms to reflect new favorite status
            QTimer.singleShot(500, self.update_favorite_button_for_subcategory)
    
    def update_favorite_button_for_subcategory(self):
        """Update the favorite button text and functionality based on the active subcategory"""
        if self.current_category in ["Recent & Favorites", "recent_favorites"] and self.current_subcategory == "favorites":
            # In Favorites tab, always use Remove from favorites
            self.add_favorite_button.setText("Remove from favorites")
            self.add_favorite_button.setFixedSize(165, 30)  # Wider to fit the text
            self.reconnect_signal(self.add_favorite_button.clicked, self.remove_from_favorites)
        else:
            # In all other cases (Recent, Frequently used, and other categories), check if selected emoji is in favorites
            self.update_favorite_button_for_selected_emoji()
    
    def update_favorite_button_for_selected_emoji(self):
        """Update the favorite button based on whether the selected emoji is already in favorites"""
        if self.selected_emoji and self.selected_emoji in self.favorite_emojis:
            # Selected emoji is in favorites, show Remove option
            self.add_favorite_button.setText("Remove from favorites")
            self.add_favorite_button.setFixedSize(165, 30)
            self.reconnect_signal(self.add_favorite_button.clicked, self.remove_from_favorites)
        else:
            # Selected emoji is not in favorites or no emoji selected, show Add option
            self.add_favorite_button.setText("Add to favorites")
            self.add_favorite_button.setFixedSize(130, 30)
            self.reconnect_signal(self.add_favorite_button.clicked, self.add_to_favorites)
    
    def show_hotkeys_dialog(self):
        """Show Hotkeys dialog"""
        dialog = HotkeysDialog(self)
        dialog.exec_()
    
    def show_settings_dialog(self):
        """Show Settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Save the updated preferences
            self.data_manager.save_data('save_preferences', self.save_preferences)
    
    def show_about_dialog(self):
        """Show About dialog"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def wheelEvent(self, event):
        """Handle mouse wheel event for Ctrl + Wheel size adjustment"""
        # Check if Ctrl is pressed
        if event.modifiers() & Qt.ControlModifier:
            # Get the wheel delta (positive for up, negative for down)
            delta = event.angleDelta().y()
            
            if delta > 0:
                # Wheel up with Ctrl - increase size
                self.on_increase_size()
            elif delta < 0:
                # Wheel down with Ctrl - decrease size
                self.on_decrease_size()
            
            # Accept the event to prevent default scrolling
            event.accept()
        else:
            # Let the default wheel event handler process the event
            super().wheelEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_recent_emojis()
        event.accept()
    
    
    def detect_custom_emoji_formats(self):
        """Detect available emoji formats (PNG, SVG, TTF) in the custom folder"""
        custom_folder = self.emoji_packages.get("Custom", {}).get("folder", "")
        
        # Reset formats availability
        self.custom_emoji_formats_available = {"png": False, "svg": False, "ttf": False}
        
        # Return if custom folder doesn't exist
        if not os.path.exists(custom_folder):
            return
        
        # Check for available file formats in the custom folder
        try:
            for filename in os.listdir(custom_folder):
                filename_lower = filename.lower()
                if filename_lower.endswith('.png'):
                    self.custom_emoji_formats_available["png"] = True
                elif filename_lower.endswith('.svg'):
                    self.custom_emoji_formats_available["svg"] = True
                elif filename_lower.endswith('.ttf'):
                    self.custom_emoji_formats_available["ttf"] = True
        except Exception:
            # If error reading folder, just keep defaults (all False)
            pass
    
    def update_category_visibility(self, visible):
        """Show or hide category and subcategory buttons based on package type
        
        This function centralizes grid height management for all packages:
        - For standard packages (with categories): reduces height by 10px to prevent overlap
        - For Custom package (no categories): expands height to fill the freed space
        """
        # Hide/show category buttons container
        self.category_buttons_container.setVisible(visible)
        
        # Hide/show subcategory container
        self.subcategory_container.setVisible(visible)
        
        # Adjust emoji grid height consistently for all packages
        if visible:
            # Categories and subcategories are visible (non-Custom packages)
            # Reduce height by 10px to prevent overlap with size buttons
            reduced_height = self.base_grid_height - 10
            self.emoji_scroll_area.setFixedSize(780, reduced_height)
        else:
            # Categories and subcategories are hidden (Custom package)
            # Expand grid height to fill space freed by hidden category tabs (~50px) and subcategory area (~40px)
            expanded_height = self.base_grid_height + 90
            self.emoji_scroll_area.setFixedSize(780, expanded_height)
    
    def open_custom_emoji_folder(self):
        """Open the custom emoji folder in Windows Explorer"""
        import subprocess
        import os
        
        custom_folder = self.emoji_packages.get("Custom", {}).get("folder", "")
        
        try:
            # Ensure the custom folder exists
            os.makedirs(custom_folder, exist_ok=True)
            
            # Open Windows Explorer with the custom folder
            subprocess.Popen(f'explorer "{custom_folder}"', shell=True)
        except Exception:
            # Silently fail - the folder opening is not critical
            pass
    
    def refresh_custom_emojis(self):
        """Refresh custom emojis folder and detect new formats"""
        # Re-detect available formats in custom folder (in case user added new files)
        self.detect_custom_emoji_formats()
        
        # Update radio buttons state to reflect new formats
        self.update_radio_buttons_for_package()
        
        # Clear existing emojis
        self.recent_emojis = []
        self.favorite_emojis = []
        
        # Clear icon cache to force reload
        self.cache_manager.clear()
        
        # Update UI to reflect the refreshed custom emojis
        self.update_emoji_folder()
        self.refresh_emoji_display()
        self.update_displayed_emoji_source_label()
        self.update_category_button_icons()
    
    def update_search_filter_ui_state(self, state):
        """Enable or disable search and filter UI elements based on package type"""
        self.search_edit.setEnabled(state)
        self.variation_filter_combo.setEnabled(state)
        self.clear_button.setEnabled(state)
    
    def create_custom_emoji_icon(self, image_path, size):
        """Create an icon for a custom emoji file (PNG, SVG, or TTF)"""
        # Check cache
        cache_key = (image_path, size)
        cached_icon = self.cache_manager.get(cache_key)
        if cached_icon:
            return cached_icon
        
        icon = None
        
        if not os.path.exists(image_path):
            return None
        
        file_ext = os.path.splitext(image_path)[1].lower()
        
        # Handle different file types
        if file_ext == '.svg':
            # Load SVG file
            svg_renderer = QSvgRenderer(image_path)
            if svg_renderer.isValid():
                pixmap = QPixmap(size, size)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                svg_renderer.render(painter)
                painter.end()
                icon = QIcon(pixmap)
        elif file_ext == '.png':
            # Load PNG file
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to desired size while maintaining aspect ratio
                pixmap = pixmap.scaledToWidth(size, Qt.SmoothTransformation)
                icon = QIcon(pixmap)
        elif file_ext == '.ttf':
            # For TTF files, we need to render them as fonts
            # This is more complex - we'll skip for now as TTF rendering requires special handling
            # Users would typically not put TTF files directly as emojis
            pass
        
        # Cache the icon
        if icon:
            self.cache_manager.set(cache_key, icon)
        
        return icon
    
    def on_custom_emoji_click(self, filename, button=None):
        """Handle custom emoji button single click - select and display preview"""
        self.handle_item_click(filename, button, 'single')
    
    def on_custom_emoji_double_click(self, filename, button=None):
        """Handle custom emoji button double click - copy image to clipboard"""
        self.handle_item_click(filename, button, 'double')
    
    def on_custom_emoji_shift_click(self, filename, button=None):
        """Handle custom emoji button Shift+Click for custom package"""
        self.handle_item_click(filename, button, 'shift')
    
    def on_kaomoji_click(self, kaomoji, button=None):
        """Handle kaomoji button single click - select and display preview"""
        self.handle_item_click(kaomoji, button, 'single')
    
    def on_kaomoji_double_click(self, kaomoji, button=None):
        """Handle kaomoji button double click - copy text to clipboard and add to recent"""
        self.handle_item_click(kaomoji, button, 'double')
    
    def on_kaomoji_shift_click(self, kaomoji, button=None):
        """Handle kaomoji button Shift+Click - toggle favorites (add/remove)"""
        self.handle_item_click(kaomoji, button, 'shift')
    
