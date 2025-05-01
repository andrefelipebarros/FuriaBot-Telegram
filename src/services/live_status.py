import httpx
import os

PANDASCORE_TOKEN = os.getenv("PANDASCORE_TOKEN")

async def fetch_live_match():
    """
    Consulta o endpoint de live score da Pandascore e devolve:
      {
        "round": int,        # rodada atual
        "score": "1x0",      # placar atual
        "team1": "FURIA",
        "team2": "MongolZ"
      }
    ou None se não houver partida ao vivo.
    """
    url = "https://api.pandascore.co/csgo/matches/live"
    params = {"token": PANDASCORE_TOKEN}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        match = data[0]
        
        # supondo que o JSON traga scores por rodada e infos necessárias:
        round_num = match["live"]["round"]
        t1 = match["opponents"][0]["opponent"]["name"]
        t2 = match["opponents"][1]["opponent"]["name"]
        score = f"{match['scores']['1']}x{match['scores']['2']}"
        return {
            "round": round_num,
            "score": score,
            "team1": t1,
            "team2": t2
        }
