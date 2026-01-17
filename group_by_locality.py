import os
import glob
from collections import defaultdict
from tqdm import tqdm
from datetime import datetime

def convert_archive_date(archive_date):
    """
    Convert archive date format (DD/MM/YYYY) to current format (CCYYMMDD).
    """
    if not archive_date or archive_date.strip() == '':
        return ''
    
    try:
        # Parse DD/MM/YYYY format
        date_obj = datetime.strptime(archive_date.strip(), '%d/%m/%Y')
        # Convert to CCYYMMDD format
        return date_obj.strftime('%Y%m%d')
    except ValueError:
        # If parsing fails, return empty string
        return ''

def detect_archive_field_structure(file_path, sample_size=10):
    """
    Analyze archive file structure to determine field mapping.
    Returns information about field positions.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            b_records = []
            for i, line in enumerate(file):
                line = line.strip()
                if line.startswith('B;') and len(b_records) < sample_size:
                    b_records.append(line.split(';'))
                if i > 100 or len(b_records) >= sample_size:  # Don't read too many lines
                    break
            
            if b_records:
                # Analyze field structure
                avg_fields = sum(len(record) for record in b_records) / len(b_records)
                print(f"Archive file {file_path}: avg {avg_fields:.1f} fields per B record")
                return True
            else:
                print(f"Archive file {file_path}: no B records found")
                return False
                
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return False

def convert_archive_to_standard_format(line):
    """
    Convert archive format record to standard B; format.
    Maps archive fields to current format field positions.
    
    Archive format key fields:
    - Field 9 (index 8): Suburb_name → Current field 10 (index 9): Property Locality  
    - Field 11 (index 10): Contract_date → Current field 15 (index 14): Settlement Date
    - Field 12 (index 11): Purchase_Price → Current field 16 (index 15): Purchase Price
    - Field 18 (index 17): Zone_code → Current field 19 (index 18): Primary Purpose
    """
    # Only process if it's a B record
    if not line.startswith('B;'):
        return None  # Skip non-B records
    
    # Split archive fields
    archive_fields = line.split(';')
    
    # Archive should have at least 18 fields for basic mapping
    if len(archive_fields) < 18:
        return None
    
    # Create new field array with 24 fields to match current format
    current_fields = [''] * 24
    
    # Map the fields we can directly convert:
    current_fields[0] = 'B'  # Record Type
    current_fields[1] = archive_fields[1] if len(archive_fields) > 1 else ''  # District Code
    current_fields[2] = archive_fields[4] if len(archive_fields) > 4 else ''  # Property ID
    current_fields[3] = ''  # Sale Counter (not in archive)
    current_fields[4] = ''  # Download Date/Time (not in archive)
    current_fields[5] = ''  # Property Name (not in archive)
    current_fields[6] = archive_fields[5] if len(archive_fields) > 5 else ''  # Unit Number
    current_fields[7] = archive_fields[6] if len(archive_fields) > 6 else ''  # House Number  
    current_fields[8] = archive_fields[7] if len(archive_fields) > 7 else ''  # Street Name
    current_fields[9] = archive_fields[8] if len(archive_fields) > 8 else ''  # Property Locality (Suburb_name)
    current_fields[10] = archive_fields[9] if len(archive_fields) > 9 else ''  # Post Code
    current_fields[11] = archive_fields[13] if len(archive_fields) > 13 else ''  # Area
    current_fields[12] = archive_fields[14] if len(archive_fields) > 14 else ''  # Area Type
    current_fields[13] = convert_archive_date(archive_fields[10]) if len(archive_fields) > 10 else ''  # Contract Date
    current_fields[14] = convert_archive_date(archive_fields[10]) if len(archive_fields) > 10 else ''  # Settlement Date (same as contract)
    current_fields[15] = archive_fields[11] if len(archive_fields) > 11 else ''  # Purchase Price
    current_fields[16] = archive_fields[17] if len(archive_fields) > 17 else ''  # Zoning (Zone_code)
    current_fields[17] = 'R'  # Nature of Property (assume Residence)
    current_fields[18] = 'RESIDENCE'  # Primary Purpose (default)
    current_fields[19] = ''  # Strata Lot Number (not in archive)
    current_fields[20] = ''  # Component code
    current_fields[21] = ''  # Sale Code
    current_fields[22] = ''  # % Interest of Sale
    current_fields[23] = ''  # Dealing Number
    
    # Validate that we have required fields (locality and price)
    if not current_fields[9].strip() or not current_fields[15].strip():
        return None
        
    # Return the reconstructed line
    return ';'.join(current_fields)

def process_dat_files():
    """
    Process all .DAT files in the extracted folder and group records by locality.
    """
    # Define paths
    extracted_folder = "extracted"
    localities_folder = "localities"
    
    # Create localities folder if it doesn't exist
    if not os.path.exists(localities_folder):
        os.makedirs(localities_folder)
    
    # Dictionary to store records grouped by locality
    locality_records = defaultdict(list)
    
    # Find all .DAT files in the extracted folder
    all_dat_files = glob.glob(os.path.join(extracted_folder, "**", "*.DAT"), recursive=True)
    
    # Separate archive and regular files
    regular_files = []
    archive_files = []
    for file_path in all_dat_files:
        filename = os.path.basename(file_path)
        if filename.startswith('ARCHIVE_SALES_'):
            archive_files.append(file_path)
        else:
            regular_files.append(file_path)
    
    print(f"Found {len(all_dat_files)} total .DAT files:")
    print(f"  - {len(regular_files)} regular files")
    print(f"  - {len(archive_files)} archive files")
    
    # Analyze archive files if they exist
    if archive_files:
        print(f"\nAnalyzing archive file structure...")
        for archive_file in archive_files[:3]:  # Just analyze first few
            detect_archive_field_structure(archive_file)
    
    print(f"Processing all files...")
    
    processed_files = 0
    total_records = 0
    error_files = 0
    
    # Combine both file lists for processing
    all_files_to_process = regular_files + archive_files
    
    # Process each .DAT file with progress bar
    for dat_file in tqdm(all_files_to_process, desc="Processing .DAT files", unit="file"):
        try:
            file_records = 0
            filename = os.path.basename(dat_file)
            is_archive = filename.startswith('ARCHIVE_SALES_')
            
            with open(dat_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Convert archive format if needed
                    if is_archive:
                        converted_line = convert_archive_to_standard_format(line)
                        if converted_line is None:
                            continue  # Skip this line if conversion failed or not a B record
                        line = converted_line
                    
                    # Check if line starts with 'B;' (after potential conversion)
                    if line.startswith('B;'):
                        # Split by semicolon
                        fields = line.split(';')
                        
                        # Check if we have at least 10 fields (locality is 10th field, index 9)
                        if len(fields) >= 10:
                            locality = fields[9].strip()
                            
                            # Only process if locality is not empty
                            if locality:
                                locality_records[locality].append(line)
                                total_records += 1
                                file_records += 1
            
            if is_archive:
                tqdm.write(f"Processed archive file: {filename} - {file_records} records")
            
            processed_files += 1
                
        except Exception as e:
            error_files += 1
            tqdm.write(f"Error processing {dat_file}: {e}")
    
    print(f"\nProcessed {processed_files} files successfully, {error_files} files had errors")
    print(f"Found {total_records} total records")
    print(f"Found {len(locality_records)} unique localities")
    
    # Write records to separate files for each locality
    print(f"\nWriting locality files...")
    for locality, records in tqdm(locality_records.items(), desc="Creating locality files", unit="locality"):
        # Create a safe filename from locality name
        safe_locality_name = "".join(c for c in locality if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_locality_name = safe_locality_name.replace(' ', '_')
        
        if safe_locality_name:  # Make sure we have a valid filename
            output_file = os.path.join(localities_folder, f"{safe_locality_name}.DAT")
            
            try:
                with open(output_file, 'w', encoding='utf-8') as file:
                    for record in records:
                        file.write(record + '\n')
                
                print(f"Created {output_file} with {len(records)} records")
                
            except Exception as e:
                print(f"Error writing to {output_file}: {e}")
    
    print("Processing complete!")

if __name__ == "__main__":
    process_dat_files()