import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1/2023/driverStandings.json"

def test_top3_driver_standings_2023():

    response = requests.get(BASE_URL)

    # Validate status code
    assert response.status_code == 200

    data = response.json()

    standings = data["MRData"]["StandingsTable"]["StandingsLists"][0]["DriverStandings"]

    top3 = standings[:3]

    extracted_drivers = [
        f"{driver['Driver']['givenName']} {driver['Driver']['familyName']}"
        for driver in top3
    ]

    expected_top3 = [
        "Max Verstappen",
        "Sergio Pérez",
        "Lewis Hamilton"
    ]

    assert extracted_drivers == expected_top3

    # Validate points are numeric
    for driver in top3:
        assert driver["points"].isdigit()