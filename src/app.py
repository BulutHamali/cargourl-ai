from flask import Flask, request, jsonify
from sklearn.cluster import KMeans
import pandas as pd
from prophet import Prophet
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'CargoURL AI API is running!', 'status': 'healthy'})

@app.route('/optimize', methods=['POST'])
def optimize():
    # API Key Check
    api_key = os.getenv('FLASK_API_KEY')
    if not api_key or request.headers.get('X-API-Key') != api_key:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        data = request.json.get('clicks', [])
        df = pd.DataFrame(data)
        
        # Posting Time Prediction
        optimal_time = None
        if not df.empty and 'click_time' in df.columns:
            df['ds'] = pd.to_datetime(df['click_time'])
            df['y'] = 1
            model = Prophet()
            model.fit(df[['ds', 'y']])
            future = model.make_future_dataframe(periods=7)
            forecast = model.predict(future)
            best_time = forecast[forecast['yhat'] == forecast['yhat'].max()]['ds'].iloc[0]
            optimal_time = best_time.strftime('%A %I %p')
        
        # Audience Targeting
        target_audience = None
        if not df.empty and 'location' in df.columns and 'platform' in df.columns:
            # Convert categorical data to numerical for clustering
            location_encoded = pd.factorize(df['location'].fillna('Unknown'))[0]
            platform_encoded = pd.factorize(df['platform'].fillna('Unknown'))[0]

            if len(df) >= 3:  # Need at least 3 data points for clustering
                cluster_data = list(zip(location_encoded, platform_encoded))
                kmeans = KMeans(n_clusters=min(3, len(df)), random_state=42)
                df['cluster'] = kmeans.fit_predict(cluster_data)
                top_cluster = df['cluster'].mode().iloc[0]
                top_rows = df[df['cluster'] == top_cluster]
                top_location = top_rows['location'].mode().iloc[0]
                top_platform = top_rows['platform'].mode().iloc[0]
                target_audience = f'{top_location} {top_platform} users'
        
        # Description suggestions via trend keywords — planned feature
        description = None
        
        # CTR Calculation
        # baseline_ctr is an optional request field (default 2.0%); used for delta reporting only
        baseline_ctr = float(request.json.get('baseline_ctr', 2.0))
        ctr = None
        ctr_delta = None
        if not df.empty and 'impressions' in df.columns:
            impressions = df['impressions'].sum()
            clicks = len(df)
            if impressions > 0:
                ctr = round((clicks / impressions) * 100, 2)
                ctr_delta = round(ctr - baseline_ctr, 2)

        return jsonify({
            'optimalTime': optimal_time,
            'targetAudience': target_audience,
            'description': description,
            'ctr': ctr,
            'ctrDelta': ctr_delta,
            'baselineCtr': baseline_ctr
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)