from fastapi.testclient import TestClient

from project1.app import app

client = TestClient(app)

def test_add_user():
    response = client.post(
        "/users/add_user",
        json={"username":"user", "password":"user!"},
    )
    assert response.status_code == 200
    assert response.json() == {
        null
    }
def test_authenticate_user():
    response = client.post(
        "/users/authenticate_user",
        json={"username":"user", "password":"user!"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "access_tocken":access_tocken
    }
def test_calculate_percents():
    response = client.post(
        "/percents/calculate_percents",
        json={"value":"100", "percent":"10"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "added":"110","subtracted":"90","percent":"10"
    }


