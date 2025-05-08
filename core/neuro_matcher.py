import pandas as pd
import numpy as np

def neuro_match(profile_a, profile_b):
    score = 0
    traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    for trait in traits:
        score += 1 - abs(profile_a[trait] - profile_b[trait])
    return score / len(traits)

def filter_toxic_profiles(df):
    return df[~df['tags'].str.contains('narcissist|love bomber|manipulative', case=False)]

if __name__ == "__main__":
    df_profiles = pd.read_csv('user_profiles.csv')
    clean_profiles = filter_toxic_profiles(df_profiles)
    matches = []
    for i, row_a in clean_profiles.iterrows():
        for j, row_b in clean_profiles.iterrows():
            if i >= j:
                continue
            match_score = neuro_match(row_a, row_b)
            if match_score > 0.8:
                matches.append((row_a['id'], row_b['id'], match_score))
    pd.DataFrame(matches, columns=['UserA', 'UserB', 'Score']).to_csv('matches.csv', index=False)
