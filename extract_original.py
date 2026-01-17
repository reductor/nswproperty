#!/usr/bin/env python3
"""
Extract all archive files from 'original' folder to 'extracted' folder
with progress tracking and clean start.
"""

import os
import shutil
import zipfile
import tarfile
import gzip
import rarfile
from pathlib import Path
from tqdm import tqdm
import py7zr
import tempfile


def clear_extracted_folder(extracted_path):
    """Clear the extracted folder completely"""
    if extracted_path.exists():
        print(f"Clearing existing content from {extracted_path}...")
        shutil.rmtree(extracted_path)
    extracted_path.mkdir(exist_ok=True)
    print(f"Prepared clean extraction directory: {extracted_path}")


def get_all_archive_files(original_path):
    """Get all archive files recursively from original folder"""
    archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.tbz2', '.txz'}
    archive_files = []
    
    for root, dirs, files in os.walk(original_path):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in archive_extensions:
                archive_files.append(file_path)
            # Handle .tar.gz, .tar.bz2, etc.
            elif len(file_path.suffixes) > 1:
                combined_suffix = ''.join(file_path.suffixes[-2:])
                if combined_suffix.lower() in {'.tar.gz', '.tar.bz2', '.tar.xz'}:
                    archive_files.append(file_path)
    
    return sorted(archive_files)


def extract_zip_file(zip_path, extract_to):
    """Extract a ZIP file"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


def extract_7z_file(archive_path, extract_to):
    """Extract a 7z file"""
    with py7zr.SevenZipFile(archive_path, mode='r') as archive:
        archive.extractall(path=extract_to)


def extract_rar_file(rar_path, extract_to):
    """Extract a RAR file"""
    with rarfile.RarFile(rar_path) as rar_ref:
        rar_ref.extractall(extract_to)


def extract_tar_file(tar_path, extract_to):
    """Extract various tar formats"""
    with tarfile.open(tar_path, 'r:*') as tar_ref:
        tar_ref.extractall(extract_to)


def extract_gz_file(gz_path, extract_to):
    """Extract a single .gz file (not tar.gz)"""
    output_file = extract_to / gz_path.stem
    with gzip.open(gz_path, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)


def find_nested_archives(directory):
    """Find all archive files in a directory recursively"""
    archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.tbz2', '.txz'}
    archive_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in archive_extensions:
                archive_files.append(file_path)
            # Handle .tar.gz, .tar.bz2, etc.
            elif len(file_path.suffixes) > 1:
                combined_suffix = ''.join(file_path.suffixes[-2:])
                if combined_suffix.lower() in {'.tar.gz', '.tar.bz2', '.tar.xz'}:
                    archive_files.append(file_path)
    
    return archive_files


def extract_single_archive(archive_path, extracted_path, max_depth=3, current_depth=0):
    """Extract a single archive file to the extracted folder with recursive nested archive support"""
    if current_depth >= max_depth:
        print(f"  Warning: Maximum extraction depth ({max_depth}) reached for {archive_path.name}")
        return False
    
    # Create subfolder based on archive name (without extension)
    archive_name = archive_path.stem
    if archive_path.suffix.lower() == '.gz' and archive_path.stem.endswith('.tar'):
        archive_name = archive_path.name.replace('.tar.gz', '')
    
    extract_to = extracted_path / archive_name
    extract_to.mkdir(parents=True, exist_ok=True)
    
    try:
        suffix = archive_path.suffix.lower()
        suffixes = ''.join(archive_path.suffixes[-2:]).lower()
        
        # Extract the archive
        if suffix == '.zip':
            extract_zip_file(archive_path, extract_to)
        elif suffix == '.rar':
            extract_rar_file(archive_path, extract_to)
        elif suffix == '.7z':
            extract_7z_file(archive_path, extract_to)
        elif suffixes in ['.tar.gz', '.tar.bz2', '.tar.xz'] or suffix in ['.tar', '.tgz', '.tbz2', '.txz']:
            extract_tar_file(archive_path, extract_to)
        elif suffix == '.gz' and not archive_path.name.endswith('.tar.gz'):
            extract_gz_file(archive_path, extract_to)
        else:
            print(f"Unsupported archive format: {archive_path}")
            return False
        
        # Look for nested archives and extract them recursively
        nested_archives = find_nested_archives(extract_to)
        if nested_archives:
            indent = "  " * (current_depth + 1)
            print(f"{indent}Found {len(nested_archives)} nested archive(s) in {archive_name}")
            
            for nested_archive in nested_archives:
                rel_path = nested_archive.relative_to(extract_to)
                print(f"{indent}Extracting nested: {rel_path}")
                
                # Extract nested archive in the same parent directory
                nested_success = extract_single_archive(
                    nested_archive, 
                    nested_archive.parent,
                    max_depth=max_depth,
                    current_depth=current_depth + 1
                )
                
                if nested_success:
                    # Remove the nested archive file after successful extraction
                    try:
                        nested_archive.unlink()
                    except:
                        pass  # Don't fail if we can't delete the nested archive
        
        return True
        
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
    
    print("Note: Will recursively extract any archives found within archives (max depth: 3)")
    print()
    
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
