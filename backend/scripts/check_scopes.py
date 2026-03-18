import base64
import json
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="spine",
    user="spine",
    password="spinepassword"
)
cur = conn.cursor()
cur.execute("SELECT outlook_access_token FROM users WHERE email = 'test@test.com'")
result = cur.fetchone()

if not result:
    print("❌ User not found")
    exit(1)

token = result[0]

# Decode JWT payload
try:
    payload_b64 = token.split('.')[1]
    payload_b64 += '=' * (4 - len(payload_b64) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload_b64))
    
    print("📋 TOKEN SCOPES:")
    scopes = decoded.get("scp", "NO SCOPES")
    if isinstance(scopes, str):
        scopes = scopes.split(" ")
    for scope in scopes:
        print(f"  - {scope}")
    
    print("\n📋 OTHER INFO:")
    print(f"  - Issued at: {decoded.get('iat')}")
    print(f"  - Expires at: {decoded.get('exp')}")
    print(f"  - App ID: {decoded.get('appid')}")
    
except Exception as e:
    print(f"❌ Error decoding token: {e}")

cur.close()
conn.close()
