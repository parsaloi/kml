import time
import logging
import requests
import pandas as pd
import numpy as np
from prophet import Prophet
from prometheus_client import start_http_server, Gauge

# Suppress Prophet's chatty cmdline output
logging.getLogger('cmdstanpy').setLevel(logging.WARNING)

PROMETHEUS_URL = "http://prometheus-server.monitoring.svc.cluster.local/api/v1/query"
PREDICTED_QPS_GAUGE = Gauge("app_predicted_qps_5m_ahead", "Predicted QPS 5 minutes ahead from ML model")

def generate_synthetic_history(days=7):
    """Generates synthetic telemetry with daily and weekly seasonality."""
    now = pd.Timestamp.now()
    dates = pd.date_range(end=now, periods=days * 24 * 60, freq='1min')
    df = pd.DataFrame({'ds': dates})
    
    # Base load
    df['y'] = 15.0 
    
    # Daily seasonality: Traffic spikes between 8 AM and 10 AM
    hours = df['ds'].dt.hour
    df['y'] += np.where((hours >= 8) & (hours <= 10), 60, 0)
    
    # Weekly seasonality: Drop traffic by 50% on weekends (Saturday=5, Sunday=6)
    weekdays = df['ds'].dt.dayofweek
    df['y'] = np.where(weekdays >= 5, df['y'] * 0.5, df['y'])
    
    # Add random noise
    df['y'] += np.random.normal(0, 3, len(df))
    df['y'] = df['y'].clip(lower=1) # Ensure no negative QPS
    
    return df

# Initialize the rolling dataframe with 7 days of synthetic data
history_df = generate_synthetic_history()

def fetch_current_qps():
    query = 'sum(rate(nginx_http_requests_total[1m])) or vector(15)'
    try:
        response = requests.get(PROMETHEUS_URL, params={'query': query}, timeout=5)
        results = response.json()['data']['result']
        if results:
            return float(results[0]['value'][1])
    except Exception as e:
        pass
    return 15.0 

def run_forecast():
    global history_df
    current_qps = fetch_current_qps()
    now = pd.Timestamp.now()
    
    # Append the real-time live observation
    new_row = pd.DataFrame([{"ds": now, "y": current_qps}])
    history_df = pd.concat([history_df, new_row], ignore_index=True)
    
    # Prune to keep exactly the last 7 days of data to prevent memory leaks
    history_df = history_df.tail(7 * 24 * 60)
    
    # Fit Facebook Prophet (optimized for speed)
    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=True,
        mcmc_samples=0 # Fast MAP estimation
    )
    model.fit(history_df)
    
    # Predict exactly 5 minutes into the future
    future = model.make_future_dataframe(periods=5, freq='1min')
    forecast = model.predict(future)
    
    predicted_qps = max(10.0, float(forecast.iloc[-1]['yhat']))
    
    print(f"[{now.strftime('%H:%M:%S')}] Live QPS: {current_qps:.2f} | Predicted QPS (+5m): {predicted_qps:.2f}")
    PREDICTED_QPS_GAUGE.set(predicted_qps)

if __name__ == "__main__":
    start_http_server(8000)
    print("KML Prophet Forecaster listening on port :8000")
    while True:
        run_forecast()
        time.sleep(30)
