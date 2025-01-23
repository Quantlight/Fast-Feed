import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import db, FeedEntry

user_data = {
    'vectorizer': TfidfVectorizer(stop_words='english', max_features=5000),
    'tfidf_array': np.empty((0, 5000)),  # Empty array initialization
    'article_ids': [],
    'starred_ids': set()
}

def refresh_data(user_id):
    """Refresh all data with proper array conversions"""
    # Get all non-starred articles first
    non_starred = FeedEntry.query.filter_by(account_id=user_id, is_starred=False).all()
    starred = FeedEntry.query.filter_by(account_id=user_id, is_starred=True).all()
    
    # Combine and convert to array
    all_articles = non_starred + starred
    texts = [f"{a.title} {a.full_content}" for a in all_articles]
    
    if texts:
        # Convert sparse matrix to dense array
        user_data['tfidf_array'] = user_data['vectorizer'].fit_transform(texts).toarray()
        user_data['article_ids'] = [a.id for a in all_articles]
        user_data['starred_ids'] = {a.id for a in starred}

def calculate_scores(user_id):
    """Calculate scores and explicitly zero out starred articles"""
    if user_data['tfidf_array'].size == 0:
        return  # No data to process

    # Get all article IDs in the current batch
    all_article_ids = user_data['article_ids']

    # Reset ALL scores to 0 first (avoids stale values)
    for idx in range(len(all_article_ids)):
        article = FeedEntry.query.get(all_article_ids[idx])
        article.similarity_score = 0.0

    # If no starred articles, leave everything at 0 and exit
    if not user_data['starred_ids']:
        db.session.commit()
        return

    # Calculate similarities for NON-STARRED articles
    starred_indices = [i for i, aid in enumerate(all_article_ids) 
                      if aid in user_data['starred_ids']]
    
    profile = np.mean(user_data['tfidf_array'][starred_indices], axis=0)
    profile = profile.reshape(1, -1)  # Ensure 2D

    non_starred_mask = [aid not in user_data['starred_ids'] 
                       for aid in all_article_ids]
    
    similarities = cosine_similarity(
        profile, 
        user_data['tfidf_array'][non_starred_mask]
    ).flatten()

    # Update scores ONLY for non-starred articles
    for idx, score in zip(np.where(non_starred_mask)[0], similarities):
        article = FeedEntry.query.get(all_article_ids[idx])
        article.similarity_score = float(score)

    db.session.commit()