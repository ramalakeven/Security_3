import requests

BASE = "http://127.0.0.1:8000"

def test_idor():
    r = requests.get(BASE + "/files/2", headers={"X-User": "alice"})
    assert r.status_code == 404

def test_access():
    r = requests.get(BASE + "/files/1", headers={"X-User": "alice"})
    assert r.status_code == 200

def test_admin_delete():
    r = requests.delete(BASE + "/files/2", headers={"X-User": "admin"})
    assert r.status_code == 200

    r2 = requests.get(BASE + "/files/2", headers={"X-User": "admin"})
    assert r2.status_code == 404

if __name__ == "__main__":
    test_idor()
    test_access()
    test_admin_delete()
    print("ALL TESTS PASSED")
