"""nflverse injury reports (injury-history 6.6.5): weekly IR, PUP and Out statuses by Sleeper id."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ffapp.injury_reports import fetch_log, path, read_reports, reports_url, rosters_url, statuses, sync_reports
from ffapp.sleeper import SleeperError
from ffapp.store import Store, read_json

ROSTERS = """season,team,position,status,gsis_id,sleeper_id,week,game_type,status_description_abbr
2024,KC,WR,ACT,00-0039000,10229,4,REG,A01
2024,KC,WR,RES,00-0039000,10229,5,REG,R01
2024,KC,WR,RES,00-0039000,10229,7,REG,R01
2024,KC,WR,RES,00-0039000,10229,18,REG,R48
2024,SF,RB,RES,00-0031000,4034,9,REG,R04
2024,SF,RB,ACT,00-0032000,9999,9,REG,A01
2024,SF,OL,RES,00-0033000,7777,9,REG,R01
"""
REPORTS = """season,game_type,team,week,gsis_id,position,full_name,report_status
2024,REG,SF,9,00-0032000,RB,Back Up,Out
2024,REG,SF,9,00-0031000,RB,Star Back,Out
2024,REG,SF,10,00-0032000,RB,Back Up,Questionable
2024,REG,SF,10,00-0099999,RB,Unknown,Out
"""


def test_statuses_from_rosters_and_reports():
    """6.6.5: IR (R01, R48) and PUP (R04) from the weekly rosters, Out from the report; fantasy positions only."""
    weeks = statuses(ROSTERS, REPORTS)
    assert weeks["5"] == {"10229": "IR"} and weeks["7"] == {"10229": "IR"} and weeks["18"] == {"10229": "IR"}
    assert "4" not in weeks, "an active week has no status"
    assert weeks["9"] == {"4034": "PUP", "9999": "Out"}, "PUP wins over Out; offensive linemen are left out"
    assert "10" not in weeks, "Questionable and unmapped Players are not kept"


class Fake:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def get_text(self, url):
        self.calls.append(url)
        if self.fail:
            raise SleeperError("HTTP 503", url, 503)
        return ROSTERS if "weekly_rosters" in url else REPORTS


NOW = datetime(2026, 11, 27, 12, tzinfo=timezone.utc)


def test_fetch_schedule(tmp_path):
    """6.6.5.1: a completed season once; the current season again only after 20 hours."""
    store = Store(tmp_path)
    client = Fake()
    run = sync_reports(client, store, ["2020", "2023", "2026"], "2026", NOW)
    assert run.saved == ["2023", "2026"], "nothing before 2021"
    assert client.calls == [rosters_url("2023"), reports_url("2023"), rosters_url("2026"), reports_url("2026")]
    assert read_reports(store, "2023")["5"] == {"10229": "IR"}
    assert "fetched_at" not in read_json(path(store, "2023")), "the record carries no fetch time"
    assert set(read_json(fetch_log(store))) == {"2023", "2026"}

    client = Fake()
    assert sync_reports(client, store, ["2023", "2026"], "2026", NOW + timedelta(hours=19)).saved == []
    assert client.calls == []
    client = Fake()
    assert sync_reports(client, store, ["2023", "2026"], "2026", NOW + timedelta(hours=21)).saved == ["2026"]


def test_failure_keeps_file_and_only_warns(tmp_path):
    """6.6.5.2: a failed fetch keeps the stored file and warns with the season."""
    store = Store(tmp_path)
    sync_reports(Fake(), store, ["2026"], "2026", NOW)
    before = path(store, "2026").read_bytes()
    run = sync_reports(Fake(fail=True), store, ["2026"], "2026", NOW + timedelta(days=1))
    assert run.saved == [] and run.warnings and "2026" in run.warnings[0]
    assert path(store, "2026").read_bytes() == before
