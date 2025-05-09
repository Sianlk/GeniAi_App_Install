import os

def scan_project(root_dir='.'):
    report = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if os.path.getsize(filepath) == 0:
                report.append("EMPTY FILE: " + filepath)
            elif file.endswith(('.py', '.js', '.yml', '.json', '.html', '.css', '.md', '.qasm')):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content.strip()) < 10:
                        report.append("POSSIBLY INCOMPLETE FILE: " + filepath)
    return report

if __name__ == "__main__":
    results = scan_project()
    if results:
        with open('diagnostic_report.txt', 'w') as out:
            out.write("\n".join(results))
        print("Diagnostic report generated: diagnostic_report.txt")
    else:
        print("All files look complete."
