import pandas as pd
import numpy as np
import re
import json
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
import os

# Load BERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

def normalize_text(text):
    if pd.isna(text):
        return ""
    return re.sub(r'[^\w\s]', '', str(text).lower())

def get_ngrams(text, n):
    words = text.split()
    return [' '.join(words[i:i+n]) for i in range(len(words)-n+1)]

def multi_ngram_search(query, text, max_n=3):
    query = normalize_text(query)
    text = normalize_text(text)
    
    query_ngrams = [get_ngrams(query, i) for i in range(1, max_n+1)]
    text_ngrams = [get_ngrams(text, i) for i in range(1, max_n+1)]
    
    score = 0
    max_score = 0
    
    for n in range(1, max_n+1):
        for q_gram in query_ngrams[n-1]:
            best_match = max((fuzz.ratio(q_gram, t_gram) for t_gram in text_ngrams[n-1]), default=0)
            score += best_match * n * n  # Weight longer n-grams more
        max_score += 100 * len(query_ngrams[n-1]) * n * n
    
    return score / max_score if max_score > 0 else 0.0

def get_embedding(text):
    if pd.isna(text):
        return np.zeros(384)  # Return zero vector for NaN values (384 is the dimension of 'all-MiniLM-L6-v2' embeddings)
    text = str(text).replace("\n", " ")
    return model.encode(text)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def calculate_category_scores(text, categories, embeddings):
    text_embedding = get_embedding(text)
    scores = {}
    for category, phrases in categories.items():
        category_embedding = embeddings[category]
        cosine_score = cosine_similarity(text_embedding, category_embedding)
        ngram_score = max(multi_ngram_search(phrase, text) for phrase in phrases)
        scores[f'{category}_cosine'] = cosine_score
        scores[f'{category}_ngram'] = ngram_score
    return scores

def analyze_faculty(input_file, target_categories, avoid_categories, target_score, avoid_score, cosine_weight, ngram_weight):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    school = input_file.split('_')[-1].split('.')[0]

    # find which keys are in the df that are from this list: specilities, publications, intro, courses and create a new column called combined_text with content from whichever keys are present
    df['combined_text'] = ""
    keys_present = ['specialties', 'publications', 'intro', 'courses']
    for key in keys_present:
        if key in df.columns:    
            df[key] = df[key].apply(lambda x: ' '.join(x) if isinstance(x, list) else (x if isinstance(x, str) else ''))
            df['combined_text'] += df[key].fillna('') + ' '
    
    # Get embeddings for each category
    target_embeddings = {category: get_embedding(' '.join(phrases)) for category, phrases in target_categories.items()}
    avoid_embeddings = {category: get_embedding(' '.join(phrases)) for category, phrases in avoid_categories.items()}
    
    tqdm.pandas(desc=f"Processing {school} faculty data")
    target_scores = df['combined_text'].progress_apply(lambda x: calculate_category_scores(x, target_categories, target_embeddings))
    avoid_scores = df['combined_text'].progress_apply(lambda x: calculate_category_scores(x, avoid_categories, avoid_embeddings))
    
    target_df = pd.DataFrame(target_scores.tolist(), index=df.index)
    avoid_df = pd.DataFrame(avoid_scores.tolist(), index=df.index)
    
    df = pd.concat([df, target_df, avoid_df], axis=1)
    
    for category in target_categories.keys():
        df[f'{category}_score'] = (df[f'{category}_cosine'] * cosine_weight + df[f'{category}_ngram'] * ngram_weight) * target_score
    for category in avoid_categories.keys():
        df[f'{category}_score'] = (df[f'{category}_cosine'] * cosine_weight + df[f'{category}_ngram'] * ngram_weight) * avoid_score
    
    target_columns = [f'{category}_score' for category in target_categories.keys()]
    avoid_columns = [f'{category}_score' for category in avoid_categories.keys()]

    df['target_score'] = df[target_columns].apply(lambda x: np.average(x, weights=np.abs(x)), axis=1)
    df['avoid_score'] = df[avoid_columns].apply(lambda x: np.average(x, weights=np.abs(x)), axis=1)
    df['total_score'] = df['target_score'] + df['avoid_score']
    
    output_columns = ['name', 'target_score', 'avoid_score', 'total_score'] + \
                     [f'{category}_score' for category in target_categories.keys()] + \
                     [f'{category}_score' for category in avoid_categories.keys()]
    df['school'] = school
    output_df = df[output_columns + ['school']]
    
    output_df.to_csv(f'faculty_analysis_{school}.csv', index=False)
    
    plt.figure(figsize=(10, 6))
    sns.boxplot(x=output_df['total_score'])
    plt.title(f'Distribution of Total Scores - {school.capitalize()}')
    plt.savefig(f'score_distribution_{school}.png')
    plt.close()
    
    return output_df

def analyze_all_schools(schools, target_categories, avoid_categories, target_score, avoid_score, cosine_weight, ngram_weight):
    all_results = []
    
    for school in schools:
        print(f"\nAnalyzing {school}...")
        result = analyze_faculty(
            f'faculty_data_{school}.json',
            target_categories,
            avoid_categories,
            target_score,
            avoid_score,
            cosine_weight,
            ngram_weight
        )
        all_results.append(result)
    
    combined_df = pd.concat(all_results, ignore_index=True)
    combined_df.to_csv('faculty_analysis_all_schools.csv', index=False)
    
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='school', y='total_score', data=combined_df)
    plt.title('Distribution of Total Scores by School')
    plt.savefig('score_distribution_all_schools.png')
    plt.close()
    
    print("\nOverall Statistics:")
    print(combined_df['total_score'].describe())
    
    print("\nTop scorers across all schools:")
    print(combined_df.sort_values('total_score', ascending=False).head())
    
    print("\nBottom scorers across all schools:")
    print(combined_df.sort_values('total_score', ascending=True).head())
    
    return combined_df

# Example usage
target_categories = {
    'military': ['military', 'warfare', 'war and society'],
    'american_wars': ['World War I', 'World War II'],
    'revolutionary war': ['revolutionary war', 'american revolution'],
    'war of 1812': ['war of 1812', '1812'],
    'cold war': ['cold war', 'soviet', 'communism'],
    'jackson': ['jackson', 'andrew jackson', 'jacksonian democracy'],
    'geopolitics': ['geopolitical', 'diplomatic', 'international relations'],
    'early_america': ['early American', 'colonial America'],
    'economic': ['economic', 'economics', 'economy', "industry"]
}

avoid_categories = {
    'decolonization': ['decolonization', 'postcolonial'],
    'critical_theory': ['critical race theory', 'feminism', 'queer studies', 'intersectional'],
    'social_issues': ['race', 'class', 'gender', 'LGBTQ+', 'social justice', 'inequality'],
    'economic_systems': ['capitalism', 'Marxism', 'labor movements'],
    'cultural_studies': ['cultural', 'postmodern', 'transnational'],
    'environmental': ['environmental', 'climate'],
    'migration': ['migration', 'diaspora'],
    'transnational': ['transnational', 'global', 'world'],
    'indigenous': ['indigenous', 'native', 'tribal', 'indian'],
    'african': ['african', 'africa', 'nigeria', 'kenya'],
    'rousseau': ['rousseau', 'social contract', 'general will'],
    'empire_studies': ['empire', 'colonial', 'imperial', 'postcolonial'],
    'post-wwii': ['post-wwii', 'postwar', 'post-war'],
    '1960s': ['1960s', 'sixties', 'civil rights', 'vietnam'],
    'islam': ['islam', 'Middle East', 'arab spring']
}

target_score = 1
avoid_score = -1.25
cosine_weight = 0.35
ngram_weight = 0.65

# list of schools are all the stripped school names from the faculty_data files in the current directory
schools = [f.split('_')[-1].split('.')[0] for f in os.listdir() if f.startswith('faculty_data_') and f.endswith('.json')]


combined_result = analyze_all_schools(
    schools,
    target_categories,
    avoid_categories,
    target_score,
    avoid_score,
    cosine_weight,
    ngram_weight
)