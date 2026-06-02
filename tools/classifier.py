#!/usr/bin/env python3
"""
Lithological classifier — Random Forest pipeline with holdout validation.

Trains and applies RF classification to spectral index features for
Kem Kem Group lithological mapping. Random Forest chosen based on
analogous Moroccan terrain studies (76-91% accuracy).

Deep learning explicitly excluded per intelligence brief:
insufficient spatial resolution at 10-20m and limited training data.

Layer 4 — Domain Tools for Season 1.
"""
# FILE_TRAJECTORY: load-bearing
# TRAJECTORY_NOTE: The analytical core. Consumes features from
# spectral_indices.py, produces classifications stored in territory_manager.
# Holdout validation is critical — this is what makes findings publishable.

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger("nse.classifier")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
MODELS_DIR = STATE_DIR / "models"

# Kem Kem lithological classes (from Ibrahim & Sereno 2020)
LITHOLOGY_CLASSES = {
    0: "unclassified",
    1: "ferruginous_sandstone",    # Gara Sbaa Fm — iron oxide target
    2: "limestone",                 # Cenomanian-Turonian cap — carbonate target
    3: "mudstone",                  # Clay-rich horizons
    4: "alluvium",                  # Recent deposits
    5: "vegetation",                # Agricultural/riparian (mask target)
}

# Default RF parameters — tuned for small training sets typical of
# remote sensing studies in novel terrain
DEFAULT_RF_PARAMS = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_leaf": 5,
    "random_state": 42,
    "n_jobs": -1,
    "class_weight": "balanced",  # Handle class imbalance in training data
}

# Holdout fraction for validation
HOLDOUT_FRACTION = 0.2


class LithologyClassifier:
    """
    Random Forest lithological classifier for Kem Kem Group mapping.

    Workflow:
        1. Train on labeled samples (from training dataset)
        2. Predict on new tiles (from spectral indices)
        3. Report accuracy metrics and confidence
    """

    def __init__(self):
        self.model = None
        self.feature_names: list[str] = []
        self.train_metrics: dict = {}
        self.model_version: str = ""

    def train(self, features: np.ndarray, labels: np.ndarray,
              feature_names: Optional[list[str]] = None,
              rf_params: Optional[dict] = None) -> dict:
        """
        Train the RF classifier with holdout validation.

        Args:
            features: 2D array (n_samples, n_features) of spectral indices.
            labels: 1D array (n_samples,) of lithology class labels.
            feature_names: Optional names for features (for importance ranking).
            rf_params: Optional override for RF hyperparameters.

        Returns:
            Training metrics dict:
            {
                "accuracy": float,
                "holdout_accuracy": float,
                "per_class": dict[str, dict],  # precision, recall, f1
                "feature_importance": list[dict],
                "n_train": int,
                "n_holdout": int,
                "model_version": str,
            }
        """
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report

        params = {**DEFAULT_RF_PARAMS, **(rf_params or {})}
        self.feature_names = feature_names or [
            f"feature_{i}" for i in range(features.shape[1])
        ]

        # Split holdout
        X_train, X_hold, y_train, y_hold = train_test_split(
            features, labels,
            test_size=HOLDOUT_FRACTION,
            random_state=params["random_state"],
            stratify=labels if len(np.unique(labels)) > 1 else None,
        )

        # Train
        self.model = RandomForestClassifier(**params)
        self.model.fit(X_train, y_train)

        # Evaluate
        train_acc = self.model.score(X_train, y_train)
        hold_acc = self.model.score(X_hold, y_hold)

        hold_pred = self.model.predict(X_hold)
        report = classification_report(
            y_hold, hold_pred,
            target_names=[LITHOLOGY_CLASSES.get(c, str(c))
                          for c in sorted(np.unique(labels))],
            output_dict=True,
            zero_division=0,
        )

        # Feature importance
        importances = self.model.feature_importances_
        importance_list = sorted(
            [{"feature": name, "importance": float(imp)}
             for name, imp in zip(self.feature_names, importances)],
            key=lambda x: x["importance"],
            reverse=True,
        )

        self.model_version = datetime.now(timezone.utc).strftime("v%Y%m%d-%H%M")

        self.train_metrics = {
            "accuracy": float(train_acc),
            "holdout_accuracy": float(hold_acc),
            "per_class": {
                k: v for k, v in report.items()
                if isinstance(v, dict) and "precision" in v
            },
            "feature_importance": importance_list,
            "n_train": len(X_train),
            "n_holdout": len(X_hold),
            "model_version": self.model_version,
        }

        logger.info(
            "Classifier trained: train=%.3f holdout=%.3f (%d/%d samples) %s",
            train_acc, hold_acc, len(X_train), len(X_hold),
            self.model_version,
        )

        # Record M1 metric — self-measurement infrastructure
        try:
            import sys
            sys.path.insert(0, str(PROJECT_ROOT / "harness"))
            from metrics_collector import MetricsCollector
            mc = MetricsCollector()
            mc.record_classification_accuracy(
                model_version=self.model_version,
                train_accuracy=float(train_acc),
                holdout_accuracy=float(hold_acc),
                per_class=self.train_metrics["per_class"],
                n_train=len(X_train),
                n_holdout=len(X_hold),
                feature_importance=importance_list,
            )
        except Exception as e:
            logger.debug("M1 metric recording failed (non-blocking): %s", e)

        return self.train_metrics

    def predict(self, features: np.ndarray) -> dict:
        """
        Predict lithology classes and confidence for new data.

        Args:
            features: 2D array (n_pixels, n_features) of spectral indices.

        Returns:
            {
                "predictions": np.ndarray,    # class labels
                "confidence": np.ndarray,     # max class probability
                "probabilities": np.ndarray,  # full probability matrix
                "model_version": str,
            }
        """
        if self.model is None:
            raise RuntimeError("Classifier not trained. Call train() first.")

        predictions = self.model.predict(features)
        probabilities = self.model.predict_proba(features)
        confidence = probabilities.max(axis=1)

        return {
            "predictions": predictions,
            "confidence": confidence,
            "probabilities": probabilities,
            "model_version": self.model_version,
        }

    def predict_tile(self, index_arrays: dict[str, np.ndarray]) -> dict:
        """
        Classify a full tile from spectral index arrays.

        Flattens spatial dimensions, excludes NaN pixels, predicts,
        and reshapes back to the tile's spatial dimensions.

        Args:
            index_arrays: Dict from spectral_indices.compute_all().

        Returns:
            {
                "classification_map": np.ndarray,  # 2D class labels
                "confidence_map": np.ndarray,       # 2D confidence values
                "valid_fraction": float,            # fraction of classifiable pixels
                "class_distribution": dict,         # class → pixel count
                "model_version": str,
            }
        """
        if self.model is None:
            raise RuntimeError("Classifier not trained. Call train() first.")

        # Stack features in training order
        feature_arrays = []
        for name in self.feature_names:
            if name in index_arrays:
                feature_arrays.append(index_arrays[name])
            else:
                raise ValueError(f"Missing feature '{name}' in index arrays")

        # Get spatial shape from first array
        h, w = feature_arrays[0].shape

        # Flatten and stack
        flat = np.stack([arr.ravel() for arr in feature_arrays], axis=1)

        # Find valid (non-NaN) pixels
        valid_mask = ~np.any(np.isnan(flat), axis=1)
        valid_fraction = float(valid_mask.sum() / valid_mask.size)

        # Initialize output
        class_map = np.full(h * w, 0, dtype=np.int32)
        conf_map = np.full(h * w, np.nan, dtype=np.float32)

        if valid_mask.sum() > 0:
            result = self.predict(flat[valid_mask])
            class_map[valid_mask] = result["predictions"]
            conf_map[valid_mask] = result["confidence"]

        class_map = class_map.reshape(h, w)
        conf_map = conf_map.reshape(h, w)

        # Class distribution
        unique, counts = np.unique(class_map[valid_mask.reshape(h, w)],
                                   return_counts=True)
        distribution = {
            LITHOLOGY_CLASSES.get(int(c), str(c)): int(n)
            for c, n in zip(unique, counts)
        }

        return {
            "classification_map": class_map,
            "confidence_map": conf_map,
            "valid_fraction": valid_fraction,
            "class_distribution": distribution,
            "model_version": self.model_version,
        }

    def save(self, path: Optional[Path] = None) -> Path:
        """Save the trained model to disk."""
        import joblib

        if self.model is None:
            raise RuntimeError("No model to save.")

        if path is None:
            MODELS_DIR.mkdir(parents=True, exist_ok=True)
            path = MODELS_DIR / f"rf_{self.model_version}.joblib"

        joblib.dump({
            "model": self.model,
            "feature_names": self.feature_names,
            "train_metrics": self.train_metrics,
            "model_version": self.model_version,
            "lithology_classes": LITHOLOGY_CLASSES,
        }, path)

        logger.info("Model saved: %s", path)
        return path

    def load(self, path: Path) -> None:
        """Load a trained model from disk."""
        import joblib

        data = joblib.load(path)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        self.train_metrics = data["train_metrics"]
        self.model_version = data["model_version"]

        logger.info("Model loaded: %s (%s)", path, self.model_version)

    def summary_for_briefing(self) -> str:
        """Compact model summary for agent briefing injection."""
        if not self.train_metrics:
            return "Classifier: No model trained yet."

        m = self.train_metrics
        top_features = ", ".join(
            f["feature"] for f in m.get("feature_importance", [])[:3]
        )

        return (
            f"Classifier {m.get('model_version', '?')}: "
            f"holdout accuracy {m.get('holdout_accuracy', 0):.1%} "
            f"({m.get('n_holdout', 0)} samples). "
            f"Top features: {top_features}."
        )
