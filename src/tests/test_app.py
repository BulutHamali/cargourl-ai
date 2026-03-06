import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_optimize_requires_api_key(client):
    response = client.post('/optimize', json={'clicks': []})
    assert response.status_code == 401


def test_optimize_returns_fields(client, monkeypatch):
    monkeypatch.setenv('FLASK_API_KEY', 'test-key')
    response = client.post(
        '/optimize',
        json={'clicks': []},
        headers={'X-API-Key': 'test-key'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'optimalTime' in data
    assert 'targetAudience' in data
    assert 'ctr' in data
    assert 'ctrDelta' in data
    assert 'baselineCtr' in data


def test_optimize_with_click_data(client, monkeypatch):
    monkeypatch.setenv('FLASK_API_KEY', 'test-key')
    clicks = [
        {'click_time': '2024-06-01T14:30:00', 'location': 'US', 'platform': 'Instagram', 'impressions': 500},
        {'click_time': '2024-06-02T19:00:00', 'location': 'US', 'platform': 'Instagram', 'impressions': 300},
        {'click_time': '2024-06-03T12:00:00', 'location': 'UK', 'platform': 'Twitter',   'impressions': 200},
    ]
    response = client.post(
        '/optimize',
        json={'clicks': clicks},
        headers={'X-API-Key': 'test-key'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['targetAudience'] is not None
    assert data['ctr'] is not None
    assert isinstance(data['ctr'], float)
