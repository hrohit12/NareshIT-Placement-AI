import os

mit_license_mads = """MIT License

Copyright (c) 2026 Mads Lorentzen

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

with open("lib/JobSearchAgent/LICENSE", "w") as f:
    f.write(mit_license_mads)
print("Created lib/JobSearchAgent/LICENSE")

headers_to_remove = [
    "# Copyright (c) 2026 Rohit Satywan Kamble\n# Licensed under the MIT License. See LICENSE file for details.\n",
    "/*\n * Copyright (c) 2026 Rohit Satywan Kamble\n * Licensed under the MIT License. See LICENSE file for details.\n */\n",
    "<!--\n  Copyright (c) 2026 Rohit Satywan Kamble\n  Licensed under the MIT License. See LICENSE file for details.\n-->\n"
]

modified_files = []

for root, dirs, files in os.walk('lib/JobSearchAgent'):
    for file in files:
        if file.startswith('.'):
            continue
        filepath = os.path.join(root, file)
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            modified = False
            for header in headers_to_remove:
                if content.startswith(header):
                    content = content[len(header):]
                    modified = True
                    break
            
            if modified:
                with open(filepath, 'w') as f:
                    f.write(content)
                modified_files.append(filepath)
        except Exception as e:
            pass

readme_path = "README.md"
if os.path.exists(readme_path):
    with open(readme_path, 'r') as f:
        content = f.read()
    
    ack_text = "\n## Acknowledgments\nThe job search agent in `/lib/JobSearchAgent/` is based on [ai-job-search](https://github.com/MadsLorentzen/ai-job-search) by Mads Lorentzen, used under the MIT License.\n"
    if "## Acknowledgments" not in content:
        with open(readme_path, 'a') as f:
            f.write(ack_text)
        modified_files.append(readme_path)

print(f"Modified {len(modified_files)} files:")
for f in modified_files:
    print(f)
