import pandas as pd
import numpy as np

def neuro_match(a, b):
    score = 0
    traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    for trait in traits:
        score += 1 - abs(a[trait] - b[trait])
    return score / len(traits)

def filter_toxic(df):
    return df[~df['tags'].str.contains('narcissist|love bomber|manipulative', case=False, na=False)]

if __name__ == "__main__":
    profiles = pd.read_csv('user_profiles.csv')
    profiles = filter_toxic(profiles)
    matches = []
    for i, user_a in profiles.iterrows():
        for j, user_b in profiles.iterrows():
            if i >= j:
                continue
            score = neuro_match(user_a, user_b)
            if score > 0.8:
                matches.append((user_a['id'], user_b['id'], score))
    pd.DataFrame(matches, columns=['UserA', 'UserB', 'Score']).to_csv('matches.csv', index=False)
