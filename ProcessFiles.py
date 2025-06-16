import os
import json
import re
from collections import defaultdict

ROOT_DIR = "your/code/folder/path"
OUTPUT_DIR = "jsonl_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_java_methods(file_path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    class_match = re.search(r'\bclass\s+(\w+)', content)
    class_name = class_match.group(1) if class_match else "UnknownClass"

    method_pattern = re.finditer(
        r'((public|private|protected|static|\s)+[\w\<\>]+\s+(\w+)\s*[^]*\s*\{)',
        content
    )

    chunks = []
    for match in method_pattern:
        method_start = match.start()
        method_name = match.group(3)

        open_braces = 0
        method_body = ''
        found_start = False
        for c in content[method_start:]:
            method_body += c
            if c == '{':
                open_braces += 1
                found_start = True
            elif c == '}':
                open_braces -= 1
            if found_start and open_braces == 0:
                break

        if method_body.strip():
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

def get_relative_subdir(file_path):
    """Return relative subdirectory path (flattened with underscores)"""
    rel_path = os.path.relpath(os.path.dirname(file_path), ROOT_DIR)
    clean_name = rel_path.replace(os.sep, "_")
    return clean_name if clean_name else "root"

def process_directory(root_dir):
    module_chunks = defaultdict(list)

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith("Test.java"):
                continue  # skip unit tests

            full_path = os.path.join(dirpath, filename)

            if filename.endswith(".java"):
                print(f"Processing Java file: {full_path}")
                java_chunks = extract_java_methods(full_path)
                module_name = get_relative_subdir(full_path)
                module_chunks[module_name].extend(java_chunks)

            elif filename.endswith(".feature"):
                print(f"Processing BDD file: {full_path}")
                bdd_chunks = extract_bdd_scenarios(full_path)
                module_name = get_relative_subdir(full_path)
                module_chunks[module_name].extend(bdd_chunks)

    for module, chunks in module_chunks.items():
        output_path = os.path.join(OUTPUT_DIR, f"{module}.jsonl")
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + "\n")
        print(f"✅ Written: {output_path} ({len(chunks)} chunks)")

# Run it
process_directory(ROOT_DIR)