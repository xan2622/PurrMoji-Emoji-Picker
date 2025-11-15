#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
EmojiManager - Centralized emoji operations (conversion, mapping, etc.)
"""

import os
import unicodedata


class EmojiManager:
    """Manages emoji operations: conversions, mappings, and variations"""
    
    def __init__(self):
        """Initialize emoji manager"""
        self.emoji_to_filename = {}
        self.compound_emoji_variations = {}
    
    def unicode_to_emoji(self, unicode_str):
        """Convert Unicode code point string to emoji character
        
        Args:
            unicode_str: Unicode string (e.g., "1F600" or "1F600-FE0F")
        
        Returns:
            str: Emoji character or None if conversion fails
        """
        try:
            # Handle compound emojis with multiple code points (flags, ZWJ sequences, etc.)
            codes = unicode_str.replace('.png', '').replace('.svg', '').split('-')
            chars = []
            for code in codes:
                try:
                    # Convert hex code to character
                    char_code = int(code, 16)
                    chars.append(chr(char_code))
                except (ValueError, OverflowError):
                    # Skip invalid codes
                    continue
            
            if chars:
                emoji = ''.join(chars)
                return unicodedata.normalize('NFC', emoji)
            return None
        except (ValueError, OverflowError):
            return None
    
    def emoji_to_unicode(self, emoji):
        """Convert emoji character to Unicode code points string
        
        Args:
            emoji: Emoji character
        
        Returns:
            str: Unicode codes separated by dashes (e.g., "1F600-FE0F")
        """
        codes = []
        for char in emoji:
            codes.append(hex(ord(char))[2:].upper().zfill(4))
        return '-'.join(codes)
    
    def create_emoji_mapping(self, emoji_folder):
        """Create mapping from emoji characters to PNG/SVG filenames
        
        Args:
            emoji_folder: Path to the emoji folder
        
        Returns:
            tuple: (emoji_to_filename dict, compound_emoji_variations dict)
        """
        self.emoji_to_filename = {}
        self.compound_emoji_variations = {}
        
        # Determine file extension based on folder
        file_extension = '.svg' if 'svg' in emoji_folder else '.png'
        
        # Get all files in the emoji folder
        if not os.path.exists(emoji_folder):
            return self.emoji_to_filename, self.compound_emoji_variations
        
        for filename in os.listdir(emoji_folder):
            if filename.endswith(file_extension):
                # Extract Unicode code points from filename
                unicode_codes = filename.replace(file_extension, '').split('-')
                
                # Convert Unicode codes to emoji character
                try:
                    emoji_char = ''.join(chr(int(code, 16)) for code in unicode_codes)
                    normalized_emoji = unicodedata.normalize('NFC', emoji_char)
                    self.emoji_to_filename[normalized_emoji] = filename
                    
                    # For compound emojis, store the main emoji and its variations
                    if len(unicode_codes) > 1:
                        main_emoji_code = unicode_codes[0]  # First code is usually the main emoji
                        try:
                            main_char = chr(int(main_emoji_code, 16))
                            main_normalized = unicodedata.normalize('NFC', main_char)
                            
                            # Store the main emoji mapping
                            if main_normalized not in self.emoji_to_filename:
                                self.emoji_to_filename[main_normalized] = filename
                            
                            # Store variations for context menu
                            if main_normalized not in self.compound_emoji_variations:
                                self.compound_emoji_variations[main_normalized] = []
                            self.compound_emoji_variations[main_normalized].append({
                                'filename': filename,
                                'codes': unicode_codes,
                                'full_emoji': normalized_emoji
                            })
                        except (ValueError, OverflowError):
                            continue
                            
                except (ValueError, OverflowError):
                    # Skip invalid Unicode codes
                    continue
        
        return self.emoji_to_filename, self.compound_emoji_variations
    
    def get_emoji_filename(self, emoji):
        """Get filename for an emoji character
        
        Args:
            emoji: Emoji character
        
        Returns:
            str: Filename or None if not found
        """
        return self.emoji_to_filename.get(emoji)
    
    def get_emoji_variations(self, emoji):
        """Get variations for a compound emoji
        
        Args:
            emoji: Base emoji character
        
        Returns:
            list: List of variation dictionaries or empty list
        """
        return self.compound_emoji_variations.get(emoji, [])
    
    def has_variations(self, emoji):
        """Check if emoji has variations
        
        Args:
            emoji: Emoji character
        
        Returns:
            bool: True if emoji has variations
        """
        return emoji in self.compound_emoji_variations
    
    def convert_emoji_code_to_character(self, emoji_code):
        """Convert emoji code to emoji character if needed
        
        Args:
            emoji_code: Emoji code (hex string) or emoji character
        
        Returns:
            str: Emoji character
        """
        if not isinstance(emoji_code, str):
            return emoji_code
        
        # Check if it's a hex Unicode code (with or without dashes)
        if all(c in '0123456789ABCDEFabcdef-' for c in emoji_code):
            # This looks like a Unicode code point or compound code, convert it
            emoji_char = self.unicode_to_emoji(emoji_code)
            if emoji_char:
                return emoji_char
            return emoji_code  # Fallback to original if conversion fails
        return emoji_code  # Already an emoji character

