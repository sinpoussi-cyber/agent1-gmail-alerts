import os
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

TABLE = "google_alerts_rapports"


def _client():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def insert_rapport(data):
    try:
        response = _client().table(TABLE).insert(data).execute()
        return response.data
    except Exception as e:
        print(f"[supabase] insert_rapport error: {e}")
        return None


def get_rapports_today():
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    try:
        response = (
            _client()
            .table(TABLE)
            .select("*")
            .gte("created_at", today)
            .lt("created_at", tomorrow)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[supabase] get_rapports_today error: {e}")
        return []


def get_rapports_week():
    since = (date.today() - timedelta(days=7)).isoformat()
    try:
        response = (
            _client()
            .table(TABLE)
            .select("*")
            .gte("created_at", since)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[supabase] get_rapports_week error: {e}")
        return []


def get_rapports_month():
    first_day = date.today().replace(day=1).isoformat()
    try:
        response = (
            _client()
            .table(TABLE)
            .select("*")
            .gte("created_at", first_day)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[supabase] get_rapports_month error: {e}")
        return []


def mark_sent(ids):
    if not ids:
        return None
    try:
        response = (
            _client()
            .table(TABLE)
            .update({"envoye_email": True})
            .in_("id", ids)
            .execute()
        )
        return response.data
    except Exception as e:
        print(f"[supabase] mark_sent error: {e}")
        return None
