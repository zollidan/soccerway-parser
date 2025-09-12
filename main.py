import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
import sys
import time

from tqdm import tqdm

# Режим тестирования (True - загрузка из файлов, False - запросы к API)
TESTING = True

BASE_URL = "https://int.soccerway.com/v1/english/matches/soccer/from/{}/to/{}/"
GAME_URL = "https://int.soccerway.com/v1/english/match/soccer/full/{}}/"
H2H_URL = "https://int.soccerway.com/legacy/v1/english/matches/?h2hIds={}%2C{}&limit=50&onlydetails=true"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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

logging.basicConfig(filename='app.log', filemode='a', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

H2H_RATE_LIMIT_SECONDS = 1.0  # минимальный интервал между запросами H2H
H2H_MAX_RETRIES = 3           # количество повторов при ошибках/429
H2H_BACKOFF_FACTOR = 1.5      # коэффициент экспоненциальной паузы

# Кэш и контроль частоты запросов
H2H_CACHE = {}
_last_request_time = 0.0
_session = requests.Session()


def _rate_limit_wait():
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < H2H_RATE_LIMIT_SECONDS:
        time.sleep(H2H_RATE_LIMIT_SECONDS - elapsed)
    _last_request_time = time.time()


def _get_with_retries(url, headers=None, max_retries=H2H_MAX_RETRIES):
    """HTTP GET с ограничением частоты, повторами и обработкой 429/5xx."""
    attempt = 0
    delay = H2H_RATE_LIMIT_SECONDS
    while True:
        try:
            _rate_limit_wait()
            resp = _session.get(url, headers=headers, timeout=30)
            if resp.status_code == 429:
                retry_after = resp.headers.get('Retry-After')
                wait_s = float(
                    retry_after) if retry_after and retry_after.isdigit() else delay
                logging.warning(
                    f"Получен 429 Too Many Requests. Ожидание {wait_s} сек и повтор…")
                time.sleep(wait_s)
                attempt += 1
            elif resp.status_code == 403:
                logging.warning(
                    f"Получен 403 Forbidden. Возможна блокировка. Ожидание {delay * 2:.1f} сек и повтор…")
                time.sleep(delay * 2)  # Увеличенная задержка для 403
                attempt += 1
            elif 500 <= resp.status_code < 600:
                logging.warning(
                    f"Серверная ошибка {resp.status_code}. Повтор через {delay:.1f} сек…")
                time.sleep(delay)
                attempt += 1
            else:
                resp.raise_for_status()
                return resp.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            logging.warning(
                f"Сетевой сбой: {e}. Повтор через {delay:.1f} сек…")
            time.sleep(delay)
            attempt += 1
        except requests.exceptions.HTTPError as e:
            # Для прочих кодов HTTP — не повторяем бесконечно
            logging.error(f"HTTP ошибка: {e}")
            raise
        except json.JSONDecodeError as e:
            logging.warning(f"Ошибка JSON: {e}. URL: {url} Повтор через {delay:.1f} сек…")
            time.sleep(delay)
            attempt += 1

        if attempt >= max_retries:
            raise RuntimeError("Превышено число попыток запроса")


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


def fetch_h2h_data(team1_id, team2_id):
    """Запрос H2H статистики между двумя командами с кэшем и повторами."""
    key = tuple(sorted([str(team1_id), str(team2_id)]))
    if key in H2H_CACHE:
        return H2H_CACHE[key]

    if TESTING:
        try:
            with open('h2h.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(
                f"Загружена тестовая H2H статистика из файла для команд {team1_id} и {team2_id}")
            H2H_CACHE[key] = data
            return data
        except FileNotFoundError:
            logging.error("Файл h2h.json не найден")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"Ошибка парсинга тестового H2H JSON: {e}")
            return None
    else:
        try:
            h2h_url = H2H_URL.format(team1_id, team2_id)
            data = _get_with_retries(h2h_url, headers=HEADERS)
            logging.info(
                f"Получена H2H статистика для команд {team1_id} и {team2_id}")
            H2H_CACHE[key] = data
            return data
        except Exception as e:
            logging.error(f"Ошибка получения H2H: {e}")
            return None


def parse_h2h_stats(h2h_data, team1_id, team2_id):
    """Парсинг H2H статистики для обеих команд"""
    stats = {
        'h2h_игры_дома_ком1': 0,
        'h2h_побед_дома_ком1': 0,
        'h2h_ничьи_ком1': 0,
        'h2h_побед_гостей_ком1': 0,
        'h2h_игры_дома_ком2': 0,
        'h2h_побед_дома_ком2': 0,
        'h2h_ничьи_ком2': 0,
        'h2h_побед_гостей_ком2': 0,
    }

    if not h2h_data or 'matches' not in h2h_data:
        return stats

    for match in h2h_data['matches'][:15]:
        teams = match.get('teams', [])
        if len(teams) < 2:
            continue

        home_team = teams[0]
        away_team = teams[1]

        home_team_id = home_team.get('id')
        away_team_id = away_team.get('id')

        # Учитываем только личные встречи этих двух команд
        if (str(home_team_id) == str(team1_id) and str(away_team_id) == str(team2_id)) or \
           (str(home_team_id) == str(team2_id) and str(away_team_id) == str(team1_id)):

            winner = match.get('winner', -1)

            # FIXME: непраильный подсчет победа ничья
            # Статистика, когда команда 1 играла дома
            if str(home_team_id) == str(team1_id):
                stats['h2h_игры_дома_ком1'] += 1
                if winner == 0:
                    stats['h2h_побед_дома_ком1'] += 1
                elif winner == 1:
                    stats['h2h_побед_гостей_ком1'] += 1
                elif winner == -1:
                    stats['h2h_ничьи_ком1'] += 1

            # Статистика, когда команда 2 играла дома
            if str(home_team_id) == str(team2_id):
                stats['h2h_игры_дома_ком2'] += 1
                if winner == 0:
                    stats['h2h_побед_дома_ком2'] += 1
                elif winner == 1:
                    stats['h2h_побед_гостей_ком2'] += 1
                elif winner == -1:
                    stats['h2h_ничьи_ком2'] += 1

    return stats


def parse_match_data(data):
    """Парсинг данных матчей из полученного JSON"""
    matches = []

    if not data or not isinstance(data, list):
        logging.warning("Нет данных для парсинга")
        return matches

    for tournament in tqdm(data, desc="Лиги"):
        tournament_info = {
            'st_name': tournament.get('st_name', ''),
            'st_code': tournament.get('st_code', ''),
            'c_name': tournament.get('c_name', ''),
            'season_info': tournament.get('season_info', {}).get('name', ''),
            'phase_info': tournament.get('phase_info', {}).get('name', '')
        }

        for match in tqdm(tournament.get('matches', []), desc="Игры в лиге", leave=False):
            # Парсинг даты и времени
            match_datetime = datetime.fromtimestamp(
                match.get('start', 0)) if match.get('start') else datetime.now()

            match_data = {
                'число': match_datetime.day,
                'месяц': match_datetime.month,
                'год': match_datetime.year,
                'время': match_datetime.strftime('%H:%M'),
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
                    'команда 1': home_team.get('name', ''),
                    'команда 2': away_team.get('name', ''),
                    'команда1команда2': f"{home_team.get('name', '')}{away_team.get('name', '')}",
                    'соревнование': tournament_info['st_name'],
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

            # Добавляем H2H статистику для каждого матча с защитой и кэшем
            if len(teams) >= 2:
                home_team_id = teams[0].get('id')
                away_team_id = teams[1].get('id')
                try:
                    if home_team_id and away_team_id:
                        h2h_data = fetch_h2h_data(home_team_id, away_team_id)
                        h2h_stats = parse_h2h_stats(
                            h2h_data, home_team_id, away_team_id)
                        match_data.update(h2h_stats)
                    else:
                        match_data.update({
                            'h2h_игры_дома': 0,
                            'h2h_побед_дома': 0,
                            'h2h_ничьи': 0,
                            'h2h_побед_гостей': 0,
                            'h2h_игры_дома_ком2': 0,
                            'h2h_побед_дома_ком2': 0,
                            'h2h_ничьи_ком2': 0,
                            'h2h_побед_гостей_ком2': 0,
                        })
                except Exception as e:
                    logging.warning(
                        f"Не удалось получить H2H для матча {match.get('id')}: {e}")
                    # Заполняем нулями при ошибках — сохраняем максимум данных
                    match_data.update({
                        'h2h_игры_дома': 0,
                        'h2h_побед_дома': 0,
                        'h2h_ничьи': 0,
                        'h2h_побед_гостей': 0,
                        'h2h_игры_дома_ком2': 0,
                        'h2h_побед_дома_ком2': 0,
                        'h2h_ничьи_ком2': 0,
                        'h2h_побед_гостей_ком2': 0,
                    })

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


def get_date_input():
    """Получение даты от пользователя через консоль"""
    print("\n=== Выбор периода для поиска матчей ===")

    while True:
        print("\nВыберите способ ввода даты:")
        print("1 - Указать конкретную дату (YYYY-MM-DD)")
        print("2 - Сегодня")
        print("3 - Вчера")
        print("4 - Завтра")
        print("5 - Указать период (от и до)")

        try:
            choice = input("\nВведите номер (1-5): ").strip()

            if choice == "1":
                date_str = input("Введите дату (YYYY-MM-DD): ").strip()
                selected_date = datetime.strptime(date_str, "%Y-%m-%d")
                from_date = selected_date.strftime("%Y-%m-%dT21:00:00")
                to_date = (selected_date + timedelta(days=1)
                           ).strftime("%Y-%m-%dT21:00:00")
                return from_date, to_date

            elif choice == "2":
                today = datetime.now()
                from_date = today.strftime("%Y-%m-%dT21:00:00")
                to_date = (today + timedelta(days=1)
                           ).strftime("%Y-%m-%dT21:00:00")
                return from_date, to_date

            elif choice == "3":
                yesterday = datetime.now() - timedelta(days=1)
                from_date = yesterday.strftime("%Y-%m-%dT21:00:00")
                to_date = datetime.now().strftime("%Y-%m-%dT21:00:00")
                return from_date, to_date

            elif choice == "4":
                tomorrow = datetime.now() + timedelta(days=1)
                from_date = tomorrow.strftime("%Y-%m-%dT21:00:00")
                to_date = (tomorrow + timedelta(days=1)
                           ).strftime("%Y-%m-%dT21:00:00")
                return from_date, to_date

            elif choice == "5":
                from_str = input("Введите дату начала (YYYY-MM-DD): ").strip()
                to_str = input("Введите дату окончания (YYYY-MM-DD): ").strip()

                from_date = datetime.strptime(from_str, "%Y-%m-%d")
                to_date = datetime.strptime(
                    to_str, "%Y-%m-%d") + timedelta(days=1)

                return from_date.strftime("%Y-%m-%dT21:00:00"), to_date.strftime("%Y-%m-%dT21:00:00")

            else:
                print("Ошибка: выберите номер от 1 до 5")

        except ValueError as e:
            print(f"Ошибка формата даты: {e}")
            print("Используйте формат YYYY-MM-DD (например, 2025-09-10)")
        except KeyboardInterrupt:
            print("\nВыход из программы...")
            sys.exit(0)


def main():
    """Основная функция программы"""
    logging.info("Запуск приложения")

    try:
        from_date, to_date = get_date_input()
        url = BASE_URL.format(from_date, to_date)

        print(f"\nЗапрос данных за период: {from_date[:10]} - {to_date[:10]}")

        if TESTING:
            # В режиме тестирования загружаем данные из файлов
            try:
                with open('example.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logging.info("Загружены тестовые данные из файла example.json")
            except FileNotFoundError:
                logging.error("Файл example.json не найден, пробуем h2h.json")
                try:
                    with open('h2h.json', 'r', encoding='utf-8') as f:
                        h2h_example = json.load(f)

                    data = [{'matches': [h2h_example['matches'][0]], 'st_name': 'Test', 'st_code': 'test',
                             'c_name': 'Test', 'season_info': {'name': 'Test'}, 'phase_info': {'name': 'Test'}}]
                    logging.info("Загружены тестовые данные из файла h2h.json")
                except FileNotFoundError:
                    logging.error("Файлы example.json и h2h.json не найдены")
                    data = None
        else:
            data = fetch_matches_data(url)

        if not data:
            logging.error("Не удалось получить данные")
            return

        matches = parse_match_data(data)

        if matches:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"matches_{timestamp}.xlsx"

            if save_to_excel(matches, filename):
                logging.info(
                    f"Успешно сохранено {len(matches)} матчей в файл: {filename}")
            else:
                logging.error("Ошибка при сохранении данных")
        else:
            logging.error("Нет данных для сохранения")

    except KeyboardInterrupt:
        logging.info("Выход из программы...")
        sys.exit(0)


if __name__ == '__main__':
    main()
