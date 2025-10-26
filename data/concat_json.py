import json
import os
from glob import glob

def concat_json_files():
    # Get all JSON files in the current directory
    json_files = glob('*.json')
    
    if not json_files:
        print("No JSON files found in the current directory")
        return
    
    all_questions = []
    
    # Read each JSON file and concatenate the contents
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                questions = json.load(file)
                # Handle both single question and question list formats
                if isinstance(questions, list):
                    all_questions.extend(questions)
                else:
                    all_questions.append(questions)
        except json.JSONDecodeError as e:
            print(f"Error reading {file_path}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error with {file_path}: {e}")
            continue
    
    if not all_questions:
        print("No valid questions found in JSON files")
        return
    
    # Write the combined questions to a new file
    output_file = 'combined_questions.json'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_questions, f, ensure_ascii=False, indent=2)
        print(f"Successfully combined {len(all_questions)} questions into {output_file}")
    except Exception as e:
        print(f"Error writing combined file: {e}")

if __name__ == "__main__":
    concat_json_files()
