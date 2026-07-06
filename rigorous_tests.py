from fastapi.testclient import TestClient
from api.main import app, ip_registration_tracker
from api.database import Base, engine, get_db
from sqlalchemy.orm import sessionmaker
import uuid

# Use a separate in-memory SQLite database for testing
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_registration_and_anti_alt():
    print("[TEST] Running Registration & Anti-Alt Tests...")
    
    # Clean state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    ip_registration_tracker.clear()
    
    unique_email = f"test_{uuid.uuid4().hex[:6]}@example.com"
    unique_username = f"user_{uuid.uuid4().hex[:6]}"
    
    # 1. Successful Registration
    res = client.post("/api/register", json={
        "username": unique_username,
        "email": unique_email,
        "password": "strongpassword123",
        "device_fingerprint": "device_1"
    })
    
    assert res.status_code == 200, f"Failed to register: {res.text}"
    data = res.json()
    assert data["username"] == unique_username
    assert "qr_code_string" in data
    print("  [+] Successful Registration Verified. QR Code:", data["qr_code_string"])
    
    # 2. Anti-Alt IP Rate Limit Check
    res_alt_ip = client.post("/api/register", json={
        "username": "another_user",
        "email": "another@example.com",
        "password": "password123"
    })
    
    assert res_alt_ip.status_code == 429, "Anti-Alt IP Limit Failed!"
    print("  [+] Anti-Alt IP Rate Limiting Verified.")
    
    # Clear IP tracker to test device fingerprint
    ip_registration_tracker.clear()
    
    # 3. Anti-Alt Device Fingerprint Check
    res_alt_device = client.post("/api/register", json={
        "username": "different_user",
        "email": "different@example.com",
        "password": "password123",
        "device_fingerprint": "device_1"
    })
    
    assert res_alt_device.status_code == 403, "Anti-Alt Device Fingerprint Failed!"
    print("  [+] Anti-Alt Device Fingerprinting Verified.")
    
    return data["id"], data["qr_code_string"], unique_email

def test_login(email):
    print("\n[TEST] Running Login Tests...")
    res = client.post("/api/login", json={
        "email": email,
        "password": "strongpassword123"
    })
    assert res.status_code == 200, "Login Failed!"
    print("  [+] Successful Login Verified.")

def test_friend_adding(user1_id, user1_qr):
    print("\n[TEST] Running Friend System Tests...")
    ip_registration_tracker.clear()
    
    # Create User 2
    res2 = client.post("/api/register", json={
        "username": "user2_test",
        "email": "user2@example.com",
        "password": "password123",
        "device_fingerprint": "device_2"
    })
    assert res2.status_code == 200
    user2_id = res2.json()["id"]
    
    # User 2 adds User 1 via QR Code
    add_res = client.post(f"/api/add_friend?user_id={user2_id}&target_identifier={user1_qr}&by_qr=true")
    assert add_res.status_code == 200, f"Failed to add friend: {add_res.text}"
    print("  [+] Adding Friend via QR Code Verified.")

if __name__ == "__main__":
    print("="*50)
    print("  CIPHER - RIGOROUS API TESTING")
    print("="*50)
    try:
        u1_id, u1_qr, u1_email = test_registration_and_anti_alt()
        test_login(email=u1_email)
        test_friend_adding(u1_id, u1_qr)
        print("\n[+] ALL TESTS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"Test failed with error: {e}")
