
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

# --- Page Configuration ---
st.set_page_config(
    page_title="Telematics UBI Dashboard",
    page_icon="🚗",
    layout="wide"
)

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000"
API_TOKEN = os.getenv("API_TOKEN", "your_default_api_token") # Fallback for local testing
FEATURES_PATH = Path(__file__).parent.parent.parent / "data" / "features" / "driver_features.parquet"

# --- Helper Functions ---
@st.cache_data
def get_driver_ids():
    """Load driver IDs from the features file to populate the dropdown."""
    if not FEATURES_PATH.exists():
        st.error(f"Feature file not found at {FEATURES_PATH}. Please run the feature engineering script.")
        return []
    df = pd.read_parquet(FEATURES_PATH)
    return sorted(df['driver_id'].unique())

@st.cache_data
def load_feature_data():
    """Load the entire driver features dataframe and cache it."""
    if not FEATURES_PATH.exists():
        return None
    df = pd.read_parquet(FEATURES_PATH)
    return df

def get_risk_score(driver_id):
    """Call the FastAPI to get the risk score for a driver."""
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.post(f"{API_BASE_URL}/score", json={"driver_id": driver_id}, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the API. Please ensure the API server is running and accessible. Error: {e}")
        return None

def get_premium(driver_id, base_premium):
    """Call the FastAPI to get the premium for a driver."""
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try:
        response = requests.post(f"{API_BASE_URL}/price", json={"driver_id": driver_id, "base_premium": base_premium}, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to the API. Please ensure the API server is running and accessible. Error: {e}")
        return None

# --- UI Layout ---
st.title("Driver Risk & Premium Dashboard")
st.markdown("Select a driver to view their risk score, key behaviors, and estimated premium.")

# --- Main Panel ---
features_df = load_feature_data()
if features_df is None:
    st.warning("No feature data found. Please run the data simulation and feature engineering scripts.")
else:
    driver_ids = sorted(features_df['driver_id'].unique())
    selected_driver = st.selectbox("Select Driver ID", driver_ids)

    if st.button("Analyze Driver Risk"):
        if selected_driver:
            with st.spinner(f"Analyzing risk for {selected_driver}..."):
                score_data = get_risk_score(int(selected_driver))
            
            if score_data:
                risk_score = score_data.get('risk_score', 0)
                top_features = score_data.get('top_features', [])

                st.header(f"Risk Profile for: `{selected_driver}`")
                
                col1, col2 = st.columns(2)

                with col1:
                    # --- Risk Score Gauge ---
                    st.subheader("Driver Risk Score")
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = risk_score * 100,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Score (0-100)"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "#2ca02c" if risk_score < 0.4 else ("#ff7f0e" if risk_score < 0.7 else "#d62728")},
                            'steps' : [
                                {'range': [0, 40], 'color': "lightgreen"},
                                {'range': [40, 70], 'color': "lightyellow"},
                                {'range': [70, 100], 'color': "lightcoral"}]}))
                    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # --- Premium Estimation ---
                    st.subheader("Dynamic Premium Estimation")
                    base_premium = 100.0 # Monthly base premium in USD
                    
                    premium_data = get_premium(int(selected_driver), base_premium)

                    if premium_data:
                        premium = premium_data.get('premium', base_premium)
                        delta = premium_data.get('delta', 0)

                        st.metric("Estimated Monthly Premium", f"${premium:.2f}", delta=f"{delta:.2f}")
                        st.slider(
                            "Simulate Score Change vs. Premium", 
                            min_value=0.0, max_value=1.0, value=risk_score, disabled=True, 
                            help="This shows the current score's impact on premium."
                        )
                        st.markdown(f"A score of **{risk_score*100:.0f}** results in a premium of **${premium:.2f}**. Lower scores lead to lower premiums.")
                    else:
                        st.warning("Could not retrieve premium data.")

                # --- Achievements ---
                st.divider()
                st.subheader("Your Achievements")
                driver_data = features_df[features_df['driver_id'] == int(selected_driver)].iloc[-1]
                
                badges_earned = []
                
                if risk_score < 0.1:
                    badges_earned.append(("🏆 Top Performer", "Your risk score is in the top tier of safe drivers."))
                
                if driver_data.get('harsh_brakes_per_100mi', 1) == 0 and driver_data.get('rapid_accels_per_100mi', 1) == 0:
                    badges_earned.append(("✨ Smooth Operator", "No harsh braking or acceleration events recorded."))
                
                if driver_data.get('speeding_percentage', 1) < 0.05:
                    badges_earned.append(("🛡️ Safe Speeder", "You consistently drive within speed limits."))

                if not badges_earned:
                    st.info("No badges earned in the last 30 days. Keep driving safely to earn them!")
                else:
                    cols = st.columns(len(badges_earned))
                    for i, (badge_text, badge_desc) in enumerate(badges_earned):
                        with cols[i]:
                            st.success(badge_text)
                            st.caption(badge_desc)

                st.divider()

                # --- Peer Comparison Feedback ---
                st.subheader("Your Driving Analysis vs. Peers")

                if not top_features:
                    st.success("✅ Your driving behavior is in line with the safest drivers. Keep up the great work!")
                else:
                    st.write("Here's how your driving habits compare to the average driver. These are the main factors influencing your score.")
                    for item in top_features:
                        if isinstance(item, dict):
                            feature_name = item.get('feature', 'N/A').replace('_', ' ').title()
                            driver_value = item.get('value', 0)
                            avg_value = item.get('average', 0)
                            
                            if avg_value > 0.001: # Avoid division by zero
                                percent_diff = ((driver_value - avg_value) / avg_value) * 100
                            else:
                                percent_diff = driver_value * 100

                            if percent_diff > 10:
                                st.warning(f"**{feature_name}:** Your behavior is **{percent_diff:.0f}% higher** than the average driver.")
                            elif percent_diff < -10:
                                 st.success(f"**{feature_name}:** Your behavior is **{-percent_diff:.0f}% lower** than the average driver.")
                        else:
                            st.error("Received an unexpected data format for top features.")
                            break
