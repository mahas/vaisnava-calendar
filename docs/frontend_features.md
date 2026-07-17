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

### 3. Detailed Day Dialog Modal
* **Element**: A native HTML5 `<dialog>` component with custom backdrop blur is used for premium aesthetics.
* **Dismissal**: Supports standard platform controls (`Esc` key) and a JavaScript fallback for backdrop click "light-dismiss" on browsers lacking native `<dialog closedby="any">` support.
* **Timings**: Displays sunrise, sunset, solar noon, lunar phase, masa month, and gaurabda year in a clean grid.
* **Google Calendar Links**: Clicking the shortcut button constructs a templated URL to directly save the event online.

### 4. Custom ICS Exporter & Presets
* **Presets**: Offers buttons to set ranges quickly for "Este mes", "Mes siguiente", or "Este año".
* **ICS Options**:
  - Includes custom alarm offsets in the VEVENT header.
  - Allows exporting fasting dates exclusively.

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
