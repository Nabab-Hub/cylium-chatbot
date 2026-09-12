"""
Automated Test Suite for CyliumOS Gemini RAG Chatbot API.
Tests:
1. Health & Service Info Endpoints
2. Gemini RAG Chat Endpoint (Anonymous Guest)
3. Multi-turn Session Memory (Follow-up Question)
4. Authenticated User Chat with X-User-Id
5. Action Chip Suggestions
6. Server-Sent Events (SSE) Streaming
"""

import sys
import json

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("RUNNING CYLIUMOS CHATBOT API TEST SUITE")
    print("=" * 60)

    # -------------------------------------------------------------
    # Test 1: Service Root & Healthcheck
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing GET / and GET /health...")
    res_root = client.get("/")
    assert res_root.status_code == 200, f"Root failed: {res_root.text}"
    print("  -> Root endpoint status:", res_root.status_code, res_root.json().get("service"))

    res_health = client.get("/health")
    assert res_health.status_code == 200, f"Healthcheck failed: {res_health.text}"
    health_data = res_health.json()
    print("  -> Health status:", health_data.get("status"))
    print("  -> LLM Provider:", health_data.get("llm_provider"))
    print("  -> Model:", health_data.get("model"))
    print("  -> LLM Ready:", health_data.get("llm_ready"))
    print("  -> Firebase Connected:", health_data.get("firebase_connected"))

    # -------------------------------------------------------------
    # Test 2: Anonymous Guest Chat (General CyliumOS query)
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing POST /api/v1/chat (Anonymous Guest)...")
    prompt = "What services does CyliumOS offer and how does pricing work?"
    chat_payload = {
        "message": prompt,
    }
    res_chat = client.post("/api/v1/chat", json=chat_payload)
    print("  -> Status code:", res_chat.status_code)
    assert res_chat.status_code == 200, f"Chat failed: {res_chat.text}"
    chat_data = res_chat.json()
    session_id = chat_data.get("session_id")
    response_text = chat_data.get("response")
    actions = chat_data.get("actions", [])

    print(f"  -> Generated Session ID: {session_id}")
    print(f"  -> Response preview (first 200 chars):\n     {response_text[:200]}...")
    print(f"  -> Suggested Actions: {[a.get('label') for a in actions]}")
    assert session_id is not None
    assert len(response_text) > 20
    assert len(actions) > 0

    # -------------------------------------------------------------
    # Test 3: Multi-turn Context Memory (Using existing session_id)
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Multi-turn conversation memory with session_id...")
    follow_up_payload = {
        "session_id": session_id,
        "message": "Which of those services supports bounding box coordinates?",
    }
    res_followup = client.post("/api/v1/chat", json=follow_up_payload)
    print("  -> Follow-up status code:", res_followup.status_code)
    assert res_followup.status_code == 200, f"Follow-up failed: {res_followup.text}"
    followup_data = res_followup.json()
    followup_text = followup_data.get("response")
    print(f"  -> Follow-up response preview:\n     {followup_text[:200]}...")
    # Verify it references NSFW or detection coordinates
    assert any(k in followup_text.lower() for k in ["nsfw", "bounding", "detection_point", "detector"])

    # -------------------------------------------------------------
    # Test 4: Authenticated User Chat (X-User-Id)
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Authenticated User Chat with X-User-Id...")
    auth_payload = {
        "message": "Hello, can you tell me what my account benefits and API key options are?",
    }
    res_auth = client.post(
        "/api/v1/chat",
        json=auth_payload,
        headers={"X-User-Id": "test_user_demo_123"},
    )
    print("  -> Auth Chat status code:", res_auth.status_code)
    assert res_auth.status_code == 200, f"Auth chat failed: {res_auth.text}"
    auth_data = res_auth.json()
    print("  -> Is Authenticated:", auth_data.get("is_authenticated"))
    print(f"  -> Response preview:\n     {auth_data.get('response')[:200]}...")
    assert auth_data.get("is_authenticated") is True

    # -------------------------------------------------------------
    # Test 5: SSE Streaming Chat (stream=true)
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing POST /api/v1/chat (Server-Sent Events streaming)...")
    stream_payload = {
        "message": "Explain the zero-retention privacy policy in one sentence.",
        "stream": True,
    }
    res_stream = client.post("/api/v1/chat", json=stream_payload)
    print("  -> Stream status code:", res_stream.status_code)
    print("  -> Content-Type:", res_stream.headers.get("content-type"))
    assert res_stream.status_code == 200
    assert "text/event-stream" in res_stream.headers.get("content-type")
    
    stream_lines = res_stream.text.split("\n\n")
    valid_events = [l for l in stream_lines if l.startswith("data:")]
    print(f"  -> Received {len(valid_events)} SSE chunk events.")
    assert len(valid_events) > 1

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! CHATBOT IS 100% OPERATIONAL.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        run_tests()
    except Exception as exc:
        print("\nTEST FAILED:", exc)
        sys.exit(1)
