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

### Calendar Navigation Bar Layout

The `.calendar-nav-bar` is a single flex row containing three logical groups:

```
[ ◀  Month Year  ▶ ]    [ Lista | Calendario ]  [ 🗓️ ]
   .month-navigation          .view-selector    #toggleDateSettingsBtn
         ←──── flex: 1 ────→  └────── .nav-bar-controls ──────────┘
```

* **`.month-navigation`**: Previous/next arrow buttons and the month/year title (`#currentPeriodLabel`). Gets `flex: 1` on mobile so it fills available width.
* **`.nav-bar-controls`**: A `flex-shrink: 0` wrapper on the right that holds the view toggle and the 🗓️ date-range button side by side.
* **`.view-selector`**: Switches between List and Grid calendar view. Buttons call `setCalendarView('list')` and `setCalendarView('grid')`. The active button carries the `.active` class.
* **`#toggleDateSettingsBtn`** (`#datesBtnText` + 🗓️ emoji): Opens/closes `#dateSettingsPanel`. On mobile (`≤640px`) `#datesBtnText` is hidden so only the emoji shows — keeping the button compact without losing discoverability.

### Mobile Layout — Calendar as Protagonist (`≤640px`)

The calendar grid (`#calendarOutput`) must be the **first content element** the user sees below the location bar on mobile. No extra control rows are allowed between `.calendar-nav-bar` and the calendar.

| Element | Desktop | Mobile |
|---|---|---|
| `.calendar-nav-bar` | `flex-direction: row` | `flex-direction: row` (unchanged) |
| `#datesBtnText` (button label) | Visible ("Other date ranges") | Hidden — emoji 🗓️ only |
| `.calendar-toolbar` | Visible (export buttons) | `display: none` |
| `#soloAyunos` (fasting filter) | Inside `#dateSettingsPanel` | Inside `#dateSettingsPanel` |

**Export buttons on mobile**: The `.calendar-toolbar` is hidden on mobile. Users access the `.ics` and Google Calendar export buttons by tapping 🗓️ → expanding "Ajustes de Exportación (.ics)" inside `#dateSettingsPanel`.

**Fasting filter**: The `#soloAyunos` checkbox lives exclusively inside `#dateSettingsPanel` (above the presets). **Do not duplicate this element** in the toolbar or anywhere else; the JS reads its state by `id` and there must be exactly one instance.

### Date Range Selector (`#toggleDateSettingsBtn`)
* Label: *"Otros rangos de fechas"* / *"Other date ranges"* with 🗓️ emoji (no gear ⚙️).
* Toggles `#dateSettingsPanel` and synchronises the `.mini-btn.active` CSS class.
* Panel contents: fasting filter checkbox, preset buttons (This Month, This Year), date pickers, Generate button, and the collapsible export settings sub-panel.

### City Search Button Active State
* `#toggleCitySearchBtn` toggles `.mini-btn.active` in sync with `#citySearchPanel`.
* The class is also managed programmatically when a city is selected from autocomplete or loaded from `localStorage`, ensuring the button always reflects actual panel visibility.

---

## BhaktiLib Integration

The calendar integrates natively with the BhaktiLib database to enrich daily details with literature and biographies:
1. **Ekadashi Story Linking**:
   - If a day is an Ekadashi, a custom styled, gold-themed banner (`.bhaktilib-ekadasi-banner`) is rendered inside the events section in the day detail modal.
   - The banner features a **"Leer" / "Read"** button that redirects the user to the exact chapter of the book *"Ekadasi, el día del Señor Hari"* on BhaktiLib using a pre-calculated Epub.js CFI mapped in `EKADASI_MAPPING` for all 26 Ekadashis.
   - The banner is dynamically positioned below the main events to ensure the primary calendar events are prioritized visually.
2. **Semantic Biography Linking**:
   - Event descriptions are scanned for names of prominent acharyas and characters (e.g., *Srila Prabhupada*, *Sri Caitanya Mahaprabhu*, *Sanatana Gosvami*).
   - If matched, a **"Ver en BhaktiLib" / "View on BhaktiLib"** button (`.bhaktilib-semantic-btn`) is rendered beside the event.
   - Links target the canonical author permalinks on BhaktiLib (e.g. `https://bhaktilib.com/autor/sri-caitanya-mahaprabhu/`).
3. **PWA Secure Navigation**:
   - All BhaktiLib reader and author link clicks use programmatically generated `<a>` elements with `target="_blank"` and `rel="noopener noreferrer"` to guarantee proper external browser launch outside of PWA standalone containers on iOS/Android.

