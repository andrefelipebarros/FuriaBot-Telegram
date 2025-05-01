import re
import requests
from bs4 import BeautifulSoup

def get_latest_match_info(team_slug: str, headers: dict) -> dict | None:
    """
    Recupera os dados do último jogo para `team_slug` em Liquipedia,
    lendo a página de Matches (não Results).

    Args:
        team_slug: 'FURIA' ou 'FURIA_Female'
        headers: dicionário de headers (User-Agent, Referer, etc.)

    Retorna um dict com:
        Date, Event, Opponent, Score, Result
    ou None se não encontrar nada.
    """

    url = f'https://liquipedia.net/counterstrike/{team_slug}/Matches?action=render'
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        table = soup.find('table', class_='wikitable')
        if not table:
            return None

        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            # neste layout há pelo menos 9 colunas.
            if len(cols) >= 9:
                # 0 = data, 5 = evento, 7 = placar, 8 = adversário
                date     = cols[0].text.strip()
                event    = cols[5].text.strip()
                score    = cols[7].text.strip()

                # extrai adversário via <a title="…">
                opp_a    = cols[8].find('a', title=True)
                opponent = opp_a['title'].strip() if opp_a else cols[8].text.strip()

                # determina vitória/derrota comparando números do placar
                m = re.findall(r'\d+', score)
                if len(m) >= 2:
                    left, right = map(int, m[:2])
                    result = "Vitória!🎉" if left > right else "Derrota...😿"
                else:
                    result = "Vitória!🎉" if "win" in score.lower() else "Derrota...😿"

                return {
                    "Date": date,
                    "Event": event,
                    "Opponent": opponent,
                    "Score": score,
                    "Result": result
                }

        # se não achou nenhuma linha válida
        return None

    except requests.exceptions.RequestException:
        return None
