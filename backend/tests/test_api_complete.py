"""
Spine CRM - Complete API Test Suite
Tests all endpoints and generates HTML report
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER = {
    "email": "test_api@test.com",
    "password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "API"
}

# Results storage
test_results = []
access_token = None


class Colors:
    """Terminal colors"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_test(name: str, passed: bool, details: str = ""):
    """Log test result"""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"{status} | {name}")
    if details and not passed:
        print(f"     {Colors.YELLOW}{details}{Colors.RESET}")
    
    test_results.append({
        "name": name,
        "passed": passed,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })


def test_health_check():
    """Test health endpoints"""
    print(f"\n{Colors.BOLD}=== HEALTH CHECKS ==={Colors.RESET}")
    
    # Test root endpoint
    try:
        r = requests.get(f"{BASE_URL}/")
        log_test("GET / (Root)", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_test("GET / (Root)", False, str(e))
    
    # Test health endpoint
    try:
        r = requests.get(f"{BASE_URL}/health")
        log_test("GET /health", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_test("GET /health", False, str(e))


def test_auth():
    """Test authentication endpoints"""
    global access_token
    print(f"\n{Colors.BOLD}=== AUTHENTICATION ==={Colors.RESET}")
    
    # Test registration
    try:
        r = requests.post(f"{BASE_URL}/api/auth/register", json=TEST_USER)
        if r.status_code in [200, 201, 400]:  # 400 if already exists
            log_test("POST /api/auth/register", True, f"Status: {r.status_code}")
        else:
            log_test("POST /api/auth/register", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        log_test("POST /api/auth/register", False, str(e))
    
    # Test login
    try:
        r = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={
                "username": TEST_USER["email"],
                "password": TEST_USER["password"]
            }
        )
        if r.status_code == 200:
            data = r.json()
            access_token = data.get("access_token")
            log_test("POST /api/auth/login", access_token is not None, f"Got token: {bool(access_token)}")
        else:
            log_test("POST /api/auth/login", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        log_test("POST /api/auth/login", False, str(e))
    
    # Test get current user
    if access_token:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            r = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
            log_test("GET /api/auth/me", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log_test("GET /api/auth/me", False, str(e))


def get_headers():
    """Get auth headers"""
    return {"Authorization": f"Bearer {access_token}"}


def test_products():
    """Test product endpoints"""
    print(f"\n{Colors.BOLD}=== PRODUCTS ==={Colors.RESET}")
    
    if not access_token:
        log_test("Products", False, "No access token - skipping")
        return None
    
    headers = get_headers()
    product_id = None
    
    # Create product
    try:
        product_data = {
            "item_number": "TEST-001",
            "name": "Test Product",
            "short_description": "Test description"
        }
        r = requests.post(f"{BASE_URL}/api/products/", json=product_data, headers=headers)
        if r.status_code in [200, 201, 400]:  # 400 if already exists
            if r.status_code in [200, 201]:
                product_id = r.json().get("id")
            log_test("POST /api/products/", True, f"Status: {r.status_code}")
        else:
            log_test("POST /api/products/", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        log_test("POST /api/products/", False, str(e))
    
    # List products
    try:
        r = requests.get(f"{BASE_URL}/api/products/", headers=headers)
        log_test("GET /api/products/", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200 and not product_id:
            products = r.json()
            if products:
                product_id = products[0]["id"]
    except Exception as e:
        log_test("GET /api/products/", False, str(e))
    
    # Get single product
    if product_id:
        try:
            r = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=headers)
            log_test(f"GET /api/products/{product_id}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log_test(f"GET /api/products/{product_id}", False, str(e))
    
    # Update product
    if product_id:
        try:
            update_data = {"name": "Updated Test Product"}
            r = requests.patch(f"{BASE_URL}/api/products/{product_id}", json=update_data, headers=headers)
            log_test(f"PATCH /api/products/{product_id}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log_test(f"PATCH /api/products/{product_id}", False, str(e))
    
    return product_id


def test_prospects(product_id: int = None):
    """Test prospect endpoints"""
    print(f"\n{Colors.BOLD}=== PROSPECTS ==={Colors.RESET}")
    
    if not access_token:
        log_test("Prospects", False, "No access token - skipping")
        return None
    
    headers = get_headers()
    prospect_id = None
    
    # Create prospect
    try:
        prospect_data = {
            "email": "test.prospect@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "company_name": "Test Company",
            "product_interest_ids": [product_id] if product_id else []
        }
        r = requests.post(f"{BASE_URL}/api/prospects/", json=prospect_data, headers=headers)
        if r.status_code in [200, 201, 400]:
            if r.status_code in [200, 201]:
                prospect_id = r.json().get("id")
            log_test("POST /api/prospects/", True, f"Status: {r.status_code}")
        else:
            log_test("POST /api/prospects/", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        log_test("POST /api/prospects/", False, str(e))
    
    # List prospects
    try:
        r = requests.get(f"{BASE_URL}/api/prospects/", headers=headers)
        log_test("GET /api/prospects/", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200 and not prospect_id:
            prospects = r.json()
            if prospects:
                prospect_id = prospects[0]["id"]
    except Exception as e:
        log_test("GET /api/prospects/", False, str(e))
    
    # Get single prospect
    if prospect_id:
        try:
            r = requests.get(f"{BASE_URL}/api/prospects/{prospect_id}", headers=headers)
            log_test(f"GET /api/prospects/{prospect_id}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log_test(f"GET /api/prospects/{prospect_id}", False, str(e))
    
    # Update prospect
    if prospect_id:
        try:
            update_data = {"company_name": "Updated Company"}
            r = requests.put(f"{BASE_URL}/api/prospects/{prospect_id}", json=update_data, headers=headers)
            log_test(f"PUT /api/prospects/{prospect_id}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log_test(f"PUT /api/prospects/{prospect_id}", False, str(e))
    
    return prospect_id


def test_campaigns(prospect_id: int = None):
    """Test campaign endpoints"""
    print(f"\n{Colors.BOLD}=== CAMPAIGNS ==={Colors.RESET}")
    
    if not access_token:
        log_test("Campaigns", False, "No access token - skipping")
        return None
    
    headers = get_headers()
    campaign_id = None
    
    # Create campaign
    try:
        campaign_data = {
            "name": "Test Campaign",
            "event_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "location": "Test Location",
            "distributor_name": "Test Distributor"
        }
        r = requests.post(f"{BASE_URL}/api/campaigns/", json=campaign_data, headers=headers)
        if r.status_code in [200, 201]:
            campaign_id = r.json().get("id")
            log_test("POST /api/campaigns/", True, f"Status: {r.status_code}")
        else:
            log_test("POST /api/campaigns/", False, f"Status: {r.status_code}, Body: {r.text}")
    except Exception as e:
        log_test("POST /api/campaigns/", False, str(e))
    
    # List campaigns
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/", headers=headers)
        log_test("GET /api/campaigns/", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200 and not campaign_id:
            campaigns = r.json()
            if campaigns:
                campaign_id = campaigns[0]["id"]
    except Exception as e:
        log_test("GET /api/campaigns/", False, str(e))
    
    # Get single campaign
    if campaign_id:
        try:
            r = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=headers)
            log_test(f"GET /api/campaigns/{campaign_id}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log_test(f"GET /api/campaigns/{campaign_id}", False, str(e))
    
    # Add contact to campaign
    if campaign_id and prospect_id:
        try:
            contact_data = {"prospect_ids": [prospect_id]}
            r = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/contacts/bulk", json=contact_data, headers=headers)
            log_test(f"POST /api/campaigns/{campaign_id}/contacts/bulk", r.status_code in [200, 201, 400], f"Status: {r.status_code}")
        except Exception as e:
            log_test(f"POST /api/campaigns/{campaign_id}/contacts/bulk", False, str(e))
    
    # List campaign contacts
    if campaign_id:
        try:
            r = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/contacts", headers=headers)
            log_test(f"GET /api/campaigns/{campaign_id}/contacts", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log_test(f"GET /api/campaigns/{campaign_id}/contacts", False, str(e))
    
    return campaign_id


def test_oauth():
    """Test OAuth endpoints"""
    print(f"\n{Colors.BOLD}=== OAUTH ==={Colors.RESET}")
    
    if not access_token:
        log_test("OAuth", False, "No access token - skipping")
        return
    
    headers = get_headers()
    
    # Get OAuth status
    try:
        r = requests.get(f"{BASE_URL}/api/oauth/status", headers=headers)
        log_test("GET /api/oauth/status", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_test("GET /api/oauth/status", False, str(e))
    
    # Test connect endpoints (should return auth URLs)
    try:
        r = requests.get(f"{BASE_URL}/api/oauth/gmail/connect", headers=headers)
        log_test("GET /api/oauth/gmail/connect", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_test("GET /api/oauth/gmail/connect", False, str(e))
    
    try:
        r = requests.get(f"{BASE_URL}/api/oauth/outlook/connect", headers=headers)
        log_test("GET /api/oauth/outlook/connect", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_test("GET /api/oauth/outlook/connect", False, str(e))


def generate_html_report():
    """Generate HTML test report"""
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Spine CRM API Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .summary h2 {{ margin-top: 0; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ flex: 1; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-passed {{ background: #c8e6c9; }}
        .stat-failed {{ background: #ffcdd2; }}
        .stat-total {{ background: #fff9c4; }}
        .stat-value {{ font-size: 32px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #1976d2; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .pass {{ color: #4caf50; font-weight: bold; }}
        .fail {{ color: #f44336; font-weight: bold; }}
        .details {{ color: #666; font-size: 12px; }}
        .timestamp {{ color: #999; font-size: 11px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Spine CRM API Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="stats">
                <div class="stat stat-total">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">Total Tests</div>
                </div>
                <div class="stat stat-passed">
                    <div class="stat-value">{passed}</div>
                    <div class="stat-label">Passed</div>
                </div>
                <div class="stat stat-failed">
                    <div class="stat-value">{failed}</div>
                    <div class="stat-label">Failed</div>
                </div>
            </div>
            <p><strong>Success Rate:</strong> {success_rate:.1f}%</p>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Test Name</th>
                    <th>Details</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for result in test_results:
        status = '<span class="pass">✅ PASS</span>' if result["passed"] else '<span class="fail">❌ FAIL</span>'
        details = f'<div class="details">{result["details"]}</div>' if result["details"] else ''
        timestamp = datetime.fromisoformat(result["timestamp"]).strftime('%H:%M:%S')
        
        html += f"""
                <tr>
                    <td>{status}</td>
                    <td>{result["name"]}</td>
                    <td>{details}</td>
                    <td class="timestamp">{timestamp}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    
    # Save report
    report_path = "tests/test_report.html"
    with open(report_path, "w") as f:
        f.write(html)
    
    print(f"\n{Colors.GREEN}📄 HTML Report generated: {report_path}{Colors.RESET}")
    return report_path


def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}   SPINE CRM - COMPLETE API TEST SUITE{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"\nBase URL: {BASE_URL}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all test suites
    test_health_check()
    test_auth()
    
    if access_token:
        product_id = test_products()
        prospect_id = test_prospects(product_id)
        campaign_id = test_campaigns(prospect_id)
        test_oauth()
    else:
        print(f"\n{Colors.RED}⚠️  Skipping authenticated tests (no access token){Colors.RESET}")
    
    # Print summary
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}SUMMARY:{Colors.RESET}")
    print(f"  Total Tests: {total}")
    print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {failed}{Colors.RESET}")
    print(f"  Success Rate: {(passed/total*100):.1f}%")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    # Generate HTML report
    report_path = generate_html_report()
    print(f"Open report: file://{os.path.abspath(report_path)}\n")
    
    # Exit with error code if tests failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    import os
    main()
