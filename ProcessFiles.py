import os
import json
import re
from collections import defaultdict

# 🔧 Set your directories
ROOT_DIR = "your/code/folder/path"
OUTPUT_DIR = "jsonl_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_java_methods(file_path):
    """Extract Java methods from a file, excluding classes without method bodies."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    class_match = re.search(r'\bclass\s+(\w+)', content)
    class_name = class_match.group(1) if class_match else "UnknownClass"

    # Match method declarations with their content using simple bracket matching
    method_pattern = re.finditer(
        r'((public|private|protected|static|\s)+[\w\<\>]+\s+(\w+)\s*[^]*\s*\{)',
        content
    )

    chunks = []
    for match in method_pattern:
        method_start = match.start()
        method_name = match.group(3)

        # Bracket matching to extract full method body
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
    """Extract BDD scenarios from a .feature file."""
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

def get_module_name(full_path):
    """Get top-level folder under ROOT_DIR to use as module name."""
    relative_path = os.path.relpath(full_path, ROOT_DIR)
    parts = relative_path.split(os.sep)
    return parts[0] if len(parts) > 1 else "root"

def process_directory(root_dir):
    module_chunks = defaultdict(list)

    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)

            # Exclude Java test files
            if filename.endswith("Test.java"):
                continue

            # Process .java files
            if filename.endswith(".java"):
                print(f"Processing Java file: {full_path}")
                java_chunks = extract_java_methods(full_path)
                if java_chunks:
                    module_name = get_module_name(full_path)
                    module_chunks[module_name].extend(java_chunks)

            # Process .feature files
            elif filename.endswith(".feature"):
                print(f"Processing BDD file: {full_path}")
                bdd_chunks = extract_bdd_scenarios(full_path)
                if bdd_chunks:
                    module_name = get_module_name(full_path)
                    module_chunks[module_name].extend(bdd_chunks)

    # Write per-module .jsonl files
    for module, chunks in module_chunks.items():
        out_path = os.path.join(OUTPUT_DIR, f"{module}.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + "\n")
        print(f"✅ Written: {out_path} ({len(chunks)} chunks)")

# Run it
process_directory(ROOT_DIR)