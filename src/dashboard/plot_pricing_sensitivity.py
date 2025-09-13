import yaml
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Define base directory
BASE_DIR = Path(__file__).parent.parent.parent

# Path to pricing configuration
PRICING_CONFIG_PATH = BASE_DIR / "src" / "config" / "pricing_config.yaml"
METRICS_PATH = BASE_DIR / "docs" / "metrics.json"

def calculate_premium(base_premium, score, alpha, min_cap, max_cap, score_mu, score_sigma):
    """Calculates the insurance premium based on risk score and pricing parameters."""
    premium = base_premium * (1 + alpha * (score - score_mu) / score_sigma)
    clamped_premium = max(min_cap, min(premium, max_cap))
    return clamped_premium

def generate_pricing_sensitivity_plot():
    # Load pricing parameters
    try:
        with open(PRICING_CONFIG_PATH, 'r') as f:
            pricing_config = yaml.safe_load(f)
        pricing_params = pricing_config.get("pricing", {})
        alpha = pricing_params["alpha"]
        min_cap = pricing_params["min_cap"]
        max_cap = pricing_params["max_cap"]
    except Exception as e:
        print(f"Error loading pricing configuration: {e}")
        return

    # Load score statistics (mu and sigma)
    try:
        with open(METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        score_mu = metrics["holdout_score_mean"]
        score_sigma = metrics["holdout_score_std"]
    except Exception as e:
        print(f"Error loading metrics: {e}")
        return

    base_premium = 100.0  # Example base premium
    risk_scores = np.linspace(0, 1, 100)  # Risk scores from 0 to 1

    premiums = [
        calculate_premium(base_premium, score, alpha, min_cap, max_cap, score_mu, score_sigma)
        for score in risk_scores
    ]

    plt.figure(figsize=(10, 6))
    plt.plot(risk_scores, premiums, label=f'Alpha: {alpha}, Min Cap: {min_cap}, Max Cap: {max_cap}')
    plt.axhline(y=min_cap, color='r', linestyle='--', label='Min Cap')
    plt.axhline(y=max_cap, color='g', linestyle='--', label='Max Cap')

    plt.title('Pricing Sensitivity to Risk Score')
    plt.xlabel('Risk Score')
    plt.ylabel('Calculated Premium')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Save the plot
    plot_path = BASE_DIR / "docs" / "evaluation" / "pricing_sensitivity_plot.png"
    plt.savefig(plot_path)
    print(f"Pricing sensitivity plot saved to {plot_path}")

if __name__ == "__main__":
    import json # Import json here as it's only used in main or this function
    generate_pricing_sensitivity_plot()
