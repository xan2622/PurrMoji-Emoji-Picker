#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
About Dialog for PurrMoji Emoji Picker
Displays information about the application, emoji packages, credits, and licenses.
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, 
                             QWidget, QLabel, QApplication)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QFont, QPixmap, QDesktopServices
from managers import ThemeManager, PathManager
from ui.base_dialog import ThemedDialogMixin


class AboutDialog(ThemedDialogMixin, QDialog):
    """Custom About dialog with native Qt widgets"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(860, 700)
        
        # Get PathManager from parent or create new instance
        if parent and hasattr(parent, 'path_manager'):
            self.path_manager = parent.path_manager
        else:
            self.path_manager = PathManager()
        
        # Set window icon
        icon_path = self.path_manager.get_misc_file("Kitty-Head.svg")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Remove question mark button from title bar
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
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)
        
        # Title row with icon positioned at top right
        title_row_layout = QHBoxLayout()
        title_row_layout.setContentsMargins(0, 0, 0, 0)
        title_row_layout.setSpacing(10)  # 10px spacing between title and icon
        
        # Title
        title_label = QLabel("About PurrMoji Emoji Picker")
        title_font = QFont("Segoe UI", 12, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {link_color}; margin-bottom: 10px;")
        title_row_layout.addWidget(title_label)
        
        # Load and display icon positioned at top right of title
        icon_path = self.path_manager.get_misc_file("Sleeping-Kitty.svg")
        if os.path.exists(icon_path):
            icon_label = QLabel()
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                icon_pixmap = icon_pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(icon_pixmap)
                icon_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            title_row_layout.addWidget(icon_label, 0, Qt.AlignLeft | Qt.AlignTop)
        
        title_row_layout.addStretch()
        content_layout.addLayout(title_row_layout)
        
        # Main description with rich text for links
        desc_text = ("PurrMoji Emoji Picker is an open-source emoji picker developed in Python and released "
                    "under the GPL 3.0 license. This license only covers the source code of PurrMoji.<br><br>"
                    "All emojis are made by their respective authors and are released under their respective "
                    "licenses, see links below.<br><br>"
                    "<b>Rendering Engine:</b><br>"
                    "All emoji formats (PNG, SVG, TTF) are rendered using "
                    f'<a href="https://github.com/kyamagu/skia-python/" style="color: {link_color}; text-decoration: none;">Skia-Python</a> '
                    "for optimal performance and quality. "
                    f'<a href="https://skia.org/" style="color: {link_color}; text-decoration: none;">Skia</a> '
                    "provides hardware-accelerated rendering with direct memory processing, "
                    "ensuring fast loading and beautiful emoji display across all formats. "
                    "When Skia is not available or fails to render an emoji, "
                    f'<a href="https://www.riverbankcomputing.com/software/pyqt/download" style="color: {link_color}; text-decoration: none;">PyQt5</a>\'s '
                    "native renderer (QSvgRenderer for SVG, QPixmap for PNG) is used as a fallback system.<br><br>"
                    "If you have suggestions or want to report bugs about PurrMoji, please post them on the "
                    f'following Github repository: <a href="https://github.com/xan2622/PurrMoji-Emoji-Picker" style="color: {link_color}; text-decoration: none;">https://github.com/xan2622/PurrMoji-Emoji-Picker</a>')
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", 10))
        desc_label.setOpenExternalLinks(True)
        desc_label.setTextFormat(Qt.RichText)
        desc_label.setStyleSheet("QLabel { background-color: transparent; } QLabel a:hover { text-decoration: underline; }")
        content_layout.addWidget(desc_label)
        
        # Discord link
        discord_url = "https://discord.gg/DSVQthQKsf"
        discord_link = QLabel(f'If you want to chat about PurrMoji, you can join my Discord server: <a href="{discord_url}" style="color: {link_color}; text-decoration: none;">{discord_url}</a>')
        discord_link.setOpenExternalLinks(True)
        discord_link.setTextFormat(Qt.RichText)
        discord_link.setFont(QFont("Segoe UI", 10))
        discord_link.setStyleSheet("QLabel { background-color: transparent; } QLabel a:hover { text-decoration: underline; }")
        content_layout.addWidget(discord_link)
        
        # Empty line after GitHub link
        content_layout.addSpacing(10)
        
        # Separator
        separator = QLabel()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #ccc; margin: 10px 0;")
        content_layout.addWidget(separator)
        
        # Packages section title
        packages_title = QLabel("Emoji Packages & Credits")
        packages_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        packages_title.setStyleSheet(f"color: {link_color}; margin-top: 10px; margin-bottom: 10px;")
        content_layout.addWidget(packages_title)
        
        # Package entries
        packages = [
            ("Emojitwo (2.2.5)", [
                ("Preview", "https://emojipedia.org/joypixels/2.2.5"),
                ("Official page", "https://emojitwo.github.io/"),
                ("License", "https://emojitwo.github.io/#emojione-2x-artwork-license")
            ]),
            ("Google Noto Color Emoji (17.0)", [
                ("Preview", "https://emojipedia.org/google/17.0"),
                ("Colored emojis", "https://fonts.google.com/noto/specimen/Noto+Color+Emoji"),
                ("Monochrome emojis", "https://fonts.google.com/noto/specimen/Noto+Emoji"),
                ("Github page", "https://github.com/googlefonts/noto-emoji"),
                ("License", "https://github.com/googlefonts/noto-emoji?tab=OFL-1.1-1-ov-file")
            ]),
            ("Microsoft Segoe UI Emoji (1.33)", [
                ("Preview", "https://emojipedia.org/microsoft"),
                ("Official page", "https://learn.microsoft.com/en-us//typography/font-list/segoe-ui-emoji"),
                ("Font redistribution FAQ", "https://learn.microsoft.com/en-us/typography/fonts/font-faq"),
                ("Note", "Segoe UI Emoji is not bundled with this software.")
            ]),
            ("OpenMoji (16.0)", [
                ("Preview", "https://emojipedia.org/openmoji"),
                ("Official page", "https://openmoji.org/"),
                ("Github page", "https://github.com/hfg-gmuend/openmoji"),
                ("License", "https://github.com/hfg-gmuend/openmoji?tab=CC-BY-SA-4.0-1-ov-file#readme")
            ]),
            ("Twemoji (14.0)", [
                ("Preview", "https://emojipedia.org/twitter/twemoji-14.0"),
                ("Github page", "https://github.com/twitter/twemoji"),
                ("License", "https://github.com/twitter/twemoji/blob/master/LICENSE-GRAPHICS")
            ]),
            ("Custom", [
                ("Description", "The \"Custom\" folder allows you to add your own PNG/SVG/TTF icons or emojis. "
                              "The test icons provided in \"Custom\" are from the following websites. "
                              "You can remove them from the \"Custom\" folder and add your own ones."),
                ("SVG Icons", "https://www.svgrepo.com/"),
                ("SVGrepo License", "https://www.svgrepo.com/page/licensing/"),
                ("PNG Icons", "https://3dicons.co/"),
                ("3dicons License", "https://3dicons.co/about")
            ]),
            ("Sleeping Kitty SVG Icon", [
                ("Source page", "https://freesvg.org/sleeping-kitty"),
                ("License", "Public Domain")
            ]),
            ("Mono Contrast SVG Icon", [
                ("Source page", "https://freesvg.org/mono-contrast"),
                ("License", "Public Domain")
            ])
        ]
        
        for package_name, links in packages:
            package_label = QLabel(package_name)
            package_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            content_layout.addWidget(package_label)
            
            for link_text, link_url in links:
                if link_url.startswith("http"):
                    # Create layout for link text and URL link
                    link_layout = QHBoxLayout()
                    link_layout.setContentsMargins(20, 0, 0, 0)
                    link_layout.setSpacing(5)
                    
                    # Text label
                    text_label = QLabel(f"{link_text}:")
                    text_label.setFont(QFont("Segoe UI", 10))
                    link_layout.addWidget(text_label)
                    
                    # URL link
                    url_link = QLabel(f'<a href="{link_url}" style="color: {link_color}; text-decoration: none;">{link_url}</a>')
                    url_link.setOpenExternalLinks(True)
                    url_link.setTextFormat(Qt.RichText)
                    url_link.setFont(QFont("Segoe UI", 10))
                    url_link.setStyleSheet("QLabel { background-color: transparent; } QLabel a:hover { text-decoration: underline; }")
                    link_layout.addWidget(url_link)
                    link_layout.addStretch()
                    
                    link_widget = QWidget()
                    link_widget.setLayout(link_layout)
                    content_layout.addWidget(link_widget)
                else:
                    link_label = QLabel(f"{link_text}: {link_url}")
                    link_label.setFont(QFont("Segoe UI", 10))
                    link_label.setWordWrap(True)
                    link_label.setIndent(20)
                    content_layout.addWidget(link_label)
            
            content_layout.addSpacing(5)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Add buttons layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        
        button_layout.addSpacing(20)  # Add some spacing between buttons
        
        # Add OK button
        ok_button = QPushButton("OK")
        ok_button.setFixedSize(100, 30)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    

