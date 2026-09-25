import os

mit_license = """MIT License

Copyright (c) 2026 Rohit Satywan Kamble

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

with open("LICENSE", "w") as f:
    f.write(mit_license)
print("Created LICENSE")

header_py = """# Copyright (c) 2026 Rohit Satywan Kamble
# Licensed under the MIT License. See LICENSE file for details.
"""

header_js_css = """/*
 * Copyright (c) 2026 Rohit Satywan Kamble
 * Licensed under the MIT License. See LICENSE file for details.
 */
"""

header_html_md = """<!--
  Copyright (c) 2026 Rohit Satywan Kamble
  Licensed under the MIT License. See LICENSE file for details.
-->
"""

def get_header(ext):
    if ext == '.py': return header_py
    elif ext in ['.js', '.css']: return header_js_css
    elif ext in ['.html']: return header_html_md
    return None

skip_dirs = {'.git', 'venv', '__pycache__', '.bun', 'ai-job-search', 'scratch', 'docs'}
skip_files = {'.env', '.DS_Store'}

modified_files = []

for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
    for file in files:
        if file in skip_files or file.startswith('.'):
            continue
        ext = os.path.splitext(file)[1]
        header = get_header(ext)
        if not header:
            continue
            
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            if "Copyright (c) 2026 Rohit Satywan Kamble" in content:
                continue
                
            with open(filepath, 'w') as f:
                f.write(header + "\n" + content)
            modified_files.append(filepath)
        except Exception as e:
            pass

readme_path = "README.md"
if os.path.exists(readme_path):
    with open(readme_path, 'r') as f:
        content = f.read()
    if "## License" not in content:
        with open(readme_path, 'a') as f:
            f.write("\n## License\nThis project is licensed under the MIT License - see the LICENSE file for details.\nCopyright (c) 2026 Rohit Satywan Kamble\n")
        modified_files.append(readme_path)

print(f"Modified {len(modified_files)} files:")
for f in modified_files:
    print(f)
