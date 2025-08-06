from flask import Flask, request, jsonify
from sklearn.cluster import KMeans
import pandas as pd
from prophet import Prophet
import requests
import os

app = Flask(__name__)

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        # Receive click data from Supabase Edge Function
        data = request.json['clicks']
        df = pd.DataFrame(data)

        # Posting Time Prediction (Prophet)
        optimal_time = '7 PM weekdays'  # Fallback if no data
        if not df.empty and 'click_time' in df:
            df['ds'] = pd.to_datetime(df['click_time'])
            df['y'] = 1  # Dummy value for click events
            model = Prophet()
            model.fit(df[['ds', 'y']])
            future = model.make_future_dataframe(periods=7)
            forecast = model.predict(future)
            best_time = forecast[forecast['yhat'] == forecast['yhat'].max()]['ds'].iloc[0]
            optimal_time = best_time.strftime('%I %p weekdays')

        # Audience Targeting (scikit-learn)
        target_audience = 'US Instagram users'  # Fallback
        if not df.empty and 'location' in df and 'platform' in df:
            kmeans = KMeans(n_clusters=3)
            df['cluster'] = kmeans.fit_predict(df[['location', 'platform']].fillna('Unknown'))
            top_segment = df['cluster'].mode().iloc[0]
            target_audience = 'US Instagram users' if top_segment == 0 else 'Other'

        # Description Rewriting (Twitter API)
        description = 'Discover our #ProductLaunch with #SummerSale deals!'  # Fallback
        try:
            trends = requests.get('https://api.twitter.com/2/trends/place/1', headers={
                'Authorization': f'Bearer {os.getenv("TWITTER_API_KEY")}'
            }).json()
            keywords = [trend['name'] for trend in trends.get('trends', [])[:2]]
            if keywords:
                description = f"Discover our #ProductLaunch with #{keywords[0]} deals!"
        except:
            pass

        # CTR Calculation
        impressions = df['impressions'].sum() if not df.empty else 1000
        clicks = len(df) if not df.empty else 100
        manual_ctr = 10  # Baseline CTR (assumed)
        ai_ctr = (clicks / impressions) * 100 if impressions else manual_ctr
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
    app.run(host='0.0.0.0', port=5000)