from flask import Flask, request, jsonify
from sklearn.cluster import KMeans
import pandas as pd
from prophet import Prophet
import requests
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'CargoURL AI API is running!', 'status': 'healthy'})

@app.route('/optimize', methods=['POST'])
def optimize():
    # API Key Check
    if request.headers.get('X-API-Key') != os.getenv('FLASK_API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        data = request.json.get('clicks', [])
        df = pd.DataFrame(data)
        
        # Posting Time Prediction
        optimal_time = '7 PM weekdays'
        if not df.empty and 'click_time' in df.columns:
            df['ds'] = pd.to_datetime(df['click_time'])
            df['y'] = 1
            model = Prophet()
            model.fit(df[['ds', 'y']])
            future = model.make_future_dataframe(periods=7)
            forecast = model.predict(future)
            best_time = forecast[forecast['yhat'] == forecast['yhat'].max()]['ds'].iloc[0]
            optimal_time = best_time.strftime('%I %p weekdays')
        
        # Audience Targeting
        target_audience = 'US Instagram users'
        if not df.empty and 'location' in df.columns and 'platform' in df.columns:
            # Convert categorical data to numerical for clustering
            location_encoded = pd.factorize(df['location'].fillna('Unknown'))[0]
            platform_encoded = pd.factorize(df['platform'].fillna('Unknown'))[0]
            
            if len(df) >= 3:  # Need at least 3 data points for clustering
                cluster_data = list(zip(location_encoded, platform_encoded))
                kmeans = KMeans(n_clusters=min(3, len(df)), random_state=42)
                df['cluster'] = kmeans.fit_predict(cluster_data)
                top_segment = df['cluster'].mode().iloc[0]
                target_audience = 'US Instagram users' if top_segment == 0 else 'Global Social Media users'
        
        # Description Rewriting
        description = 'Discover our #ProductLaunch with #SummerSale deals!'
        try:
            twitter_api_key = os.getenv("TWITTER_API_KEY")
            if twitter_api_key:
                trends = requests.get(
                    'https://api.twitter.com/2/trends/place/1', 
                    headers={'Authorization': f'Bearer {twitter_api_key}'},
                    timeout=5
                ).json()
                keywords = [trend['name'] for trend in trends.get('trends', [])[:2]]
                if keywords:
                    description = f"Discover our #ProductLaunch with #{keywords[0].replace('#', '')} deals!"
        except Exception as e:
            print(f"Twitter API error: {e}")
            pass
        
        # CTR Calculation
        impressions = df['impressions'].sum() if not df.empty and 'impressions' in df.columns else 1000
        clicks = len(df) if not df.empty else 100
        manual_ctr = 10
        ai_ctr = (clicks / impressions) * 100 if impressions > 0 else manual_ctr
        ctr_improvement = ((ai_ctr - manual_ctr) / manual_ctr * 100)
        
        return jsonify({
            'optimalTime': optimal_time,
            'targetAudience': target_audience,
            'description': description,
            'ctrImprovement': f'{ctr_improvement:.2f}% higher than manual posting'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)