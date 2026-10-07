import time
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("=" * 65)
    print("  BULK CERTIFICATE GENERATOR - END-TO-END DEMO")
    print("=" * 65)

    # 1. Health Check
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=3)
        if r.status_code != 200:
            print("API server is not reachable at http://127.0.0.1:8000. Start it with:")
            print("  python -m uvicorn app.main:app --reload")
            return
    except Exception as e:
        print(f"Error connecting to {BASE_URL}: {e}")
        print("Please start the server first: python -m uvicorn app.main:app")
        return

    # 2. Submit Bulk Generation Job
    payload = {
        "event_name": "Full Stack & Cloud Architecture Masterclass",
        "issue_date": "2026-10-07",
        "issuer_name": "Global Tech Institute",
        "issuer_title": "Dean of Engineering",
        "custom_message": "for successfully completing the comprehensive 12-week program with distinction.",
        "recipients": [
            {"name": "Alice Johnson", "email": "alice.j@example.com"},
            {"name": "Bob Smith", "email": "bob.s@example.com"},
            {"name": "Charlie Davis", "email": "charlie.d@example.com"},
            {"name": "Diana Prince", "email": "diana.p@example.com"}
        ]
    }

    print("\n[1] Submitting bulk certificate request for 4 recipients...")
    resp = httpx.post(f"{BASE_URL}/api/certificates/generate", json=payload)
    print(f"Status Code: {resp.status_code}")
    job_info = resp.json()
    job_id = job_info["job_id"]
    print(f"Created Job ID: {job_id}")
    print(f"Initial Status: {job_info['status']}")

    # 3. Polling for Completion
    print("\n[2] Polling job status...")
    max_wait = 20
    start = time.time()
    job_status = None

    while time.time() - start < max_wait:
        r = httpx.get(f"{BASE_URL}/api/jobs/{job_id}")
        job_status = r.json()
        print(f"  > Status: {job_status['status']} | Progress: {job_status['progress_percentage']}% "
              f"({job_status['successful_count']}/{job_status['total_recipients']} completed)")
        if job_status["status"] in ["COMPLETED", "PARTIALLY_COMPLETED", "FAILED"]:
            break
        time.sleep(1)

    # 4. Show Details & Download Link
    print("\n[3] Job Generation Complete!")
    print(f"Final Status: {job_status['status']}")
    print("Recipients & Generated Certificates:")
    for cert in job_status.get("certificates", []):
        print(f"  • {cert['recipient_name']} ({cert['recipient_email']})")
        print(f"    Code: {cert['certificate_code']} | Status: {cert['status']}")
        if cert.get("download_url"):
            print(f"    Download: {BASE_URL}{cert['download_url']}")

    # 5. Download ZIP archive
    zip_url = f"{BASE_URL}/api/jobs/{job_id}/download-zip"
    print(f"\n[4] Batch ZIP download URL:")
    print(f"    {zip_url}")
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
