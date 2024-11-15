import pandas as pd
import numpy as np
import re
import json
import matplotlib.pyplot as plt
import seaborn as sns
from openai import OpenAI
import os
from tqdm import tqdm
from rapidfuzz import fuzz

# Assuming you've set your OpenAI API key as an environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def chunk_text(text, max_tokens=4000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def get_embedding(text):
    if pd.isna(text):
        return np.zeros(1536)  # Return zero vector for NaN values
    text = str(text).replace("\n", " ")
    chunks = chunk_text(text)
    embeddings = []
    for chunk in chunks:
        embedding = client.embeddings.create(input=[chunk], model="text-embedding-ada-002").data[0].embedding
        embeddings.append(embedding)
    return np.mean(embeddings, axis=0)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def calculate_scores(text, target_phrase, avoid_phrase, target_embedding, avoid_embedding):
    text_embedding = get_embedding(text)
    return {
        'target_cosine': cosine_similarity(text_embedding, target_embedding),
        'avoid_cosine': cosine_similarity(text_embedding, avoid_embedding),
        'target_ngram': multi_ngram_search(target_phrase, text),
        'avoid_ngram': multi_ngram_search(avoid_phrase, text)
    }

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
    
    df['combined_text'] = df['specialties'].fillna('') + ' ' + df['publications'].fillna('') + ' ' + df['intro'].fillna('')
    
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
    # add school
    df['school'] = school
    output_df = df[output_columns]
    
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
    'american_wars': ['World War I', 'World War II', 'revolutionary war', 'war of 1812'],
    'geopolitics': ['geopolitical', 'international relations', 'diplomatic'],
    'early_america': ['early American', 'colonial America', 'American revolution'],
    'economic': ['economic']
}

avoid_categories = {
    'decolonization': ['decolonization', 'postcolonial'],
    'critical_theory': ['critical race theory', 'feminism', 'queer studies', 'intersectional'],
    'social_issues': ['race', 'class', 'gender', 'LGBTQ+', 'social justice', 'inequality'],
    'economic_systems': ['capitalism', 'Marxism', 'labor movements'],
    'cultural_studies': ['cultural', 'postmodern', 'transnational'],
    'environmental': ['environmental', 'climate'],
    'migration': ['migration', 'diaspora'],
    'islam': ['islam', 'Middle East', 'arab spring']
}

target_score = 1
avoid_score = -1
cosine_weight = 0.4
ngram_weight = 0.6
schools = ["harvard", "stanford", "uva"]

combined_result = analyze_all_schools(
    schools,
    target_categories,
    avoid_categories,
    target_score,
    avoid_score,
    cosine_weight,
    ngram_weight
)