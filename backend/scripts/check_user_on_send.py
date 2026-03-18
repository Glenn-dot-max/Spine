import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5433,
    database="spine",
    user="spine",
    password="spine"
)
cur = conn.cursor()

# Get all users
cur.execute("""
    SELECT id, email, outlook_connected, outlook_email, 
           LENGTH(outlook_access_token) as token_len,
           default_email_provider
    FROM users
""")

print("📋 ALL USERS IN DB:")
for row in cur.fetchall():
    print(f"  ID: {row[0]}")
    print(f"    Email: {row[1]}")
    print(f"    Outlook Connected: {row[2]}")
    print(f"    Outlook Email: {row[3]}")
    print(f"    Token Length: {row[4]}")
    print(f"    Default Provider: {row[5]}")
    print()

cur.close()
conn.close()
