from __future__ import annotations

import bisect
import statistics
from typing import Optional

from demoparser2 import DemoParser

DEFAULT_TICKRATE = 64
ROUND_TIME_SECONDS = 115  # раунд 1:55
WARNING_SECONDS_LEFT = 10


def detect_tickrate(parser: DemoParser) -> tuple[int, str]:
    """
    Оцінка tickrate з демки: round_time_warning vs round_freeze_end.
    Повертає (tickrate, джерело: 'detected' | 'default').
    """
    try:
        freeze_ends = parser.parse_event("round_freeze_end").sort_values("tick")["tick"].tolist()
        warnings = parser.parse_event("round_time_warning").sort_values("tick")["tick"].tolist()
    except Exception:
        return DEFAULT_TICKRATE, "default"

    if not freeze_ends or not warnings:
        return DEFAULT_TICKRATE, "default"

    elapsed_at_warning = ROUND_TIME_SECONDS - WARNING_SECONDS_LEFT
    estimates: list[float] = []

    for warning_tick in warnings:
        freezes_before = [tick for tick in freeze_ends if tick < warning_tick]
        if not freezes_before:
            continue

        delta_ticks = int(warning_tick) - int(freezes_before[-1])
        if delta_ticks > 0:
            estimates.append(delta_ticks / elapsed_at_warning)

    if not estimates:
        return DEFAULT_TICKRATE, "default"

    detected = round(statistics.median(estimates))
    if detected in (64, 128):
        return detected, "detected"

    return DEFAULT_TICKRATE, "default"


def _team_by_name(player_info) -> dict[str, int]:
    return dict(zip(player_info["name"], player_info["team_number"]))


def _load_freeze_end_ticks(parser: DemoParser) -> list[int]:
    return sorted(int(t) for t in parser.parse_event("round_freeze_end")["tick"].tolist())


def _freeze_end_before_tick(tick: int, freeze_ends: list[int]) -> Optional[int]:
    """Останній round_freeze_end перед подією — початок ігрового часу раунду."""
    idx = bisect.bisect_right(freeze_ends, tick) - 1
    if idx < 0:
        return None
    return freeze_ends[idx]


def _round_clock(tick: int, freeze_end_tick: Optional[int], tickrate: int) -> Optional[str]:
    """
    Round-relative clock: час, що залишився на таймері раунду (1:55 → 0:00).
  """
    if freeze_end_tick is None or tick < freeze_end_tick:
        return None

    elapsed = (tick - freeze_end_tick) / tickrate
    remaining = max(0.0, ROUND_TIME_SECONDS - elapsed)
    minutes = int(remaining) // 60
    seconds = int(remaining) % 60
    return f"{minutes}:{seconds:02d}"


def _normalize_kill(row, team_by_name: dict[str, int]) -> dict:
    victim_name = row["user_name"]
    attacker_name = row.get("attacker_name")

    victim_pos = None
    if row.get("user_X") is not None:
        victim_pos = {
            "x": float(row["user_X"]),
            "y": float(row["user_Y"]),
            "z": float(row["user_Z"]),
        }

    round_num = (
        int(row["total_rounds_played"]) + 1
        if row.get("total_rounds_played") is not None
        else None
    )

    return {
        "tick": int(row["tick"]),
        "round": round_num,
        "attacker_name": attacker_name,
        "attacker_steamid": int(row["attacker_steamid"]) if row.get("attacker_steamid") else None,
        "attacker_team": team_by_name.get(attacker_name),
        "victim_name": victim_name,
        "victim_steamid": int(row["user_steamid"]) if row.get("user_steamid") else None,
        "victim_team": team_by_name.get(victim_name),
        "victim_pos": victim_pos,
        "weapon": row.get("weapon"),
        "headshot": bool(row.get("headshot", False)),
        "kill_distance": round(float(row["distance"]), 1) if row.get("distance") is not None else None,
    }


def parse_demo(path: str, tickrate: Optional[int] = None) -> dict:
    parser = DemoParser(path)
    header = parser.parse_header()
    player_info = parser.parse_player_info()
    team_by_name = _team_by_name(player_info)
    freeze_ends = _load_freeze_end_ticks(parser)

    if tickrate is None:
        tickrate, tickrate_source = detect_tickrate(parser)
    else:
        tickrate_source = "manual"

    deaths = parser.parse_event(
        "player_death",
        player=["X", "Y", "Z"],
        other=["total_rounds_played"],
    )

    kills = []
    for _, row in deaths.iterrows():
        if not row.get("attacker_name") or not row.get("user_name"):
            continue
        if row.get("attacker_steamid") == row.get("user_steamid"):
            continue

        kill = _normalize_kill(row, team_by_name)
        kill["gameTime"] = round(kill["tick"] / tickrate, 2)
        kill["roundClock"] = _round_clock(
            kill["tick"],
            _freeze_end_before_tick(kill["tick"], freeze_ends),
            tickrate,
        )
        kills.append(kill)

    kills.sort(key=lambda k: k["tick"])

    return {
        "map_name": header.get("map_name"),
        "tickrate": tickrate,
        "tickrate_source": tickrate_source,
        "kills": kills,
        "players": player_info.to_dict(orient="records"),
    }
