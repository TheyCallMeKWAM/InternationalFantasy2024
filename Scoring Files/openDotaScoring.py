import json
import requests
import logging
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load submission data
with open('submissions.json', 'r') as file:
    data = json.load(file)
submissions = data.get('submissions', {})

# Constants
OPENDOTA_MATCH_URL = 'https://api.opendota.com/api/matches/'
SCORING_VALUES = {
    'kills': 3, 
    'assists': 2, 
    'deaths': -1, 
    'last_hits': 0.02,
    'denies': 0.02, 
    'obs_placed': 0.2, 
    'sen_placed': 0.2, 
    'camps_stacked': .5,
    'match_win_bonus': 15, 
    'under_25_min_bonus': 15, 
    '20_plus_kills_assists_bonus': 2
}

TEAM_SCORING_VALUES = {
    'tower_kills': 1,
    'barrack_kills': 1,
    'roshan_kills': 3,
    'first_blood': 2,
    'win': 2,
}

# Player dictionary (player map)
player_dict = {
    "Collapse": 302214028,
    "Miposhka": 113331514,
    "Raddan": 321580662,
    "Mira": 256156323,
    "Larl": 106305042,
    "Dy": 143693439,
    "XinQ": 157475523,
    "Xm": 137129583,
    "Xxs": 129958758,
    "Ame": 898754153,
    "Insania": 54580962,
    "miCKe": 152962063,
    "Boxi": 77490514,
    "Nisha": 201358612,
    "33": 86698277,
    "Seleri": 91730177,
    "Ace": 97590558,
    "tOfu": 16497807,
    "dyrachyo": 116934015,
    "Quinn": 221666230,
    "Save-": 317880638,
    "Saika": 124801257,
    "gpk~": 480412663,
    "TORONTOTOKYO": 431770905,
    "MieRo": 165564598,
    "Topson": 94054712,
    "Whitemon": 136829091,
    "9Class": 164199202,
    "Pure": 331855530,
    "Tobi": 140288368,
    "zzq": 249835593,
    "7eeeeeee": 179313961,
    "Beyond": 139031324,
    "ponlo": 193884241,
    "YSR-04E": 170896543,
    "Gunnar": 126238768,
    "Lelis": 87063175,
    "Yuma": 177203952,
    "Fly": 94155156,
    "Copy": 115651292,
    "KingJungles": 81306398,
    "The Hector 'K1' Rodriguez": 164685175,
    "4nalog <01": 131303632,
    "Davai Lama": 138880576,
    "Scofield": 157989498,
    "AMMAR_THE_F": 183719386,
    "Cr1t-": 25907144,
    "skiter": 100058342,
    "Sneyking": 10366616,
    "Malr1ne": 898455820,
    "CHIRA_JUNIOR": 312436974,
    "RESPECT": 123787715,
    "swedenstrong": 175311897,
    "Munkushi~": 904131336,
    "Cloud": 168126336,
    "JT-": 138857296,
    "BoBoKa": 207829314,
    "NothingToSay": 173978074,
    "Monet": 148215639,
    "xNova": 94296097,
    "Mikoto": 301750126,
    "ponyo": 293904640,
    "Jhocam": 152859296,
    "Ws": 126842529,
    "Akashi": 330534326,
    "payk": 425588742,
    "MoOz": 349310876,
    "Vitaly": 138177198,
    "Lumpy": 118948666,
    "Elmisho": 1031547092,
    "Oli~": 101259972,
    "Jabz": 100471531,
    "Q": 193815691,
    "23savage": 375507918,
    "lorenof": 210053851,
    "Kataomi`": 196878136,
    "Fishman": 127565532,
    "watson`": 171262902,
    "DM": 56351509,
    "No[o]ne-": 106573901,
    "Saksa": 103735745
}

def get_match_data(match_id):
    retries = 1
    for _ in range(retries):
        try:
            response = requests.get(f'{OPENDOTA_MATCH_URL}{match_id}')
            response.raise_for_status()
            match_data = response.json()
            return match_data
        except requests.RequestException as e:
            logging.error(f"Error fetching match data for match ID {match_id}: {e}")
    return {}

def calculate_player_score(player_data):
    score = sum(
        player_data.get(stat, 0) * multiplier
        for stat, multiplier in SCORING_VALUES.items() if stat in player_data
    )
    logging.debug(f"Calculated player score: {score} for data: {player_data}")
    return score

def count_destroyed_towers(bitmask):
    bitmask_binary = bin(bitmask)[2:].zfill(11)
    destroyed_towers = bitmask_binary.count('0')
    return destroyed_towers

def count_destroyed_barracks(bitmask):
    bitmask_binary = bin(bitmask)[2:].zfill(6)
    destroyed_barracks = bitmask_binary.count('0')
    return destroyed_barracks

def calculate_team_score(match_data, team_name):
    team_score = 0

    radiant_team = match_data.get('radiant_name', '')
    dire_team = match_data.get('dire_name', '')

    if team_name == radiant_team:
        tower_status_bitmask = match_data.get('tower_status_dire', 0)
        barrack_status_bitmask = match_data.get('barracks_status_dire', 0)
        win = match_data.get('radiant_win')
    elif team_name == dire_team:
        tower_status_bitmask = match_data.get('tower_status_radiant', 0)
        barrack_status_bitmask = match_data.get('barracks_status_radiant', 0)
        win = not match_data.get('radiant_win')
    else:
        return team_score

    destroyed_towers = count_destroyed_towers(tower_status_bitmask)
    team_score += destroyed_towers * TEAM_SCORING_VALUES['tower_kills']

    destroyed_barracks = count_destroyed_barracks(barrack_status_bitmask)
    team_score += destroyed_barracks * TEAM_SCORING_VALUES['barrack_kills']

    if win:
        team_score += TEAM_SCORING_VALUES['win']

    first_blood = 0
    for objective in match_data.get('objectives', []):
        if objective.get('type') == 'CHAT_MESSAGE_FIRSTBLOOD':
            player_slot = objective.get('player_slot')
            if (player_slot < 128 and team_name == radiant_team) or (player_slot >= 128 and team_name == dire_team):
                first_blood += TEAM_SCORING_VALUES['first_blood']
                break

    team_score += first_blood

    logging.debug(f"Calculated team score: {team_score} for team '{team_name}'")
    return team_score

def process_player(player_name, match_data_cache):
    player_id = player_dict.get(player_name)
    if not player_id:
        logging.warning(f"Player ID not found for {player_name}")
        return 0

    player_score = 0
    found_in_any_match = False

    for match_id, match_data in match_data_cache.items():
        player_data = next((p for p in match_data.get('players', []) if p.get('account_id') == player_id), {})
        
        if player_data:
            player_score += calculate_player_score(player_data)
            found_in_any_match = True

    if not found_in_any_match:
        logging.warning(f"Player data not found for player ID {player_id} in any of the match IDs provided")

    logging.debug(f"Total player score for {player_name}: {player_score}")
    return player_score

def process_submission(submission_id, submission, match_data_cache):
    user_name = submission.get('userName', 'Unknown User')
    team_name = submission.get('team', 'Unknown Team')

    players = {role: submission.get(role, 'Unknown Player') for role in ['captain', 'carry1', 'carry2', 'carry3', 'support4', 'support5']}
    
    captain_name = players.get('captain')
    player_scores = {}
    if captain_name and captain_name != 'Unknown Player':
        player_scores[captain_name] = process_player(captain_name, match_data_cache) * 1.5

    player_scores.update({
        player_name: process_player(player_name, match_data_cache)
        for role, player_name in players.items()
        if player_name != 'Unknown Player' and role != 'captain'
    })
    
    total_player_score = sum(player_scores.values())
    total_team_score = sum(calculate_team_score(match_data_cache[match_id], team_name) for match_id in match_data_cache)

    player_scores_log = ', '.join(f"{name}: {score}" for name, score in player_scores.items())
    logging.info(f"Player scores for submission {user_name}: {player_scores_log}, team: {total_team_score}")

    total_score = total_player_score + total_team_score
    logging.info(f"Total score for submission {user_name}: {total_score}")

    return total_score

def main():
    match_ids = [7928957343,
                    7928927852,
                    7928964450,
                    7928915377,
                    7928969814,
                    7929126875,
                    7929199194,
                    7929170690,
                    7929250556,
                    7929545363,
                    7929598163,
                    7929019186,
                    7929087653,
                    7929005346,
                    7929057445,
                    7929316152,
                    7929405044,
                    7929024760,
                    7929080268,
                    7929188090,
                    7929314904]  # Example match IDs

    # Fetch match data once and store in a cache
    match_data_cache = {}
    for match_id in match_ids:
        match_data_cache[match_id] = get_match_data(match_id)

    results = {}
    
    with ThreadPoolExecutor() as executor:
        futures = {
            submission_id: executor.submit(process_submission, submission_id, submission, match_data_cache)
            for submission_id, submission in submissions.items()
        }

        for submission_id, future in futures.items():
            total_score = future.result()
            user_name = submissions.get(submission_id, {}).get('userName', 'Unknown User')
            results[user_name] = total_score

    logging.info(f"Results: {json.dumps(results, indent=2)}")

if __name__ == '__main__':
    main()
