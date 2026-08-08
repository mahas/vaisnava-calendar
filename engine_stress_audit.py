import sys
import os
sys.path.insert(0, os.getcwd())

from gaurabda.TCalendar import CalculateCalendar
from gaurabda.TLocation import TLocation

nodes = {
    "Mayapur":    TLocation(latitude=23.4222, longitude=88.3846, timezone="Asia/Kolkata"),
    "London":     TLocation(latitude=51.5074, longitude=-0.1278, timezone="Europe/London"),
    "LosAngeles": TLocation(latitude=34.0522, longitude=-118.2437, timezone="America/Los_Angeles")
}

# Generate 2027 datasets
datasets = {city: CalculateCalendar(2027, loc) for city, loc in nodes.items()}

print("================================================================================")
print("             CROSS-CONTINENTAL FESTIVAL & EKADASI SHIFT AUDIT (2027)            ")
print("================================================================================")

# 1. Scan for major festival shifts (Janmastami, Gaura Purnima, Radhastami)
critical_festivals = ["Sri Krsna Janmastami", "Gaura Purnima", "Sri Radhastami"]

for fest in critical_festivals:
    dates = {}
    for city, cal in datasets.items():
        for day in cal:
            if fest in day.festivals:
                dates[city] = day.gregorian_date
                break
    print(f"\n[FESTIVAL] {fest}:")
    print(f"  - India (Mayapur): {dates.get('Mayapur', 'NOT FOUND')}")
    print(f"  - Europe (London): {dates.get('London', 'NOT FOUND')}")
    print(f"  - America (Los Angeles): {dates.get('LosAngeles', 'NOT FOUND')}")

# 2. Scan all Ekadasi Fasting days for 1-day continental deltas
print("\n================================================================================")
print("                   DETECTED CROSS-CONTINENTAL EKADASI SHIFTS                    ")
print("================================================================================")

# Collect all days where any location triggers an Ekadasi fast
all_fast_dates = set()
for cal in datasets.values():
    for day in cal:
        if any("Fasting" in f for f in day.festivals):
            all_fast_dates.add(day.gregorian_date)

for g_date in sorted(list(all_fast_dates)):
    f_status = {}
    for city, cal in datasets.items():
        day_data = cal.get_date(g_date)
        if day_data:
            fast_desc = [f for f in day_data.festivals if "Fasting" in f]
            if fast_desc:
                f_status[city] = fast_desc[0]
    
    # If there is a disagreement in execution presence or timing across the matrix, log it
    if len(f_status) < 3: 
        # This confirms a 1-day continental shift happened!
        print(f"\n[SHIFT TRIGGERED] Date: {g_date}")
        for city, status in f_status.items():
            print(f"  - {city}: {status}")
