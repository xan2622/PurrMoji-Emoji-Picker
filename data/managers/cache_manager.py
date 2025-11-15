#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
CacheManager - Centralized cache management for icon rendering
"""


class CacheManager:
    """Manages icon caching with automatic size management"""
    
    def __init__(self, max_size=1000):
        """Initialize cache manager
        
        Args:
            max_size: Maximum number of items to keep in cache
        """
        self.icon_cache = {}
        self.max_size = max_size
    
    def get(self, key):
        """Get an item from the cache
        
        Args:
            key: Cache key (typically a tuple of emoji, size, context)
        
        Returns:
            Cached value or None if not found
        """
        return self.icon_cache.get(key)
    
    def set(self, key, value):
        """Set an item in the cache with automatic size management
        
        Args:
            key: Cache key
            value: Value to cache
        """
        # If cache is full, remove oldest entries (FIFO)
        if len(self.icon_cache) >= self.max_size:
            # Remove the first inserted item
            first_key = next(iter(self.icon_cache))
            del self.icon_cache[first_key]
        
        self.icon_cache[key] = value
    
    def clear(self, filter_fn=None):
        """Clear cache optionally with a filter function
        
        Args:
            filter_fn: Optional function to filter which items to remove.
                      Should return True for items to remove.
                      Example: lambda key: key[2] == old_folder_path
        """
        if filter_fn:
            # Remove items matching the filter
            keys_to_remove = [k for k in self.icon_cache.keys() if filter_fn(k)]
            for key in keys_to_remove:
                del self.icon_cache[key]
        else:
            # Clear everything
            self.icon_cache.clear()
    
    def size(self):
        """Get current cache size
        
        Returns:
            int: Number of items in cache
        """
        return len(self.icon_cache)
    
    def contains(self, key):
        """Check if key exists in cache
        
        Args:
            key: Cache key to check
        
        Returns:
            bool: True if key exists in cache
        """
        return key in self.icon_cache

