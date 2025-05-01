import httpx
import os
from datetime import datetime, timezone

PANDASCORE_TOKEN = os.getenv("PANDASCORE_TOKEN")

async def fetch_next_match():
    if not PANDASCORE_TOKEN:
        raise RuntimeError("PANDASCORE_TOKEN não definido")
    url = "https://api.pandascore.co/csgo/matches/upcoming"
    params = {"per_page": 1, "token": PANDASCORE_TOKEN}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None
        match = data[0]

        begin_str = match.get("begin_at", "")  # Ex: "2025-04-28T17:00:00Z" ou "2025-04-28"
        # Converte para datetime (lida tanto com timestamp quanto só data)
        try:
            dt = datetime.fromisoformat(begin_str.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.fromisoformat(begin_str)

        hoje = datetime.now(timezone.utc).date()

        if dt.date() == hoje:
            date_text = "É HOJE! 🎉"
        else:
            if "T" not in begin_str:
                date_text = dt.strftime("%d/%m/%Y")
            else:
                date_text = dt.astimezone().strftime("%d/%m/%Y %H:%M")

        opponent = next(
            (op["opponent"]["name"]
             for op in match.get("opponents", [])
             if op["opponent"]["name"].lower() != "furia"),
            "Desconhecido"
        )

        return {
            "opponent": opponent,
            "date": date_text,
            "league": match.get("league", {}).get("name", ""),
        }
