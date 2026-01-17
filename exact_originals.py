#!/usr/bin/env python3
"""
Extract all archive files from 'original' folder to 'extracted' folder
with progress tracking and clean start.
"""

import os
import shutil
import zipfile
from pathlib import Path

# Try to import tqdm, fallback to basic progress if not available
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    class tqdm:
        def __init__(self, total=None, desc="", unit=""):
            self.total = total
            self.current = 0
            self.desc = desc
            print(f"{desc}: 0/{total} {unit}")
        
        def update(self, n=1):
            self.current += n
            print(f"\r{self.desc}: {self.current}/{self.total}", end="", flush=True)
        
        def set_description(self, desc):
            self.desc = desc
        
        def __enter__(self):
            return self
        
        def __exit__(self, *args):
            print()  # New line when done


def clear_extracted_folder(extracted_path):
    """Clear the extracted folder completely"""
    if extracted_path.exists():
        print(f"Clearing existing content from {extracted_path}...")
        shutil.rmtree(extracted_path)
    extracted_path.mkdir(exist_ok=True)
    print(f"Prepared clean extraction directory: {extracted_path}")


def get_all_archive_files(original_path):
    """Get all ZIP files recursively from original folder"""
    archive_files = []
    
    for root, dirs, files in os.walk(original_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() == '.zip':
                archive_files.append(file_path)
    
    return sorted(archive_files)


def extract_zip_file(zip_path, extract_to):
    """Extract a ZIP file"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def extract_single_archive(archive_path, extracted_path):
    """Extract a single ZIP archive file to the extracted folder"""
    # Create subfolder based on archive name (without extension)
    archive_name = archive_path.stem
    extract_to = extracted_path / archive_name
    extract_to.mkdir(parents=True, exist_ok=True)
    
    try:
        if archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            return True
        else:
            print(f"Unsupported archive format: {archive_path}")
            return False
        
    except Exception as e:
        print(f"Error extracting {archive_path}: {e}")
        return False


def main():
    # Define paths
    script_dir = Path(__file__).parent
    original_path = script_dir / 'original'
    extracted_path = script_dir / 'extracted'
    
    print("NSW Property Sales Archive Extractor")
    print("=" * 40)
    
    # Check if original folder exists
    if not original_path.exists():
        print(f"Error: Original folder not found at {original_path}")
        return
    
    # Clear extracted folder
    clear_extracted_folder(extracted_path)
    
    # Find all archive files
    print("Scanning for archive files...")
    archive_files = get_all_archive_files(original_path)
    
    if not archive_files:
        print("No archive files found in original folder.")
        return
    
    print(f"Found {len(archive_files)} archive files to extract:")
    for archive_file in archive_files:
        rel_path = archive_file.relative_to(original_path)
        print(f"  - {rel_path}")
    
    print("\nStarting extraction...")
    
    # Extract all files with progress bar
    successful_extractions = 0
    failed_extractions = 0
    
    with tqdm(total=len(archive_files), desc="Extracting archives", unit="file") as pbar:
        for archive_file in archive_files:
            pbar.set_description(f"Extracting {archive_file.name}")
            
            if extract_single_archive(archive_file, extracted_path):
                successful_extractions += 1
            else:
                failed_extractions += 1
            
            pbar.update(1)
    
    # Summary
    print("\nExtraction Summary:")
    print(f"✓ Successful: {successful_extractions}")
    if failed_extractions > 0:
        print(f"✗ Failed: {failed_extractions}")
    
    print(f"\nAll archives extracted to: {extracted_path}")
    
    # Show extracted folder structure
    print("\nExtracted folder structure:")
    for item in sorted(extracted_path.iterdir()):
        if item.is_dir():
            file_count = len(list(item.rglob('*'))) if item.exists() else 0
            print(f"  📁 {item.name}/ ({file_count} files)")
        else:
            print(f"  📄 {item.name}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExtraction cancelled by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
