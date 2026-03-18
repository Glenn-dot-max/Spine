import base64
import json
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
    print("No access token found for test user.")
    exit(1)

token = result[0]

# DEcode JWT payload
try:
    payload_b64 = token.split('.')[1]
    payload_b64 += '=' * (4 - len(payload_b64) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload_b64))

    print("📋 TOKEN SCOPES:")
    scopes = decoded.get("scp", "NO SCOPES")
    if isinstance(scopes, str):
        scopes_list = scopes.split(" ")
    else:
        scopes_list = scopes

    for scope in scopes_list:
        print(f" - {'✅' if 'Mail.Send' in scope else '❌'} {scope}")

    print("\n🔍 CHECKING:")
    has_mail_send = any('Mail.Send' in s for s in scopes_list)
    if has_mail_send:
        print("✅ Token HAS Mail.Send permission")
    else:
        print("❌ Token is MISSING Mail.Send permission")
        print("\n💡 SOLUTION: You need to reconnect Outlook with consent!")

except Exception as e:
    print(f"Error decoding token: {e}")

cur.close()
conn.close()
