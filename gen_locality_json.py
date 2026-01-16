import os
import json

def generate_localities_json(localities_folder, output_file):
    try:
        # List all .DAT files in the localities folder and remove the .DAT extension
        localities = []
        for name in os.listdir(localities_folder):
            if name.endswith('.DAT') and os.path.isfile(os.path.join(localities_folder, name)):
                # Remove the .DAT extension
                locality_name = name[:-4]  # Remove last 4 characters (.DAT)
                localities.append(locality_name)
        
        # Write the localities to a JSON file
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(localities, json_file, separators=(',', ':'))
        
        print(f"Successfully generated {output_file} with {len(localities)} localities.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Define the localities folder and output file
    localities_folder = "localities"
    output_file = "localities.json"
    
    # Generate the localities.json file
    generate_localities_json(localities_folder, output_file)