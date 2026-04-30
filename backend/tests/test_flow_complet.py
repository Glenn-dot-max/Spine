f"""lenn
Spine CRM - Test du flow complet avec vrais envois d'emails
Compte test : test_flow@spine.com (Gmail + Outlook déjà connectés)
Destinataires : glenn_duval@outlook.com, gduval@charbonneaux.com, glenn.duval14cd@gmail.com
"""
import requests
import json
from datetime import datetime, timedelta
import sys
import os

# ==================== CONFIG ====================
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test_flow@spine.com"
TEST_USER_PASSWORD = "TestFlow123!"

# Les 3 prospects réels
PROSPECTS = [
    {
        "email": "glenn_duval@outlook.com",
        "first_name": "Glenn",
        "last_name": "Duval",
        "company_name": "Outlook Inc.",
        "position": "Chef",
        "phone_number": "+1 555 000 0001",
        "source": "trade_show"
    },
    {
        "email": "gduval@charbonneaux.com",
        "first_name": "Glenn",
        "last_name": "Duval",
        "company_name": "Charbonneaux",
        "position": "Chef",
        "phone_number": "+1 555 000 0002",
        "source": "trade_show"
    },
    {
        "email": "glenn.duval14cd@gmail.com",
        "first_name": "Glenn",
        "last_name": "Duval",
        "company_name": "Gmail Corp.",
        "position": "Chef",
        "phone_number": "+1 555 000 0003",
        "source": "trade_show"
    }
]

# State global
access_token = None
test_results = []
created_ids = {
    "product_id": None,
    "prospect_ids": [],
    "campaign_id": None,
}


# ==================== HELPERS ====================
class Colors:
    GREEN  = '\033[92m'
    RED    = '\033[91m'
    YELLOW = '\033[93m'
    BLUE   = '\033[94m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'


def log(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"  {status} | {name}")
    if details and not passed:
        print(f"         {Colors.YELLOW}{details}{Colors.RESET}")
    if details and passed:
        print(f"         {Colors.BLUE}{details}{Colors.RESET}")
    test_results.append({"name": name, "passed": passed, "details": details})


def h():
    return {"Authorization": f"Bearer {access_token}"}


def section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*55}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*55}{Colors.RESET}")


# ==================== 0. PRÉ-NETTOYAGE ====================
def step_0_cleanup_before():
    section("0. PRÉ-NETTOYAGE")

    r = requests.post(f"{BASE_URL}/api/auth/login", data={
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })

    if r.status_code != 200:
        print(f"  {Colors.RED}❌ Impossible de se connecter pour nettoyer{Colors.RESET}")
        return

    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Supprimer campaigns (cascade supprime les contacts)
    campaigns = requests.get(f"{BASE_URL}/api/campaigns/", headers=headers).json()
    if isinstance(campaigns, list):
        for c in campaigns:
            requests.delete(f"{BASE_URL}/api/campaigns/{c['id']}", headers=headers)
        print(f"  {Colors.YELLOW}🗑  {len(campaigns)} campaign(s) supprimée(s){Colors.RESET}")

    # Supprimer prospects
    prospects = requests.get(f"{BASE_URL}/api/prospects/", headers=headers).json()
    if isinstance(prospects, list):
        for p in prospects:
            requests.delete(f"{BASE_URL}/api/prospects/{p['id']}", headers=headers)
        print(f"  {Colors.YELLOW}🗑  {len(prospects)} prospect(s) supprimé(s){Colors.RESET}")

    # Supprimer products
    products = requests.get(f"{BASE_URL}/api/products/", headers=headers).json()
    if isinstance(products, list):
        for p in products:
            requests.delete(f"{BASE_URL}/api/products/{p['id']}", headers=headers)
        print(f"  {Colors.YELLOW}🗑  {len(products)} product(s) supprimé(s){Colors.RESET}")

    print(f"  {Colors.GREEN}✅ Base nettoyée — prêt pour les tests{Colors.RESET}")


# ==================== 1. AUTH ====================
def step_1_auth():
    global access_token
    section("1. AUTHENTIFICATION")

    # Login
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if r.status_code == 200:
            access_token = r.json().get("access_token")
        log("POST /api/auth/login", r.status_code == 200 and bool(access_token), f"Status: {r.status_code}")
    except Exception as e:
        log("POST /api/auth/login", False, str(e))
        return

    # /me
    try:
        r = requests.get(f"{BASE_URL}/api/auth/me", headers=h())
        data = r.json()
        log("GET /api/auth/me", r.status_code == 200,
            f"User: {data.get('email')} | Gmail: {data.get('gmail_connected')} | Outlook: {data.get('outlook_connected')}")
    except Exception as e:
        log("GET /api/auth/me", False, str(e))

    # Vérifier Gmail + Outlook connectés
    try:
        r = requests.get(f"{BASE_URL}/api/oauth/status", headers=h())
        data = r.json()
        gmail_ok = data.get("gmail", {}).get("connected", False)
        outlook_ok = data.get("outlook", {}).get("connected", False)
        log("GET /api/oauth/status — Gmail connecté", gmail_ok,
            f"Email: {data.get('gmail', {}).get('email')}")
        log("GET /api/oauth/status — Outlook connecté", outlook_ok,
            f"Email: {data.get('outlook', {}).get('email')}")
    except Exception as e:
        log("GET /api/oauth/status", False, str(e))

    # Mauvais mot de passe → 401
    try:
        r = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": TEST_USER_EMAIL,
            "password": "mauvais_mdp_123"
        })
        log("POST /api/auth/login (mauvais mdp → 401)", r.status_code == 401, f"Status: {r.status_code}")
    except Exception as e:
        log("POST /api/auth/login (mauvais mdp → 401)", False, str(e))

    # Sans token → 401
    try:
        r = requests.get(f"{BASE_URL}/api/auth/me")
        log("GET /api/auth/me (sans token → 401)", r.status_code == 401, f"Status: {r.status_code}")
    except Exception as e:
        log("GET /api/auth/me (sans token → 401)", False, str(e))


# ==================== 2. PRODUCTS ====================
def step_2_products():
    section("2. PRODUCTS")

    # Create
    try:
        r = requests.post(f"{BASE_URL}/api/products/", headers=h(), json={
            "item_number": "KNIFE-001",
            "name": "Couteau de Chef Pro",
            "short_description": "Couteau japonais 21cm"
        })
        log("POST /api/products/", r.status_code == 201, f"Status: {r.status_code} | {r.text}")
        if r.status_code == 201:
            created_ids["product_id"] = r.json().get("id")
    except Exception as e:
        log("POST /api/products/", False, str(e))

    pid = created_ids["product_id"]

    # List
    try:
        r = requests.get(f"{BASE_URL}/api/products/", headers=h())
        products = r.json()
        log("GET /api/products/", r.status_code == 200, f"{len(products)} produit(s)")
    except Exception as e:
        log("GET /api/products/", False, str(e))

    if pid:
        # Get
        try:
            r = requests.get(f"{BASE_URL}/api/products/{pid}", headers=h())
            log(f"GET /api/products/{pid}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log(f"GET /api/products/{pid}", False, str(e))

        # Update
        try:
            r = requests.patch(f"{BASE_URL}/api/products/{pid}", headers=h(), json={
                "name": "Couteau de Chef Pro — MAJ"
            })
            log(f"PATCH /api/products/{pid}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log(f"PATCH /api/products/{pid}", False, str(e))

    # 404
    try:
        r = requests.get(f"{BASE_URL}/api/products/999999", headers=h())
        log("GET /api/products/999999 (→ 404)", r.status_code == 404, f"Status: {r.status_code}")
    except Exception as e:
        log("GET /api/products/999999 (→ 404)", False, str(e))


# ==================== 3. PROSPECTS ====================
def step_3_prospects():
    section("3. PROSPECTS (3 destinataires réels)")

    pid = created_ids["product_id"]

    for prospect_data in PROSPECTS:
        data = {**prospect_data, "product_interest_ids": [pid] if pid else []}
        try:
            r = requests.post(f"{BASE_URL}/api/prospects/", headers=h(), json=data)
            log(f"POST /api/prospects/ — {prospect_data['email']}",
                r.status_code == 201,
                f"Status: {r.status_code} | {r.text}")
            if r.status_code == 201:
                created_ids["prospect_ids"].append(r.json().get("id"))
        except Exception as e:
            log(f"POST /api/prospects/ — {prospect_data['email']}", False, str(e))

    # List
    try:
        r = requests.get(f"{BASE_URL}/api/prospects/", headers=h())
        prospects = r.json()
        log("GET /api/prospects/", r.status_code == 200, f"{len(prospects)} prospect(s)")
    except Exception as e:
        log("GET /api/prospects/", False, str(e))

    # Get + Update sur le premier
    if created_ids["prospect_ids"]:
        sid = created_ids["prospect_ids"][0]

        try:
            r = requests.get(f"{BASE_URL}/api/prospects/{sid}", headers=h())
            log(f"GET /api/prospects/{sid}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log(f"GET /api/prospects/{sid}", False, str(e))

        try:
            r = requests.put(f"{BASE_URL}/api/prospects/{sid}", headers=h(), json={
                "company_name": "Outlook Inc. — MAJ"
            })
            log(f"PUT /api/prospects/{sid}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log(f"PUT /api/prospects/{sid}", False, str(e))

    # 404
    try:
        r = requests.get(f"{BASE_URL}/api/prospects/999999", headers=h())
        log("GET /api/prospects/999999 (→ 404)", r.status_code == 404, f"Status: {r.status_code}")
    except Exception as e:
        log("GET /api/prospects/999999 (→ 404)", False, str(e))


# ==================== 4. CAMPAIGN ====================
def step_4_campaigns():
    section("4. CAMPAIGN")

    # Create
    try:
        r = requests.post(f"{BASE_URL}/api/campaigns/", headers=h(), json={
            "name": "Show Chefs LA 2026",
            "event_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=33)).strftime("%Y-%m-%d"),
            "location": "Los Angeles Convention Center",
            "distributor_name": "US Foods",
            "description": "Campagne de test avec vrais envois",
            "status": "upcoming"
        })
        log("POST /api/campaigns/", r.status_code == 201, f"Status: {r.status_code} | {r.text}")
        if r.status_code == 201:
            created_ids["campaign_id"] = r.json().get("id")
    except Exception as e:
        log("POST /api/campaigns/", False, str(e))

    cid = created_ids["campaign_id"]

    # List
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/", headers=h())
        log("GET /api/campaigns/", r.status_code == 200, f"{len(r.json())} campagne(s)")
    except Exception as e:
        log("GET /api/campaigns/", False, str(e))

    # List filtrée
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/?status_filter=upcoming", headers=h())
        log("GET /api/campaigns/?status_filter=upcoming", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log("GET /api/campaigns/?status_filter=upcoming", False, str(e))

    if cid:
        # Get
        try:
            r = requests.get(f"{BASE_URL}/api/campaigns/{cid}", headers=h())
            log(f"GET /api/campaigns/{cid}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log(f"GET /api/campaigns/{cid}", False, str(e))

        # Update → active
        try:
            r = requests.put(f"{BASE_URL}/api/campaigns/{cid}", headers=h(), json={"status": "active"})
            log(f"PUT /api/campaigns/{cid} (status → active)", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log(f"PUT /api/campaigns/{cid}", False, str(e))

    # 404
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/999999", headers=h())
        log("GET /api/campaigns/999999 (→ 404)", r.status_code == 404, f"Status: {r.status_code}")
    except Exception as e:
        log("GET /api/campaigns/999999 (→ 404)", False, str(e))


# ==================== 5. CAMPAIGN CONTACTS ====================
def step_5_campaign_contacts():
    section("5. CAMPAIGN CONTACTS")

    cid = created_ids["campaign_id"]
    prospect_ids = created_ids["prospect_ids"]

    if not cid or not prospect_ids:
        print(f"  {Colors.YELLOW}⚠️  Skipped{Colors.RESET}")
        return

    # Ajouter les 3 prospects
    for sid in prospect_ids:
        try:
            r = requests.post(
                f"{BASE_URL}/api/campaigns/{cid}/contacts?prospect_id={sid}",
                headers=h()
            )
            log(f"POST contacts — prospect {sid}", r.status_code == 201, f"Status: {r.status_code}")
        except Exception as e:
            log(f"POST contacts — prospect {sid}", False, str(e))

    # Doublon → 400
    try:
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{cid}/contacts?prospect_id={prospect_ids[0]}",
            headers=h()
        )
        log("POST doublon contact (→ 400)", r.status_code == 400, f"Status: {r.status_code}")
    except Exception as e:
        log("POST doublon contact (→ 400)", False, str(e))

    # List contacts
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/contacts", headers=h())
        contacts = r.json()
        log(f"GET /api/campaigns/{cid}/contacts", r.status_code == 200, f"{len(contacts)} contact(s)")
    except Exception as e:
        log(f"GET /api/campaigns/{cid}/contacts", False, str(e))

    # Stats
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/stats", headers=h())
        log(f"GET /api/campaigns/{cid}/stats", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log(f"GET /api/campaigns/{cid}/stats", False, str(e))


# ==================== 6. CAMPAIGN PRODUCTS ====================
def step_6_campaign_products():
    section("6. CAMPAIGN PRODUCTS")

    cid = created_ids["campaign_id"]
    pid = created_ids["product_id"]

    if not cid or not pid:
        print(f"  {Colors.YELLOW}⚠️  Skipped{Colors.RESET}")
        return

    # Add
    try:
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/products?product_id={pid}", headers=h())
        log(f"POST /api/campaigns/{cid}/products", r.status_code == 201, f"Status: {r.status_code}")
    except Exception as e:
        log(f"POST /api/campaigns/{cid}/products", False, str(e))

    # Doublon → 400
    try:
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/products?product_id={pid}", headers=h())
        log("POST doublon product (→ 400)", r.status_code == 400, f"Status: {r.status_code}")
    except Exception as e:
        log("POST doublon product (→ 400)", False, str(e))

    # List
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/products", headers=h())
        log(f"GET /api/campaigns/{cid}/products", r.status_code == 200, f"{len(r.json())} produit(s)")
    except Exception as e:
        log(f"GET /api/campaigns/{cid}/products", False, str(e))


# ==================== 7. EMAIL PREVIEW ====================
def step_7_email_preview():
    section("7. EMAIL PREVIEW (sans envoi)")

    cid = created_ids["campaign_id"]
    prospect_ids = created_ids["prospect_ids"]

    if not cid or not prospect_ids:
        print(f"  {Colors.YELLOW}⚠️  Skipped{Colors.RESET}")
        return

    for sid in prospect_ids:
        try:
            r = requests.get(
                f"{BASE_URL}/api/campaigns/{cid}/contacts/{sid}/emails/preview",
                headers=h()
            )
            subject = r.json().get("subject", "") if r.status_code == 200 else ""
            log(f"GET email preview — prospect {sid}", r.status_code == 200,
                f"Subject: {subject}")
        except Exception as e:
            log(f"GET email preview — prospect {sid}", False, str(e))


# ==================== 8. ENVOI EMAILS RÉELS ====================
def step_8_send_emails():
    section("8. 📨 ENVOI EMAILS RÉELS")

    cid = created_ids["campaign_id"]
    prospect_ids = created_ids["prospect_ids"]

    if not cid or not prospect_ids:
        print(f"  {Colors.YELLOW}⚠️  Skipped{Colors.RESET}")
        return

    print(f"  {Colors.YELLOW}⚠️  Envoi réel vers les 3 adresses...{Colors.RESET}")

    for i, sid in enumerate(prospect_ids):
        email = PROSPECTS[i]["email"]
        try:
            r = requests.post(
                f"{BASE_URL}/api/campaigns/{cid}/contacts/{sid}/emails/send",
                headers=h(),
                json={}
            )
            data = r.json() if r.status_code == 200 else {}
            log(
                f"POST emails/send → {email}",
                r.status_code == 200,
                f"Provider: {data.get('provider')} | Thread: {data.get('thread_id')} | Step: {data.get('sequence_step')} | Status: {r.status_code} {r.text if r.status_code != 200 else ''}"
            )
        except Exception as e:
            log(f"POST emails/send → {email}", False, str(e))


# ==================== 9. FOLLOW-UPS ====================
def step_9_followups():
    section("9. FOLLOW-UPS")

    cid = created_ids["campaign_id"]
    prospect_ids = created_ids["prospect_ids"]

    if not cid or not prospect_ids:
        print(f"  {Colors.YELLOW}⚠️  Skipped{Colors.RESET}")
        return

    # Planifier un follow-up dans 3 jours pour chaque prospect
    for sid in prospect_ids:
        try:
            r = requests.post(
                f"{BASE_URL}/api/campaigns/{cid}/contacts/{sid}/schedule-followup/suggest",
                headers=h(),
                json={"days_from_now": 3}
            )
            log(f"POST schedule-followup — prospect {sid}", r.status_code == 200,
                f"Status: {r.status_code} | {r.text[:100]}")
        except Exception as e:
            log(f"POST schedule-followup — prospect {sid}", False, str(e))

    # Liste des follow-ups planifiés
    try:
        r = requests.get(f"{BASE_URL}/api/campaigns/{cid}/followups/scheduled", headers=h())
        data = r.json()
        log("GET followups/scheduled", r.status_code == 200,
            f"{data.get('total_scheduled', 0)} follow-up(s) planifié(s)")
    except Exception as e:
        log("GET followups/scheduled", False, str(e))

    # Send-due (rien à envoyer car dans 3 jours)
    try:
        r = requests.post(f"{BASE_URL}/api/campaigns/{cid}/followups/send-due", headers=h())
        data = r.json()
        log("POST followups/send-due (0 dû)", r.status_code == 200,
            f"Sent: {data.get('sent', 0)} | Message: {data.get('message')}")
    except Exception as e:
        log("POST followups/send-due", False, str(e))

    # Annuler les follow-ups
    for sid in prospect_ids:
        try:
            r = requests.post(
                f"{BASE_URL}/api/campaigns/{cid}/contacts/{sid}/followup",
                headers=h()
            )
            log(f"POST cancel followup — prospect {sid}", r.status_code == 200, f"Status: {r.status_code}")
        except Exception as e:
            log(f"POST cancel followup — prospect {sid}", False, str(e))


# ==================== 10. NETTOYAGE FINAL ====================
def step_10_cleanup():
    section("10. NETTOYAGE FINAL")

    cid = created_ids["campaign_id"]
    prospect_ids = created_ids["prospect_ids"]
    pid = created_ids["product_id"]

    if cid:
        r = requests.delete(f"{BASE_URL}/api/campaigns/{cid}", headers=h())
        log(f"DELETE campaign {cid}", r.status_code == 204, f"Status: {r.status_code}")

    for sid in prospect_ids:
        r = requests.delete(f"{BASE_URL}/api/prospects/{sid}", headers=h())
        log(f"DELETE prospect {sid}", r.status_code == 204, f"Status: {r.status_code}")

    if pid:
        r = requests.delete(f"{BASE_URL}/api/products/{pid}", headers=h())
        log(f"DELETE product {pid}", r.status_code == 204, f"Status: {r.status_code}")


# ==================== RAPPORT HTML ====================
def generate_report():
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)
    rate = (passed / total * 100) if total > 0 else 0

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Spine CRM - Test Flow Complet</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 950px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #1976d2; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-total {{ background: #fff9c4; }}
        .stat-pass {{ background: #c8e6c9; }}
        .stat-fail {{ background: #ffcdd2; }}
        .stat-value {{ font-size: 40px; font-weight: bold; }}
        .rate {{ font-size: 18px; font-weight: bold; color: #1976d2; margin: 10px 0 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #1976d2; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
        tr:hover {{ background: #f9f9f9; }}
        .pass {{ color: #4caf50; font-weight: bold; }}
        .fail {{ color: #f44336; font-weight: bold; }}
        .details {{ color: #666; font-size: 12px; margin-top: 3px; }}
    </style>
</head>
<body>
<div class="container">
    <h1>🧪 Spine CRM — Test Flow Complet</h1>
    <p>Généré le <strong>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
    <div class="stats">
        <div class="stat stat-total"><div class="stat-value">{total}</div>Total</div>
        <div class="stat stat-pass"><div class="stat-value">{passed}</div>✅ Passés</div>
        <div class="stat stat-fail"><div class="stat-value">{failed}</div>❌ Échoués</div>
    </div>
    <p class="rate">Taux de succès : {rate:.1f}%</p>
    <table>
        <thead><tr><th width="100">Status</th><th>Test</th><th>Détails</th></tr></thead>
        <tbody>"""

    for r in test_results:
        s = '<span class="pass">✅ PASS</span>' if r["passed"] else '<span class="fail">❌ FAIL</span>'
        d = f'<div class="details">{r["details"]}</div>' if r["details"] else ""
        html += f"<tr><td>{s}</td><td>{r['name']}</td><td>{d}</td></tr>"

    html += "</tbody></table></div></body></html>"

    os.makedirs("reports", exist_ok=True)
    path = "tests/test_flow_report.html"
    with open(path, "w") as f:
        f.write(html)
    return path


# ==================== MAIN ====================
def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*55}")
    print(f"   SPINE CRM — TEST FLOW COMPLET")
    print(f"   Compte : {TEST_USER_EMAIL}")
    print(f"{'='*55}{Colors.RESET}")
    print(f"Heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    step_0_cleanup_before()
    step_1_auth()

    if not access_token:
        print(f"\n{Colors.RED}❌ Pas de token — arrêt{Colors.RESET}")
        sys.exit(1)

    step_2_products()
    step_3_prospects()
    step_4_campaigns()
    step_5_campaign_contacts()
    step_6_campaign_products()
    step_7_email_preview()
    step_8_send_emails()   # 📨 vrais envois ici
    step_9_followups()
    step_10_cleanup()

    # Résumé
    passed = sum(1 for r in test_results if r["passed"])
    failed = sum(1 for r in test_results if not r["passed"])
    total = len(test_results)

    print(f"\n{Colors.BOLD}{'='*55}{Colors.RESET}")
    print(f"{Colors.BOLD}RÉSUMÉ FINAL{Colors.RESET}")
    print(f"  Total   : {total}")
    print(f"  {Colors.GREEN}Passés  : {passed}{Colors.RESET}")
    print(f"  {Colors.RED}Échoués : {failed}{Colors.RESET}")
    print(f"  Taux    : {(passed/total*100):.1f}%")
    print(f"{Colors.BOLD}{'='*55}{Colors.RESET}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()