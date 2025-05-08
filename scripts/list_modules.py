import os

def list_modules(root_dir='.'):
    modules = []
    for root, dirs, files in os.walk(root_dir):
        if '__init__.py' in files:
            modules.append(os.path.relpath(root, root_dir))
    return modules

if __name__ == "__main__":
    mods = list_modules()
    with open('module_list.txt', 'w') as out:
        out.write("\n".join(mods))
    print("Module list saved to module_list.txt")
