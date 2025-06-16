import os
import json
import re

OUTPUT_FILE = "code_and_bdd_chunks.jsonl"

def extract_java_methods(file_path):
    """Extract methods from a Java file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    class_match = re.search(r'\bclass\s+(\w+)', content)
    class_name = class_match.group(1) if class_match else "UnknownClass"

    # Rough regex to split on method definitions (doesn’t capture method body fully)
    method_pattern = re.finditer(
        r'((public|private|protected|static|\s)+[\w\<\>]+\s+(\w+)\s*.*?\s*\{)',
        content
    )

    chunks = []
    for i, match in enumerate(method_pattern):
        method_start = match.start()
        method_name = match.group(3)

        # Try to extract method body (bracket matching logic for better parsing)
        open_braces = 0
        in_method = False
        method_body = ''
        for c in content[method_start:]:
            method_body += c
            if c == '{':
                open_braces += 1
                in_method = True
            elif c == '}':
                open_braces -= 1
            if in_method and open_braces == 0:
                break

        chunks.append({
            "source": file_path,
            "type": "code",
            "chunk_type": "method",
            "class_name": class_name,
            "name": method_name,
            "content": method_body.strip()
        })

    return chunks

def extract_bdd_scenarios(file_path):
    """Extract BDD scenarios from a feature file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    scenarios = []
    scenario_lines = []
    scenario_name = ""
    for line in lines:
        if line.strip().startswith("Scenario"):
            if scenario_lines:
                scenarios.append({
                    "source": file_path,
                    "type": "bdd",
                    "chunk_type": "scenario",
                    "name": scenario_name,
                    "content": "".join(scenario_lines).strip()
                })
                scenario_lines = []
            scenario_name = line.strip()
            scenario_lines.append(line)
        elif line.strip() or scenario_lines:
            scenario_lines.append(line)

    if scenario_lines:
        scenarios.append({
            "source": file_path,
            "type": "bdd",
            "chunk_type": "scenario",
            "name": scenario_name,
            "content": "".join(scenario_lines).strip()
        })

    return scenarios

def process_directory(root_dir, output_file_path):
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                if filename.endswith(".java"):
                    java_chunks = extract_java_methods(full_path)
                    for chunk in java_chunks:
                        output_file.write(json.dumps(chunk) + "\n")
                elif filename.endswith(".feature"):
                    bdd_chunks = extract_bdd_scenarios(full_path)
                    for chunk in bdd_chunks:
                        output_file.write(json.dumps(chunk) + "\n")
                else:
                    continue  # Ignore other file types

# 🔧 Replace with your root folder path
process_directory("your/code/folder/path", OUTPUT_FILE)
