import requests
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="spine",
    user="spine",
    password="spine"
)
cur = conn.cursor()
cur.execute("SELECT outlook_access_token FROM users WHERE email = 'test@test.com'")
result = cur.fetchone()

if not result or not result[0]:
    print("❌ No token found")
    exit(1)

token = result[0]

print("🧪 TESTING MICROSOFT GRAPH API:")

# Test 1: Get user info (should work with User.Read)
print("\n1️⃣ Testing /me endpoint...")
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ User: {data.get('displayName')} ({data.get('mail') or data.get('userPrincipalName')})")
else:
    print(f"   ❌ Error: {response.text}")

# Test 2: Get mailbox (should work with Mail.Read)
print("\n2️⃣ Testing /me/messages endpoint...")
response = requests.get("https://graph.microsoft.com/v1.0/me/messages?$top=1", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✅ Can read mailbox")
else:
    print(f"   ❌ Error: {response.text}")

# Test 3: Test send mail endpoint
print("\n3️⃣ Testing /me/sendMail endpoint (without actually sending)...")
# We'll just check if the endpoint is accessible by doing a malformed request
test_payload = {"message": {}}  # Incomplete payload
response = requests.post(
    "https://graph.microsoft.com/v1.0/me/sendMail",
    headers={**headers, "Content-Type": "application/json"},
    json=test_payload
)
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   ❌ 401 UNAUTHORIZED - Token not accepted!")
    print(f"   Response: {response.text}")
elif response.status_code == 400:
    print(f"   ✅ 400 BAD REQUEST - Endpoint accessible (just bad payload)")
else:
    print(f"   Status {response.status_code}: {response.text}")

cur.close()
conn.close()
