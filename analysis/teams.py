from typing import Optional

TEAM_LABELS = {
    0: "Unassigned",
    1: "Spectator",
    2: "T",
    3: "CT",
}


def team_label(team_number: Optional[int]) -> Optional[str]:
    if team_number is None:
        return None
    return TEAM_LABELS.get(team_number, f"Team{team_number}")
