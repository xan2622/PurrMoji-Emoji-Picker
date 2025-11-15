#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
ZipExtractor - Manages extraction of emoji packages from ZIP archives
"""

import os
import sys
import zipfile
import platform


class ZipExtractor:
    """Manages extraction of emoji package ZIP archives to user directory"""
    
    # Allowed file extensions for extraction (only emoji files)
    ALLOWED_EXTENSIONS = {'.png', '.svg', '.ttf', '.otf', '.woff', '.woff2'}
    
    # Configuration for each package: (zip_filename, extracted_folder_name)
    PACKAGE_CONFIG = {
        "Emojitwo": {
            "zip_name": "emojitwo-master.zip",
            "extracted_folder": "emojitwo-master",
            "required_subfolders": ["png", "svg", "png_bw", "svg_bw"]
        },
        "OpenMoji": {
            "zip_name": "openmoji-master.zip",
            "extracted_folder": "openmoji-master",
            "required_subfolders": ["color", "black"]
        },
        "Twemoji": {
            "zip_name": "twemoji-14.0.2.zip",
            "extracted_folder": "twemoji-14.0.2",
            "required_subfolders": ["assets"]
        },
        "Noto": {
            "type": "multi_zip",
            "zip_files": [
                {
                    "zip_name": "Noto_Color_Emoji.zip",
                    "required_files": ["NotoColorEmoji-Regular.ttf"]
                },
                {
                    "zip_name": "Noto_Emoji.zip",
                    "required_files": ["NotoEmoji-VariableFont_wght.ttf"]
                }
            ]
        }
    }
    
    def __init__(self):
        """Initialize ZipExtractor with source and target directories"""
        self.source_packages_dir = self.get_source_packages_dir()
        self.user_packages_dir = self.calculate_user_packages_dir()
    
    def should_extract_file(self, file_path):
        """Check if a file should be extracted based on its extension
        
        Args:
            file_path: Path of the file in the ZIP archive
        
        Returns:
            bool: True if file should be extracted, False otherwise
        """
        # Skip directories
        if file_path.endswith('/'):
            return False
        
        # Get file name and extension
        file_name = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Always extract license files (important for legal compliance)
        license_keywords = ['license', 'licence', 'copyright', 'copying', 'ofl', 'notice', 'authors']
        if any(keyword in file_name for keyword in license_keywords):
            # Only extract text-based license files
            if file_ext in {'.txt', '.md', ''}:
                return True
        
        # Check if extension is allowed for emoji files
        return file_ext in self.ALLOWED_EXTENSIONS
    
    def get_source_packages_dir(self):
        """Get the source emoji_packages directory (where ZIP files are stored)"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            exe_dir = os.path.dirname(sys.executable)
            data_dir = os.path.join(exe_dir, "data")
            if os.path.exists(data_dir):
                return os.path.join(data_dir, "emoji_packages")
            else:
                base_dir = getattr(sys, '_MEIPASS', exe_dir)
                return os.path.join(base_dir, "emoji_packages")
        else:
            # Running as script
            current_file = os.path.abspath(__file__)
            data_dir = os.path.dirname(os.path.dirname(current_file))
            return os.path.join(data_dir, "emoji_packages")
    
    def calculate_user_packages_dir(self):
        """Calculate and create the user directory where packages will be extracted"""
        system = platform.system()
        
        if system == "Windows":
            # %APPDATA%/PurrMoji/emoji_packages/
            base_dir = os.environ.get('APPDATA')
            if not base_dir:
                base_dir = os.path.expanduser('~\\AppData\\Roaming')
        elif system == "Darwin":  # macOS
            # ~/Library/Application Support/PurrMoji/emoji_packages/
            base_dir = os.path.expanduser('~/Library/Application Support')
        else:  # Linux and others
            # ~/.local/share/PurrMoji/emoji_packages/
            base_dir = os.environ.get('XDG_DATA_HOME')
            if not base_dir:
                base_dir = os.path.expanduser('~/.local/share')
        
        packages_dir = os.path.join(base_dir, 'PurrMoji', 'emoji_packages')
        os.makedirs(packages_dir, exist_ok=True)
        return packages_dir
    
    def is_package_extracted(self, package_name):
        """Check if a package is already extracted in user directory
        
        Args:
            package_name: Name of the package (e.g., "Emojitwo", "OpenMoji", "Twemoji", "Noto")
        
        Returns:
            bool: True if package is extracted and valid, False otherwise
        """
        if package_name not in self.PACKAGE_CONFIG:
            return False
        
        config = self.PACKAGE_CONFIG[package_name]
        
        # Handle multi_zip type (multiple ZIP archives to extract)
        if config.get("type") == "multi_zip":
            package_dir = os.path.join(self.user_packages_dir, package_name)
            if not os.path.exists(package_dir):
                return False
            # Check if all required files from all ZIP archives exist
            for zip_config in config["zip_files"]:
                for file_name in zip_config["required_files"]:
                    # Search for the file recursively in the package directory
                    file_found = False
                    for root, dirs, files in os.walk(package_dir):
                        if file_name in files:
                            file_found = True
                            break
                    if not file_found:
                        return False
            return True
        
        # Handle ZIP extraction type
        package_dir = os.path.join(
            self.user_packages_dir,
            package_name,
            config["extracted_folder"]
        )
        
        # Check if extracted folder exists
        if not os.path.exists(package_dir):
            return False
        
        # Verify required subfolders exist
        for subfolder in config["required_subfolders"]:
            subfolder_path = os.path.join(package_dir, subfolder)
            if not os.path.exists(subfolder_path):
                return False
        
        return True
    
    def extract_package(self, package_name, progress_callback=None):
        """Extract a package from ZIP to user directory or copy files
        
        Args:
            package_name: Name of the package to extract
            progress_callback: Optional callback function(current, total, message)
        
        Returns:
            bool: True if extraction/copy succeeded, False otherwise
        """
        if package_name not in self.PACKAGE_CONFIG:
            return False
        
        config = self.PACKAGE_CONFIG[package_name]
        
        # Handle multi_zip type (multiple ZIP archives to extract)
        if config.get("type") == "multi_zip":
            return self.extract_multi_zip(package_name, config, progress_callback)
        
        # Handle ZIP extraction type
        return self.extract_zip(package_name, config, progress_callback)
    
    def extract_multi_zip(self, package_name, config, progress_callback=None):
        """Extract multiple ZIP archives for a package to user directory
        
        Args:
            package_name: Name of the package
            config: Package configuration
            progress_callback: Optional callback function
        
        Returns:
            bool: True if all extractions succeeded, False otherwise
        """
        target_dir = os.path.join(self.user_packages_dir, package_name)
        os.makedirs(target_dir, exist_ok=True)
        
        total_zips = len(config["zip_files"])
        
        try:
            for zip_index, zip_config in enumerate(config["zip_files"]):
                zip_path = os.path.join(
                    self.source_packages_dir,
                    package_name,
                    zip_config["zip_name"]
                )
                
                # Check if ZIP file exists
                if not os.path.exists(zip_path):
                    if progress_callback:
                        progress_callback(0, 100, f"ERROR: {zip_config['zip_name']} not found")
                    return False
                
                if progress_callback:
                    result = progress_callback(
                        zip_index,
                        total_zips,
                        f"Extracting {package_name} ({zip_index + 1}/{total_zips}): {zip_config['zip_name']}..."
                    )
                    if result is False:
                        return False
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # Get list of files to extract
                    all_files = zip_ref.namelist()
                    
                    # Filter files to extract only emoji files
                    files_to_extract = [f for f in all_files if self.should_extract_file(f)]
                    
                    # Extract only filtered files
                    for file_index, file in enumerate(files_to_extract):
                        zip_ref.extract(file, target_dir)
                        
                        # Check for cancellation periodically (every 50 files)
                        if progress_callback and file_index % 50 == 0:
                            result = progress_callback(zip_index, total_zips, f"Extracting {len(files_to_extract)} emoji files...")
                            if result is False:
                                return False
            
            if progress_callback:
                progress_callback(
                    total_zips,
                    total_zips,
                    f"{package_name} extracted successfully"
                )
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, 100, f"ERROR extracting {package_name}: {e}")
            return False
    
    def extract_zip(self, package_name, config, progress_callback=None):
        """Extract ZIP package to user directory
        
        Args:
            package_name: Name of the package
            config: Package configuration
            progress_callback: Optional callback function
        
        Returns:
            bool: True if extraction succeeded, False otherwise
        """
        zip_path = os.path.join(
            self.source_packages_dir,
            package_name,
            config["zip_name"]
        )
        
        # Check if ZIP file exists
        if not os.path.exists(zip_path):
            if progress_callback:
                progress_callback(0, 100, f"ERROR: {config['zip_name']} not found")
            return False
        
        # Target directory for this package
        target_dir = os.path.join(self.user_packages_dir, package_name)
        os.makedirs(target_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get list of all files in archive
                all_files = zip_ref.namelist()
                
                # Filter files to extract only emoji files
                files_to_extract = [f for f in all_files if self.should_extract_file(f)]
                total_files = len(files_to_extract)
                
                if progress_callback:
                    result = progress_callback(0, total_files, f"Extracting {package_name} ({total_files} emoji files)...")
                    if result is False:
                        return False
                
                # Extract only filtered files
                for index, file in enumerate(files_to_extract):
                    zip_ref.extract(file, target_dir)
                    
                    if progress_callback and index % 100 == 0:
                        result = progress_callback(
                            index + 1,
                            total_files,
                            f"Extracting {package_name}... ({index + 1}/{total_files})"
                        )
                        if result is False:
                            return False
                
                if progress_callback:
                    progress_callback(
                        total_files,
                        total_files,
                        f"{package_name} extracted successfully"
                    )
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(0, 100, f"ERROR extracting {package_name}: {e}")
            return False
    
    def extract_all_packages(self, progress_callback=None):
        """Extract all packages that are not yet extracted
        
        Args:
            progress_callback: Optional callback function(current, total, message)
        
        Returns:
            dict: {package_name: success_bool}
        """
        results = {}
        packages_to_extract = []
        
        # Check which packages need extraction
        for package_name in self.PACKAGE_CONFIG.keys():
            if not self.is_package_extracted(package_name):
                packages_to_extract.append(package_name)
        
        if not packages_to_extract:
            if progress_callback:
                progress_callback(100, 100, "All packages already extracted")
            return {pkg: True for pkg in self.PACKAGE_CONFIG.keys()}
        
        # Extract each package
        total_packages = len(packages_to_extract)
        for index, package_name in enumerate(packages_to_extract):
            if progress_callback:
                result = progress_callback(
                    index,
                    total_packages,
                    f"Extracting package {index + 1}/{total_packages}: {package_name}"
                )
                if result is False:
                    # Cancellation requested, mark remaining packages as failed
                    for remaining_pkg in packages_to_extract[index:]:
                        results[remaining_pkg] = False
                    return results
            
            success = self.extract_package(package_name, progress_callback)
            results[package_name] = success
            
            # If extraction failed and it might be due to cancellation, stop
            if not success:
                # Mark remaining packages as not attempted
                for remaining_pkg in packages_to_extract[index + 1:]:
                    results[remaining_pkg] = False
                break
        
        return results
    
    def get_user_packages_dir(self):
        """Get the user packages directory path
        
        Returns:
            str: Path to user packages directory
        """
        return self.user_packages_dir
    
    def clear_package(self, package_name):
        """Remove an extracted package from user directory
        
        Args:
            package_name: Name of the package to remove
        
        Returns:
            bool: True if removal succeeded, False otherwise
        """
        if package_name not in self.PACKAGE_CONFIG:
            return False
        
        import shutil
        package_dir = os.path.join(self.user_packages_dir, package_name)
        
        try:
            if os.path.exists(package_dir):
                shutil.rmtree(package_dir)
            return True
        except Exception:
            return False
    
    def clear_all_packages(self):
        """Remove all extracted packages from user directory
        
        Returns:
            bool: True if all removals succeeded, False otherwise
        """
        import shutil
        try:
            if os.path.exists(self.user_packages_dir):
                shutil.rmtree(self.user_packages_dir)
                os.makedirs(self.user_packages_dir, exist_ok=True)
            return True
        except Exception:
            return False

