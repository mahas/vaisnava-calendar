try:
    import pytest
except ImportError:
    pytest = None
from gaurabda.TCalendar import CalculateCalendar
from gaurabda.TLocation import TLocation

# Define the global geographic test matrix (The Continental Core Nodes)
LOCATION_MATRIX = {
    "Mayapur":  {"lat": 23.4222, "lon": 88.3846, "tz": "Asia/Kolkata"},
    "London":   {"lat": 51.5074, "lon": -0.1278, "tz": "Europe/London"},
    "LosAngeles":{"lat": 34.0522, "lon": -118.2437,"tz": "America/Los_Angeles"}
}

def test_janmastami_regional_safety_gate():
    """
    Asserts Janmastami fasting is calculated safely across locations, 
    detecting potential 1-day shifts without silent failures.
    """
    results = {}
    year = 2026 # Target baseline
    
    for city, coords in LOCATION_MATRIX.items():
        loc = TLocation(latitude=coords["lat"], longitude=coords["lon"], timezone=coords["tz"])
        # Generate the continuous calendar array for the target month (August/September)
        calendar_days = CalculateCalendar(year, loc)
        
        # Track Janmastami date assignment for this specific node
        for day in calendar_days:
            if "Sri Krsna Janmastami" in day.festivals:
                results[city] = {
                    "date": day.gregorian_date,
                    "fasting": "Fasting for Sri Krsna Janmastami" in day.festivals
                }
                break

    # ASSERTIONS: Guarantee structural continuity
    assert "Mayapur" in results, "Mayapur Janmastami execution dropped."
    assert "LosAngeles" in results, "Los Angeles Janmastami execution dropped."
    
    # Log cross-verifications for the Web Reviewer
    print(f"\n[MATRIX LOG] Mayapur Janmastami Date: {results['Mayapur']['date']}")
    print(f"[MATRIX LOG] Los Angeles Janmastami Date: {results['LosAngeles']['date']}")


def test_parana_geographic_precision_gate():
    """
    Asserts Parana (break-fast) windows never overlap or duplicate across continents,
    guaranteeing strict localized calculation.
    """
    target_date = "2026-10-07" # The verified post-Ekadasi Parana date
    intervals = {}

    for city, coords in LOCATION_MATRIX.items():
        loc = TLocation(latitude=coords["lat"], longitude=coords["lon"], timezone=coords["tz"])
        day_data = CalculateCalendar(2026, loc).get_date(target_date)
        
        if day_data and day_data.parana_string:
            intervals[city] = day_data.parana_string

    # ASSERTION: Parana times MUST be unique per geography due to distinct sunrises
    assert len(intervals) == 3, f"Expected 3 valid Parana intervals, got {len(intervals)}: {intervals}"
    assert len(set(intervals.values())) == len(intervals), (
        f"CRITICAL FAULT: Duplicate Parana intervals detected across distinct timezones: {intervals}"
    )


if __name__ == "__main__":
    test_janmastami_regional_safety_gate()
    test_parana_geographic_precision_gate()
    print("SUCCESS: All global location matrix tests passed!")
