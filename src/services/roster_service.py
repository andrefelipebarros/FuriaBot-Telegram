import httpx
from bs4 import BeautifulSoup

async def get_current_roster(team_slug: str) -> list[str]:
    """
    Retorna lista de nicknames do roster de `team_slug` em Liquipedia.
    """
    url = f'https://liquipedia.net/counterstrike/{team_slug}?action=render'
    headers = {
        'User-Agent': 'FuriaRosterBot/1.0',
        'Referer': f'https://liquipedia.net/counterstrike/{team_slug}'
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, timeout=10.0)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', class_='wikitable wikitable-striped roster-card')
    if not table:
        return []

    players = []
    for row in table.find_all('tr', class_='Player'):
        if 'roster-coach' in row.get('class', []):
            continue
        id_cell = row.find('td', class_='ID')
        if not id_cell:
            continue
        link = id_cell.find('a')
        if link and link.text.strip():
            players.append(link.text.strip())
    return players
