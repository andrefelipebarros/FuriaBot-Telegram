from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import asyncio

async def fetch_upcoming_matches(team_slug: str = '330-FURIA') -> list[dict]:
    url = f'https://draft5.gg/equipe/{team_slug}/proximas-partidas'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        # espera o container de partidas aparecer
        await page.wait_for_selector('p.MatchList__MatchListDate-sc-1pio0qc-0', timeout=10000)
        content = await page.content()
        await browser.close()

    soup = BeautifulSoup(content, 'html.parser')
    results = []
    for date_tag in soup.select('p.MatchList__MatchListDate-sc-1pio0qc-0'):
        date_text = date_tag.get_text(strip=True).replace('📅 ', '')
        for card in date_tag.find_next_siblings():
            if card.name == 'p' and 'MatchList__MatchListDate-sc-1pio0qc-0' in card.get('class', []):
                break
            if card.name == 'a' and 'MatchCardSimple__MatchContainer-sc-wcmxha-0' in card.get('class', []):
                time_text = card.select_one('small.MatchCardSimple__MatchTime-sc-wcmxha-3').get_text(strip=True)
                teams = card.select('div.MatchCardSimple__MatchTeam-sc-wcmxha-11')
                (team1, score1), (team2, score2) = [
                    (
                        div.select_one('span').get_text(strip=True),
                        div.select_one('div.MatchCardSimple__Score-sc-wcmxha-15').get_text(strip=True)
                    )
                    for div in teams
                ]
                best_of = card.select_one('div.MatchCardSimple__Badge-sc-wcmxha-18').get_text(strip=True)
                tournament = card.select_one('div.MatchCardSimple__Tournament-sc-wcmxha-34').get_text(strip=True)
                results.append({
                    'date': date_text,
                    'time': time_text,
                    'team1': team1, 'score1': score1,
                    'team2': team2, 'score2': score2,
                    'best_of': best_of,
                    'tournament': tournament
                })
    return results

# para testar
if __name__ == '__main__':
    data = asyncio.run(fetch_upcoming_matches())
    print(data)
