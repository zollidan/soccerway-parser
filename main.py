import requests
import json
import pandas as pd
from datetime import datetime
import logging

ALL_GAMES_URL = "https://int.soccerway.com/v1/english/matches/soccer/from/2025-09-09T21:00:00/to/2025-09-10T21:00:00/"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
    "Host": "int.soccerway.com",
    "Priority": "u=0, i",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "TE": "trailers",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0"
}

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_matches_data(url):
    """Запрос данных с API"""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        data = response.json()
        logging.info(f"Успешно получены данные с API")
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка запроса к API: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON: {e}")
        return None


def parse_match_data(data):
    """Парсинг данных матчей из полученного JSON"""
    matches = []

    if not data or not isinstance(data, list):
        logging.warning("Нет данных для парсинга")
        return matches

    for tournament in data:
        tournament_info = {
            'st_name': tournament.get('st_name', ''),
            'st_code': tournament.get('st_code', ''),
            'c_name': tournament.get('c_name', ''),
            'season_info': tournament.get('season_info', {}).get('name', ''),
            'phase_info': tournament.get('phase_info', {}).get('name', '')
        }

        for match in tournament.get('matches', []):
            match_data = {
                'Турнир': tournament_info['st_name'],
                'Код_турнира': tournament_info['st_code'],
                'Континент': tournament_info['c_name'],
                'Сезон': tournament_info['season_info'],
                'Фаза': tournament_info['phase_info'],
                'ID_матча': match.get('id', ''),
                'Статус': match.get('status', ''),
                'Дата_время': datetime.fromtimestamp(match.get('start', 0)).strftime('%Y-%m-%d %H:%M:%S') if match.get('start') else '',
                'Тур': match.get('round', ''),
                'Длительность': f"{match.get('elapsed', '')} {match.get('elapsed_t', '').lower()}",
            }

            teams = match.get('teams', [])
            if len(teams) >= 2:
                home_team = teams[0]
                away_team = teams[1]

                match_data.update({
                    'Команда_дома': home_team.get('name', ''),
                    'Команда_гостей': away_team.get('name', ''),
                    'Счет_дома': home_team.get('scores', {}).get('FINAL_RESULT', ''),
                    'Счет_гостей': away_team.get('scores', {}).get('FINAL_RESULT', ''),
                    'Счет_1тайм_дома': home_team.get('scores', {}).get('HALF_TIME', ''),
                    'Счет_1тайм_гостей': away_team.get('scores', {}).get('HALF_TIME', ''),
                })

                home_stats = home_team.get('stats', {})
                away_stats = away_team.get('stats', {})

                match_data.update({
                    'Желтые_карты_дома': home_stats.get('YELLOW_CARD', 0),
                    'Желтые_карты_гостей': away_stats.get('YELLOW_CARD', 0),
                    'Красные_карты_дома': home_stats.get('RED_CARD', 0),
                    'Красные_карты_гостей': away_stats.get('RED_CARD', 0),
                    'Угловые_дома': home_stats.get('CORNER_KICK', 0),
                    'Угловые_гостей': away_stats.get('CORNER_KICK', 0),
                    'Замены_дома': home_stats.get('SUBSTITUTION', 0),
                    'Замены_гостей': away_stats.get('SUBSTITUTION', 0),
                })

                home_form = home_team.get('form_o', {})
                away_form = away_team.get('form_o', {})

                match_data.update({
                    'Форма_дома_ppg': home_form.get('avg_ppg', 0),
                    'Форма_гостей_ppg': away_form.get('avg_ppg', 0),
                })

            odds = match.get('odds', [])
            if odds:
                bookmaker = odds[0].get('bookmaker', {})
                values = odds[0].get('values', [])

                match_data['Букмекер'] = bookmaker.get('name', '')

                for value in values:
                    outcome_code = value.get('outcome', {}).get('code', '')
                    price = value.get('price', {}).get('decimal', '')

                    if outcome_code == 'HOME':
                        match_data['Коэфф_П1'] = price
                    elif outcome_code == 'DRAW':
                        match_data['Коэфф_X'] = price
                    elif outcome_code == 'AWAY':
                        match_data['Коэфф_П2'] = price

            matches.append(match_data)

    logging.info(f"Обработано {len(matches)} матчей")
    return matches


def save_to_excel(matches, filename='matches.xlsx'):
    """Сохранение данных в Excel файл"""
    try:
        df = pd.DataFrame(matches)

        if df.empty:
            logging.warning("Нет данных для сохранения")
            return False

        df.to_excel(filename, index=False, engine='openpyxl')
        logging.info(f"Данные сохранены в файл: {filename}")
        return True

    except Exception as e:
        logging.error(f"Ошибка при сохранении в Excel: {e}")
        return False


def main():
    """Основная функция программы"""
    logging.info("Запуск приложения")

    data = fetch_matches_data(ALL_GAMES_URL)

    if not data:
        logging.error("Не удалось получить данные")
        return

    matches = parse_match_data(data)

    if matches:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matches_{timestamp}.xlsx"

        if save_to_excel(matches, filename):
            print(
                f"Успешно сохранено {len(matches)} матчей в файл: {filename}")
        else:
            print("Ошибка при сохранении данных")
    else:
        print("Нет данных для сохранения")


if __name__ == '__main__':
    main()
