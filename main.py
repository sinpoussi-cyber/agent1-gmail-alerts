import argparse
from datetime import datetime


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


# ── MODE COLLECT ──────────────────────────────────────────────────────────────

def run_collect():
    from gmail_reader import get_google_alerts, delete_mail
    from web_scraper import scrape_url
    from claude_analyzer import analyze
    from supabase_client import insert_rapport

    log("Démarrage de la collecte Google Alerts...")

    alerts = get_google_alerts()
    log(f"{len(alerts)} mail(s) non lu(s) trouvé(s).")

    total_mails = 0
    total_links = 0

    for mail in alerts:
        mail_id = mail["id"]
        subject = mail["subject"]
        links = mail["links"]

        log(f"Traitement du mail : {subject!r} — {len(links)} lien(s)")

        keyword = subject.replace("Google Alertes -", "").replace("Google Alerts -", "").strip()

        for url in links:
            log(f"  Scraping : {url[:80]}...")
            scraped = scrape_url(url)
            if not scraped:
                log(f"  Echec du scraping, URL ignorée.")
                continue

            log(f"  Analyse Claude : {scraped['title'][:60]}...")
            analysis = analyze(
                title=scraped["title"],
                content=scraped["content"],
                url=scraped["url"],
                keyword=keyword,
            )
            if not analysis:
                log(f"  Echec de l'analyse Claude, URL ignorée.")
                continue

            rapport = {
                "mot_cle": keyword,
                "titre": scraped["title"],
                "url": scraped["url"],
                "resume": analysis.get("resume"),
                "points_cles": analysis.get("points_cles"),
                "sentiment": analysis.get("sentiment"),
                "pertinence": analysis.get("pertinence"),
                "categorie": analysis.get("categorie"),
                "envoye_email": False,
            }

            insert_rapport(rapport)
            total_links += 1
            log(f"  Sauvegarde Supabase OK — sentiment: {analysis.get('sentiment')}, pertinence: {analysis.get('pertinence')}/10")

        delete_mail(mail_id)
        log(f"Mail supprimé : {mail_id}")
        total_mails += 1

    log("─" * 50)
    log(f"Collecte terminée — {total_mails} mail(s) traité(s), {total_links} lien(s) analysé(s).")


# ── MODE RAPPORT-JOUR ─────────────────────────────────────────────────────────

def run_rapport_jour():
    from datetime import datetime, timezone
    from report_generator import generate_rapport_jour
    from email_sender import send_report
    from supabase_client import get_rapports_since_yesterday_20h, get_rapports_week, get_rapports_month, mark_sent

    log("Génération du rapport journalier...")

    rapports_jour = get_rapports_since_yesterday_20h()
    log(f"{len(rapports_jour)} alerte(s) depuis hier 20h00 UTC.")

    now = datetime.now(timezone.utc)
    rapports_hebdo = None
    rapports_mensuel = None

    if now.weekday() == 0:  # lundi
        rapports_hebdo = get_rapports_week()
        log(f"Lundi détecté — {len(rapports_hebdo)} alerte(s) cette semaine incluses.")

    if now.day == 1:  # 1er du mois
        rapports_mensuel = get_rapports_month()
        log(f"1er du mois détecté — {len(rapports_mensuel)} alerte(s) ce mois incluses.")

    report = generate_rapport_jour(rapports_jour, rapports_hebdo, rapports_mensuel)
    log(f"Rapport généré : {report['subject']!r}")

    success = send_report(subject=report["subject"], html_body=report["body_html"])

    if success and rapports_jour:
        ids = [r["id"] for r in rapports_jour if r.get("id")]
        mark_sent(ids)
        log(f"{len(ids)} alerte(s) marquée(s) comme envoyée(s).")

    log("─" * 50)
    log(f"Rapport journalier — {'OK' if success else 'ECHEC'}.")


# ── MODES RAPPORT HEBDO / MENSUEL ─────────────────────────────────────────────

def run_rapport(type_rapport, fetch_fn):
    from report_generator import generate
    from email_sender import send_report
    from supabase_client import mark_sent

    log(f"Génération du rapport {type_rapport}...")

    rapports = fetch_fn()
    log(f"{len(rapports)} rapport(s) récupéré(s) depuis Supabase.")

    report = generate(rapports, type_rapport)
    log(f"Rapport généré : {report['subject']!r}")

    log("Envoi de l'email...")
    success = send_report(
        subject=report["subject"],
        html_body=report["body_html"],
    )

    if success and rapports:
        ids = [r["id"] for r in rapports if r.get("id")]
        mark_sent(ids)
        log(f"{len(ids)} rapport(s) marqué(s) comme envoyé(s).")

    log("─" * 50)
    status = "OK" if success else "ECHEC"
    log(f"Rapport {type_rapport} — {status}.")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agent Google Alerts — collecte et envoi de rapports",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["collect", "rapport-jour", "rapport-hebdo", "rapport-mensuel"],
        help=(
            "collect         : collecte et analyse les nouvelles alertes Gmail\n"
            "rapport-jour    : envoie le rapport journalier\n"
            "rapport-hebdo   : envoie le rapport hebdomadaire\n"
            "rapport-mensuel : envoie le rapport mensuel"
        ),
    )

    args = parser.parse_args()

    log(f"Mode sélectionné : {args.mode}")

    if args.mode == "collect":
        run_collect()

    elif args.mode == "rapport-jour":
        run_rapport_jour()

    elif args.mode == "rapport-hebdo":
        from supabase_client import get_rapports_week
        run_rapport("hebdo", get_rapports_week)

    elif args.mode == "rapport-mensuel":
        from supabase_client import get_rapports_month
        run_rapport("mensuel", get_rapports_month)


if __name__ == "__main__":
    main()
