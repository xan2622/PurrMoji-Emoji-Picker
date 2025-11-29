#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
KeyboardManager - Global keyboard shortcut management for PurrMoji
Handles global hotkey registration and callback execution.
"""

import threading
from typing import Any, Callable, Optional, Set, Tuple

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None
    PYNPUT_AVAILABLE = False


class KeyboardManager:
    """Manages global keyboard shortcuts for showing/hiding PurrMoji window"""
    
    # Default hotkey: Ctrl+Alt+X
    DEFAULT_HOTKEY = {'ctrl', 'alt', 'x'}
    
    # Key name mappings for display
    KEY_DISPLAY_NAMES = {
        'ctrl': 'Ctrl',
        'alt': 'Alt',
        'shift': 'Shift',
        'cmd': 'Win',
        'ctrl_l': 'Ctrl',
        'ctrl_r': 'Ctrl',
        'alt_l': 'Alt',
        'alt_r': 'Alt',
        'shift_l': 'Shift',
        'shift_r': 'Shift',
        'cmd_l': 'Win',
        'cmd_r': 'Win',
        # Numpad keys
        'numpad_0': 'Numpad 0', 'numpad_1': 'Numpad 1', 'numpad_2': 'Numpad 2',
        'numpad_3': 'Numpad 3', 'numpad_4': 'Numpad 4', 'numpad_5': 'Numpad 5',
        'numpad_6': 'Numpad 6', 'numpad_7': 'Numpad 7', 'numpad_8': 'Numpad 8',
        'numpad_9': 'Numpad 9',
        'numpad_+': 'Numpad +', 'numpad_-': 'Numpad -', 'numpad_*': 'Numpad *',
        'numpad_/': 'Numpad /', 'numpad_.': 'Numpad .', 'numpad_separator': 'Numpad Sep',
        'numpad_enter': 'Numpad Enter',
        # Additional special keys
        'insert': 'Insert', 'print_screen': 'Print Screen', 'scroll_lock': 'Scroll Lock',
        'pause': 'Pause', 'caps_lock': 'Caps Lock', 'num_lock': 'Num Lock',
        'menu': 'Menu',
        # Note: Symbol/punctuation keys (like ; , . / etc.) use the actual character
        # Media keys
        'volume_mute': 'Mute', 'volume_down': 'Vol Down', 'volume_up': 'Vol Up',
        'media_next': 'Media Next', 'media_prev': 'Media Prev',
        'media_stop': 'Media Stop', 'media_play_pause': 'Play/Pause',
        'browser_back': 'Browser Back', 'browser_forward': 'Browser Fwd',
        'browser_refresh': 'Browser Refresh',
        # F13-F24
        'f13': 'F13', 'f14': 'F14', 'f15': 'F15', 'f16': 'F16',
        'f17': 'F17', 'f18': 'F18', 'f19': 'F19', 'f20': 'F20',
        'f21': 'F21', 'f22': 'F22', 'f23': 'F23', 'f24': 'F24',
    }
    
    # Modifier keys that can be combined
    MODIFIER_KEYS = {'ctrl', 'alt', 'shift', 'cmd', 'ctrl_l', 'ctrl_r', 
                     'alt_l', 'alt_r', 'shift_l', 'shift_r', 'cmd_l', 'cmd_r'}
    
    def __init__(self):
        """Initialize keyboard manager"""
        self._listener: Optional[Any] = None  # keyboard.Listener when pynput available
        self._callback: Optional[Callable] = None
        self._hotkey: Set[str] = self.DEFAULT_HOTKEY.copy()
        self._pressed_keys: Set[str] = set()
        self._enabled: bool = True
        self._lock = threading.Lock()
        self._recording: bool = False
        self._recording_callback: Optional[Callable] = None
        self._recording_finished_callback: Optional[Callable] = None
        self._recorded_keys: Set[str] = set()
    
    @property
    def is_available(self) -> bool:
        """Check if pynput is available"""
        return PYNPUT_AVAILABLE
    
    @property
    def hotkey(self) -> Set[str]:
        """Get current hotkey set"""
        return self._hotkey.copy()
    
    @hotkey.setter
    def hotkey(self, keys: Set[str]):
        """Set new hotkey combination
        
        Args:
            keys: Set of key names (e.g., {'ctrl', 'alt', 'e'})
        """
        with self._lock:
            self._hotkey = set(k.lower() for k in keys)
    
    def set_hotkey_from_string(self, hotkey_str: str):
        """Set hotkey from a string representation
        
        Supports all keyboard layouts (AZERTY, QWERTY, QWERTZ).
        
        Args:
            hotkey_str: String like 'Ctrl+Alt+E' or 'ctrl+shift+;'
        """
        if not hotkey_str:
            return
        
        keys = set()
        # Handle special case: 'Numpad +' contains '+' which is our delimiter
        temp_str = hotkey_str.replace('Numpad +', 'PLACEHOLDER_NUMPAD_PLUS')
        
        parts = temp_str.split('+')
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            part_lower = part.lower()
            
            # Restore placeholder
            if part_lower == 'placeholder_numpad_plus':
                keys.add('numpad_+')
                continue
            
            # Normalize key names
            if part_lower in ('control', 'ctrl'):
                keys.add('ctrl')
            elif part_lower in ('option', 'alt'):
                keys.add('alt')
            elif part_lower == 'shift':
                keys.add('shift')
            elif part_lower in ('win', 'windows', 'cmd', 'super', 'meta'):
                keys.add('cmd')
            # Handle numpad keys from display names
            elif part_lower.startswith('numpad'):
                # Convert display format to internal format (e.g., 'numpad 9' -> 'numpad_9')
                numpad_key = part_lower.replace(' ', '_')
                keys.add(numpad_key)
            # Handle VK codes (vk_XXX format)
            elif part_lower.startswith('vk_'):
                keys.add(part_lower)
            # Handle space-separated key names (e.g., 'page up' -> 'pageup')
            elif ' ' in part_lower:
                keys.add(part_lower.replace(' ', ''))
            # Single character symbols (like ; , . / etc.) - keep original case
            elif len(part) == 1:
                keys.add(part)
            else:
                keys.add(part_lower)
        
        self.hotkey = keys
    
    def get_hotkey_string(self) -> str:
        """Get current hotkey as a displayable string
        
        Returns:
            String like 'Ctrl+Alt+E'
        """
        # Order: Ctrl, Alt, Shift, Win, then other keys
        order = ['ctrl', 'alt', 'shift', 'cmd']
        result = []
        
        # Add modifiers in order
        for mod in order:
            if mod in self._hotkey:
                display_name = self.KEY_DISPLAY_NAMES.get(mod, mod.capitalize())
                result.append(display_name)
        
        # Add non-modifier keys
        for key in sorted(self._hotkey):
            if key not in order:
                # Check if there's a display name for this key
                if key in self.KEY_DISPLAY_NAMES:
                    result.append(self.KEY_DISPLAY_NAMES[key])
                # Handle unknown VK codes (vk_XXX format)
                elif key.startswith('vk_'):
                    result.append(key.upper())
                else:
                    result.append(key.upper() if len(key) == 1 else key.capitalize())
        
        return '+'.join(result)
    
    def set_callback(self, callback: Callable):
        """Set the callback function to execute when hotkey is pressed
        
        Args:
            callback: Function to call (should toggle window visibility)
        """
        self._callback = callback
    
    # Windows Virtual Key codes - comprehensive mapping for all keyboard layouts
    VK_CODE_TO_LETTER = {
        # Letters A-Z (0x41-0x5A) - physical key based, works on all layouts
        0x41: 'a', 0x42: 'b', 0x43: 'c', 0x44: 'd', 0x45: 'e',
        0x46: 'f', 0x47: 'g', 0x48: 'h', 0x49: 'i', 0x4A: 'j',
        0x4B: 'k', 0x4C: 'l', 0x4D: 'm', 0x4E: 'n', 0x4F: 'o',
        0x50: 'p', 0x51: 'q', 0x52: 'r', 0x53: 's', 0x54: 't',
        0x55: 'u', 0x56: 'v', 0x57: 'w', 0x58: 'x', 0x59: 'y',
        0x5A: 'z',
        # Numbers 0-9
        0x30: '0', 0x31: '1', 0x32: '2', 0x33: '3', 0x34: '4',
        0x35: '5', 0x36: '6', 0x37: '7', 0x38: '8', 0x39: '9',
        # Numpad numbers 0-9
        0x60: 'numpad_0', 0x61: 'numpad_1', 0x62: 'numpad_2', 0x63: 'numpad_3',
        0x64: 'numpad_4', 0x65: 'numpad_5', 0x66: 'numpad_6', 0x67: 'numpad_7',
        0x68: 'numpad_8', 0x69: 'numpad_9',
        # Numpad operators
        0x6A: 'numpad_*', 0x6B: 'numpad_+', 0x6C: 'numpad_separator',
        0x6D: 'numpad_-', 0x6E: 'numpad_.', 0x6F: 'numpad_/',
        # Function keys F1-F12
        0x70: 'f1', 0x71: 'f2', 0x72: 'f3', 0x73: 'f4',
        0x74: 'f5', 0x75: 'f6', 0x76: 'f7', 0x77: 'f8',
        0x78: 'f9', 0x79: 'f10', 0x7A: 'f11', 0x7B: 'f12',
        # Function keys F13-F24 (rare but exist on some keyboards)
        0x7C: 'f13', 0x7D: 'f14', 0x7E: 'f15', 0x7F: 'f16',
        0x80: 'f17', 0x81: 'f18', 0x82: 'f19', 0x83: 'f20',
        0x84: 'f21', 0x85: 'f22', 0x86: 'f23', 0x87: 'f24',
        # Navigation keys
        0x20: 'space', 0x0D: 'enter', 0x1B: 'escape', 0x09: 'tab',
        0x08: 'backspace', 0x2E: 'delete', 0x24: 'home', 0x23: 'end',
        0x21: 'pageup', 0x22: 'pagedown', 0x2D: 'insert',
        0x25: 'left', 0x26: 'up', 0x27: 'right', 0x28: 'down',
        # System keys
        0x2C: 'print_screen', 0x91: 'scroll_lock', 0x13: 'pause',
        0x14: 'caps_lock', 0x90: 'num_lock', 0x5D: 'menu',
        # Media/Browser keys
        0xA6: 'browser_back', 0xA7: 'browser_forward', 0xA8: 'browser_refresh',
        0xAD: 'volume_mute', 0xAE: 'volume_down', 0xAF: 'volume_up',
        0xB0: 'media_next', 0xB1: 'media_prev', 0xB2: 'media_stop', 0xB3: 'media_play_pause',
    }
    
    # VK codes for OEM keys (symbols/punctuation) - these vary by keyboard layout
    # For these keys, we prefer using the actual character instead of the VK code
    OEM_VK_CODES = {0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF, 0xC0, 
                   0xDB, 0xDC, 0xDD, 0xDE, 0xDF, 0xE2}
    
    def _normalize_key(self, key) -> Optional[str]:
        """Normalize a pynput key to a string name
        
        Uses virtual key codes for letters/numbers (to fix keyboard layout issues),
        but uses actual characters for symbol/punctuation keys (for user readability).
        
        Args:
            key: pynput key object
        
        Returns:
            Normalized key name or None if not usable
        """
        if not PYNPUT_AVAILABLE:
            return None
        
        try:
            # Handle special keys (modifiers, etc.) first
            if hasattr(key, 'name') and key.name:
                name = key.name.lower()
                # Normalize modifier names
                if name.startswith('ctrl'):
                    return 'ctrl'
                elif name.startswith('alt'):
                    return 'alt'
                elif name.startswith('shift'):
                    return 'shift'
                elif name.startswith('cmd') or name == 'super' or name.startswith('super'):
                    return 'cmd'
                return name
            
            # Get VK code if available
            vk = getattr(key, 'vk', None)
            
            # For OEM keys (symbols/punctuation), prefer the actual character
            # This makes the display more user-friendly (shows ";" instead of "OEM 1")
            if vk and vk in self.OEM_VK_CODES:
                if hasattr(key, 'char') and key.char:
                    char = key.char
                    if char.isprintable() and len(char) == 1:
                        return char
            
            # For letters, numbers, and function keys, use VK code
            # This fixes issues with keyboard layouts (e.g., Ctrl+Alt+E = € on French keyboards)
            if vk and vk in self.VK_CODE_TO_LETTER:
                return self.VK_CODE_TO_LETTER[vk]
            
            # Fallback to character for any other key
            if hasattr(key, 'char') and key.char:
                char = key.char
                if char.isprintable() and len(char) == 1:
                    return char
            
            # Last resort: use VK code directly for unknown keys
            if vk and vk > 0:
                return f'vk_{vk}'
            
            return None
            
        except Exception:
            return None
    
    def _on_press(self, key):
        """Handle key press event
        
        Uses "Snapshot" recording logic (like Discord):
        - Records all currently pressed keys
        - When user releases a non-modifier key, recording stops automatically
        - The recorded combination is the snapshot of keys pressed at that moment
        
        Args:
            key: pynput key object
        """
        key_name = self._normalize_key(key)
        if not key_name:
            return
        
        with self._lock:
            self._pressed_keys.add(key_name)
            
            if self._recording:
                # Snapshot mode: record all currently pressed keys
                self._recorded_keys = self._pressed_keys.copy()
                
                if self._recording_callback:
                    self._recording_callback(self._recorded_keys.copy())
                return
            
            # Check if hotkey is pressed
            if self._enabled and self._callback:
                if self._hotkey.issubset(self._pressed_keys):
                    # Prevent multiple triggers - only trigger once per key combination
                    if not getattr(self, '_hotkey_triggered', False):
                        self._hotkey_triggered = True
                        try:
                            self._callback()
                        except Exception as e:
                            print(f"[ERROR] Hotkey callback error: {e}")
    
    def _on_release(self, key):
        """Handle key release event
        
        Uses "Snapshot" recording logic (like Discord):
        - When a non-modifier key is released, recording stops automatically
        - The recorded hotkey is finalized with all keys that were pressed
        
        Args:
            key: pynput key object
        """
        key_name = self._normalize_key(key)
        if not key_name:
            return
        
        # Variables to store callback info (will be called outside the lock)
        should_call_finished = False
        callback_to_call = None
        recorded_keys_copy = None
        
        with self._lock:
            self._pressed_keys.discard(key_name)
            
            # Reset hotkey trigger flag when any hotkey key is released
            if hasattr(self, '_hotkey_triggered') and self._hotkey_triggered:
                if key_name in self._hotkey:
                    self._hotkey_triggered = False
            
            # Snapshot mode: when a non-modifier key is released, stop recording
            if self._recording:
                is_modifier = key_name in self.MODIFIER_KEYS or key_name in ('ctrl', 'alt', 'shift', 'cmd')
                
                # Only stop if a non-modifier was released AND we have recorded keys
                if not is_modifier and self._recorded_keys:
                    self._recording = False
                    # Prepare callback (will be called outside lock to prevent deadlocks)
                    if self._recording_finished_callback:
                        should_call_finished = True
                        callback_to_call = self._recording_finished_callback
                        recorded_keys_copy = self._recorded_keys.copy()
        
        # Call the callback outside the lock to prevent deadlocks
        if should_call_finished and callback_to_call:
            try:
                callback_to_call(recorded_keys_copy)
            except Exception as e:
                print(f"[ERROR] Recording finished callback error: {e}")
    
    def start(self):
        """Start listening for keyboard events"""
        if not PYNPUT_AVAILABLE:
            return False
        
        if self._listener is not None:
            return True  # Already running
        
        try:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.start()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start keyboard listener: {e}")
            return False
    
    def stop(self):
        """Stop listening for keyboard events"""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        
        with self._lock:
            self._pressed_keys.clear()
    
    def enable(self):
        """Enable hotkey detection"""
        self._enabled = True
    
    def disable(self):
        """Disable hotkey detection (keeps listener running)"""
        self._enabled = False
    
    def start_recording(self, callback: Optional[Callable] = None, 
                        finished_callback: Optional[Callable] = None) -> bool:
        """Start recording a new hotkey combination
        
        Uses "Snapshot" recording (like Discord):
        - Records all currently pressed keys in real-time
        - Automatically stops when a non-modifier key is released
        - The finished_callback is called with the final recorded keys
        
        Args:
            callback: Optional callback to receive key updates during recording
            finished_callback: Optional callback called when recording finishes automatically
                              (when user releases the non-modifier key)
        
        Returns:
            True if recording started, False if pynput not available
        """
        if not PYNPUT_AVAILABLE:
            return False
        
        with self._lock:
            self._recording = True
            self._recorded_keys.clear()
            self._recording_callback = callback
            self._recording_finished_callback = finished_callback
            self._pressed_keys.clear()
        
        return True
    
    def stop_recording(self) -> Set[str]:
        """Stop recording and return the recorded hotkey
        
        Returns:
            Set of recorded key names
        """
        with self._lock:
            self._recording = False
            self._recording_callback = None
            self._recording_finished_callback = None
            result = self._recorded_keys.copy()
            self._recorded_keys.clear()
        
        return result
    
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._recording
    
    def validate_hotkey(self, keys: Set[str]) -> Tuple[bool, str]:
        """Validate a hotkey combination
        
        Args:
            keys: Set of key names to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not keys:
            return False, "No keys recorded"
        
        # Check for at least one modifier
        has_modifier = any(k in self.MODIFIER_KEYS or k in ('ctrl', 'alt', 'shift', 'cmd') 
                         for k in keys)
        if not has_modifier:
            return False, "Hotkey must include at least one modifier (Ctrl, Alt, Shift, or Win)"
        
        # Check for at least one non-modifier key
        non_modifiers = [k for k in keys if k not in self.MODIFIER_KEYS 
                        and k not in ('ctrl', 'alt', 'shift', 'cmd')]
        if not non_modifiers:
            return False, "Hotkey must include at least one non-modifier key"
        
        return True, ""

