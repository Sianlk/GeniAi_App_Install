import json

def create_ofqual_module(title, learning_outcomes, assessments):
    module = {
        'title': title,
        'standard': 'OFQUAL-CPD',
        'learning_outcomes': learning_outcomes,
        'assessments': assessments
    }
    with open(f"{title.replace(' ', '_')}.json", 'w') as f:
        json.dump(module, f, indent=4)
    print(f"Module '{title}' created.")

if __name__ == "__main__":
    title = 'AI Ethics for Business'
    learning_outcomes = ['Understand AI principles', 'Apply ethical frameworks', 'Avoid bias']
    assessments = ['Quiz', 'Case Study', 'Final Project']
    create_ofqual_module(title, learning_outcomes, assessments)
