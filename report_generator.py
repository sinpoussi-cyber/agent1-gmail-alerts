from datetime import date

HEADER_COLORS = {
    "journalier": "#1a73e8",
    "hebdo": "#0f9d58",
    "mensuel": "#f4511e",
}

SENTIMENT_EMOJI = {
    "positif": "&#x1F7E2;",   # green circle
    "neutre":  "&#x1F7E1;",   # yellow circle
    "négatif": "&#x1F534;",   # red circle
}

MONTHS_FR = [
    "", "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _date_fr(d=None):
    d = d or date.today()
    return f"{d.day} {MONTHS_FR[d.month]} {d.year}"


def _subject(type_rapport):
    labels = {"journalier": "journalier", "hebdo": "hebdomadaire", "mensuel": "mensuel"}
    label = labels.get(type_rapport, type_rapport)
    return f"Rapport {label} Google Alerts \u2014 {_date_fr()}"


def _sentiment_counts(rapports):
    counts = {"positif": 0, "neutre": 0, "négatif": 0}
    for r in rapports:
        s = (r.get("sentiment") or "neutre").lower()
        if s in counts:
            counts[s] += 1
        else:
            counts["neutre"] += 1
    return counts


# ── HTML ──────────────────────────────────────────────────────────────────────

def _alert_card_html(r):
    keyword = r.get("keyword") or r.get("mot_cle") or ""
    title = r.get("title") or r.get("titre") or ""
    resume = r.get("resume") or ""
    points = r.get("points_cles") or []
    url = r.get("url") or r.get("source_url") or "#"
    sentiment = r.get("sentiment") or "neutre"
    pertinence = r.get("pertinence") or "—"
    categorie = r.get("categorie") or ""

    points_html = "".join(f"<li>{p}</li>" for p in points)
    emoji = SENTIMENT_EMOJI.get(sentiment.lower(), "&#x1F7E1;")

    return f"""
    <div style="border:1px solid #e0e0e0;border-radius:8px;padding:20px;margin-bottom:20px;background:#ffffff;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
        <span style="background:#e8f0fe;color:#1a73e8;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;">{keyword}</span>
        <span style="font-size:13px;color:#555;">{emoji} {sentiment.capitalize()} &nbsp;|&nbsp; Pertinence : <strong>{pertinence}/10</strong></span>
      </div>
      <h3 style="margin:0 0 8px 0;font-size:16px;color:#202124;">
        <a href="{url}" style="color:#1a73e8;text-decoration:none;">{title}</a>
      </h3>
      {f'<p style="font-size:12px;color:#888;margin:0 0 10px 0;">{categorie}</p>' if categorie else ""}
      <p style="font-size:14px;color:#444;line-height:1.6;margin:0 0 12px 0;">{resume}</p>
      <ul style="margin:0 0 12px 0;padding-left:20px;font-size:14px;color:#444;line-height:1.8;">
        {points_html}
      </ul>
      <a href="{url}" style="font-size:13px;color:#1a73e8;">Lire l'article complet &rarr;</a>
    </div>"""


def _summary_table_html(rapports, counts):
    total = len(rapports)
    return f"""
    <table style="width:100%;border-collapse:collapse;margin-top:10px;font-size:14px;">
      <thead>
        <tr style="background:#f1f3f4;">
          <th style="padding:10px;text-align:left;border:1px solid #e0e0e0;">Indicateur</th>
          <th style="padding:10px;text-align:center;border:1px solid #e0e0e0;">Valeur</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="padding:10px;border:1px solid #e0e0e0;">Nombre total d'alertes</td>
          <td style="padding:10px;text-align:center;border:1px solid #e0e0e0;"><strong>{total}</strong></td>
        </tr>
        <tr style="background:#f9f9f9;">
          <td style="padding:10px;border:1px solid #e0e0e0;">&#x1F7E2; Positif</td>
          <td style="padding:10px;text-align:center;border:1px solid #e0e0e0;">{counts['positif']}</td>
        </tr>
        <tr>
          <td style="padding:10px;border:1px solid #e0e0e0;">&#x1F7E1; Neutre</td>
          <td style="padding:10px;text-align:center;border:1px solid #e0e0e0;">{counts['neutre']}</td>
        </tr>
        <tr style="background:#f9f9f9;">
          <td style="padding:10px;border:1px solid #e0e0e0;">&#x1F534; Négatif</td>
          <td style="padding:10px;text-align:center;border:1px solid #e0e0e0;">{counts['négatif']}</td>
        </tr>
      </tbody>
    </table>"""


def _build_html(type_rapport, rapports, subject):
    color = HEADER_COLORS.get(type_rapport, "#1a73e8")
    cards = "".join(_alert_card_html(r) for r in rapports)
    counts = _sentiment_counts(rapports)
    summary = _summary_table_html(rapports, counts)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f3f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f3f4;padding:30px 0;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

        <!-- HEADER -->
        <tr><td style="background:{color};border-radius:8px 8px 0 0;padding:30px 30px 20px 30px;">
          <h1 style="margin:0;color:#ffffff;font-size:22px;">{subject}</h1>
          <p style="margin:6px 0 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
            {len(rapports)} alerte{"s" if len(rapports) > 1 else ""} analysée{"s" if len(rapports) > 1 else ""}
          </p>
        </td></tr>

        <!-- BODY -->
        <tr><td style="background:#f8f9fa;padding:24px 30px;">
          {cards}
        </td></tr>

        <!-- SUMMARY -->
        <tr><td style="background:#ffffff;padding:24px 30px;border-top:1px solid #e0e0e0;">
          <h2 style="margin:0 0 14px 0;font-size:16px;color:#202124;">Tableau récapitulatif</h2>
          {summary}
        </td></tr>

        <!-- FOOTER -->
        <tr><td style="background:{color};border-radius:0 0 8px 8px;padding:16px 30px;text-align:center;">
          <p style="margin:0;color:rgba(255,255,255,0.8);font-size:12px;">
            Rapport généré automatiquement par Google Alerts Agent &mdash; {_date_fr()}
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ── TEXT ──────────────────────────────────────────────────────────────────────

def _build_text(type_rapport, rapports, subject):
    lines = [subject, "=" * len(subject), ""]

    for i, r in enumerate(rapports, 1):
        keyword = r.get("keyword") or r.get("mot_cle") or ""
        title = r.get("title") or r.get("titre") or ""
        resume = r.get("resume") or ""
        points = r.get("points_cles") or []
        url = r.get("url") or r.get("source_url") or ""
        sentiment = r.get("sentiment") or "neutre"
        pertinence = r.get("pertinence") or "—"
        categorie = r.get("categorie") or ""

        lines.append(f"[{i}] {title}")
        lines.append(f"    Mot-clé   : {keyword}")
        if categorie:
            lines.append(f"    Catégorie : {categorie}")
        lines.append(f"    Sentiment : {sentiment.capitalize()}  |  Pertinence : {pertinence}/10")
        lines.append(f"    Résumé    : {resume}")
        if points:
            lines.append("    Points clés :")
            for p in points:
                lines.append(f"      - {p}")
        lines.append(f"    Source    : {url}")
        lines.append("")

    counts = _sentiment_counts(rapports)
    lines += [
        "─" * 40,
        "RÉCAPITULATIF",
        "─" * 40,
        f"Nombre total d'alertes : {len(rapports)}",
        f"  Positif  : {counts['positif']}",
        f"  Neutre   : {counts['neutre']}",
        f"  Négatif  : {counts['négatif']}",
        "",
        f"Rapport généré le {_date_fr()}",
    ]

    return "\n".join(lines)


# ── RAPPORT JOUR (avec sections hebdo/mensuel optionnelles) ───────────────────

def _build_html_jour(rapports_jour, rapports_hebdo, rapports_mensuel, subject):
    color = HEADER_COLORS["journalier"]
    nb = len(rapports_jour)
    cards = "".join(_alert_card_html(r) for r in rapports_jour) if rapports_jour else (
        '<p style="color:#888;font-style:italic;">Aucune alerte collectée dans les dernières 24h.</p>'
    )
    counts_jour = _sentiment_counts(rapports_jour)
    summary_jour = _summary_table_html(rapports_jour, counts_jour)

    extra_sections = ""
    if rapports_hebdo is not None:
        counts_hebdo = _sentiment_counts(rapports_hebdo)
        extra_sections += f"""
        <tr><td style="background:#ffffff;padding:24px 30px;border-top:1px solid #e0e0e0;">
          <h2 style="margin:0 0 14px 0;font-size:16px;color:#0f9d58;">&#x1F4C5; R&eacute;sum&eacute; de la semaine ({len(rapports_hebdo)} alertes)</h2>
          {_summary_table_html(rapports_hebdo, counts_hebdo)}
        </td></tr>"""

    if rapports_mensuel is not None:
        counts_mensuel = _sentiment_counts(rapports_mensuel)
        extra_sections += f"""
        <tr><td style="background:#f8f9fa;padding:24px 30px;border-top:1px solid #e0e0e0;">
          <h2 style="margin:0 0 14px 0;font-size:16px;color:#f4511e;">&#x1F4C6; R&eacute;sum&eacute; du mois ({len(rapports_mensuel)} alertes)</h2>
          {_summary_table_html(rapports_mensuel, counts_mensuel)}
        </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f3f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f3f4;padding:30px 0;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;">

        <!-- HEADER -->
        <tr><td style="background:{color};border-radius:8px 8px 0 0;padding:30px 30px 20px 30px;">
          <h1 style="margin:0;color:#ffffff;font-size:22px;">{subject}</h1>
          <p style="margin:6px 0 0 0;color:rgba(255,255,255,0.85);font-size:14px;">
            {nb} alerte{"s" if nb != 1 else ""} collect&eacute;e{"s" if nb != 1 else ""} dans les derni&egrave;res 24h
          </p>
        </td></tr>

        <!-- ALERTES DU JOUR -->
        <tr><td style="background:#f8f9fa;padding:24px 30px;">
          {cards}
        </td></tr>

        <!-- RÉCAP JOUR -->
        <tr><td style="background:#ffffff;padding:24px 30px;border-top:1px solid #e0e0e0;">
          <h2 style="margin:0 0 14px 0;font-size:16px;color:#202124;">R&eacute;capitulatif du jour</h2>
          {summary_jour}
        </td></tr>

        {extra_sections}

        <!-- FOOTER -->
        <tr><td style="background:{color};border-radius:0 0 8px 8px;padding:16px 30px;text-align:center;">
          <p style="margin:0;color:rgba(255,255,255,0.8);font-size:12px;">
            Rapport g&eacute;n&eacute;r&eacute; automatiquement par Google Alerts Agent &mdash; {_date_fr()}
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def generate_rapport_jour(rapports_jour, rapports_hebdo=None, rapports_mensuel=None):
    subject = _subject("journalier")
    body_html = _build_html_jour(rapports_jour, rapports_hebdo, rapports_mensuel, subject)
    body_text = _build_text("journalier", rapports_jour, subject)
    return {"subject": subject, "body_html": body_html, "body_text": body_text}


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def generate(rapports, type_rapport):
    subject = _subject(type_rapport)

    if not rapports:
        no_alert_msg = f"Aucune alerte Google Alerts pour ce rapport {type_rapport} ({_date_fr()})."
        body_html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;padding:40px;color:#444;">
  <h2 style="color:#1a73e8;">{subject}</h2>
  <p>{no_alert_msg}</p>
</body></html>"""
        return {"subject": subject, "body_html": body_html, "body_text": f"{subject}\n\n{no_alert_msg}"}

    return {
        "subject": subject,
        "body_html": _build_html(type_rapport, rapports, subject),
        "body_text": _build_text(type_rapport, rapports, subject),
    }
