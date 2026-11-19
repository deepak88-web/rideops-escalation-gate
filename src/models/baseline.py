"""
Baseline Classifier Module: Historical Category Avoidable Rate
"""

from typing import Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin


class CategoryRateBaselineClassifier(BaseEstimator, ClassifierMixin):
    """
    Predicts probability of avoidable escalation based on the historical avoidable rate
    of the ticket's category. Backs off to the global rate for unseen categories.
    """

    def __init__(self, threshold: float = 0.55):
        self.threshold = threshold
        self.category_rates_ = {}
        self.global_rate_ = 0.5
        self.classes_ = np.array([0, 1])

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        y_arr = np.asarray(y)
        cat_series = X["category"] if isinstance(X, pd.DataFrame) else pd.Series(X[:, 0])
        rates = pd.Series(y_arr, index=cat_series).groupby(level=0).mean()
        self.category_rates_ = rates.to_dict()
        self.global_rate_ = float(np.mean(y_arr))
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        cat_series = X["category"] if isinstance(X, pd.DataFrame) else pd.Series(X[:, 0])
        p1 = cat_series.map(self.category_rates_).fillna(self.global_rate_).values
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        p1 = self.predict_proba(X)[:, 1]
        return (p1 >= self.threshold).astype(int)
