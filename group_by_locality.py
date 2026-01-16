import os
import glob
from collections import defaultdict
from tqdm import tqdm

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
    
    # Exclude files that start with 'ARCHIVE_SALES_'
    dat_files = []
    for file_path in all_dat_files:
        filename = os.path.basename(file_path)
        if not filename.startswith('ARCHIVE_SALES_'):
            dat_files.append(file_path)
    
    print(f"Found {len(all_dat_files)} total .DAT files, excluding {len(all_dat_files) - len(dat_files)} archive files")
    print(f"Processing {len(dat_files)} .DAT files...")
    
    processed_files = 0
    total_records = 0
    error_files = 0
    
    # Process each .DAT file with progress bar
    for dat_file in tqdm(dat_files, desc="Processing .DAT files", unit="file"):
        try:
            file_records = 0
            with open(dat_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line in file:
                    line = line.strip()
                    
                    # Check if line starts with 'B;'
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