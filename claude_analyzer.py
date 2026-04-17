import json
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-20250514"

PROMPT_TEMPLATE = """Tu es un analyste de veille stratégique. Analyse l'article suivant et retourne UNIQUEMENT un objet JSON valide, sans texte avant ni après.

Mot-clé de recherche : {keyword}
URL : {url}
Titre : {title}

Contenu :
{content}

Retourne ce JSON et rien d'autre :
{{
  "resume": "résumé en 3 phrases maximum",
  "points_cles": ["point 1", "point 2", "point 3", "point 4", "point 5"],
  "sentiment": "positif" | "neutre" | "négatif",
  "pertinence": <entier de 1 à 10>,
  "categorie": "thème principal de l'article"
}}"""


def analyze(title, content, url, keyword):
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = PROMPT_TEMPLATE.format(
        keyword=keyword,
        url=url,
        title=title,
        content=content,
    )

    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    except anthropic.APIError as e:
        print(f"[claude_analyzer] API error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"[claude_analyzer] JSON parse error: {e}\nRaw response: {raw}")
        return None
