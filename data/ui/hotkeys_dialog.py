#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Hotkeys Dialog for PurrMoji Emoji Picker
Displays and allows customization of keyboard shortcuts and mouse actions.
"""

import os
import platform
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QApplication, QScrollArea, QWidget,
                             QLineEdit, QCheckBox, QFrame, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from managers import ThemeManager, PathManager, FontManager, KeyboardManager, PYNPUT_AVAILABLE
from ui.base_dialog import ThemedDialogMixin
from ui.settings_dialog import CheckBoxWithCheckmark


class HotkeysDialog(ThemedDialogMixin, QDialog):
    """Hotkeys dialog with customization options"""
    
    # Signal emitted when recording finishes (thread-safe way to update UI from pynput thread)
    recording_finished_signal = pyqtSignal(object)
    
    # Default application shortcuts
    DEFAULT_SHORTCUTS = {
        'increase_size': 'Numpad +',
        'decrease_size': 'Numpad -',
        'previous_package': 'Page Up',
        'next_package': 'Page Down',
        'cycle_theme': 'T'
    }
    
    # Shortcut descriptions
    SHORTCUT_DESCRIPTIONS = {
        'increase_size': 'Increase emoji size',
        'decrease_size': 'Decrease emoji size',
        'previous_package': 'Previous package',
        'next_package': 'Next package',
        'cycle_theme': 'Cycle themes'
    }
    
    # Default mouse actions (modifier + action)
    DEFAULT_MOUSE_ACTIONS = {
        'copy_to_clipboard': 'Double-click',
        'toggle_favorites': 'Shift+Left Click',
        'resize_wheel': 'Shift+Wheel'
    }
    
    # Mouse action descriptions
    MOUSE_ACTION_DESCRIPTIONS = {
        'copy_to_clipboard': 'Copy emoji to clipboard',
        'toggle_favorites': 'Add/Remove from favorites',
        'resize_wheel': 'Resize emoji in grid'
    }
    
    # Mouse action types (fixed, not user-modifiable)
    MOUSE_ACTION_TYPES = {
        'copy_to_clipboard': 'Click',
        'toggle_favorites': 'Click',
        'resize_wheel': 'Wheel'
    }
    
    # Available modifiers for click actions (includes Double)
    CLICK_MODIFIER_OPTIONS = [
        'None',
        'Shift',
        'Ctrl',
        'Alt',
        'Shift+Ctrl',
        'Shift+Alt',
        'Ctrl+Alt',
        'Shift+Ctrl+Alt'
    ]
    
    # Available modifiers for wheel actions (no Double)
    WHEEL_MODIFIER_OPTIONS = [
        'None',
        'Shift',
        'Ctrl',
        'Alt',
        'Shift+Ctrl',
        'Shift+Alt',
        'Ctrl+Alt',
        'Shift+Ctrl+Alt'
    ]
    
    # Available event types
    EVENT_OPTIONS = ['Left Click', 'Double-click', 'Right-click', 'Mouse button 4', 'Mouse button 5']
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Hotkeys")
        self.setFixedSize(610, 580)
        
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
        self.category_subcategory_color = '#00557f'
        if parent and hasattr(parent, 'category_subcategory_color'):
            self.category_subcategory_color = parent.category_subcategory_color
        
        # Apply theme to this dialog
        self.setStyleSheet(ThemeManager.get_dialog_stylesheet(self.current_theme, self.category_subcategory_color))
        
        # Set Windows titlebar theme with custom colors
        self.set_windows_titlebar_theme(self.current_theme)
        
        # Initialize keyboard manager for recording
        self.keyboard_manager = KeyboardManager() if PYNPUT_AVAILABLE else None
        self.is_recording = False
        self.recording_target = None
        
        # Connect the recording finished signal (thread-safe UI update)
        self.recording_finished_signal.connect(self._finalize_recording)
        
        # Store UI elements for later access
        self.shortcut_inputs = {}
        self.record_buttons = {}
        self.reset_buttons = {}  # Store reset buttons for enabling/disabling
        self.mouse_modifier_combos = {}
        self.mouse_event_widgets = {}  # Combos or LineEdit
        self.mouse_reset_buttons = {}  # Store mouse action reset buttons
        
        # Build UI
        self.init_ui()
        
        # Center the dialog on the screen
        self.center_on_screen()
        
    def init_ui(self):
        """Initialize the user interface"""
        link_color = ThemeManager.get_link_color(self.current_theme)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(8)
        
        # ========== GLOBAL HOTKEY SECTION ==========
        global_title_label = QLabel("Global Hotkey (system-wide)")
        global_title_label.setFont(FontManager.get_font(11, QFont.Bold))
        global_title_label.setStyleSheet(f"color: {link_color};")
        content_layout.addWidget(global_title_label)
        
        # Enable global hotkey checkbox
        self.enable_hotkey_checkbox = CheckBoxWithCheckmark(
            "Enable global hotkey to show/hide PurrMoji", 
            self.current_theme, 
            self.category_subcategory_color
        )
        self.enable_hotkey_checkbox.setFont(FontManager.get_font(10))
        if self.parent_window and hasattr(self.parent_window, 'data_manager'):
            self.enable_hotkey_checkbox.setChecked(self.parent_window.data_manager.global_hotkey_enabled)
        else:
            self.enable_hotkey_checkbox.setChecked(True)
        self.enable_hotkey_checkbox.stateChanged.connect(self.on_enable_hotkey_changed)
        content_layout.addWidget(self.enable_hotkey_checkbox)
        
        # Uniform widths for alignment across all sections
        self.LABEL_WIDTH = 210
        self.INPUT_WIDTH = 140    # Match modifier width
        self.MODIFIER_WIDTH = 140 # Modifier dropdowns
        self.ACTION_WIDTH = 140   # Event dropdowns (Left Click, etc.)
        self.RECORD_WIDTH = 140   # Record buttons
        self.RESET_WIDTH = 28
        
        # Global hotkey input row
        global_hotkey_layout = QHBoxLayout()
        global_hotkey_layout.setSpacing(8)
        
        self.global_hotkey_label = QLabel("Show/Hide PurrMoji:")
        self.global_hotkey_label.setFont(FontManager.get_font(10))
        self.global_hotkey_label.setFixedWidth(self.LABEL_WIDTH)
        self.global_hotkey_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        global_hotkey_layout.addWidget(self.global_hotkey_label)
        
        self.global_hotkey_input = QLineEdit()
        self.global_hotkey_input.setFixedSize(self.INPUT_WIDTH, 28)
        self.global_hotkey_input.setFont(FontManager.get_font(10))
        self.global_hotkey_input.setReadOnly(True)
        self.global_hotkey_input.setAlignment(Qt.AlignCenter)
        if self.parent_window and hasattr(self.parent_window, 'data_manager'):
            self.global_hotkey_input.setText(self.parent_window.data_manager.global_hotkey)
            self.current_global_hotkey = self.parent_window.data_manager.global_hotkey
        else:
            self.global_hotkey_input.setText("Ctrl+Alt+X")
            self.current_global_hotkey = "Ctrl+Alt+X"
        global_hotkey_layout.addWidget(self.global_hotkey_input)
        
        self.global_record_button = QPushButton("Record")
        self.global_record_button.setFixedSize(self.RECORD_WIDTH, 28)
        self.global_record_button.setFont(FontManager.get_font(9))
        self.global_record_button.clicked.connect(lambda: self.on_record_click('global'))
        global_hotkey_layout.addWidget(self.global_record_button)
        
        self.global_reset_button = QPushButton("↩")
        self.global_reset_button.setFixedSize(self.RESET_WIDTH, 28)
        self.global_reset_button.setFont(FontManager.get_font(12))
        self.global_reset_button.setToolTip("Reset to default (Ctrl+Alt+X)")
        self.global_reset_button.clicked.connect(lambda: self.reset_shortcut('global'))
        global_hotkey_layout.addWidget(self.global_reset_button)
        
        # Connect text change to update reset button state
        self.global_hotkey_input.textChanged.connect(self.update_global_reset_button_state)
        
        # Initialize global reset button state
        self.update_global_reset_button_state()
        
        global_hotkey_layout.addStretch()
        content_layout.addLayout(global_hotkey_layout)
        
        # Win+. warning row (hidden by default, shown when Win+. is selected)
        self.win_period_warning_widget = QWidget()
        win_period_layout = QHBoxLayout(self.win_period_warning_widget)
        win_period_layout.setContentsMargins(0, 4, 0, 4)
        win_period_layout.setSpacing(8)
        
        # Stretch at the beginning to push text to the right
        win_period_layout.addStretch()
        
        self.win_period_text = QLabel("⚠ This hotkey conflicts with Windows' own emoji picker")
        self.win_period_text.setFont(FontManager.get_font(9))
        self.win_period_text.setStyleSheet(f"color: {link_color};")
        win_period_layout.addWidget(self.win_period_text)
        
        # Hide by default (only shown on Windows when Win+. is selected)
        self.win_period_warning_widget.setVisible(False)
        content_layout.addWidget(self.win_period_warning_widget)
        
        # Check initial state for Win+. warning
        self.update_win_period_warning()
        
        # Pynput warning if not available
        if not PYNPUT_AVAILABLE:
            pynput_warning = QLabel("⚠ pynput not installed. Global hotkey unavailable.")
            pynput_warning.setFont(FontManager.get_font(9))
            pynput_warning.setStyleSheet("color: #ff6600; margin-left: 10px;")
            content_layout.addWidget(pynput_warning)
            self.enable_hotkey_checkbox.setEnabled(False)
            self.global_hotkey_input.setEnabled(False)
            self.global_record_button.setEnabled(False)
            self.global_reset_button.setEnabled(False)
        
        self.update_global_hotkey_controls_state()
        
        # Separator
        self.add_separator(content_layout)
        
        # ========== KEYBOARD SHORTCUTS SECTION ==========
        app_title_label = QLabel("Keyboard Shortcuts")
        app_title_label.setFont(FontManager.get_font(11, QFont.Bold))
        app_title_label.setStyleSheet(f"color: {link_color};")
        content_layout.addWidget(app_title_label)
        
        # Load saved shortcuts
        self.load_shortcuts()
        
        # Create customizable shortcut rows
        for shortcut_id, description in self.SHORTCUT_DESCRIPTIONS.items():
            self.create_shortcut_row(content_layout, shortcut_id, description)
        
        # Separator
        self.add_separator(content_layout)
        
        # ========== MOUSE ACTIONS SECTION ==========
        mouse_title_label = QLabel("Mouse Actions")
        mouse_title_label.setFont(FontManager.get_font(11, QFont.Bold))
        mouse_title_label.setStyleSheet(f"color: {link_color};")
        content_layout.addWidget(mouse_title_label)
        
        # Load saved mouse actions
        self.load_mouse_actions()
        
        # Create mouse action rows with modifier dropdown + action dropdown
        for action_id, description in self.MOUSE_ACTION_DESCRIPTIONS.items():
            self.create_mouse_action_row(content_layout, action_id, description)
        
        content_layout.addStretch()
        
        # Set the content widget in the scroll area
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # ========== BUTTONS ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(80, 30)
        ok_button.setFont(FontManager.get_font(9))
        ok_button.clicked.connect(self.accept_changes)
        button_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setFixedSize(80, 30)
        cancel_button.setFont(FontManager.get_font(9))
        cancel_button.clicked.connect(self.reject_changes)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def add_separator(self, layout):
        """Add a horizontal separator line"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("margin: 8px 0;")
        layout.addWidget(separator)
    
    def create_shortcut_row(self, parent_layout, shortcut_id, description):
        """Create a row for a customizable keyboard shortcut"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
        
        # Description label (right-aligned)
        desc_label = QLabel(f"{description}:")
        desc_label.setFont(FontManager.get_font(10))
        desc_label.setFixedWidth(self.LABEL_WIDTH)
        desc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row_layout.addWidget(desc_label)
        
        # Shortcut input
        shortcut_input = QLineEdit()
        shortcut_input.setFixedSize(self.INPUT_WIDTH, 28)
        shortcut_input.setFont(FontManager.get_font(10))
        shortcut_input.setReadOnly(True)
        shortcut_input.setAlignment(Qt.AlignCenter)
        shortcut_input.setText(self.current_shortcuts.get(shortcut_id, self.DEFAULT_SHORTCUTS[shortcut_id]))
        self.shortcut_inputs[shortcut_id] = shortcut_input
        row_layout.addWidget(shortcut_input)
        
        # Record button
        record_button = QPushButton("Record")
        record_button.setFixedSize(self.RECORD_WIDTH, 28)
        record_button.setFont(FontManager.get_font(9))
        record_button.clicked.connect(lambda checked, sid=shortcut_id: self.on_record_click(sid))
        self.record_buttons[shortcut_id] = record_button
        row_layout.addWidget(record_button)
        
        # Reset button
        reset_button = QPushButton("↩")
        reset_button.setFixedSize(self.RESET_WIDTH, 28)
        reset_button.setFont(FontManager.get_font(12))
        reset_button.setToolTip(f"Reset to default ({self.DEFAULT_SHORTCUTS[shortcut_id]})")
        reset_button.clicked.connect(lambda checked, sid=shortcut_id: self.reset_shortcut(sid))
        self.reset_buttons[shortcut_id] = reset_button
        row_layout.addWidget(reset_button)
        
        # Connect text change to update reset button state
        shortcut_input.textChanged.connect(lambda text, sid=shortcut_id: self.update_shortcut_reset_button_state(sid))
        
        # Initialize reset button state
        current_value = self.current_shortcuts.get(shortcut_id, self.DEFAULT_SHORTCUTS[shortcut_id])
        reset_button.setEnabled(current_value != self.DEFAULT_SHORTCUTS[shortcut_id])
        
        row_layout.addStretch()
        parent_layout.addLayout(row_layout)
    
    def create_mouse_action_row(self, parent_layout, action_id, description):
        """Create a row for a customizable mouse action with modifier dropdown"""
        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
        
        # Description label (right-aligned)
        desc_label = QLabel(f"{description}:")
        desc_label.setFont(FontManager.get_font(10))
        desc_label.setFixedWidth(self.LABEL_WIDTH)
        desc_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        row_layout.addWidget(desc_label)
        
        # Parse current action to split modifier and event
        current_action = self.current_mouse_actions.get(action_id, self.DEFAULT_MOUSE_ACTIONS[action_id])
        current_modifier, current_event = self.parse_mouse_action(current_action, action_id)
        
        # Modifier dropdown
        modifier_combo = QComboBox()
        modifier_combo.setFixedSize(self.MODIFIER_WIDTH, 28)
        modifier_combo.setFont(FontManager.get_font(10))
        
        # Add appropriate options based on action type
        action_type = self.MOUSE_ACTION_TYPES[action_id]
        if action_type == 'Wheel':
            modifier_combo.addItems(self.WHEEL_MODIFIER_OPTIONS)
        else:
            modifier_combo.addItems(self.CLICK_MODIFIER_OPTIONS)
        
        modifier_index = modifier_combo.findText(current_modifier)
        if modifier_index >= 0:
            modifier_combo.setCurrentIndex(modifier_index)
        
        self.mouse_modifier_combos[action_id] = modifier_combo
        row_layout.addWidget(modifier_combo)
        
        # Event widget (ComboBox or fixed LineEdit)
        if action_id == 'resize_wheel':
            # Fixed Wheel label, but styled like input
            event_widget = QLineEdit("Wheel")
            event_widget.setFixedSize(self.ACTION_WIDTH, 28)
            event_widget.setFont(FontManager.get_font(10))
            event_widget.setReadOnly(True)
            event_widget.setAlignment(Qt.AlignCenter)
            # Standard style
        else:
            # Click/Double-click dropdown
            event_widget = QComboBox()
            event_widget.setFixedSize(self.ACTION_WIDTH, 28)
            event_widget.setFont(FontManager.get_font(10))
            event_widget.addItems(self.EVENT_OPTIONS)
            
            event_index = event_widget.findText(current_event)
            if event_index >= 0:
                event_widget.setCurrentIndex(event_index)
        
        self.mouse_event_widgets[action_id] = event_widget
        row_layout.addWidget(event_widget)
        
        # Reset button (replacing default button to match other rows)
        reset_button = QPushButton("↩")
        reset_button.setFixedSize(self.RESET_WIDTH, 28)
        reset_button.setFont(FontManager.get_font(12))
        reset_button.setToolTip(f"Reset to default ({self.DEFAULT_MOUSE_ACTIONS[action_id]})")
        reset_button.clicked.connect(lambda checked, aid=action_id: self.reset_mouse_action(aid))
        self.mouse_reset_buttons[action_id] = reset_button
        row_layout.addWidget(reset_button)
        
        # Connect modifier and event changes to update reset button state
        modifier_combo.currentIndexChanged.connect(lambda idx, aid=action_id: self.update_mouse_reset_button_state(aid))
        if isinstance(event_widget, QComboBox):
            event_widget.currentIndexChanged.connect(lambda idx, aid=action_id: self.update_mouse_reset_button_state(aid))
        
        # Initialize reset button state
        self.update_mouse_reset_button_state(action_id)
        
        row_layout.addStretch()
        parent_layout.addLayout(row_layout)
    
    def parse_mouse_action(self, action_string, action_id):
        """Split mouse action string into modifier and event type
        
        Args:
            action_string: Full action string (e.g., 'Shift+Left Click', 'Double-click')
            action_id: ID of the action (to determine default event type)
            
        Returns:
            tuple: (modifier, event)
        """
        if not action_string:
            return ('None', 'Left Click')
            
        # Special case for Wheel
        if action_id == 'resize_wheel':
            if 'Wheel' in action_string:
                if action_string == 'Wheel':
                    return ('None', 'Wheel')
                # Format: "Ctrl+Wheel"
                parts = action_string.rsplit('+', 1)
                return (parts[0], 'Wheel')
            return ('None', 'Wheel')
        
        # Define all click event types to check
        click_events = ['Double-click', 'Right-click', 'Mouse button 4', 'Mouse button 5', 'Left Click']
        # Also handle legacy "Click" format
        legacy_click = 'Click'
        
        # Check for each event type
        for event in click_events:
            if event in action_string:
                if action_string == event:
                    return ('None', event)
                # Find where the event starts
                event_pos = action_string.rfind(event)
                if event_pos > 0 and action_string[event_pos - 1] == '+':
                    modifier = action_string[:event_pos - 1]
                    return (modifier, event)
                return ('None', event)
        
        # Handle legacy "Click" -> convert to "Left Click"
        if legacy_click in action_string and 'Left Click' not in action_string:
            if action_string == legacy_click:
                return ('None', 'Left Click')
            parts = action_string.rsplit('+', 1)
            if parts[-1] == legacy_click:
                return (parts[0], 'Left Click')
            
        return ('None', 'Left Click')
    
    def build_mouse_action_string(self, modifier, event):
        """Build the full mouse action string
        
        Args:
            modifier: Modifier string (None, Shift, etc.)
            event: Event string (Click, Double-click, Wheel)
        
        Returns:
            Full action string
        """
        if modifier == 'None' or modifier == '':
            return event
        
        return f"{modifier}+{event}"
    
    def load_shortcuts(self):
        """Load saved keyboard shortcuts from data manager"""
        self.current_shortcuts = {}
        if self.parent_window and hasattr(self.parent_window, 'data_manager'):
            saved = getattr(self.parent_window.data_manager, 'app_shortcuts', {})
            for shortcut_id in self.DEFAULT_SHORTCUTS:
                self.current_shortcuts[shortcut_id] = saved.get(shortcut_id, self.DEFAULT_SHORTCUTS[shortcut_id])
        else:
            self.current_shortcuts = self.DEFAULT_SHORTCUTS.copy()
    
    def load_mouse_actions(self):
        """Load saved mouse actions from data manager"""
        self.current_mouse_actions = {}
        if self.parent_window and hasattr(self.parent_window, 'data_manager'):
            saved = getattr(self.parent_window.data_manager, 'mouse_actions', {})
            for action_id in self.DEFAULT_MOUSE_ACTIONS:
                self.current_mouse_actions[action_id] = saved.get(action_id, self.DEFAULT_MOUSE_ACTIONS[action_id])
        else:
            self.current_mouse_actions = self.DEFAULT_MOUSE_ACTIONS.copy()
    
    def on_enable_hotkey_changed(self):
        """Handle enable hotkey checkbox change"""
        self.update_global_hotkey_controls_state()
    
    def update_global_hotkey_controls_state(self):
        """Update enabled state of global hotkey controls"""
        enabled = self.enable_hotkey_checkbox.isChecked() and PYNPUT_AVAILABLE
        self.global_hotkey_label.setEnabled(enabled)
        self.global_hotkey_input.setEnabled(enabled)
        self.global_record_button.setEnabled(enabled)
        self.win_period_text.setEnabled(enabled)
        # Reset button also depends on whether value differs from default
        self.update_global_reset_button_state()
    
    def update_global_reset_button_state(self, text=None):
        """Update enabled state of global hotkey reset button
        
        The reset button is enabled only if:
        - Global hotkey is enabled
        - Current value differs from default (Ctrl+Alt+X)
        """
        hotkey_enabled = self.enable_hotkey_checkbox.isChecked() and PYNPUT_AVAILABLE
        current_value = self.global_hotkey_input.text()
        is_default = current_value == "Ctrl+Alt+X"
        self.global_reset_button.setEnabled(hotkey_enabled and not is_default)
    
    def update_shortcut_reset_button_state(self, shortcut_id):
        """Update enabled state of a shortcut reset button
        
        The reset button is enabled only if current value differs from default
        """
        if shortcut_id not in self.reset_buttons or shortcut_id not in self.shortcut_inputs:
            return
        current_value = self.shortcut_inputs[shortcut_id].text()
        default_value = self.DEFAULT_SHORTCUTS.get(shortcut_id, "")
        self.reset_buttons[shortcut_id].setEnabled(current_value != default_value)
    
    def update_mouse_reset_button_state(self, action_id):
        """Update enabled state of a mouse action reset button
        
        The reset button is enabled only if current value differs from default
        """
        if action_id not in self.mouse_reset_buttons:
            return
        if action_id not in self.mouse_modifier_combos:
            return
            
        # Get current modifier
        current_modifier = self.mouse_modifier_combos[action_id].currentText()
        
        # Get current event
        event_widget = self.mouse_event_widgets.get(action_id)
        if isinstance(event_widget, QComboBox):
            current_event = event_widget.currentText()
        else:
            current_event = "Wheel"
        
        # Build current action string
        current_action = self.build_mouse_action_string(current_modifier, current_event)
        
        # Compare with default
        default_action = self.DEFAULT_MOUSE_ACTIONS.get(action_id, "")
        self.mouse_reset_buttons[action_id].setEnabled(current_action != default_action)
    
    def on_record_click(self, shortcut_id):
        """Handle record button click for keyboard shortcuts"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording(shortcut_id)
    
    def start_recording(self, target_id):
        """Start recording a new shortcut
        
        Uses "Snapshot" mode like Discord:
        - User presses their key combination (e.g., Ctrl+Shift+E)
        - Recording stops automatically when the non-modifier key is released
        """
        self.is_recording = True
        self.recording_target = target_id
        
        # Update UI
        if target_id == 'global':
            self.global_record_button.setText("Stop")
            self.global_hotkey_input.setText("Press keys...")
            self.global_hotkey_input.setStyleSheet("background-color: #ffffcc; color: #000000;")
        else:
            self.record_buttons[target_id].setText("Stop")
            self.shortcut_inputs[target_id].setText("Press keys...")
            self.shortcut_inputs[target_id].setStyleSheet("background-color: #ffffcc; color: #000000;")
        
        # Start keyboard listener with auto-stop callback
        if self.keyboard_manager:
            self.keyboard_manager.start_recording(
                callback=self.on_keys_changed,
                finished_callback=self.on_recording_finished
            )
            self.keyboard_manager.start()
    
    def on_recording_finished(self, recorded_keys):
        """Called automatically when recording finishes (user released non-modifier key)
        
        This is called from a background thread (pynput), so we emit a signal
        to safely update the UI from the main Qt thread.
        
        Args:
            recorded_keys: Set of recorded key names
        """
        # Emit signal to update UI on main thread (thread-safe)
        self.recording_finished_signal.emit(recorded_keys)
    
    def stop_recording(self):
        """Stop recording manually (user clicked Stop button)"""
        if not self.is_recording:
            return
        
        # Get recorded keys before stopping
        recorded_keys = set()
        if self.keyboard_manager:
            recorded_keys = self.keyboard_manager.stop_recording()
            self.keyboard_manager.stop()
        
        self._finalize_recording(recorded_keys)
    
    def _finalize_recording(self, recorded_keys):
        """Finalize recording and apply the new shortcut
        
        This is called either:
        - Automatically when user releases the non-modifier key (Snapshot mode)
        - Manually when user clicks Stop button
        
        Args:
            recorded_keys: Set of recorded key names
        """
        if not self.is_recording and not self.recording_target:
            return
        
        target = self.recording_target
        self.is_recording = False
        self.recording_target = None
        
        # Make sure the keyboard manager is stopped
        if self.keyboard_manager:
            self.keyboard_manager.stop_recording()
            self.keyboard_manager.stop()
        
        # Reset UI and apply new shortcut
        if target == 'global':
            self.global_record_button.setText("Record")
            self.global_hotkey_input.setStyleSheet("")
            
            if recorded_keys:
                is_valid, _ = self.keyboard_manager.validate_hotkey(recorded_keys) if self.keyboard_manager else (False, "")
                if is_valid:
                    self.keyboard_manager.hotkey = recorded_keys
                    new_hotkey = self.keyboard_manager.get_hotkey_string()
                    self.global_hotkey_input.setText(new_hotkey)
                    self.current_global_hotkey = new_hotkey
                else:
                    self.global_hotkey_input.setText(self.current_global_hotkey)
            else:
                self.global_hotkey_input.setText(self.current_global_hotkey)
            
            # Update Win+. warning
            self.update_win_period_warning()
        elif target in self.record_buttons:
            self.record_buttons[target].setText("Record")
            self.shortcut_inputs[target].setStyleSheet("")
            
            if recorded_keys:
                shortcut_str = self.format_shortcut(recorded_keys)
                if shortcut_str:
                    self.shortcut_inputs[target].setText(shortcut_str)
                    self.current_shortcuts[target] = shortcut_str
                else:
                    self.shortcut_inputs[target].setText(self.current_shortcuts.get(target, ""))
            else:
                self.shortcut_inputs[target].setText(self.current_shortcuts.get(target, ""))
    
    def format_shortcut(self, keys):
        """Format a set of keys into a display string"""
        if not keys:
            return ""
        
        order = ['ctrl', 'alt', 'shift', 'cmd']
        result = []
        
        key_display = {
            'ctrl': 'Ctrl', 'alt': 'Alt', 'shift': 'Shift', 'cmd': 'Win',
            'space': 'Space', 'enter': 'Enter', 'escape': 'Escape', 'tab': 'Tab',
            'backspace': 'Backspace', 'delete': 'Delete', 'home': 'Home', 'end': 'End',
            'pageup': 'Page Up', 'pagedown': 'Page Down', 'insert': 'Insert',
            'left': 'Left', 'right': 'Right', 'up': 'Up', 'down': 'Down',
            # Numpad keys
            'numpad_0': 'Numpad 0', 'numpad_1': 'Numpad 1', 'numpad_2': 'Numpad 2',
            'numpad_3': 'Numpad 3', 'numpad_4': 'Numpad 4', 'numpad_5': 'Numpad 5',
            'numpad_6': 'Numpad 6', 'numpad_7': 'Numpad 7', 'numpad_8': 'Numpad 8',
            'numpad_9': 'Numpad 9',
            'numpad_+': 'Numpad +', 'numpad_-': 'Numpad -', 'numpad_*': 'Numpad *',
            'numpad_/': 'Numpad /', 'numpad_.': 'Numpad .', 'numpad_separator': 'Numpad Sep',
            'numpad_enter': 'Numpad Enter',
            # System keys
            'print_screen': 'Print Screen', 'scroll_lock': 'Scroll Lock', 'pause': 'Pause',
            'caps_lock': 'Caps Lock', 'num_lock': 'Num Lock', 'menu': 'Menu',
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
        
        for mod in order:
            if mod in keys:
                result.append(key_display.get(mod, mod.capitalize()))
        
        for key in sorted(keys):
            if key not in order:
                if key in key_display:
                    result.append(key_display[key])
                # Handle unknown VK codes (vk_XXX format)
                elif key.startswith('vk_'):
                    result.append(key.upper())
                else:
                    result.append(key.upper() if len(key) == 1 else key.capitalize())
        
        return '+'.join(result) if result else ""
    
    def on_keys_changed(self, keys):
        """Callback when keys are pressed during shortcut recording"""
        if not keys or not self.is_recording:
            return
        
        shortcut_str = self.format_shortcut(keys)
        
        if self.recording_target == 'global':
            self.global_hotkey_input.setText(shortcut_str)
        elif self.recording_target in self.shortcut_inputs:
            self.shortcut_inputs[self.recording_target].setText(shortcut_str)
    
    def reset_shortcut(self, shortcut_id):
        """Reset a keyboard shortcut to its default value"""
        if shortcut_id == 'global':
            self.global_hotkey_input.setText("Ctrl+Alt+X")
            self.current_global_hotkey = "Ctrl+Alt+X"
            # Update Win+. warning (hide it since default is not Win+.)
            self.update_win_period_warning()
        else:
            default = self.DEFAULT_SHORTCUTS.get(shortcut_id, "")
            self.shortcut_inputs[shortcut_id].setText(default)
            self.current_shortcuts[shortcut_id] = default
    
    def reset_mouse_action(self, action_id):
        """Reset a mouse action to its default modifier and event"""
        default_action = self.DEFAULT_MOUSE_ACTIONS.get(action_id, "")
        default_modifier, default_event = self.parse_mouse_action(default_action, action_id)
        
        # Reset modifier
        if action_id in self.mouse_modifier_combos:
            index = self.mouse_modifier_combos[action_id].findText(default_modifier)
            if index >= 0:
                self.mouse_modifier_combos[action_id].setCurrentIndex(index)
        
        # Reset event (if it's a combo)
        if action_id in self.mouse_event_widgets and isinstance(self.mouse_event_widgets[action_id], QComboBox):
            index = self.mouse_event_widgets[action_id].findText(default_event)
            if index >= 0:
                self.mouse_event_widgets[action_id].setCurrentIndex(index)
    
    def accept_changes(self):
        """Save changes and close dialog"""
        if self.is_recording:
            self.stop_recording()
        
        if self.parent_window and hasattr(self.parent_window, 'data_manager'):
            dm = self.parent_window.data_manager
            
            # Save global hotkey settings
            dm.global_hotkey_enabled = self.enable_hotkey_checkbox.isChecked()
            dm.global_hotkey = self.current_global_hotkey
            dm.save_data('global_hotkey_enabled', dm.global_hotkey_enabled)
            dm.save_data('global_hotkey', dm.global_hotkey)
            
            # Save keyboard shortcuts
            dm.app_shortcuts = {}
            for shortcut_id, input_field in self.shortcut_inputs.items():
                dm.app_shortcuts[shortcut_id] = input_field.text()
            dm.save_data('app_shortcuts', dm.app_shortcuts)
            
            # Save mouse actions
            dm.mouse_actions = {}
            for action_id, modifier_combo in self.mouse_modifier_combos.items():
                modifier = modifier_combo.currentText()
                
                # Get event type
                event_widget = self.mouse_event_widgets.get(action_id)
                if isinstance(event_widget, QComboBox):
                    event = event_widget.currentText()
                else:
                    event = "Wheel" # Fixed for wheel action
                    
                full_action = self.build_mouse_action_string(modifier, event)
                dm.mouse_actions[action_id] = full_action
            dm.save_data('mouse_actions', dm.mouse_actions)
            
            # Update parent window
            if hasattr(self.parent_window, 'update_global_hotkey'):
                self.parent_window.update_global_hotkey()
            if hasattr(self.parent_window, 'update_app_shortcuts'):
                self.parent_window.update_app_shortcuts()
            if hasattr(self.parent_window, 'update_mouse_actions'):
                self.parent_window.update_mouse_actions()
        
        self.accept()
    
    def reject_changes(self):
        """Discard changes and close dialog"""
        if self.is_recording:
            self.stop_recording()
        self.reject()
    
    def is_win_period_hotkey(self, hotkey_string):
        """Check if the hotkey is Win + . (Windows + Period)
        
        On AZERTY keyboards, the period key (without Shift) produces ';' instead of '.'
        On some other keyboards, it may produce ':' or other characters.
        We detect all these variants since they all correspond to the same physical key
        that Windows uses for its emoji picker (Win + .).
        
        Args:
            hotkey_string: The hotkey string to check
            
        Returns:
            True if the hotkey is Win + . (or equivalent on other keyboard layouts)
        """
        if not hotkey_string:
            return False
        
        normalized = hotkey_string.lower().replace(' ', '')
        
        # Check various formats for Win + . and keyboard layout variants
        # QWERTY: Win + .
        # AZERTY: Win + ; (period key without Shift produces semicolon)
        # Other layouts may produce : or other characters
        win_period_formats = [
            # Period (QWERTY and explicit)
            'win+.', 'win+period', 'cmd+.', 'cmd+period',
            'super+.', 'super+period', 'meta+.', 'meta+period',
            # Semicolon (AZERTY - same physical key as period)
            'win+;', 'win+semicolon', 'cmd+;', 'cmd+semicolon',
            'super+;', 'super+semicolon', 'meta+;', 'meta+semicolon',
            # Colon (some keyboard layouts)
            'win+:', 'win+colon', 'cmd+:', 'cmd+colon',
            'super+:', 'super+colon', 'meta+:', 'meta+colon',
        ]
        
        return normalized in win_period_formats
    
    def update_win_period_warning(self):
        """Update visibility of the Win+. warning based on current hotkey"""
        # Only show on Windows
        if platform.system() != "Windows":
            self.win_period_warning_widget.setVisible(False)
            return
        
        current_hotkey = self.global_hotkey_input.text()
        show_warning = self.is_win_period_hotkey(current_hotkey)
        self.win_period_warning_widget.setVisible(show_warning)
