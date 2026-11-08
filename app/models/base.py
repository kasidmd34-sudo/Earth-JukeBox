"""Base class contract for all environmental prediction models."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

class BaseEnvironmentalModel(ABC):
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.is_trained = False
        self.metrics: Dict[str, float] = {}

    @abstractmethod
    def fit(self, train_df: pd.DataFrame, target_col: str) -> Dict[str, float]:
        pass

    @abstractmethod
    def predict_forward(
        self,
        historical_df: pd.DataFrame,
        target_col: str,
        steps: int
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        """Returns predictions along with uncertainty lower/upper confidence bounds."""
        pass