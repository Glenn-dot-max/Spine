import base64
import json
import psycopg2
from datetime import datetime, timezone

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

# DEcode JWT payload
try:
    payload_b64 = token.split('.')[1]
    payload_b64 += '=' * (4 - len(payload_b64) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload_b64))

    print("📋 TOKEN PAYLOAD:")
    print(json.dumps(decoded, indent=2))

    print("\n📋 KEY FIELDS:")
    print(f"  - Audience (aud): {decoded.get('aud')}")
    print(f"  - Tenant ID (tid): {decoded.get('tid')}")
    print(f"  - App ID (appid): {decoded.get('appid')}")
    print(f"  - User ID (oid): {decoded.get('oid')}")
    print(f"  - UPN: {decoded.get('upn')}")
    
    # Check expiration
    exp = decoded.get('exp', 0)
    now = datetime.now(timezone.utc).timestamp()
    if now >= exp:
        print(f"\n❌ TOKEN IS EXPIRED!")
        print(f"  Expired at: {datetime.fromtimestamp(exp, timezone.utc)}")
        print(f"  Now: {datetime.fromtimestamp(now, timezone.utc)}")
    else:
        remaining = exp - now
        print(f"\n✅ TOKEN IS VALID")
        print(f"  Expires in: {remaining / 60:.1f} minutes")
    
except Exception as e:
    print(f"❌ Error decoding token: {e}")

cur.close()
conn.close()