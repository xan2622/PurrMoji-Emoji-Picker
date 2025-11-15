#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
DataManager - Centralized JSON data management for PurrMoji
"""

import json


# Emoji category names
EMOJI_CATEGORIES = [
    'activities', 'animals-nature', 'component', 'flags',
    'food-drink', 'objects', 'people-body', 'smileys-emotion',
    'symbols', 'travel-places', 'extras-openmoji', 'extras-unicode'
]


class DataManager:
    """Manages JSON data loading, saving, and preferences"""
    
    def __init__(self, data_file_path):
        """Initialize data manager
        
        Args:
            data_file_path: Path to the emoji_data.json file
        """
        self.data_file = data_file_path
        
        # Data storage
        self.emoji_data = {}
        self.emoji_names = {}
        self.emoji_subcategories = {}
        self.recent_emojis = []
        self.favorite_emojis = []
        self.frequently_used_emojis = []  # List of most frequently used emojis
        self.emoji_usage_count = {}  # Dictionary to track usage count: {emoji: count}
        self.emoji_background_color_light = '#ffffff'
        self.emoji_background_color_medium = '#4b4b4b'
        self.emoji_background_color_dark = '#312829'
        self.preferred_emoji_package = 'EmojiTwo'
        self.emoji_selection_color = '#3699e7'
        self.category_subcategory_color = '#3699e7'
        self.theme = 'Light'
        # Default tab for Recent & Favorites: 'recent', 'favorites', or 'frequently_used'
        self.default_recent_favorites_tab = 'recent'
        self.use_last_used_tab = True  # If True, display the last used tab instead of the default tab
        self.last_used_recent_favorites_tab = 'recent'  # Last used tab in Recent & Favorites
        
        # Preferences for what should be saved
        self.save_preferences = {
            "last_selected_package": True,
            "emoji_variation_filter": False,
            "color_black": False,
            "format_selection": True,
            "package_size": False,
            "category_button": True,
            "subcategory_tab": False,
            "emoji_size": False,
            "background_color": True,
            "background_color_light": True,
            "background_color_medium": True,
            "background_color_dark": True,
            "emoji_selection_color": True,
            "category_subcategory_color": True,
            "theme": True
        }
        
        # Other saved settings
        self.saved_settings = {}
    
    def load_data(self):
        """Load all data from JSON file
        
        Returns:
            bool: True if loading succeeded, False otherwise
        """
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Load core data
                self.emoji_data = data.get('categories', {})
                self.emoji_names = data.get('names', {})
                self.emoji_subcategories = data.get('subcategories', {})
                self.recent_emojis = data.get('recent', [])
                self.favorite_emojis = data.get('favorites', [])
                self.emoji_usage_count = data.get('emoji_usage_count', {})
                self.frequently_used_emojis = data.get('frequently_used', [])
                
                # Load background colors with theme-specific defaults
                self.emoji_background_color_light = data.get('background_color_light', '#ffffff')
                self.emoji_background_color_medium = data.get('background_color_medium', '#4b4b4b')
                self.emoji_background_color_dark = data.get('background_color_dark', '#312829')
                
                self.preferred_emoji_package = data.get('last_selected_package', 'EmojiTwo')
                self.emoji_selection_color = data.get('emoji_selection_color', '#3699e7')
                self.category_subcategory_color = data.get('category_subcategory_color', '#3699e7')
                self.theme = data.get('theme', 'Light')
                self.default_recent_favorites_tab = data.get('default_recent_favorites_tab', 'recent')
                self.use_last_used_tab = data.get('use_last_used_tab', True)
                self.last_used_recent_favorites_tab = data.get('last_used_recent_favorites_tab', 'recent')
                
                # Load save preferences
                saved_preferences = data.get('save_preferences', {})
                if saved_preferences:
                    self.save_preferences.update(saved_preferences)
                
                # Load other settings based on preferences
                self.saved_settings = {
                    'variation_filter': data.get('emoji_variation_filter', 'all'),
                    'color_mode': data.get('color_black', 'color'),
                    'format': data.get('format_selection', 'png'),
                    'package_size': data.get('package_size', '72'),
                    'category_button': data.get('category_button', 'Recent & Favorites'),
                    'subcategory_tab': data.get('subcategory_tab', 'recent'),
                    'emoji_size': data.get('emoji_size', 48)
                }
                
                return True
                
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[ERROR] Failed to load emoji data: {e}")
            # Initialize with empty data
            self.initialize_empty_data()
            return False
    
    def initialize_empty_data(self):
        """Initialize with empty data structures"""
        self.emoji_data = {category: [] for category in EMOJI_CATEGORIES}
        self.emoji_names = {}
        self.emoji_subcategories = {}
        self.recent_emojis = []
        self.favorite_emojis = []
        self.frequently_used_emojis = []
        self.emoji_usage_count = {}
        self.preferred_emoji_package = 'EmojiTwo'
    
    def save_data(self, key, value):
        """Save data to JSON file with preference checking
        
        Args:
            key: The key to save
            value: The value to save
        
        Returns:
            bool: True if saving succeeded, False otherwise
        """
        # Check if we should save this key based on preferences
        # 'save_preferences' itself is always saved
        if key != 'save_preferences' and key in self.save_preferences:
            if not self.save_preferences.get(key, True):
                return False  # Don't save if preference is disabled
        
        try:
            # Load existing data
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update data
            data[key] = value
            
            # Save back to file
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving {key}: {e}")
            return False
    
    def get_preference(self, key):
        """Get a save preference value
        
        Args:
            key: The preference key
        
        Returns:
            bool: The preference value or None if not found
        """
        return self.save_preferences.get(key)
    
    def get_saved_setting(self, key, default=None):
        """Get a saved setting value
        
        Args:
            key: The setting key
            default: Default value if not found
        
        Returns:
            The setting value or default
        """
        return self.saved_settings.get(key, default)
    
    def update_emoji_usage(self, emoji):
        """Update the usage count for an emoji and refresh frequently used list
        
        Args:
            emoji: The emoji character to track
        """
        # Increment usage count
        self.emoji_usage_count[emoji] = self.emoji_usage_count.get(emoji, 0) + 1
        
        # Update frequently used list
        self.update_frequently_used_list()
        
        # Save both usage count and frequently used list
        self.save_data('emoji_usage_count', self.emoji_usage_count)
        self.save_data('frequently_used', self.frequently_used_emojis)
    
    def update_frequently_used_list(self):
        """Update the list of frequently used emojis based on usage count
        
        Algorithm:
        - Filters emojis with at least 2 uses
        - Sorts by usage count (descending)
        - Keeps only the top 20 most used emojis
        """
        # Filter emojis with at least 2 uses
        frequently_used = {
            emoji: count
            for emoji, count in self.emoji_usage_count.items()
            if count >= 2
        }
        
        # Sort by count (descending) and take top 20
        sorted_emojis = sorted(frequently_used.items(), key=lambda x: x[1], reverse=True)
        self.frequently_used_emojis = [emoji for emoji, count in sorted_emojis[:20]]

