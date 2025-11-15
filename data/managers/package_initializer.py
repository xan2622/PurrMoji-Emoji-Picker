#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Package Initializer - Simplifies emoji package initialization using Strategy Pattern

This module provides a clean way to initialize different emoji packages without
code duplication. Each package type has its own strategy that handles its
specific initialization requirements.
"""

import os


class PackageStrategy:
    """Base strategy for package initialization"""
    
    def apply_format_defaults(self, picker):
        """Apply default format settings if preferences are not saved"""
        pass
    
    def apply_color_defaults(self, picker):
        """Apply default color mode if preferences are not saved"""
        pass
    
    def apply_size_defaults(self, picker):
        """Apply default size if preferences are not saved"""
        pass
    
    def update_ui_state(self, picker):
        """Update radio buttons and UI state"""
        picker.update_radio_buttons_for_package()
        picker.update_size_radio_buttons_state()
    
    def setup_categories(self, picker):
        """Setup category and subcategory UI"""
        # Restore category only if preference is not saved
        if not picker.save_preferences.get('category_button', False):
            picker.current_category = "Recent & Favorites"
        picker.update_category_button_styles(picker.current_category)
        picker.update_subcategory_buttons(picker.current_category)
        # Update subcategory button styles to reflect saved subcategory
        if picker.save_preferences.get('subcategory_tab', False):
            picker.update_subcategory_button_styles(picker.current_subcategory)
        picker.update_category_visibility(True)
        
        picker.clear_recent_button.show()
        picker.update_favorite_button_for_subcategory()
        picker.update_emoji_counter()
    
    def initialize_emoji_data(self, picker):
        """Initialize emoji folder and mapping"""
        picker.update_emoji_folder()
        picker.emoji_to_filename, picker.compound_emoji_variations = \
            picker.emoji_manager.create_emoji_mapping(picker.emoji_folder)
        picker.update_category_button_icons()
    
    def finalize(self, picker):
        """Finalize initialization"""
        picker.populate_emojis()
    
    def initialize(self, picker):
        """Execute the full initialization sequence"""
        self.apply_format_defaults(picker)
        self.apply_color_defaults(picker)
        self.apply_size_defaults(picker)
        self.update_ui_state(picker)
        self.initialize_emoji_data(picker)
        self.setup_categories(picker)
        self.finalize(picker)


class CustomPackageStrategy(PackageStrategy):
    """Strategy for Custom package (user-provided emojis)"""
    
    def initialize(self, picker):
        """Custom has a completely different initialization flow"""
        # Set custom folder
        picker.emoji_folder = picker.emoji_packages["Custom"]["folder"]
        
        # Ensure custom folder exists
        os.makedirs(picker.emoji_folder, exist_ok=True)
        
        # Update radio buttons for Custom package
        picker.update_radio_buttons_for_package()
        
        # Hide categories and subcategories for Custom
        picker.update_category_visibility(False)
        
        # Enable search but disable variation filter for Custom
        picker.update_search_filter_ui_state(True)
        picker.variation_filter_combo.setEnabled(False)
        
        # Create emoji mapping for custom files
        picker.emoji_to_filename, picker.compound_emoji_variations = \
            picker.emoji_manager.create_emoji_mapping(picker.emoji_folder)
        
        # Populate custom emojis
        picker.populate_emojis()


class SystemFontPackageStrategy(PackageStrategy):
    """Strategy for system font packages (Noto, Segoe UI Emoji)"""
    
    def apply_format_defaults(self, picker):
        """Force TTF format if preferences are not saved"""
        if not picker.save_preferences.get('format_selection', False):
            picker.ttf_radio.setChecked(True)
    
    def apply_color_defaults(self, picker):
        """Force Color mode if preferences are not saved"""
        if not picker.save_preferences.get('color_black', False):
            picker.color_radio.setChecked(True)


class FileBasedPackageStrategy(PackageStrategy):
    """Strategy for file-based packages (Twemoji, EmojiTwo, OpenMoji)"""
    
    def __init__(self, supports_color=False):
        self.supports_color = supports_color
    
    def apply_format_defaults(self, picker):
        """Ensure PNG is selected if format preference is not saved"""
        if not picker.save_preferences.get('format_selection', False):
            if not picker.ttf_radio.isEnabled():
                picker.png_radio.setChecked(True)
            elif (not picker.png_radio.isChecked() and
                  not picker.svg_radio.isChecked() and
                  not picker.ttf_radio.isChecked()):
                picker.png_radio.setChecked(True)
    
    def apply_size_defaults(self, picker):
        """Set 72px size if package size preference is not saved"""
        if not picker.save_preferences.get('package_size', False):
            picker.size_72_radio.setChecked(True)
    
    def apply_color_defaults(self, picker):
        """Set Color mode for packages that support it"""
        if self.supports_color:
            if not picker.save_preferences.get('color_black', False):
                picker.color_radio.setChecked(True)


class KaomojiPackageStrategy(PackageStrategy):
    """Strategy for Kaomoji package (text-based emoticons)"""
    
    def initialize(self, picker):
        """Kaomoji has a unique initialization flow with category buttons and subcategory tabs"""
        # Update radio buttons for Kaomoji package (disable all format/color/size options)
        picker.update_radio_buttons_for_package()
        
        # Hide the entire radio buttons container for Kaomoji (not applicable for text-based kaomoji)
        picker.radio_buttons_container.hide()
        
        # Load kaomoji data
        picker.load_kaomoji_data()
        
        # Create Kaomoji-specific category buttons with emoji icons
        picker.create_kaomoji_category_tabs()
        
        # Show category and subcategory containers
        picker.category_buttons_container.show()
        picker.subcategory_container.show()
        
        # Set Recent & Favorites as default category
        # Apply user's preferred tab (respects use_last_used_tab setting) when switching to Kaomoji package
        picker.current_category = "recent_favorites"
        picker.current_subcategory = picker.get_recent_favorites_tab_to_display()
        
        # Update category button styles
        picker.update_category_button_styles("recent_favorites")
        
        # Create Recent/Favorites subcategory tabs
        picker.create_recent_favorites_subcategories()
        
        # Enable search but disable variation filter for Kaomoji
        picker.update_search_filter_ui_state(True)
        picker.variation_filter_combo.setEnabled(False)
        
        # Populate kaomojis
        picker.populate_emojis()


class PackageInitializer:
    """
    Manages emoji package initialization using strategy pattern
    
    This class eliminates code duplication by delegating package-specific
    initialization logic to strategy classes.
    """
    
    def __init__(self, picker):
        """
        Initialize the PackageInitializer
        
        Args:
            picker: The EmojiPicker instance
        """
        self.picker = picker
        
        # Map package names to their initialization strategies
        self.strategies = {
            "Custom": CustomPackageStrategy(),
            "Noto": SystemFontPackageStrategy(),
            "Segoe UI Emoji": SystemFontPackageStrategy(),
            "Twemoji": FileBasedPackageStrategy(supports_color=False),
            "EmojiTwo": FileBasedPackageStrategy(supports_color=True),
            "OpenMoji": FileBasedPackageStrategy(supports_color=True),
            "Kaomoji": KaomojiPackageStrategy(),
        }
        
        # Default strategy for unknown packages
        self.default_strategy = PackageStrategy()
    
    def initialize_package(self, package_name):
        """
        Initialize a specific emoji package
        
        Args:
            package_name: Name of the package to initialize
        """
        strategy = self.strategies.get(package_name, self.default_strategy)
        strategy.initialize(self.picker)

