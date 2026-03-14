import unicodedata
import requests
import pytest
from playwright.sync_api import Page

BASE_URL_API = "https://api.jolpi.ca/ergast/f1/2023/driverStandings.json"
BASE_URL_WEB = "https://www.formula1.com/en/results/2023/drivers"


def normalize_name(name: str) -> str:
    """Normalize accented characters for comparison (e.g. Perez vs Pérez)."""
    return (
        unicodedata.normalize("NFD", name)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .strip()
    )


@pytest.fixture(scope="module")
def api_standings():
    """Fetch full driver standings from Ergast API and return normalized list."""
    response = requests.get(BASE_URL_API)
    assert response.status_code == 200, "API did not return 200"
    data = response.json()
    raw = data["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]
    return [
        {
            "position": int(d["position"]),
            "name": normalize_name(
                f"{d['Driver']['givenName']} {d['Driver']['familyName']}"
            ),
            "points": d["points"],
        }
        for d in raw
    ]


def scrape_web_standings(page: Page) -> list[dict]:
    """Navigate to F1 website and scrape the full standings table.

    NOTE: The name cell contains first/last name in separate child <span>
    elements. Using cells.nth(1).inner_text() merges them without a space,
    producing 'MaxVerstappen'. Selecting the <a> link instead gives the full
    correctly-spaced name as its accessible text.
    """
    page.goto(BASE_URL_WEB)
    rows = page.locator("table tbody tr")
    result = []
    for i in range(rows.count()):
        cells = rows.nth(i).locator("td")
        result.append(
            {
                "position": int(cells.nth(0).inner_text().strip()),
                "name": normalize_name(cells.nth(1).locator("a").inner_text().strip()),
                "points": cells.nth(4).inner_text().strip(),
            }
        )
    return result


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_driver_count_matches(page: Page, api_standings):
    """Number of drivers on the website must match the API response."""
    web = scrape_web_standings(page)
    assert len(web) == len(api_standings), (
        f"Driver count mismatch: web={len(web)}, api={len(api_standings)}"
    )


def test_top3_names_match(page: Page, api_standings):
    """Top 3 driver names on the website must match the API."""
    web = scrape_web_standings(page)
    top3_web = [d["name"] for d in web[:3]]
    top3_api = [d["name"] for d in api_standings[:3]]
    assert top3_web == top3_api, (
        f"Top 3 name mismatch:\n  Web: {top3_web}\n  API: {top3_api}"
    )


def test_all_driver_names_match(page: Page, api_standings):
    """All 20 driver names must match between website and API in order."""
    web = scrape_web_standings(page)
    mismatches = [
        f"Pos {api['position']}: web='{w['name']}' | api='{api['name']}'"
        for w, api in zip(web, api_standings)
        if w["name"] != api["name"]
    ]
    assert not mismatches, "Name mismatches:\n" + "\n".join(mismatches)


def test_all_points_match(page: Page, api_standings):
    """All driver points must match between website and API."""
    web = scrape_web_standings(page)
    mismatches = [
        f"Pos {api['position']} ({api['name']}): web='{w['points']}' | api='{api['points']}'"
        for w, api in zip(web, api_standings)
        if w["points"] != api["points"]
    ]
    assert not mismatches, "Points mismatches:\n" + "\n".join(mismatches)


def test_positions_are_sequential(page: Page):
    """Positions on the website must be sequential starting from 1."""
    web = scrape_web_standings(page)
    for i, driver in enumerate(web, start=1):
        assert driver["position"] == i, (
            f"Position gap at row {i}: got {driver['position']}"
        )


def test_champion_has_most_points(api_standings):
    """P1 driver must have the highest points total (API only)."""
    max_pts = max(int(d["points"]) for d in api_standings)
    p1_pts = int(api_standings[0]["points"])
    assert p1_pts == max_pts, (
        f"Champion doesn't have max points: P1={p1_pts}, max={max_pts}"
    )
