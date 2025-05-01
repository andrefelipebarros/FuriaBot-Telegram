import datetime
import requests
from bs4 import BeautifulSoup
from typing import Dict
from typing import Optional
from services.result_matcher import get_latest_match_info

URL_TEMPLATE = 'https://bo3.gg/matches/{team_slug}-vs-{opponent_slug}-{date_slug}'

def build_bo3_url(team_slug: str, headers: dict) -> Optional[str]:
    info = get_latest_match_info(team_slug, headers)
    if not info:
        print('❌ Não foi possível obter informações do jogo.')
        return None

    # converte data
    raw_date = info['Date'].split(' -', 1)[0].strip()
    dt = None
    for fmt in ('%d %b %Y','%b %d, %Y','%Y-%m-%d'):
        try:
            dt = datetime.datetime.strptime(raw_date, fmt)
            break
        except ValueError:
            continue
    if not dt:
        print('❌ Data em formato inesperado:', raw_date)
        return None
    date_slug = dt.strftime('%d-%m-%Y')

    # formata o slug da equipe FURIA ou FURIA_Female
    if team_slug == 'FURIA':
        team_slug_formatted = 'furia'
    elif team_slug == 'FURIA_Female':
        team_slug_formatted = 'furia-fe'
    else:
        team_slug_formatted = team_slug.lower()

    # formata slug do adversário
    raw_opp = info['Opponent'].lower()
    # remove sufixo "female" para extrair base
    base = raw_opp.replace('_female','').replace(' female','')
    # troca espaços e underscores por hífen apenas na base
    base = base.replace(' ', '-').replace('_','-')

    # se for line feminina, append "_fe", senão nada
    if team_slug == 'FURIA_Female':
        opponent_slug = f"{base}_fe"
    else:
        opponent_slug = base

    # monta as duas variantes só para debug (normal e fallback)
    url = URL_TEMPLATE.format(
        team_slug=team_slug_formatted,
        opponent_slug=opponent_slug,
        date_slug=date_slug
    )

    # checa se deu 404; se sim, tenta a variante com hífen antes do "_fe"
    try:
        r = requests.head(url, headers=headers, timeout=5)
        if r.status_code == 404 and '_fe' in opponent_slug:
            # tenta trocar "_fe" por "-fe"
            alt_slug = opponent_slug.replace('_fe','-fe')
            alt_url = URL_TEMPLATE.format(
                team_slug=team_slug_formatted,
                opponent_slug=alt_slug,
                date_slug=date_slug
            )
            print(f"⚠️ 404 na URL “{url}”, tentando fallback “{alt_url}”")
            r2 = requests.head(alt_url, headers=headers, timeout=5)
            if r2.status_code == 200:
                print(f"✅ Fallback válido: {alt_url}")
                return alt_url
    except Exception as e:
        print("⚠️ Erro no head-check:", e)

    print(f'URL montada: {url}')
    return url

def get_furia_score(url: str) -> Optional[str]:
    """
    Busca o placar da FURIA na URL fornecida.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Garantir que a requisição tenha sido bem-sucedida
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrar a tabela onde o placar da FURIA está
        players_table = soup.find_all('div', class_='table-row')
        
        for player_row in players_table:
            # Verifique se o jogador é da FURIA
            player_name = player_row.find('span', class_='nickname')
            if player_name and 'FURIA' in player_name.text:  # Confirma se é um jogador da FURIA
                score_cells = player_row.find_all('div', class_='table-cell')
                if score_cells:
                    # Extraímos os dados de "K", "D", "A" (Kills, Deaths, Assists)
                    kills = score_cells[0].text.strip()
                    deaths = score_cells[1].text.strip()
                    assists = score_cells[2].text.strip()
                    return f'Kills: {kills}, Deaths: {deaths}, Assists: {assists}'
        return None
    except Exception as e:
        print(f'Erro ao obter o placar: {e}')
        return None


def get_furia_scoreboard(url: str, max_players: int = 5) -> Dict[str, Dict[str, str]]:
    resp = requests.get(url, timeout=3)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')

    scoreboard: Dict[str, Dict[str, str]] = {}
    rows = soup.find_all('div', class_='table-row')

    for row in rows:
        if 'total' in row.get('class', []):
            continue

        nick_tag = row.find('span', class_='nickname')
        if not nick_tag:
            continue

        nick = nick_tag.text.strip()

        kills = row.select_one('div.table-cell.kills p.value')
        deaths = row.select_one('div.table-cell.deaths p.value')
        assists = row.select_one('div.table-cell.assists p.value')
        adr = row.select_one('div.table-cell.adr p.value')
        score = row.select_one('span.c-table-cell-score__value')

        scoreboard[nick] = {
            'Kills': kills.text.strip() if kills else '-',
            'Deaths': deaths.text.strip() if deaths else '-',
            'Assists': assists.text.strip() if assists else '-',
            'ADR': adr.text.strip() if adr else '-',
            'Score': score.text.strip() if score else '-',
        }

        if len(scoreboard) >= max_players:
            break

    return scoreboard