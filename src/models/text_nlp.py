"""
NLP and Text Preprocessing Transformers Module (Section J)
"""

from typing import List
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_extraction.text import TfidfVectorizer


def build_tabular_preprocessor(
    cat_features: List[str],
    num_features: List[str]
) -> ColumnTransformer:
    """Build preprocessor for numeric scaling and categorical one-hot encoding."""
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features)
    ])


def build_tfidf_preprocessor(
    text_feature: str = "description",
    max_features: int = 300
) -> ColumnTransformer:
    """Build TF-IDF preprocessor for unstructured ticket descriptions."""
    return ColumnTransformer([
        ("tfidf", TfidfVectorizer(max_features=max_features, ngram_range=(1, 2), stop_words="english"), text_feature)
    ])


def build_hybrid_preprocessor(
    cat_features: List[str],
    num_features: List[str],
    text_feature: str = "description",
    max_features: int = 300
) -> ColumnTransformer:
    """Build unified hybrid preprocessor combining tabular structured features and text TF-IDF."""
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
        ("tfidf", TfidfVectorizer(max_features=max_features, ngram_range=(1, 2), stop_words="english"), text_feature)
    ])
