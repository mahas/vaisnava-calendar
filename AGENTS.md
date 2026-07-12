# Vaishnava Calendar Agent Guide

This repository contains the **Vaishnava Calendar** application, a web-based client and a Python backend server that calculates important Vaishnava dates, festival descriptions, Ekadashi fasting days, and astronomical events.

## Repository Overview

```
.
├── AGENTS.md               # This documentation file
├── LICENSE
├── README.md               # User-facing README
├── calendar.json           # Cached/example calendar data
├── gaurabda/               # Core Python library for calendar calculations (based on GCal)
├── server/                 # Flask backend REST API server
│   ├── server.py           # Server entrypoint
│   └── README.md           # API REST documentation
├── web/                    # Frontend client assets
│   └── index.html          # Main SPA (HTML/CSS/JS)
└── run.py                  # CLI script for testing calculations
```

---

## Technical Architecture

### 1. Frontend (`web/index.html`)
The frontend is a lightweight, single-page application (SPA) with a modern cyber-spiritual dark design theme.
* **Styling**: Vanilla CSS utilizing radial gradients, modern flex/grid layouts, responsive typography, and glassmorphic panels (`backdrop-filter`).
* **State Management**:
  * `selectedCity`: Currently selected location.
  * `lastCalendarData`: Cached raw JSON response of the last calendar generation.
  * `currentLang`: Selected language, which persists in browser `localStorage.getItem('lang')` (`es` or `en`).
  * Default City: Saved in `localStorage.getItem('gcal_default_city')` to auto-calculate the calendar upon opening.
* **Loading Overlay**: Shows a progress-simulating cyan spinner and live time counter when query requests are sent. It handles the cold start delay of the backend gracefully.
* **Calendar Export**: Generates an `.ics` (iCalendar Standard RFC 5545) payload dynamically on the client-side for importing into Google Calendar, Apple Calendar, or Outlook, complete with customizable alarms for fasting days.

### 2. Backend Server (`server/server.py`)
The backend is powered by a Flask web server that wraps the custom mathematical and astrological library (`gaurabda`).
* **Port Configuration**: Defaults to `8047` (configurable via `PORT` or `GCAL_SERVER_PORT` env variables).
* **Core API Endpoints**:
  * `GET /countries`: Returns a list of all countries supported in the location database.
  * `GET /find-location?name=<city>`: Searches the database for matching cities. Returns location dictionary with `EQUALS`, `STARTS`, and `CONTAINS` results.
  * `GET /find-location?country=<country>`: Searches for cities within a specific country (maximum 200 cities, exact country name required).
  * `GET /calendar?city=<city>&country=<country>&year=<yyyy>&month=<m>&day=<d>&period=<days>`: Computes and returns calendar days, moon tithis, fast flags, and event descriptions for the specified range.

---

## Hosting & Cold Start Constraints

* **Platform**: The production server is deployed on a free tier of Render (`https://vaisnava-calendar.onrender.com`).
* **Spin-down Timeout**: Free-tier Render instances spin down after 15 minutes of inactivity.
* **Cold Start Delay**: Waking up a spun-down instance can take **up to 50 seconds**.
* **Frontend Handling**: The loading overlay displays a progress bar and a ticking timer warning the user about the cold start. It uses a `try/catch/finally` block to intercept network exceptions, notifying the user and auto-dismissing if the server fails to respond.

---

## Local Development & Setup

### Requirements
* Python 3.x
* Flask (`pip install Flask`)

### Running the Backend
To start the backend calculation server locally on port 8047:
```bash
python3 server/server.py
```

### Running the Frontend
The frontend can be opened directly in a browser from the local file system (`web/index.html`), or served using any static server. For example:
```bash
# Using python's built-in server
python3 -m http.server 8000 --directory web
```
The webpage automatically detects if it is running on `localhost` or `127.0.0.1` and adjusts the API endpoint to target the local backend on port `8047` instead of the Render cloud host.
