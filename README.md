# CS2 Demo Analyzer

Тестовое задание: из `.dem`-файлов Counter-Strike 2 находить моменты, когда игроки выходили на пик **по одному**, а не парой.



## Требования

- Python 3.9+
- Файлы `.dem` в папке `demos/`

## Структура проекта

```
cs2-demo-analyzer/
├── main.py              # точка входа
├── requirements.txt
├── demos/               # сюда кладутся .dem файлы
│   └── match1.dem
├── output/              # результаты анализа (JSON)
│   └── match1_bad_peeks.json
└── analysis/
    ├── parser.py        # парсинг демки (demoparser2)
    ├── bad_peek.py      # эвристика «пик по одному»
    └── teams.py         # CT / T
```

## Установка и запуск

Перейдите в папку проекта и положите демки в `demos/`. Дальше — команды для вашей ОС.

**macOS**

```bash
cd cs2-demo-analyzer
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python main.py
```

**Windows** (cmd или PowerShell)

```bat
cd cs2-demo-analyzer
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python main.py
```

Для каждого файла в `demos/` создаётся `output/<имя>_bad_peeks.json` (например, `match1.dem` → `match1_bad_peeks.json`).

## Формат результата (JSON)

```json
{
  "summary": {
    "demoFile": "match1.dem",
    "mapName": "de_mirage",
    "tickrate": 64,
    "tickrateSource": "detected",
    "totalKills": 207,
    "suspiciousMoments": 6
  },
  "moments": [ ... ]
}
```

### Поля `summary`

| Поле | Описание |
|------|----------|
| `demoFile` | Имя обработанной демки |
| `mapName` | Карта |
| `tickrate` | Тикрейт сервера (64 или 128) |
| `tickrateSource` | `detected` — из демки; `default` — fallback 64 |
| `totalKills` | Число убийств после фильтрации |
| `suspiciousMoments` | Найдено подозрительных моментов |

### Поля `moments[]`

```json
{
  "type": "possible_bad_peek",
  "mapName": "de_mirage",
  "round": 3,
  "attacker": "IceBerg",
  "attackerTeam": "CT",
  "victims": ["n0te", "joeski"],
  "victimTeam": "T",
  "firstKillClock": "1:08",
  "secondKillClock": "1:07",
  "timeBetweenKills": 1.66,
  "distanceBetweenVictims": 161.5,
  "weapons": ["m4a1_silencer", "m4a1_silencer"],
  "headshots": [false, false],
  "killDistances": [19.2, 15.8]
}
```


## Логика детекции

Момент считается подозрительным, если:

1. **Один и тот же** `attacker` делает **два килла подряд** (в ленте убийств демки)
2. Обе жертвы из **одной команды**
3. Между киллами **≤ 3 секунд**
4. Жертвы погибли **близко** друг к другу: `distanceBetweenVictims` **< 250** units

Паттерн: тиммейты по очереди вышли на один угол, враг забрал обоих — типичный «пик по одному».

## Технические детали

- **Парсер:** [demoparser2](https://pypi.org/project/demoparser2/) — Go не требуется
- **Tickrate:** определяется из демки (`round_freeze_end` + `round_time_warning`), иначе 64


## Зависимости

```
demoparser2>=0.30.0
pandas>=2.0.0
```
