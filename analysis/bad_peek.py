import math

from analysis.teams import team_label

MAX_DELTA_SECONDS = 3.0
MAX_VICTIM_DISTANCE = 250


def distance(a: dict, b: dict) -> float:
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)


def find_bad_peeks(parsed: dict) -> list[dict]:

    kills = parsed["kills"]
    map_name = parsed.get("map_name")
    suspicious = []

    for i in range(len(kills) - 1):
        k1 = kills[i]
        k2 = kills[i + 1]

        if k1["attacker_name"] != k2["attacker_name"]:
            continue

        team1 = k1.get("victim_team")
        team2 = k2.get("victim_team")
        if team1 is None or team2 is None or team1 != team2:
            continue

        delta = k2["gameTime"] - k1["gameTime"]
        if delta < 0 or delta > MAX_DELTA_SECONDS:
            continue

        if not k1.get("victim_pos") or not k2.get("victim_pos"):
            continue

        dist_between = round(distance(k1["victim_pos"], k2["victim_pos"]), 1)
        if dist_between >= MAX_VICTIM_DISTANCE:
            continue

        suspicious.append({
            "type": "possible_bad_peek",
            "mapName": map_name,
            "round": k2.get("round"),
            "attacker": k1["attacker_name"],
            "attackerTeam": team_label(k1.get("attacker_team")),
            "victims": [k1["victim_name"], k2["victim_name"]],
            "victimTeam": team_label(team1),
            "firstKillClock": k1.get("roundClock"),
            "secondKillClock": k2.get("roundClock"),
            "timeBetweenKills": round(delta, 2),
            "distanceBetweenVictims": dist_between,
            "weapons": [k1.get("weapon"), k2.get("weapon")],
            "headshots": [k1.get("headshot"), k2.get("headshot")],
            "killDistances": [k1.get("kill_distance"), k2.get("kill_distance")],
        })

    return suspicious
