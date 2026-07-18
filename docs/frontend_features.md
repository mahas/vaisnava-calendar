# Frontend Client Architecture & Features

This document explains the modern client-side features, caching, layouts, and PWA configuration implemented in the Vaishnava Calendar frontend.

## Client-Side Features

### 1. City Autocomplete Live Search
* **Mechanism**: Listeners are attached to the `#cityInput` element.
* **Debounce**: Inputs trigger a 300ms debounce timer to prevent flooding the backend server.
* **Keyboard Navigation**: Users can scroll through the results using the `ArrowUp` and `ArrowDown` keys and confirm their selection with `Enter`, or dismiss the dropdown using `Escape`.
* **Selection Flow**: Selecting a city automatically stores the details in the local state, displays timezone data, and generates the calendar.

### 2. Layout Views (List vs. Monthly Grid)
* **List View**: Renders days sequentially. Days containing Ekadashi or Fasting dates display gold and red gradients respectively with distinct text formatting and tags.
* **Grid View**:
  - Groups the list of days by calendar month.
  - Matches the standard Sunday/Monday day-of-week headers.
  - Calculates empty offset blocks dynamically.
  - Populates cells with day numbers, moon phase icons (calculated from `tithi` values: `🌑`, `🌒`, `🌔`, `🌕`, `🌖`, `🌘`), and small indicators representing events (blue), fasts (red), or Ekadashi (gold).

### 3. Detailed Day Dialog Modal & Calendar Exports
* **Element**: A native HTML5 `<dialog>` component with custom backdrop blur is used for premium aesthetics.
* **Dismissal**: Supports standard platform controls (`Esc` key) and backdrop click "light-dismiss" fallback.
* **Timings**: Displays sunrise, sunset, solar noon, lunar phase, masa month, and gaurabda year in a clean grid.
* **Google Calendar Links**:
  - Individual events can be added directly to Google Calendar.
  - **Combined Events**: If a day contains multiple festivals, a `"Añadir todos a Google Calendar"` button is generated to combine all festivals into a single calendar event, listing each in the event's description.
  - **Fasting Indicators**: If a day is a fasting day, `(Fast)` or `(Ayuno)` is dynamically appended to the event title.
  - **Location Details**: Event locations are set automatically to the currently selected city (e.g. `Paris, France`), making scheduling precise for travelers.
  - **Fasting Timings & Rules**: The event description includes detailed moon phase data, sunrise/sunset, fasting type rules (e.g. *Fast until sunset*), and Ekadashi Parana break-fast time intervals.

### 4. Custom ICS Exporter & Presets
* **Presets**: Offers buttons to set ranges quickly for "Este mes", "Mes siguiente", or "Este año".
* **iOS / Apple Indication**: Labeling clearly specifies that downloaded `.ics` files are suited for the iOS / Apple ecosystem.
* **ICS Properties**:
  - Automatically appends `(Fast)` or `(Ayuno)` to summary titles.
  - Compiles full day details (astrological coordinates, fasting rules, break fast hours) into the event description.
  - Applies coordinates location values matching the selected city.
  - Includes custom alarm offsets in the VEVENT header, or exports fasting dates exclusively.

---

## Client Caching & Offline Support

### Client Caching
API calendar results are cached in memory. A search query URL-like pattern is used as a cache key: `${city}-${country}-${start}-${end}`. If the user regenerates a calendar with identical dates, it loads instantly from memory rather than performing a network request.

### Progressive Web App (PWA)
* **Manifest (`manifest.json`)**: Configures application names, icons, themes, and full-screen portrait orientation.
* **Service Worker (`sw.js`)**:
  - Intercepts all fetch requests.
  - Applies a cache-first strategy for static files (`index.html`, `styles.css`, `app.js`, `manifest.json`, `favicon.png`) allowing the calendar client to load offline.
  - Employs a network-only strategy with a graceful offline warning JSON fallback for REST API endpoints.
* **Install Prompt**: After 20 seconds of first use, a modal dialog prompts the user to install the PWA. If declined, the prompt respects a 2-month cooldown before re-appearing. An `Install App` button in the header also allows manual triggering at any time.
* **iOS Install Instructions**: On iOS devices (which do not support `beforeinstallprompt`), the modal displays step-by-step instructions with icons guiding the user through Safari's Share → Add to Home Screen workflow.

---

## Calendar Export System

### 1. ICS Export (iOS / Apple)
* Button: `id="exportBtn"` — calls `exportarICS()`.
* Downloads a `.ics` file named `VaisnavaCalendar.ics` to the device.
* The file is a valid iCalendar (RFC 5545) format importable in Apple Calendar (iOS/macOS), Google Calendar, Microsoft Outlook, and other standard calendar apps.
* Configurable options (inside the collapsible `#exportSettingsPanel`):
  - Include/exclude fasting alarms (`VALARM` blocks).
  - Alarm timing: 12h, 15h, 24h before, or same day.
  - Filter to export fasting days only.
* An `#exportSettingsDesc` paragraph at the top of the panel explains the universal compatibility of the `.ics` standard.

### 2. Google Calendar Export
* Button: `id="exportGoogleBtn"` — calls `exportarAGoogleCalendar()`.
* Applies the same filtering/alarm settings as the ICS export.
* Downloads `VaisnavaCalendar_Google.ics` and then, after an 800ms delay, opens **Google Calendar's import page** (`calendar.google.com/calendar/r/settings/export`) in an external browser window.
* A toast message guides the user to complete the import: *Settings → Import*.
* **PWA External Navigation Rule**: All external URLs (Google Calendar, etc.) are opened using a programmatically clicked `<a target="_blank" rel="noopener noreferrer">` element — **never** `window.open()`. This guarantees the OS browser opens instead of the PWA webview, ensuring the user can navigate back to the app.

### 3. Single-Event Google Calendar Links
* Available from the day detail modal dialog.
* `addToGoogleCalendar()` builds a Google Calendar event creation URL and opens it externally using the same anchor pattern.
* `addToGoogleCalendarAll()` combines all festivals of a single day into one event entry for convenience.

---

## UX Interaction Patterns

### Date Range Selector Button
* The button `#toggleDateSettingsBtn` (label: *"Otros rangos de fechas"* / *"Other date ranges"*) uses a calendar icon 🗓️ (not a gear ⚙️).
* It toggles the `#dateSettingsPanel` collapsible panel and gains/loses the `.mini-btn.active` CSS class in sync with the panel state.
* Presets available: *This Month*, *This Year*, plus manual start/end date pickers.

### City Search Button Active State
* The button `#toggleCitySearchBtn` similarly toggles `.mini-btn.active` in sync with `#citySearchPanel`.
* The class is also managed programmatically when a city is selected from autocomplete or loaded from `localStorage`, ensuring the button always reflects actual panel visibility.

