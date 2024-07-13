import json
import os

def combine_json_files(input_files, output_file):
    combined_data = []

    for input_file in input_files:
        school_name = input_file.split('_')[-1].split('.')[0].capitalize()
        
        with open(input_file, 'r', encoding='utf-8') as file:
            school_data = json.load(file)
            
            for person in school_data:
                person['school'] = school_name
                combined_data.append(person)

    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(combined_data, outfile, ensure_ascii=False, indent=4)

    print(f"Combined data saved to {output_file}")

def main():
    # input files are all the faculty data files .json that are in the current directory
    input_files = [f for f in os.listdir() if f.startswith('faculty_data_') and f.endswith('.json')]
    
    
    
    output_file = 'faculty_data.json'

    # Check if all input files exist
    missing_files = [f for f in input_files if not os.path.isfile(f)]
    if missing_files:
        print(f"Error: The following input files are missing: {', '.join(missing_files)}")
        return

    combine_json_files(input_files, output_file)

if __name__ == "__main__":
    main()