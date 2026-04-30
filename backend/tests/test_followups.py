"""
Test des relances (follow-ups) avec délais custom.
Force des dates passées pour simuler des relances dues.
"""
import requests
from datetime import datetime, timedelta

# ==================== CONFIG ====================
BASE_URL = "http://localhost:8000"
EMAIL = "test_flow@spine.com"
PASSWORD = "TestFlow123!"  

# ==================== HELPERS ====================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def ok(msg, detail=""):
    print(f"  {Colors.GREEN}✅ PASS{Colors.RESET} | {msg}")
    if detail:
        print(f"         {detail}")

def fail(msg, detail=""):
    print(f"  {Colors.RED}❌ FAIL{Colors.RESET} | {msg}")
    if detail:
        print(f"         {Colors.YELLOW}{detail}{Colors.RESET}")

def header(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

def h(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# ==================== MAIN ====================

def main():
    print(f"\n{'='*55}")
    print(f"  SPINE CRM — TEST FOLLOW-UPS & DÉLAIS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}")

    passed = 0
    failed = 0

    # ── 1. LOGIN ──
    header("1. AUTHENTIFICATION")
    r = requests.post(f"{BASE_URL}/api/auth/login", data={"username": EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        fail("Login", f"Status {r.status_code} — vérifie EMAIL/PASSWORD dans le script")
        return
    token = r.json()["access_token"]
    ok("Login", f"Token obtenu")
    passed += 1

    # ── 2. CRÉER CAMPAGNE AVEC DÉLAIS CUSTOM ──
    header("2. CAMPAGNE AVEC DÉLAIS CUSTOM (3 / 6 / 10 jours)")
    r = requests.post(f"{BASE_URL}/api/campaigns/", headers=h(token), json={
        "name": "Test Followups Campaign",
        "event_date": "2026-05-01",
        "followup_delay_1": 3,
        "followup_delay_2": 6,
        "followup_delay_3": 10,
    })
    if r.status_code == 201:
        campaign = r.json()
        campaign_id = campaign["id"]
        ok("Créer campagne", f"ID: {campaign_id} | Délais: {campaign['followup_delay_1']}j / {campaign['followup_delay_2']}j / {campaign['followup_delay_3']}j")
        passed += 1
    else:
        fail("Créer campagne", r.text)
        failed += 1
        return

    # ── 3. MODIFIER LES DÉLAIS DE LA CAMPAGNE ──
    header("3. MODIFIER LES DÉLAIS DE LA CAMPAGNE (5 / 10 / 15 jours)")
    r = requests.put(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=h(token), json={
        "followup_delay_1": 5,
        "followup_delay_2": 10,
        "followup_delay_3": 15,
    })
    if r.status_code == 200:
        updated = r.json()
        ok("Modifier délais campagne", f"Nouveaux délais: {updated['followup_delay_1']}j / {updated['followup_delay_2']}j / {updated['followup_delay_3']}j")
        passed += 1
    else:
        fail("Modifier délais campagne", r.text)
        failed += 1

    # ── 4. CRÉER 2 PROSPECTS ──
    header("4. CRÉER 2 PROSPECTS")
    prospect_ids = []
    for i, email in enumerate(["gduval@charbonneaux.com", "glenn.duval14cd@gmail.com"]):
        r = requests.post(f"{BASE_URL}/api/prospects/", headers=h(token), json={
            "email": email,
            "first_name": f"Test{i+1}",
            "last_name": "Followup",
            "company_name": f"Company {i+1}",
            "source": "trade_show"
        })
        if r.status_code == 201:
            pid = r.json()["id"]
            prospect_ids.append(pid)
            ok(f"Créer prospect {i+1}", f"ID: {pid} | {email}")
            passed += 1
        else:
            fail(f"Créer prospect {i+1}", r.text)
            failed += 1

    if len(prospect_ids) < 2:
        print("\n⚠️  Pas assez de prospects — arrêt du test")
        return

    # ── 5. AJOUTER PROSPECTS À LA CAMPAGNE ──
    header("5. AJOUTER PROSPECTS À LA CAMPAGNE")
    for pid in prospect_ids:
        r = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/contacts?prospect_id={pid}", headers=h(token))
        if r.status_code == 201:
            ok(f"Ajouter prospect {pid}")
            passed += 1
        else:
            fail(f"Ajouter prospect {pid}", r.text)
            failed += 1

    # ── 6. DÉLAIS CUSTOM SUR LE PROSPECT 1 (override campagne) ──
    header("6. DÉLAIS CUSTOM SUR PROSPECT 1 (2 / 4 / 8 jours)")
    r = requests.put(
        f"{BASE_URL}/api/campaigns/{campaign_id}/contacts/{prospect_ids[0]}/followup-delays",
        headers=h(token),
        json={
            "custom_followup_delay_1": 2,
            "custom_followup_delay_2": 4,
            "custom_followup_delay_3": 8,
        }
    )
    if r.status_code == 200:
        data = r.json()
        ok("Délais custom prospect 1",
           f"Custom: {data['custom_delays']['delay_1']}j / {data['custom_delays']['delay_2']}j / {data['custom_delays']['delay_3']}j"
           f" | Effectifs: {data['effective_delays']['delay_1']}j / {data['effective_delays']['delay_2']}j / {data['effective_delays']['delay_3']}j")
        passed += 1
    else:
        fail("Délais custom prospect 1", r.text)
        failed += 1

    # ── 7. SIMULER ENVOI EMAIL INITIAL (step 0 → 1) ──
    header("7. SIMULER ENVOI EMAIL INITIAL")
    print("  ⚠️  Envoi réel vers les adresses de test...")
    for pid in prospect_ids:
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/contacts/{pid}/emails/send",
            headers=h(token)
        )
        if r.status_code == 200:
            data = r.json()
            ok(f"Email envoyé — prospect {pid}", f"Step: {data.get('step')} | Provider: {data.get('provider')}")
            passed += 1
        else:
            fail(f"Email envoyé — prospect {pid}", r.text)
            failed += 1

    # ── 8. FORCER LA DATE DU FOLLOW-UP DANS LE PASSÉ ──
    header("8. FORCER FOLLOW-UP DANS LE PASSÉ (hier)")
    past_date = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    for pid in prospect_ids:
        r = requests.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/contacts/{pid}/schedule-followup",
            headers=h(token),
            json={"scheduled_at": past_date}
        )
        if r.status_code == 200:
            ok(f"Follow-up forcé dans le passé — prospect {pid}", f"Scheduled: {past_date}")
            passed += 1
        else:
            fail(f"Follow-up forcé — prospect {pid}", r.text)
            failed += 1

    # ── 9. VÉRIFIER LES FOLLOW-UPS PLANIFIÉS ──
    header("9. VÉRIFIER FOLLOW-UPS PLANIFIÉS")
    r = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/followups/scheduled", headers=h(token))
    if r.status_code == 200:
        data = r.json()
        total_scheduled = data["total_scheduled"]
        due = sum(1 for f in data["scheduled_followups"] if f["is_due"])
        ok("GET followups/scheduled", f"Total: {total_scheduled} | Dus maintenant: {due}")
        for f in data["scheduled_followups"]:
            print(f"     → Prospect {f['prospect_id']} | Step {f['current_step']} | Due: {f['is_due']} | Délais effectifs: {f['effective_delay_1']}j / {f['effective_delay_2']}j / {f['effective_delay_3']}j")
        passed += 1
    else:
        fail("GET followups/scheduled", r.text)
        failed += 1

    # ── 10. ENVOYER LES FOLLOW-UPS DUS ──
    header("10. ENVOYER LES FOLLOW-UPS DUS")
    r = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/followups/send-due", headers=h(token))
    if r.status_code == 200:
        data = r.json()
        ok("POST followups/send-due",
           f"Dus: {data['due_contacts']} | Envoyés: {data['sent']} | Échoués: {data['failed']}")
        if data.get("next_followups_scheduled"):
            print(f"     📅 Prochains follow-ups auto-planifiés :")
            for nf in data["next_followups_scheduled"]:
                print(f"        → Prospect {nf['prospect_id']} : {nf['next_followup_at']}")
        passed += 1
    else:
        fail("POST followups/send-due", r.text)
        failed += 1

    # ── 11. VÉRIFIER QUE LES DÉLAIS ONT ÉTÉ RESPECTÉS ──
    header("11. VÉRIFIER DÉLAIS APRÈS ENVOI")
    r = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/followups/scheduled", headers=h(token))
    if r.status_code == 200:
        data = r.json()
        ok("Vérification délais post-envoi", f"Follow-ups planifiés: {data['total_scheduled']}")
        for f in data["scheduled_followups"]:
            scheduled = datetime.fromisoformat(f["scheduled_at"])
            jours_restants = (scheduled - datetime.utcnow()).days
            print(f"     → Prospect {f['prospect_id']} | Step {f['current_step']} | Dans ~{jours_restants} jours")
        passed += 1
    else:
        fail("Vérification délais post-envoi", r.text)
        failed += 1

    # ── 12. NETTOYAGE ──
    header("12. NETTOYAGE")
    r = requests.delete(f"{BASE_URL}/api/campaigns/{campaign_id}", headers=h(token))
    ok("DELETE campaign") if r.status_code == 204 else fail("DELETE campaign", r.text)
    for pid in prospect_ids:
        r = requests.delete(f"{BASE_URL}/api/prospects/{pid}", headers=h(token))
        ok(f"DELETE prospect {pid}") if r.status_code == 204 else fail(f"DELETE prospect {pid}", r.text)

    # ── RÉSUMÉ ──
    print(f"\n{'='*55}")
    print(f"  RÉSUMÉ")
    print(f"  Passés  : {Colors.GREEN}{passed}{Colors.RESET}")
    print(f"  Échoués : {Colors.RED}{failed}{Colors.RESET}")
    print(f"  Taux    : {round(passed/(passed+failed)*100, 1)}%")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()