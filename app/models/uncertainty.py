"""Empirical residual bootstrapping for physically defensible uncertainty quantification."""
import numpy as np
from typing import List, Tuple

class ResidualUncertaintyEstimator:
    @staticmethod
    def compute_prediction_intervals(
        residuals: np.ndarray,
        point_predictions: List[float],
        confidence_level: float = 0.95
    ) -> List[Tuple[float, float]]:
        if len(residuals) < 5:
            # Fallback if insufficient residuals
            return [(p * 0.9, p * 1.1) for p in point_predictions]
        
        alpha = 1.0 - confidence_level
        lower_percentile = (alpha / 2.0) * 100.0
        upper_percentile = (1.0 - alpha / 2.0) * 100.0
        
        err_lower = np.percentile(residuals, lower_percentile)
        err_upper = np.percentile(residuals, upper_percentile)

        intervals = []
        for p in point_predictions:
            intervals.append((float(p + err_lower), float(p + err_upper)))
        return intervals