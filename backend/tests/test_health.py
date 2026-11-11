from fastapi.testclient import TestClient

from app.main import app

def test_health_check():
    with TestClient(app) as client:
        response  = client.get("/health")
    
    assert response.status_code  == 200 
    
    response_data = response.json()
    
    assert response_data == {'status': 'ok'}