import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import pickle
import json
from pathlib import Path
import matplotlib.pyplot as plt
import shap

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_recall_curve, auc,
    brier_score_loss, classification_report, RocCurveDisplay, PrecisionRecallDisplay
)
from sklearn.calibration import CalibratedClassifierCV, CalibrationDisplay

# --- Configuration ---

BASE_DIR = Path(__file__).parent.parent.parent
FEATURES_DIR = BASE_DIR / "data" / "features"
MODEL_DIR = BASE_DIR / "models"
EVAL_DIR = BASE_DIR / "docs" / "evaluation"
MODEL_PATH = MODEL_DIR / "risk_model_calibrated.pkl"
EXPLAINER_PATH = MODEL_DIR / "shap_explainer.pkl"

# --- Feature & Target Definition ---
FEATURES = [
    'miles_driven', 'night_driving_percentage', 'harsh_brakes_per_100mi',
    'rapid_accels_per_100mi', 'speeding_percentage', 'stop_go_events',
    'mean_speed', 'p50_speed'
]
TARGET = 'claim_in_30d'


def train_and_calibrate_model(X_train, y_train, X_calib, y_calib):
    """Trains a base model, then calibrates it, and returns both."""
    print("Training base XGBoost classifier...")
    base_model = xgb.XGBClassifier(
        objective='binary:logistic',
        use_label_encoder=False,
        eval_metric='logloss',
        random_state=42
    )
    base_model.fit(X_train, y_train)

    print("Calibrating model with Isotonic regression...")
    calibrated_model = CalibratedClassifierCV(base_model, method='isotonic', cv='prefit')
    calibrated_model.fit(X_calib, y_calib)
    return base_model, calibrated_model


def expected_calibration_error(y_true, y_prob, n_bins=10):
    """
    Calculates the Expected Calibration Error (ECE).
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        in_bin = np.logical_and(y_prob > bin_lower, y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
    return ece


def plot_lift_chart(y_true, y_pred_proba, ax):
    """
    Plots a decile lift chart.
    """
    results = pd.DataFrame({'y_true': y_true, 'y_pred_proba': y_pred_proba})
    results['decline'] = pd.qcut(results['y_pred_proba'], 10, labels=False, duplicates='drop')
    
    lift_data = results.groupby('decline')['y_true'].agg(['count', 'sum'])
    lift_data['lift'] = (lift_data['sum'] / lift_data['count']) / (results['y_true'].sum() / len(results))
    
    lift_data['lift'].plot(kind='bar', ax=ax)
    ax.set_title('Decile Lift Chart')
    ax.set_xlabel('Decile')
    ax.set_ylabel('Lift')
    ax.grid(axis='y', linestyle='--')



def evaluate_model(model, X_test, y_test):
    """Calculates metrics and generates evaluation plots."""
    print("\n--- Model Evaluation ---")
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    brier = brier_score_loss(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    ece = expected_calibration_error(y_test.to_numpy(), y_pred_proba)
    holdout_score_mean = np.mean(y_pred_proba)
    holdout_score_std = np.std(y_pred_proba)

    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  ROC AUC: {roc_auc:.4f}")
    print(f"  PR AUC: {pr_auc:.4f}")
    print(f"  Brier Score Loss: {brier:.4f} (lower is better)")
    print(f"  Expected Calibration Error (ECE): {ece:.4f}")
    print(f"  Holdout Score Mean: {holdout_score_mean:.4f}")
    print(f"  Holdout Score Std: {holdout_score_std:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    metrics = {
        "accuracy": accuracy,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_score_loss": brier,
        "ece": ece,
        "holdout_score_mean": holdout_score_mean,
        "holdout_score_std": holdout_score_std
    }
    metrics_path = BASE_DIR / "docs" / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)
    print(f"Saved metrics to {metrics_path}")

    print("Generating evaluation plots...")
    EVAL_DIR.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    RocCurveDisplay.from_estimator(model, X_test, y_test, ax=axes[0, 0], name='Calibrated Model')
    axes[0, 0].set_title('ROC Curve')
    
    PrecisionRecallDisplay.from_estimator(model, X_test, y_test, ax=axes[0, 1], name='Calibrated Model')
    axes[0, 1].set_title('Precision-Recall Curve')
    
    CalibrationDisplay.from_estimator(model, X_test, y_test, n_bins=10, ax=axes[1, 0], name='Calibrated Model')
    axes[1, 0].set_title('Calibration Curve')
    
    plot_lift_chart(y_test, y_pred_proba, ax=axes[1, 1])
    
    # Save decile lift table to CSV
    results = pd.DataFrame({'y_true': y_test, 'y_pred_proba': y_pred_proba})
    results['decline'] = pd.qcut(results['y_pred_proba'], 10, labels=False, duplicates='drop')
    lift_data = results.groupby('decline')['y_true'].agg(['count', 'sum'])
    lift_data['lift'] = (lift_data['sum'] / lift_data['count']) / (results['y_true'].sum() / len(results))
    decile_lift_table_path = EVAL_DIR / "decile_lift_table.csv"
    lift_data.to_csv(decile_lift_table_path)
    print(f"Saved decile lift table to {decile_lift_table_path}")

    plt.tight_layout()
    plot_path = EVAL_DIR / "evaluation_plots.png"
    plt.savefig(plot_path)
    print(f"Saved evaluation plots to {plot_path}")
    plt.close()

def main():
    """Main function to run the full training, calibration, and explainer creation pipeline."""
    print("--- Starting Full Pipeline: Train, Calibrate, Explain ---")
    
    # Load features and labels
    features_df = pd.read_parquet(FEATURES_DIR / "driver_features.parquet")
    labels_df = pd.read_parquet(BASE_DIR / "data" / "labels.parquet")
    
    # Merge features and labels
    df = pd.merge(features_df, labels_df, on="driver_id")
    
    X = df[FEATURES]
    y = df[TARGET]

    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)
    X_train, X_calib, y_train, y_calib = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full)

    print(f"Data split: {len(X_train)} train, {len(X_calib)} calibration, {len(X_test)} test samples.")

    base_model, calibrated_model = train_and_calibrate_model(X_train, y_train, X_calib, y_calib)

    print(f"\nSaving calibrated model to {MODEL_PATH}...")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(calibrated_model, f)

    print(f"Creating and saving SHAP explainer to {EXPLAINER_PATH}...")
    # THIS IS THE FIX: Provide the background dataset (X_train) to the explainer
    explainer = shap.TreeExplainer(base_model, X_train)
    with open(EXPLAINER_PATH, "wb") as f:
        pickle.dump(explainer, f)

    evaluate_model(calibrated_model, X_test, y_test)

    print("\n--- Pipeline Complete ---")

if __name__ == "__main__":
    main()