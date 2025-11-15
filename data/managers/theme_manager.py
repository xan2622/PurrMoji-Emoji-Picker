#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Theme Manager for PurrMoji Emoji Picker
Provides theme styles (Light/Dark) for the application and all dialogs.
"""


class ThemeManager:
    """Manages application themes (Light/Dark)"""
    
    # Theme names
    THEME_LIGHT = "Light"
    THEME_MEDIUM = "Medium"
    THEME_DARK = "Dark"
    
    # Available themes
    AVAILABLE_THEMES = [THEME_LIGHT, THEME_MEDIUM, THEME_DARK]
    
    # Dark theme color palette
    class DarkColors:
        BG_PRIMARY = "#202020"
        BG_SECONDARY = "#2d2d2d"
        BG_HOVER = "#3a3a3a"
        BG_PRESSED = "#252525"
        BG_DISABLED = "#2B2B2B"
        
        BORDER_PRIMARY = "#3f3f3f"
        BORDER_SECONDARY = "#5a5a5a"
        BORDER_HOVER = "#505050"
        BORDER_LIGHT = "#707070"
        BORDER_DISABLED = "#3B3B3B"
        
        TEXT_PRIMARY = "#ffffff"
        TEXT_DISABLED = "#5E5E5E"
        TEXT_SECONDARY = "#888888"
        
        ACCENT = "#3699e7"
        ACCENT_PURPLE = "#aa7b9b"
        ACCENT_PURPLE_LIGHT = "#c798ba"
        
        # Radio button specific colors
        RADIO_BG_INACTIVE = "#2d2d2d"
        RADIO_BORDER_INACTIVE = "#707070"
        RADIO_BORDER_DISABLED = "#4a4a4a"
    
    # Medium theme color palette (intermediate between Light and Dark)
    class MediumColors:
        BG_PRIMARY = "#5a5a5a"
        BG_SECONDARY = "#6e6e6e"
        BG_HOVER = "#7d7d7d"
        BG_PRESSED = "#4a4a4a"
        BG_DISABLED = "#656565"
        
        BORDER_PRIMARY = "#858585"
        BORDER_SECONDARY = "#999999"
        BORDER_HOVER = "#757575"
        BORDER_LIGHT = "#ababab"
        BORDER_DISABLED = "#7d7d7d"
        
        TEXT_PRIMARY = "#ffffff"
        TEXT_DISABLED = "#adadad"
        TEXT_SECONDARY = "#c4c4c4"
        
        ACCENT = "#3699e7"
        ACCENT_PURPLE = "#aa7b9b"
        ACCENT_PURPLE_LIGHT = "#c798ba"
        
        # Radio button specific colors
        RADIO_BG_INACTIVE = "#6e6e6e"
        RADIO_BORDER_INACTIVE = "#ababab"
        RADIO_BORDER_DISABLED = "#8b8b8b"
    
    # Light theme color palette
    class LightColors:
        BG_PRIMARY = "#ffffff"
        BG_SECONDARY = "#f0f0f0"
        BG_HOVER = "#e0e0e0"
        BG_PRESSED = "#d0d0d0"
        
        BORDER_PRIMARY = "#ccc"
        BORDER_SECONDARY = "#dddddd"
        BORDER_HOVER = "#999"
        
        TEXT_PRIMARY = "#000000"
        TEXT_DISABLED = "#737373"
        
        ACCENT = "#3699e7"
        ACCENT_PURPLE = "#aa7b9b"
        
        # Radio button specific colors
        RADIO_BG_INACTIVE = "#f3f3f3"
        RADIO_BORDER_INACTIVE = "#808080"
        RADIO_BORDER_DISABLED = "#cccccc"
    
    @staticmethod
    def get_colors(theme):
        """Get color palette for a given theme
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            Color palette class
        """
        if theme == ThemeManager.THEME_DARK:
            return ThemeManager.DarkColors
        elif theme == ThemeManager.THEME_MEDIUM:
            return ThemeManager.MediumColors
        else:
            return ThemeManager.LightColors
    
    @staticmethod
    def create_button_style(bg_color, text_color, border_color, border_width="1px", 
                            border_radius="4px", padding="5px", 
                            hover_bg=None, hover_border=None,
                            pressed_bg=None):
        """Helper to create button stylesheet
        
        Args:
            bg_color: Background color
            text_color: Text color
            border_color: Border color
            border_width: Border width (default: "1px")
            border_radius: Border radius (default: "4px")
            padding: Padding (default: "5px")
            hover_bg: Hover background color (optional)
            hover_border: Hover border color (optional)
            pressed_bg: Pressed background color (optional)
        
        Returns:
            str: CSS stylesheet for button
        """
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: {border_width} solid {border_color};
                border-radius: {border_radius};
                padding: {padding};
            }}"""
        
        if hover_bg or hover_border:
            style += f"""
            QPushButton:hover {{
                {f'background-color: {hover_bg};' if hover_bg else ''}
                {f'border: {border_width} solid {hover_border};' if hover_border else ''}
            }}"""
        
        if pressed_bg:
            style += f"""
            QPushButton:pressed {{
                background-color: {pressed_bg};
            }}"""
        
        return style
    
    @staticmethod
    def create_solid_button_style(color, border_width="1px", border_radius="3px", padding="5px"):
        """Helper to create solid color button stylesheet (same color for bg and border)
        
        Args:
            color: Color for background and border
            border_width: Border width (default: "1px")
            border_radius: Border radius (default: "3px")
            padding: Padding (default: "5px")
        
        Returns:
            str: CSS stylesheet for solid button with adaptive text color
        
        Note:
            Automatically calculates optimal text color (black or white) based on background luminance
        """
        # Calculate optimal text color for readability
        text_color = ThemeManager.get_text_color_for_background(color)
        
        return f"""
            QPushButton {{
                border: {border_width} solid {color};
                border-radius: {border_radius};
                background-color: {color};
                color: {text_color};
                padding: {padding};
            }}
            QPushButton:hover {{
                background-color: {color};
                border: {border_width} solid {color};
            }}
            QPushButton:pressed {{
                background-color: {color};
            }}
        """
    
    @staticmethod
    def get_dialog_stylesheet(theme, category_subcategory_color='#3699e7'):
        """Get the main stylesheet for dialogs based on theme
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
            category_subcategory_color: Custom color for checkboxes, radio buttons, and dropdown selections (default: '#3699e7')
        
        Returns:
            str: Stylesheet string for QDialog
        
        Note:
            Light theme uses native Windows 11 style with custom colors.
            Medium and Dark themes apply modern themed styles.
        """
        if theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM]:
            dc = ThemeManager.get_colors(theme)
            # Calculate optimal text color for custom background color
            selection_text_color = ThemeManager.get_text_color_for_background(category_subcategory_color)
            return f"""
                QDialog {{
                    background-color: {dc.BG_PRIMARY};
                    color: {dc.TEXT_PRIMARY};
                }}
                QLabel {{
                    color: {dc.TEXT_PRIMARY};
                }}
                QPushButton {{
                    background-color: {dc.BG_SECONDARY};
                    color: {dc.TEXT_PRIMARY};
                    border: 1px solid {dc.BORDER_PRIMARY};
                    border-radius: 4px;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {dc.BG_HOVER};
                    border: 1px solid {dc.BORDER_HOVER};
                }}
                QPushButton:pressed {{
                    background-color: {dc.BG_PRESSED};
                }}
                QCheckBox {{
                    color: {dc.TEXT_PRIMARY};
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid {dc.BORDER_SECONDARY};
                    border-radius: 4px;
                    background-color: {dc.BG_SECONDARY};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {category_subcategory_color};
                    border: 2px solid {category_subcategory_color};
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid {dc.TEXT_SECONDARY};
                    background-color: {dc.BG_HOVER};
                }}
                QComboBox {{
                    background-color: {dc.BG_SECONDARY};
                    color: {dc.TEXT_PRIMARY};
                    border: 1px solid {dc.BORDER_PRIMARY};
                    border-radius: 4px;
                    padding: 5px;
                }}
                QComboBox:hover {{
                    border: 1px solid {dc.BORDER_HOVER};
                }}
                QComboBox:disabled {{
                    background-color: {dc.BG_DISABLED};
                    color: {dc.TEXT_DISABLED};
                    border: 1px solid {dc.BORDER_DISABLED};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {dc.BG_SECONDARY};
                    color: {dc.TEXT_PRIMARY};
                    selection-background-color: {category_subcategory_color};
                    selection-color: {selection_text_color};
                    border: 1px solid {dc.BORDER_PRIMARY};
                }}
                QTextBrowser {{
                    background-color: {dc.BG_PRIMARY};
                    color: {dc.TEXT_PRIMARY};
                    border: 1px solid {dc.BORDER_PRIMARY};
                }}
                QLineEdit {{
                    background-color: {dc.BG_SECONDARY};
                    color: {dc.TEXT_PRIMARY};
                    border: 1px solid {dc.BORDER_PRIMARY};
                    border-radius: 4px;
                    padding: 5px;
                }}
                QLineEdit:hover {{
                    border: 1px solid {dc.BORDER_HOVER};
                }}
                QLineEdit:focus {{
                    border: 1px solid {dc.ACCENT_PURPLE};
                }}
            """
        else:
            # Light theme with custom colors for checkboxes, radio buttons, and dropdown selections
            lc = ThemeManager.LightColors
            # Calculate optimal text color for custom background color
            selection_text_color = ThemeManager.get_text_color_for_background(category_subcategory_color)
            return f"""
                QCheckBox {{
                    color: {lc.TEXT_PRIMARY};
                }}
                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border: 2px solid {lc.BORDER_PRIMARY};
                    border-radius: 4px;
                    background-color: {lc.BG_PRIMARY};
                }}
                QCheckBox::indicator:checked {{
                    background-color: {category_subcategory_color};
                    border: 2px solid {category_subcategory_color};
                }}
                QCheckBox::indicator:hover {{
                    border: 2px solid {lc.BORDER_HOVER};
                    background-color: {lc.BG_SECONDARY};
                }}
                QRadioButton::indicator:checked {{
                    background-color: {category_subcategory_color};
                    border: 2px solid {category_subcategory_color};
                }}
                QComboBox QAbstractItemView {{
                    selection-background-color: {category_subcategory_color};
                    selection-color: {selection_text_color};
                }}
            """
    
    @staticmethod
    def get_settings_label_style(theme):
        """Get stylesheet for the settings dialog title label
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            str: Stylesheet string for the title label
        
        Note:
            Uses Windows 11 style with subtle background and rounded corners
        """
        colors = ThemeManager.get_colors(theme)
        return f"padding: 10px; background-color: {colors.BG_SECONDARY}; border-radius: 5px;"
    
    @staticmethod
    def get_mainwindow_stylesheet(theme, category_subcategory_color='#3699e7'):
        """Get the main stylesheet for the main window
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
            category_subcategory_color: Custom color for radio buttons and dropdown selections (default: '#3699e7')
        
        Returns:
            str: Stylesheet string for main window
        
        Note:
            Light theme uses native Windows 11 style with custom colors.
            Medium and Dark themes apply modern themed styles.
        """
        if theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM]:
            dc = ThemeManager.get_colors(theme)
            # Calculate optimal text color for custom background color
            selection_text_color = ThemeManager.get_text_color_for_background(category_subcategory_color)
            return f"""
                QMainWindow {{
                    background-color: {dc.BG_PRIMARY};
                }}
                QWidget {{
                    background-color: {dc.BG_PRIMARY};
                    color: {dc.TEXT_PRIMARY};
                }}
                QLabel {{
                    color: {dc.TEXT_PRIMARY};
                }}
                QPushButton {{
                    background-color: {dc.BG_SECONDARY};
                    color: {dc.TEXT_PRIMARY};
                    border: 1px solid {dc.BORDER_PRIMARY};
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {dc.BG_HOVER};
                    border: 1px solid {dc.BORDER_HOVER};
                }}
                QComboBox {{
                    background-color: {dc.BG_SECONDARY};
                    color: {dc.TEXT_PRIMARY};
                    border: 1px solid {dc.BORDER_PRIMARY};
                    border-radius: 4px;
                }}
                QComboBox:hover {{
                    border: 1px solid {dc.BORDER_HOVER};
                }}
                QComboBox:disabled {{
                    background-color: {dc.BG_DISABLED};
                    color: {dc.TEXT_DISABLED};
                    border: 1px solid {dc.BORDER_DISABLED};
                }}
                QComboBox QAbstractItemView {{
                    background-color: {dc.BG_SECONDARY};
                    color: {dc.TEXT_PRIMARY};
                    selection-background-color: {category_subcategory_color};
                    selection-color: {selection_text_color};
                    border: 1px solid {dc.BORDER_PRIMARY};
                }}
                QScrollArea {{
                    background-color: {dc.BG_PRIMARY};
                    border: 1px solid {dc.BORDER_SECONDARY};
                }}
                QScrollBar:vertical {{
                    background-color: transparent;
                    width: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {dc.BORDER_HOVER};
                    min-height: 20px;
                    border-radius: 6px;
                    margin: 2px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: #606060;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                    border: none;
                    background: none;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
                QRadioButton {{
                    color: {dc.TEXT_PRIMARY};
                    spacing: 3px;
                }}
                QRadioButton::indicator {{
                    width: 12px;
                    height: 12px;
                    border-radius: 7px;
                    border: 2px solid {dc.RADIO_BORDER_INACTIVE};
                    background-color: {dc.RADIO_BG_INACTIVE};
                }}
                QRadioButton::indicator:hover:!disabled {{
                    border: 2px solid {dc.TEXT_SECONDARY};
                    background-color: {dc.BG_HOVER};
                }}
                QRadioButton::indicator:checked {{
                    width: 8px;
                    height: 8px;
                    border-radius: 7px;
                    background-color: {category_subcategory_color};
                    border: 4px solid {category_subcategory_color};
                    background: radial-gradient(circle, white 0%, white 50%, {category_subcategory_color} 50%, {category_subcategory_color} 100%);
                }}
                QRadioButton::indicator:checked:hover:!disabled {{
                    border: 4px solid {dc.TEXT_SECONDARY};
                }}
                QRadioButton::indicator:disabled {{
                    width: 12px;
                    height: 12px;
                    border-radius: 7px;
                    border: 2px solid {dc.RADIO_BORDER_DISABLED};
                    background-color: {dc.RADIO_BG_INACTIVE};
                    opacity: 0.15;
                }}
            """
        else:
            # Light theme with custom color for radio buttons and dropdown selections
            lc = ThemeManager.LightColors
            # Calculate optimal text color for custom background color
            selection_text_color = ThemeManager.get_text_color_for_background(category_subcategory_color)
            return f"""
                QScrollArea {{
                    background-color: {lc.BG_PRIMARY};
                    border: 1px solid {lc.BORDER_PRIMARY};
                }}
                QScrollBar:vertical {{
                    background-color: transparent;
                    width: 12px;
                    margin: 0px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {lc.BORDER_HOVER};
                    min-height: 20px;
                    border-radius: 6px;
                    margin: 2px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: #888888;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                    border: none;
                    background: none;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
                QRadioButton {{
                    spacing: 3px;
                }}
                QRadioButton::indicator {{
                    width: 12px;
                    height: 12px;
                    border-radius: 7px;
                    border: 2px solid {lc.RADIO_BORDER_INACTIVE};
                    background-color: {lc.RADIO_BG_INACTIVE};
                }}
                QRadioButton::indicator:hover:!disabled {{
                    border: 2px solid {lc.BORDER_HOVER};
                    background-color: {lc.BG_SECONDARY};
                }}
                QRadioButton::indicator:checked {{
                    width: 8px;
                    height: 8px;
                    border-radius: 7px;
                    background-color: {category_subcategory_color};
                    border: 4px solid {category_subcategory_color};
                    background: radial-gradient(circle, white 0%, white 50%, {category_subcategory_color} 50%, {category_subcategory_color} 100%);
                }}
                QRadioButton::indicator:checked:hover:!disabled {{
                    border: 4px solid {lc.BORDER_HOVER};
                }}
                QRadioButton::indicator:disabled {{
                    width: 12px;
                    height: 12px;
                    border-radius: 7px;
                    border: 2px solid {lc.RADIO_BORDER_DISABLED};
                    background-color: {lc.RADIO_BG_INACTIVE};
                    opacity: 0.15;
                }}
                QComboBox QAbstractItemView {{
                    selection-background-color: {category_subcategory_color};
                    selection-color: {selection_text_color};
                }}
            """
    
    @staticmethod
    def get_emoji_button_stylesheet(theme, background_color='#ffffff'):
        """Get stylesheet for emoji buttons in grid
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
            background_color: Background color for emojis (hex color)
        
        Returns:
            str: Stylesheet string for emoji buttons
        
        Note:
            Uses Windows 11 style with subtle borders and hover effects
            In dark/medium themes, if background is white, use theme container color
        """
        if theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM]:
            dc = ThemeManager.get_colors(theme)
            display_bg = dc.BG_SECONDARY if background_color in ['#ffffff', '#fff', 'white'] else background_color
            return ThemeManager.create_button_style(
                display_bg, dc.TEXT_PRIMARY, dc.BORDER_SECONDARY, 
                border_radius="4px", padding="0px",
                hover_bg=dc.BG_HOVER, hover_border=dc.BORDER_LIGHT,
                pressed_bg=dc.BG_PRESSED
            )
        else:
            lc = ThemeManager.LightColors
            return ThemeManager.create_button_style(
                background_color, lc.TEXT_PRIMARY, lc.BORDER_PRIMARY, 
                border_radius="3px", padding="0px",
                hover_bg=lc.BG_HOVER, hover_border=lc.BORDER_HOVER,
                pressed_bg=lc.BG_PRESSED
            )
    
    @staticmethod
    def get_emoji_button_selected_stylesheet(theme, selection_color='#3699e7'):
        """Get stylesheet for selected emoji button
        
        Args:
            theme: Theme name (Light or Dark)
            selection_color: Selection color (hex color)
        
        Returns:
            str: Stylesheet string for selected emoji button
        """
        return ThemeManager.create_solid_button_style(selection_color, border_width="2px", padding="0px")
    
    @staticmethod
    def get_active_button_stylesheet(theme, active_color='#3699e7'):
        """Get stylesheet for active subcategory/category buttons
        
        Args:
            theme: Theme name (Light or Dark)
            active_color: Active button color (hex color)
        
        Returns:
            str: Stylesheet string for active buttons
        """
        return ThemeManager.create_solid_button_style(active_color, padding="5px")
    
    @staticmethod
    def get_inactive_button_stylesheet(theme):
        """Get stylesheet for inactive subcategory buttons
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            str: Stylesheet string for inactive buttons
        
        Note:
            Uses Windows 11 style with subtle borders and hover effects
        """
        if theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM]:
            dc = ThemeManager.get_colors(theme)
            return ThemeManager.create_button_style(
                dc.BG_SECONDARY, dc.TEXT_PRIMARY, dc.BORDER_PRIMARY,
                hover_bg=dc.BG_HOVER, hover_border=dc.BORDER_HOVER,
                pressed_bg=dc.BG_PRESSED
            )
        else:
            lc = ThemeManager.LightColors
            return ThemeManager.create_button_style(
                lc.BG_SECONDARY, lc.TEXT_PRIMARY, lc.BORDER_PRIMARY,
                border_radius="3px",
                hover_bg=lc.BG_HOVER, hover_border=lc.BORDER_HOVER,
                pressed_bg=lc.BG_PRESSED
            )
    
    @staticmethod
    def get_active_category_stylesheet(theme, active_color='#3699e7'):
        """Get stylesheet for active category buttons
        
        Args:
            theme: Theme name (Light or Dark)
            active_color: Active button color (hex color)
        
        Returns:
            str: Stylesheet string for active category buttons
        """
        return ThemeManager.create_solid_button_style(active_color, border_width="2px", border_radius="5px", padding="0px")
    
    @staticmethod
    def get_inactive_category_stylesheet(theme):
        """Get stylesheet for inactive category buttons
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            str: Stylesheet string for inactive category buttons
        
        Note:
            Uses Windows 11 style with subtle borders and hover effects
        """
        if theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM]:
            dc = ThemeManager.get_colors(theme)
            return ThemeManager.create_button_style(
                dc.BG_SECONDARY, dc.TEXT_PRIMARY, dc.BORDER_PRIMARY,
                border_width="2px", border_radius="5px", padding="0px",
                hover_bg=dc.BG_HOVER, hover_border=dc.BORDER_HOVER,
                pressed_bg=dc.BG_PRESSED
            )
        else:
            lc = ThemeManager.LightColors
            return ThemeManager.create_button_style(
                lc.BG_SECONDARY, lc.TEXT_PRIMARY, lc.BORDER_PRIMARY,
                border_width="2px", border_radius="5px", padding="0px",
                hover_bg=lc.BG_HOVER, hover_border=lc.BORDER_HOVER,
                pressed_bg=lc.BG_PRESSED
            )
    
    @staticmethod
    def get_disabled_radio_stylesheet(theme):
        """Get stylesheet for disabled radio buttons
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            str: Stylesheet string for disabled radio buttons
        
        Note:
            Uses Windows 11 Fluent Design style for disabled state
        """
        if theme in [ThemeManager.THEME_DARK, ThemeManager.THEME_MEDIUM]:
            dc = ThemeManager.get_colors(theme)
            return f"""
                QRadioButton:disabled {{
                    color: {dc.TEXT_DISABLED};
                    background-color: {dc.BG_PRIMARY};
                }}
                QRadioButton::indicator:disabled {{
                    opacity: 0.15;
                }}
            """
        else:
            lc = ThemeManager.LightColors
            return f"""
                QRadioButton:disabled {{
                    color: {lc.TEXT_DISABLED};
                    background-color: {lc.BG_SECONDARY};
                }}
                QRadioButton::indicator:disabled {{
                    opacity: 0.15;
                }}
            """
    
    @staticmethod
    def get_search_edit_stylesheet(theme):
        """Get stylesheet for search input field
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            str: Stylesheet string for QLineEdit (search field)
        
        Note:
            All themes use consistent styling with themed borders, padding, and border-radius
            Colors are theme-specific to maintain visual consistency
        """
        dc = ThemeManager.get_colors(theme)
        return f"""
            QLineEdit {{
                background-color: {dc.BG_SECONDARY};
                color: {dc.TEXT_PRIMARY};
                border: 1px solid {dc.BORDER_PRIMARY};
                border-radius: 4px;
                padding: 5px;
                min-height: 20px;
                height: 30px;
            }}
            QLineEdit:hover {{
                border: 1px solid {dc.BORDER_HOVER};
            }}
            QLineEdit:focus {{
                border: 1px solid {dc.ACCENT_PURPLE};
            }}
        """
    
    @staticmethod
    def get_size_input_stylesheet(theme):
        """Get stylesheet for size input field
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            str: Stylesheet string for QLineEdit (size input field)
        
        Note:
            Same styling as search bar but with reduced height (15px instead of 30px)
            All themes use consistent styling with themed borders, padding, and border-radius
            Colors are theme-specific to maintain visual consistency
        """
        dc = ThemeManager.get_colors(theme)
        return f"""
            QLineEdit {{
                background-color: {dc.BG_SECONDARY};
                color: {dc.TEXT_PRIMARY};
                border: 1px solid {dc.BORDER_PRIMARY};
                border-radius: 4px;
                padding: 5px;
                min-height: 5px;
                height: 15px;
            }}
            QLineEdit:hover {{
                border: 1px solid {dc.BORDER_HOVER};
            }}
            QLineEdit:focus {{
                border: 1px solid {dc.ACCENT_PURPLE};
            }}
        """
    
    @staticmethod
    def get_link_color(theme):
        """Get the optimal link and title color for a given theme
        
        Args:
            theme: Theme name (Light, Medium, or Dark)
        
        Returns:
            str: Hex color string for links and titles optimized for readability
        
        Note:
            Returns colors with high contrast ratios for accessibility:
            - Light theme (white background): dark blue #1e40af
            - Medium theme (gray background): light blue #60a5fa
            - Dark theme (dark background): very light blue #93c5fd
        """
        if theme == ThemeManager.THEME_LIGHT:
            return "#1e40af"  # Dark blue for white background
        elif theme == ThemeManager.THEME_MEDIUM:
            return "#60a5fa"  # Light blue for gray background
        else:  # Dark theme
            return "#93c5fd"  # Very light blue for dark background
    
    @staticmethod
    def get_text_color_for_background(hex_color):
        """Calculate the best text color (white or black) for a given background color
        
        Args:
            hex_color: Hex color string (e.g., "#3699e7" or "#fff")
        
        Returns:
            str: Either "#ffffff" (white) or "#000000" (black) for optimal contrast
        
        Note:
            Uses relative luminance calculation following WCAG guidelines.
            Colors with luminance > 0.5 get black text, others get white text.
        """
        # Remove # if present and handle short format
        hex_color = hex_color.lstrip('#')
        
        # Convert 3-digit hex to 6-digit
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        # Convert hex to RGB
        try:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
        except (ValueError, IndexError):
            # If conversion fails, default to white text
            return "#ffffff"
        
        # Calculate relative luminance using WCAG formula
        # https://www.w3.org/TR/WCAG20/#relativeluminancedef
        def adjust_channel(channel):
            if channel <= 0.03928:
                return channel / 12.92
            return ((channel + 0.055) / 1.055) ** 2.4
        
        r_adjusted = adjust_channel(r)
        g_adjusted = adjust_channel(g)
        b_adjusted = adjust_channel(b)
        
        luminance = 0.2126 * r_adjusted + 0.7152 * g_adjusted + 0.0722 * b_adjusted
        
        # Return black text for light backgrounds, white text for dark backgrounds
        return "#000000" if luminance > 0.5 else "#ffffff"