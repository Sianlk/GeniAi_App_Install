import json

def create_ofqual_module(title, outcomes, assessments):
    module = {
        'title': title,
        'standard': 'OFQUAL-CPD',
        'learning_outcomes': outcomes,
        'assessments': assessments
    }
    filename = f"{title.replace(' ', '_').lower()}.json"
    with open(filename, 'w') as f:
        json.dump(module, f, indent=4)

if __name__ == "__main__":
    title = 'AI Ethics for Business'
    outcomes = ['Understand AI principles', 'Apply ethical frameworks', 'Avoid bias in models']
    assessments = ['Quiz', 'Case Study', 'Final Project']
    create_ofqual_module(title, outcomes, assessments)
