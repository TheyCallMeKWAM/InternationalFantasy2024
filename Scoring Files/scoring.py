import json
import requests
import os
from dotenv import load_dotenv
load_dotenv() 

bearer_token = os.getenv('MY_KEY')

def fetch_match_data(match_id):
    url = f"https://api.stratz.com/api/v1/match/{match_id}"
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch data for match ID {match_id}: {response.status_code}")
        return {}
    
    return response.json()

def calculate_score(player_data):
    kills = player_data.get('numKills', 0)
    assists = player_data.get('numAssists', 0)
    deaths = player_data.get('numDeaths', 0)
    last_hits = player_data.get('numLastHits', 0)
    denies = player_data.get('numDenies', 0)
    wards_placed = len(player_data.get("wardPlaced", [])) # Need to Finish Wards Placed
    win = player_data.get('isVictory', False)

    score = (kills * 3) + (assists * 2) - (deaths * 1) + (last_hits * 0.02) + (denies * 0.02) + (wards_placed * 0.2)

    return score, win
    

def process_submissions(match_ids, submissions):
    player_name_to_id = {
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
        "m1CKe": 152962063,
        "Boxi": 77490514,
        "Nisha": 201358612,
        "33": 86698277,
        "Seleri": 91730177,
        "Ace ♠": 97590558,
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
        "k1 hector tqmM": 164685175,
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
        "Vitaly 誇り": 138177198,
        "Lumpy": 118948666,
        "Elmisho": 1031547092,
        "Oli~": 101259972,
        "Jabz": 100471531,
        "Q": 193815691,
        "23savage": 375507918,
        "lorenof": 210053851,
        "Kataomi": 196878136,
        "Fishman": 127565532,
        "医者watson": 171262902,
        "DM": 56351509,
        "No[o]ne-": 106573901,
    }
    
    results = {}

    for submission_id, submission in submissions.items():
        total_score = 0
        captain_score = 0
        captain_name = submission.get('captain')
        player_scores = []

        for match_id in match_ids:
            match_data = fetch_match_data(match_id)
            
            if not match_data or 'players' not in match_data:
                print(f"Warning: 'players' key not found in match data for match ID {match_id}")
                continue

            matchDuration = match_data.get('durationSeconds',0)
            
            
            

            players_data = match_data['players']

            for player_key in ['captain', 'carry1', 'carry2', 'carry3', 'support4', 'support5']:
                player_name = submission.get(player_key)
                player_id = player_name_to_id.get(player_name)
                
                if player_id is None:
                    print(f"Player {player_name} has no associated steamAccountId")
                    continue
                
                player_data = next((p for p in players_data if p.get('steamAccountId') == player_id), None)
                
                # Bonuses Being Given Out
                if player_data:
                    score, win = calculate_score(player_data)
                    
                    # Check for combined kills and assists bonus and provides points
                    if (player_data.get('numKills', 0) + player_data.get('numAssists', 0)) >= 20:
                        score += 2
                    # Check for Win Bonus and provides bonus points
                    if win:
                        score+= 15
                    # Check for Win Under 25 Bonus and provides bonus points
                    if matchDuration <= 3000 and win:
                        score += 15
                    # Apply Captain Bonus Points
                    if player_key == 'captain':
                        captain_score += score
                        captain_score *= 1.5
                    else:
                        player_scores.append((player_name, score))
                        total_score += score
                else:
                    print(f"Player {player_name} (ID: {player_id}) not found in match data")
        
        # Adds Captians Score to Final Total
        total_score += captain_score
               
        # Store the results for the current submission
        results[submission['userName']] = total_score

        # Print captain's score first, followed by player scores
        if captain_name:
            print(f"Captain: {captain_name}: {captain_score:.2f}")
        
        for player_name, score in player_scores:
            print(f"Player: {player_name}: {score:.2f}")

        # Print the total score after including the captain's adjusted score
        print(f"Total Score for {submission['userName']}: {total_score:.2f}")

    return results

# Example usage
match_ids = [7406531302]  # Replace with actual match IDs


with open('submissions.json') as f:
    submissions_data = json.load(f)

results = process_submissions(match_ids, submissions_data['submissions'])

print(json.dumps(results, indent=4))
