import os

TEMPLATE_CONTENT = {
    '.py': '# TODO: Add Python code here\n',
    '.js': '// TODO: Add JS code here\n',
    '.html': '<!-- TODO: Add HTML here -->\n',
    '.css': '/* TODO: Add CSS here */\n',
    '.yml': '# TODO: Add YAML here\n',
    '.json': '{\n  "TODO": "Add JSON here"\n}\n',
    '.md': '# TODO: Add Markdown here\n',
    '.qasm': 'OPENQASM 3.0;\n// TODO: Add Quantum code here\n',
}

def autofix_files(root_dir='.'):
    fixed = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            ext = os.path.splitext(file)[1]
            filepath = os.path.join(root, file)
            if ext in TEMPLATE_CONTENT:
                with open(filepath, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    if len(content.strip()) < 10:
                        f.seek(0)
                        f.write(TEMPLATE_CONTENT[ext])
                        f.truncate()
                        fixed.append(filepath)
    return fixed

if __name__ == "__main__":
    results = autofix_files()
    if results:
        print("Auto-fixed files:")
        for r in results:
            print(" - " + r)
    else:
        print("No files needed fixing.")
