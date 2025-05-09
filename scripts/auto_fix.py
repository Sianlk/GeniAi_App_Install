import os, subprocess

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout: print(result.stdout)
    if result.stderr: print(result.stderr)
    return result

def clean_git():
    run_cmd("git fetch --all")
    run_cmd("git checkout main")
    run_cmd("git reset --hard origin/main")
    run_cmd("git clean -fd")
    run_cmd("git pull origin main")

def fix_file_names():
    files = subprocess.check_output("git ls-files", shell=True).decode().splitlines()
    for file in files:
        if any(c in file for c in [' ', '$', '"', "'", '`']):
            safe_name = file.replace(' ', '_').replace('"','').replace("'","").replace('$','').replace('`','')
            os.rename(file, safe_name)
            run_cmd(f"git mv '{file}' '{safe_name}'")
            print(f"Renamed {file} → {safe_name}")

def split_mixed_files():
    for file in os.listdir('.'):
        if file.endswith('.py') and 'import' in open(file).read() and '{' in open(file).read():
            py_part, json_part = [], []
            with open(file) as f:
                for line in f:
                    if line.strip().startswith(('import','from')): py_part.append(line)
                    else: json_part.append(line)
            with open(file, 'w') as f: f.writelines(py_part)
            with open(file+'.json', 'w') as f: f.writelines(json_part)
            run_cmd(f"git add {file} {file}.json")
            print(f"Split {file} → {file}, {file}.json")

def check_syntax():
    run_cmd("flake8 . || true")
    run_cmd("npx eslint . || true")
    run_cmd("docker-compose config || true")

def prepare_commit():
    run_cmd("git add .")
    run_cmd("git commit -m 'Auto AI fix: filenames, splits, syntax, cleanup'")
    run_cmd("git push origin main")

if __name__ == "__main__":
    clean_git()
    fix_file_names()
    split_mixed_files()
    check_syntax()
    prepare_commit()
    print("✅ Auto-fix AI finished. You can now rerun your pull request jobs!")
