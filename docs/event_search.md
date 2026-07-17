# Event Search API & Backend Cache

This document details the backend search algorithm and caching mechanisms implemented in the Vaishnava Calendar API.

## API Endpoints

### 1. `GET /ping`
* **Purpose**: Keep-alive ping route to prevent Render instances from sleeping.
* **Response**: `{"status": "ok"}`

### 2. `GET /search-event`
* **Parameters**:
  - `query` (string, mandatory): Name of the event or Ekadashi to look up.
  - `city` (string, mandatory): Name of the city.
  - `country` (string, mandatory): Name of the country.
  - `latitude`, `longitude`, `tzname` (optional): Precise coordinates. If omitted, values are resolved from the local city database.
  - `year`, `month`, `day` (optional): Start date for the search. Defaults to today's date.
  - `count` (integer, optional): Number of occurrences to find. Defaults to `5` (min `1`, max `20`).
* **Response**:
  ```json
  {
    "query": "sat tila ekadasi",
    "location": {
      "city": "Paris",
      "country": "France",
      "latitude": 48.866665,
      "longitude": 2.333333,
      "tzname": "+1:00 Europe/Paris"
    },
    "matches": [
      {
        "date": { "day": 2, "month": 2, "year": 2027 },
        "ekadashiName": "Sat-tila Ekadasi",
        "events": [
          { "disp": 17, "prio": 10, "text": "Vyanjuli Mahadvadasi" },
          { "disp": 17, "prio": 20, "text": "Fasting for Sat-tila Ekadasi" }
        ],
        "fast": 518,
        "matching_event": "Sat-tila Ekadasi"
      }
    ]
  }
  ```

---

## Algorithms & Logic

### Phonetic & Accent Normalization
To resolve spelling variations (such as accents, double vowels, and differences in transliteration systems, e.g. "Chaitanya" vs "Caitanya"), both the search query and the target event names are simplified before comparison.

The `simplify` function applies the following steps in order:
1. Decomposes Unicode characters (NFKD) and filters out combining diacritic marks (e.g., `ā` -> `a`, `ś` -> `s`, `ī` -> `i`).
2. Converts string to lowercase.
3. Performs standard character mappings:
   - `sh` -> `s` (e.g. *Ekadashi* -> *Ekadasi*)
   - `ch` -> `c` (e.g. *Chaturdashi* -> *Caturdasi*)
   - `ri` -> `r` (e.g. *Nrisimha* -> *Nrsimha*, *Krishna* -> *Krsna*)
   - `ee` -> `i` (e.g. *Ekadasee* -> *Ekadasi*)
   - `oo` -> `u` (e.g. *Roopa* -> *Rupa*)
   - `aa` -> `a` (e.g. *Gauraanga* -> *Gauranga*)
   - `ou` -> `au` (e.g. *Gouranga* -> *Gauranga*)
4. Removes all non-alphanumeric characters (spaces, hyphens, punctuation).

### Sequential Search Loop
Rather than calculating a heavy 10-year calendar at once (which takes a long time and uses excessive memory), the server:
1. Calculates the calendar for 366 days starting from the requested date.
2. Scans each day's events and `ekadashiName` for occurrences that match the simplified query.
3. If matches are found, adds them to the results array.
4. If the target `count` is reached, returns the matches immediately.
5. If more occurrences are needed, advances the start date by 366 days and repeats the calculation for the next year.
6. The loop terminates when either `count` matches are found or `6 years` have been calculated.

---

## Server Caching

Calculations are deterministic for any given date and location. To save CPU time on subsequent searches and calendar generations:
* A thread-safe `SimpleCache` is implemented inside `TServer.py`.
* It utilizes a `collections.OrderedDict` limited to 100 entries.
* When the limit is reached, the oldest entries are automatically evicted.
* Separate caches exist for the `/calendar` and `/search-event` endpoints.
