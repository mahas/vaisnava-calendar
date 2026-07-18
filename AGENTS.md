# Vaishnava Calendar Agent Guide

This repository contains the **Vaishnava Calendar** application, a web-based client and a Python backend server that calculates important Vaishnava dates, festival descriptions, Ekadashi fasting days, and astronomical events.

## Repository Overview

```
.
├── AGENTS.md               # This documentation file
├── LICENSE
├── README.md               # User-facing README
├── calendar.json           # Cached/example calendar data
├── docs/                   # Detailed technical features
│   ├── event_search.md     # Backend event search & cache
│   └── frontend_features.md# Frontend layouts, presets & PWA
├── gaurabda/               # Core Python library for calendar calculations (based on GCal)
├── server/                 # Flask backend REST API server
│   ├── server.py           # Server entrypoint
│   └── README.md           # API REST documentation
├── web/                    # Frontend client assets
│   ├── css/
│   │   └── styles.css      # Custom stylesheet design system
│   ├── js/
│   │   └── app.js          # SPA interactive logic
│   ├── index.html          # Main SPA (semantic HTML)
│   ├── manifest.json       # PWA manifest configurations
│   └── sw.js               # Service Worker for offline use
└── run.py                  # CLI script for testing calculations
```

---

## Technical Architecture

### 1. Frontend (`web/`)
The frontend is a lightweight, single-page application (SPA) with a modern cyber-spiritual dark design theme.
* **Separation of Concerns**: Extracted HTML templates, styling rules (`css/styles.css`), and JavaScript behaviors (`js/app.js`).
* **State Management & Caching**:
  * `selectedCity`: Currently selected location.
  * `lastCalendarData`: Raw JSON response of the last calendar generation.
  * `currentLang`: Selected language, which persists in browser `localStorage` (`es` or `en`).
  * `clientCache`: In-memory calendar query cache mapped by city, country, and date range.
* **Autocomplete & Presets**: Live city search with arrow key support, and buttons to quickly select ranges (This Month, Next Month, This Year).
* **Grid and Dialogs**: Layout toggler for Monthly Grid view with moon phase representations and a detailed `<dialog>` card for daily astrological attributes.
* **Calendar Export**: Client-side `.ics` export with custom alarms and fasting filters, and direct Google Calendar integration.
* **PWA Capability**: Register service workers to cache static assets for offline use.

### 2. Backend Server (`server/server.py` & `gaurabda/TServer.py`)
The backend is powered by a Flask web server that wraps the custom mathematical and astrological library (`gaurabda`).
* **Port Configuration**: Defaults to `8047` (configurable via `PORT` or `GCAL_SERVER_PORT` env variables).
* **Server-side Caching**: Size-limited LRU in-memory cache for `/calendar` and `/search-event` results.
* **Core API Endpoints**:
  * `GET /ping`: Keep-alive endpoint to wake up Render container.
  * `GET /countries`: Returns a list of all countries supported.
  * `GET /find-location?name=<city>`: Searches database for matching cities.
  * `GET /calendar?city=<city>&country=<country>&year=<yyyy>&month=<m>&day=<d>&period=<days>`: Computes and returns calendar details.
  * `GET /search-event?city=<city>&country=<country>&query=<query>&count=<count>`: Dynamically searches sequential years for matching event occurrences.

---

## Hosting & Cold Start Constraints

* **Platform**: The production server is deployed on a free tier of Render (`https://vaisnava-calendar.onrender.com`).
* **Spin-down Timeout**: Free-tier Render instances spin down after 15 minutes of inactivity.
* **Cold Start Delay**: Waking up a spun-down instance can take **up to 50 seconds**.
* **Frontend Handling**: The loading overlay displays a progress bar and a ticking timer.

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

---

## UI Conventions & Strict Rules

### 1. Prohibición de `alert()` y Uso del Sistema de Toasts
* **REGLA ESTRICTA**: Queda **completamente prohibido** el uso de la función nativa `alert()` en el código de la aplicación.
* **Sistema de Reemplazo**: Se debe utilizar exclusivamente la función `showToast(message, type)` definida en `web/js/app.js`.
* **Uso en Código**:
  ```javascript
  // Para mensajes de éxito (ej. datos guardados)
  showToast("Ciudad guardada con éxito", "success");

  // Para advertencias de validación (ej. falta ingresar campos)
  showToast("Por favor ingresa una fecha", "warning");

  // Para errores de red o del servidor
  showToast("Error al conectar con el servidor", "error");

  // Para mensajes informativos generales
  showToast("La aplicación ya está instalada", "info");
  ```
* **Estilos y Estructura CSS**:
  * El contenedor `.toast-container` agrupa los mensajes de forma fija y flotante en la parte inferior central de la pantalla.
  * Cada `.toast-message` tiene una apariencia tipo cristal traslúcido (`rgba(13, 23, 40, 0.95)`) con un difuminado sutil (`backdrop-filter: blur(8px)`) y bordes coloreados con un brillo sutil según el tipo (`info` = cian, `success` = verde, `warning` = oro, `error` = rojo).
  * Los mensajes se introducen con una animación de deslizamiento y se retiran de forma autónoma después de 4 segundos.

---

## UX Conventions

### 2. External Navigation from PWA
* **STRICT RULE**: Never use `window.open(url, "_blank")` to open external URLs. In PWA standalone mode this call may stay within the app webview (especially on iOS), trapping the user with no way to return.
* **Correct Pattern**: Always create an anchor element, set `target="_blank"` and `rel="noopener noreferrer"`, append it to the DOM, click it programmatically, then remove it:
  ```javascript
  const extLink = document.createElement("a");
  extLink.href = url;
  extLink.target = "_blank";
  extLink.rel = "noopener noreferrer";
  document.body.appendChild(extLink);
  extLink.click();
  document.body.removeChild(extLink);
  ```
* This applies to all external links: Google Calendar event creation, Google Calendar import page, and any future third-party URLs.

### 3. Calendar Export Toolbar
* The calendar toolbar (`.calendar-toolbar`) contains two side-by-side export buttons inside `.export-button-group`:
  1. **`.ics` (iOS / Apple)** — `id="exportBtn"` — calls `exportarICS()`. Downloads a `.ics` file compatible with Apple Calendar, iOS, macOS, and importable in Google Calendar / Outlook.
  2. **Google Calendar** — `id="exportGoogleBtn"` — calls `exportarAGoogleCalendar()`. Downloads the `.ics` file and then opens the Google Calendar import page in an external browser window (using the anchor pattern above).
* Both button labels are translatable via the `translations` catalog (`exportBtn`, `exportGoogleBtn`).
* The panel below the calendar nav-bar (`#dateSettingsPanel`) contains an `#exportSettingsDesc` paragraph that explains the universal compatibility of the `.ics` standard.

### 4. Collapsible Panel Button States
* The buttons that toggle the city search panel (`#toggleCitySearchBtn`) and the date range panel (`#toggleDateSettingsBtn`) dynamically receive/lose the CSS class `.mini-btn.active` in sync with their panels.
* The active state applies a cyan glow border and background (`var(--color-cyan-glow)`) to clearly communicate which panel is currently open.
* **Rule**: Always keep button active state synchronized with its panel: add `.active` when opening, remove it when closing or when the other panel is opened.
