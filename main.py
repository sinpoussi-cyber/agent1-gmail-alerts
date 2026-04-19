import argparse
from datetime import datetime


def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


# ── MODE COLLECT ──────────────────────────────────────────────────────────────

def _build_collect_html(date_str, nb_mails, total_links, collected_rapports):
    if collected_rapports:
        rows = "".join(
            f'<tr style="border-bottom:1px solid #ddd;">'
            f'<td style="padding:8px;">{r["titre"]}</td>'
            f'<td style="padding:8px;">{r["mot_cle"]}</td>'
            f'<td style="padding:8px;"><a href="{r["url"]}">{r["url"][:60]}…</a></td>'
            f'</tr>'
            for r in collected_rapports
        )
        alerts_section = f"""
        <h3 style="color:#E65C00;">Alertes trouvées</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="background:#f0f0f0;">
              <th style="padding:8px;text-align:left;">Titre</th>
              <th style="padding:8px;text-align:left;">Mot-clé</th>
              <th style="padding:8px;text-align:left;">Lien</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""
    else:
        alerts_section = '<p style="color:#888;font-style:italic;">Aucune alerte Google ce jour.</p>'

    return f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;">
  <div style="background:#E65C00;padding:20px;border-radius:8px 8px 0 0;">
    <h1 style="color:white;margin:0;font-size:20px;">&#128236; Agent 1 Gmail &mdash; Rapport de collecte &mdash; {date_str}</h1>
  </div>
  <div style="padding:20px;background:#f9f9f9;">
    <p><strong>Mails non lus trouvés :</strong> {nb_mails}</p>
    <p><strong>Liens analysés :</strong> {total_links}</p>
    {alerts_section}
  </div>
  <div style="padding:15px;background:#eeeeee;font-size:12px;color:#888888;border-radius:0 0 8px 8px;">
    Cet email est généré automatiquement par Agent 1 Gmail. Ne pas répondre.
  </div>
</body></html>"""


def run_collect():
    from gmail_reader import get_google_alerts, delete_mail
    from web_scraper import scrape_url
    from claude_analyzer import analyze
    from supabase_client import insert_rapport
    from email_sender import send_report

    log("Démarrage de la collecte Google Alerts...")

    alerts = get_google_alerts()
    log(f"{len(alerts)} mail(s) non lu(s) trouvé(s).")

    total_mails = 0
    total_links = 0
    collected_rapports = []

    for mail in alerts:
        mail_id = mail["id"]
        subject = mail["subject"]
        links = mail["links"]

        log(f"Traitement du mail : {subject!r} — {len(links)} lien(s)")

        # Extraire le mot-clé depuis le sujet (format "Google Alertes - <mot-clé>")
        keyword = subject.replace("Google Alertes -", "").replace("Google Alerts -", "").strip()

        links_analysed = 0
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
            collected_rapports.append({"titre": scraped["title"], "mot_cle": keyword, "url": scraped["url"]})
            links_analysed += 1
            total_links += 1
            log(f"  Sauvegarde Supabase OK — sentiment: {analysis.get('sentiment')}, pertinence: {analysis.get('pertinence')}/10")

        delete_mail(mail_id)
        log(f"Mail supprimé : {mail_id}")
        total_mails += 1

    log("─" * 50)
    log(f"Collecte terminée — {total_mails} mail(s) traité(s), {total_links} lien(s) analysé(s).")

    date_str = datetime.now().strftime("%Y-%m-%d")
    subject_email = f"📬 Agent 1 Gmail — Rapport de collecte — {date_str}"
    html_body = _build_collect_html(date_str, len(alerts), total_links, collected_rapports)
    log("Envoi de l'email de collecte...")
    send_report(subject=subject_email, html_body=html_body)
    log("Email de collecte envoyé.")


# ── MODES RAPPORT ─────────────────────────────────────────────────────────────

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
        from supabase_client import get_rapports_today
        run_rapport("journalier", get_rapports_today)

    elif args.mode == "rapport-hebdo":
        from supabase_client import get_rapports_week
        run_rapport("hebdo", get_rapports_week)

    elif args.mode == "rapport-mensuel":
        from supabase_client import get_rapports_month
        run_rapport("mensuel", get_rapports_month)


if __name__ == "__main__":
    main()
