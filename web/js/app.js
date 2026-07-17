// state management
let selectedCity = null;
let lastCalendarData = null;
let currentLang = localStorage.getItem("lang") || "es";
let currentView = "list"; // 'list' or 'grid'
const clientCache = {}; // Cache key -> calendar data

const IS_LOCAL = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
const BASE_URL = IS_LOCAL ? "http://127.0.0.1:8047" : "https://vaisnava-calendar.onrender.com";

// translation catalog
const translations = {
  es: {
    title: "Calendario Vaisnava",
    searchCity: "Buscar ciudad",
    searchPlaceholder: "Escribe ciudad... ej. Vrindavan",
    searchBtn: "Buscar",
    saveDefaultBtn: "Fijar por defecto",
    savedDefaultMsg: "Ciudad guardada como predeterminada",
    selectedCity: "Ciudad seleccionada",
    noCitySelected: "Ninguna ciudad seleccionada",
    generate: "Calendario",
    searchEventsTab: "Buscar Evento",
    fastFilter: "Mostrar solo días de ayuno",
    startDate: "Fecha de inicio",
    endDate: "Fecha de fin",
    generateBtn: "Generar Calendario",
    todayBtn: "Hoy",
    exportBtn: "Descargar .ics (iOS / Apple)",
    todayLabel: "(Hoy)",
    result: "Fechas Generadas",
    loadingCity: "Buscando ciudad...",
    loadingCalendar: "Calculando fechas astrológicas...",
    loadingSearch: "Buscando próximas fechas...",
    serverNotice: "",
    elapsed: "Tiempo de espera: {sec}s",
    addToGoogleAll: "Añadir todos a Google Calendar",
    errorCity: "Ciudad no encontrada o error de red. Intenta con otra.",
    errorCalendar: "Error al generar. Intenta de nuevo.",
    errorSearch: "Error al buscar el evento.",
    viewList: "Lista",
    viewGrid: "Cuadrícula",
    searchQueryLabel: "Nombre del evento (ej: sat tila, nrisimha)",
    searchQueryPlaceholder: "Escribe el nombre del evento...",
    searchCountLabel: "Ocurrencias",
    searchBtnLabel: "Buscar Próximas Fechas",
    noMatches: "No se encontraron fechas para este evento en los próximos 6 años.",
    modalAstroTitle: "Detalles Astrológicos",
    modalEventsTitle: "Eventos y Festivales",
    addToGoogle: "Añadir a Google Calendar",
    closeModal: "Cerrar",
    exportSettingsLabel: "Ajustes de Exportación (.ics) ⚙️",
    includeAlarmsLabel: "Incluir alarmas de ayuno",
    alarmHoursLabel: "Anticipación de alarma",
    onlyFastsExportLabel: "Exportar solo días de ayuno",
    hours12: "12 horas antes",
    hours15: "15 horas antes",
    hours24: "1 día antes",
    hours0: "Mismo día",
    tithiLabel: "Tithi (Fase lunar)",
    masaLabel: "Masa (Mes vaisnava)",
    gaurabdaLabel: "Año Gaurabda",
    nakshatraLabel: "Naksatra",
    yogaLabel: "Yoga",
    sunriseLabel: "Salida del Sol",
    sunsetLabel: "Puesta del Sol",
    noonLabel: "Mediodía solar",
    fastingBadge: "Ayuno",
    ekadashiBadge: "Ekadasi",
    todayBadge: "Hoy",
    presetThisMonth: "Este Mes",
    presetNextMonth: "Mes Siguiente",
    presetThisYear: "Este Año"
  },
  en: {
    title: "Vaishnava Calendar",
    searchCity: "Search City",
    searchPlaceholder: "Type city name... e.g. Vrindavan",
    searchBtn: "Search",
    saveDefaultBtn: "Set as Default",
    savedDefaultMsg: "City saved as default location",
    selectedCity: "Selected City",
    noCitySelected: "No city selected",
    generate: "Calendar",
    searchEventsTab: "Search Event",
    fastFilter: "Show fasting days only",
    startDate: "Start Date",
    endDate: "End Date",
    generateBtn: "Generate Calendar",
    todayBtn: "Today",
    exportBtn: "Download .ics (iOS / Apple)",
    todayLabel: "(Today)",
    result: "Generated Dates",
    loadingCity: "Searching city...",
    loadingCalendar: "Calculating astronomical dates...",
    loadingSearch: "Searching upcoming dates...",
    serverNotice: "",
    elapsed: "Elapsed time: {sec}s",
    addToGoogleAll: "Add all to Google Calendar",
    errorCity: "City not found or network error. Please try again.",
    errorCalendar: "Failed to generate calendar. Please try again.",
    errorSearch: "Failed to search for the event.",
    viewList: "List",
    viewGrid: "Grid",
    searchQueryLabel: "Event name (e.g. sat tila, nrisimha)",
    searchQueryPlaceholder: "Enter event name...",
    searchCountLabel: "Occurrences",
    searchBtnLabel: "Search Upcoming Dates",
    noMatches: "No occurrences found for this event in the next 6 years.",
    modalAstroTitle: "Astronomical Details",
    modalEventsTitle: "Events & Festivals",
    addToGoogle: "Add to Google Calendar",
    closeModal: "Close",
    exportSettingsLabel: "Export Settings (.ics) ⚙️",
    includeAlarmsLabel: "Include fasting alarms",
    alarmHoursLabel: "Alarm timing",
    onlyFastsExportLabel: "Export fasting days only",
    hours12: "12 hours before",
    hours15: "15 hours before",
    hours24: "1 day before",
    hours0: "Same day",
    tithiLabel: "Tithi (Moon Phase)",
    masaLabel: "Masa (Vaishnava Month)",
    gaurabdaLabel: "Gaurabda Year",
    nakshatraLabel: "Naksatra",
    yogaLabel: "Yoga",
    sunriseLabel: "Sunrise",
    sunsetLabel: "Sunset",
    noonLabel: "Solar Noon",
    fastingBadge: "Fast",
    ekadashiBadge: "Ekadasi",
    todayBadge: "Today",
    presetThisMonth: "This Month",
    presetNextMonth: "Next Month",
    presetThisYear: "This Year"
  }
};

// DOM Content Loaded initialization
window.addEventListener("DOMContentLoaded", () => {
  initDates();
  initLanguage();
  initEventListeners();
  initPWA();
  cargarCiudadPorDefecto();
});

// Set default input date range to today
function initDates() {
  const tzoffset = new Date().getTimezoneOffset() * 60000;
  const localDateStr = new Date(Date.now() - tzoffset).toISOString().split("T")[0];
  document.getElementById("startDate").value = localDateStr;
  document.getElementById("endDate").value = localDateStr;
}

// Detect language or load from localStorage
function initLanguage() {
  const savedLang = localStorage.getItem("lang");
  if (savedLang) {
    currentLang = savedLang;
  } else {
    const navLang = navigator.language || "";
    currentLang = navLang.startsWith("en") ? "en" : "es";
  }
  applyTranslations();
}

// Attach event listeners
function initEventListeners() {
  // Tabs Navigation
  document.querySelectorAll(".tab-button").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));
      
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // Autocomplete search keystroke handler
  const cityInput = document.getElementById("cityInput");
  let debounceTimeout = null;
  
  cityInput.addEventListener("input", () => {
    clearTimeout(debounceTimeout);
    const value = cityInput.value.trim();
    
    if (value.length < 2) {
      hideAutocomplete();
      return;
    }
    
    debounceTimeout = setTimeout(() => {
      fetchCitySuggestions(value);
    }, 300);
  });

  cityInput.addEventListener("keydown", (e) => {
    const items = document.querySelectorAll(".autocomplete-item");
    if (!items.length) return;
    
    let highlightedIndex = -1;
    items.forEach((item, idx) => {
      if (item.classList.contains("highlighted")) highlightedIndex = idx;
    });

    if (e.key === "ArrowDown") {
      e.preventDefault();
      const nextIdx = (highlightedIndex + 1) % items.length;
      updateAutocompleteHighlight(items, nextIdx);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prevIdx = (highlightedIndex - 1 + items.length) % items.length;
      updateAutocompleteHighlight(items, prevIdx);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (highlightedIndex >= 0) {
        items[highlightedIndex].click();
      }
    } else if (e.key === "Escape") {
      hideAutocomplete();
    }
  });

  // Hide autocomplete when clicking outside
  document.addEventListener("click", (e) => {
    if (!cityInput.contains(e.target) && !document.getElementById("autocompleteDropdown").contains(e.target)) {
      hideAutocomplete();
    }
  });

  // Toggle ICS Custom settings panel
  document.getElementById("toggleExportSettings").addEventListener("click", () => {
    const panel = document.getElementById("exportSettingsPanel");
    panel.classList.toggle("active");
  });

  // Modal dialog outside click fallback (Light-dismiss)
  const modal = document.getElementById("dayDetailModal");
  if (!("closedBy" in HTMLDialogElement.prototype)) {
    modal.addEventListener("click", (event) => {
      if (event.target !== modal) return;
      const rect = modal.getBoundingClientRect();
      const isInside = (
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width
      );
      if (!isInside) {
        modal.close();
      }
    });
  }
}

// City predictive suggestions fetching
async function fetchCitySuggestions(query) {
  const url = `${BASE_URL}/find-location?name=${encodeURIComponent(query)}`;
  try {
    const response = await fetch(url);
    if (!response.ok) return;
    const data = await response.json();
    
    const dropdown = document.getElementById("autocompleteDropdown");
    dropdown.innerHTML = "";
    
    const cities = data.EQUALS.concat(data.STARTS, data.CONTAINS);
    if (!cities.length) {
      hideAutocomplete();
      return;
    }

    cities.forEach((c) => {
      const item = document.createElement("div");
      item.className = "autocomplete-item";
      item.textContent = `${c.city} (${c.country})`;
      item.addEventListener("click", () => {
        seleccionarCiudadAutocomplete(c);
      });
      dropdown.appendChild(item);
    });
    
    dropdown.classList.add("active");
  } catch (err) {
    console.error("Error fetching city autocompletes", err);
  }
}

function updateAutocompleteHighlight(items, index) {
  items.forEach(item => item.classList.remove("highlighted"));
  if (items[index]) {
    items[index].classList.add("highlighted");
    items[index].scrollIntoView({ block: "nearest" });
  }
}

function hideAutocomplete() {
  document.getElementById("autocompleteDropdown").classList.remove("active");
}

function seleccionarCiudadAutocomplete(city) {
  selectedCity = city;
  document.getElementById("cityInput").value = `${city.city} (${city.country})`;
  
  const textContainer = document.getElementById("selected");
  textContainer.innerHTML = `${city.city}, ${city.country}<br><small>${city.tzname}</small>`;
  
  document.getElementById("saveDefaultBtn").style.display = "inline-block";
  hideAutocomplete();
  
  // Auto-generate on selecting a city
  generarCalendario();
}

// Load default city from localStorage
function cargarCiudadPorDefecto() {
  const saved = localStorage.getItem("gcal_default_city");
  if (!saved) return;
  
  selectedCity = JSON.parse(saved);
  document.getElementById("selected").innerHTML = `${selectedCity.city}, ${selectedCity.country}<br><small>${selectedCity.tzname}</small>`;
  document.getElementById("cityInput").value = `${selectedCity.city} (${selectedCity.country})`;
  document.getElementById("saveDefaultBtn").style.display = "none";
  
  generarCalendario();
}

function guardarCiudadPorDefecto() {
  if (!selectedCity) return;
  localStorage.setItem("gcal_default_city", JSON.stringify(selectedCity));
  alert(translations[currentLang].savedDefaultMsg);
  document.getElementById("saveDefaultBtn").style.display = "none";
}

// Apply date selection presets
function applyPreset(presetType) {
  const startInput = document.getElementById("startDate");
  const endInput = document.getElementById("endDate");
  const now = new Date();
  
  if (presetType === "thisMonth") {
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    startInput.value = formatDateString(firstDay);
    endInput.value = formatDateString(lastDay);
  } else if (presetType === "nextMonth") {
    const firstDay = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 2, 0);
    startInput.value = formatDateString(firstDay);
    endInput.value = formatDateString(lastDay);
  } else if (presetType === "thisYear") {
    const firstDay = new Date(now.getFullYear(), 0, 1);
    const lastDay = new Date(now.getFullYear(), 11, 31);
    startInput.value = formatDateString(firstDay);
    endInput.value = formatDateString(lastDay);
  }
  
  generarCalendario();
}

function formatDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// Core calendar API trigger
async function generarCalendario() {
  if (!selectedCity) {
    alert(currentLang === "en" ? "Select a city first" : "Selecciona una ciudad primero");
    return;
  }

  const startDateStr = document.getElementById("startDate").value;
  const endDateStr = document.getElementById("endDate").value;
  
  if (!startDateStr || !endDateStr) {
    alert(currentLang === "en" ? "Select start and end dates" : "Selecciona las fechas de inicio y fin");
    return;
  }

  const startParts = startDateStr.split("-");
  const endParts = endDateStr.split("-");
  
  const startLocal = new Date(startParts[0], startParts[1] - 1, startParts[2]);
  const endLocal = new Date(endParts[0], endParts[1] - 1, endParts[2]);

  const year = startLocal.getFullYear();
  const month = startLocal.getMonth() + 1;
  const day = startLocal.getDate();
  
  const diffTime = endLocal.getTime() - startLocal.getTime();
  const period = Math.floor(diffTime / (1000 * 60 * 60 * 24)) + 1;
  
  if (period <= 0) {
    alert(currentLang === "en" ? "End date must be equal or after start date" : "La fecha de fin debe ser igual o posterior a la fecha de inicio");
    return;
  }

  const cacheKey = `${selectedCity.city}-${selectedCity.country}-${startDateStr}-${endDateStr}`;
  
  // Clientside caching lookup
  if (clientCache[cacheKey]) {
    lastCalendarData = clientCache[cacheKey];
    renderCalendar();
    return;
  }

  showLoader("loadingCalendar");
  const url = `${BASE_URL}/calendar?city=${encodeURIComponent(selectedCity.city)}&country=${encodeURIComponent(selectedCity.country)}&year=${year}&month=${month}&day=${day}&period=${period}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Network response error");
    const data = await response.json();
    
    lastCalendarData = data;
    clientCache[cacheKey] = data; // store in cache
    renderCalendar();
  } catch (error) {
    console.error("Error generating calendar:", error);
    alert(translations[currentLang].errorCalendar);
  } finally {
    hideLoader();
  }
}

// Render calendar results
function renderCalendar() {
  if (!lastCalendarData) return;
  const soloAyunos = document.getElementById("soloAyunos").checked;
  const container = document.getElementById("calendarOutput");
  container.innerHTML = "";

  const filteredDays = lastCalendarData.days.filter(d => !soloAyunos || d.fast);

  if (currentView === "list") {
    renderListView(filteredDays, container);
  } else {
    renderGridView(filteredDays, container);
  }
}

// List View Renderer
function renderListView(days, container) {
  if (!days.length) {
    container.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--color-text-muted);">No dates matched criteria.</div>`;
    return;
  }

  days.forEach((d) => {
    const card = document.createElement("div");
    card.className = "list-day-card";
    
    const isToday = checkIsToday(d.date);
    if (isToday) card.classList.add("today");
    if (d.ekadashiName) card.classList.add("ekadashi");
    if (d.fast) card.classList.add("fasting");

    // Click handler to open details modal
    card.addEventListener("click", () => {
      openDayDetailModal(d);
    });

    const weekdayStr = new Date(d.date.year, d.date.month - 1, d.date.day)
      .toLocaleDateString(currentLang === "en" ? "en-US" : "es-ES", {
        weekday: "short",
        day: "numeric",
        month: "short"
      });

    const moonIcon = getMoonPhaseIcon(d.astrodata.tithi);
    
    let badgeHtml = "";
    if (isToday) badgeHtml += `<span class="badge today-badge">${translations[currentLang].todayBadge}</span>`;
    if (d.ekadashiName) badgeHtml += `<span class="badge ekadashi-badge">${translations[currentLang].ekadashiBadge}</span>`;
    if (d.fast) badgeHtml += `<span class="badge fast">${translations[currentLang].fastingBadge}</span>`;

    let titleText = weekdayStr;
    if (d.ekadashiName) {
      titleText += ` — Ekādaśī: ${d.ekadashiName}`;
    }

    let eventsText = "";
    if (d.events && d.events.length > 0) {
      eventsText = d.events.map(e => translateEventText(e.text)).join(", ");
    }

    card.innerHTML = `
      <div class="day-header-line">
        <span class="day-title">${titleText}</span>
        <div class="badges-container">
          ${badgeHtml}
          <span class="day-moon-phase" title="Tithi: ${d.astrodata.tithi}">${moonIcon}</span>
        </div>
      </div>
      ${eventsText ? `<div class="day-events-text">${eventsText}</div>` : ""}
    `;
    
    container.appendChild(card);
  });
}

// Grid View Renderer
function renderGridView(days, container) {
  if (!days.length) {
    container.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--color-text-muted);">No dates matched criteria.</div>`;
    return;
  }

  // Group days by month and year
  const monthsGroup = {};
  days.forEach(d => {
    const key = `${d.date.year}-${d.date.month}`;
    if (!monthsGroup[key]) monthsGroup[key] = [];
    monthsGroup[key].push(d);
  });

  const gridContainer = document.createElement("div");
  gridContainer.className = "grid-container";

  // Render month-by-month grids
  Object.keys(monthsGroup).forEach(key => {
    const monthDays = monthsGroup[key];
    const firstDay = monthDays[0];
    
    const monthSection = document.createElement("div");
    monthSection.className = "grid-month-section";

    // Format Month Title
    const tempDate = new Date(firstDay.date.year, firstDay.date.month - 1, 1);
    const monthTitleStr = tempDate.toLocaleDateString(currentLang === "en" ? "en-US" : "es-ES", {
      month: "long",
      year: "numeric"
    });

    const title = document.createElement("h3");
    title.className = "grid-month-title";
    title.textContent = monthTitleStr.charAt(0).toUpperCase() + monthTitleStr.slice(1);
    monthSection.appendChild(title);

    const grid = document.createElement("div");
    grid.className = "grid-days-grid";

    // Add day of week headers
    const dows = currentLang === "en" ? ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] : ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];
    dows.forEach(d => {
      const header = document.createElement("div");
      header.className = "grid-dow-header";
      header.textContent = d;
      grid.appendChild(header);
    });

    // Calculate empty offset cells for the 1st of the month
    // In our header Sunday is 0, Monday is 1, etc. Match with native getDay()
    const firstOfMonthDate = new Date(firstDay.date.year, firstDay.date.month - 1, firstDay.date.day);
    const startDow = firstOfMonthDate.getDay(); 
    
    for (let i = 0; i < startDow; i++) {
      const emptyCell = document.createElement("div");
      emptyCell.className = "grid-day-cell empty";
      grid.appendChild(emptyCell);
    }

    // Add days
    monthDays.forEach(d => {
      const cell = document.createElement("div");
      cell.className = "grid-day-cell";
      
      const isToday = checkIsToday(d.date);
      if (isToday) cell.classList.add("today");
      if (d.ekadashiName) cell.classList.add("ekadashi");
      if (d.fast) cell.classList.add("fasting");

      cell.addEventListener("click", () => {
        openDayDetailModal(d);
      });

      // Indicators dots
      let dotsHtml = "";
      if (d.fast) dotsHtml += `<span class="grid-dot fast-dot" title="Fast"></span>`;
      if (d.ekadashiName) dotsHtml += `<span class="grid-dot ekadashi-dot" title="Ekadashi"></span>`;
      if (d.events && d.events.length > 0 && !d.ekadashiName) {
        dotsHtml += `<span class="grid-dot" title="Events"></span>`;
      }

      cell.innerHTML = `
        <span class="grid-day-number">${d.date.day}</span>
        <span class="grid-moon">${getMoonPhaseIcon(d.astrodata.tithi)}</span>
        <div class="grid-indicators">${dotsHtml}</div>
      `;

      grid.appendChild(cell);
    });

    monthSection.appendChild(grid);
    gridContainer.appendChild(monthSection);
  });

  container.appendChild(gridContainer);
}

function checkIsToday(dateObj) {
  const today = new Date();
  return dateObj.day === today.getDate() &&
         dateObj.month === (today.getMonth() + 1) &&
         dateObj.year === today.getFullYear();
}

// Return moon phase emojis based on lunar tithi
function getMoonPhaseIcon(tithi) {
  if (tithi === 0 || tithi === 30) return "🌑"; // Amavasya (New Moon)
  if (tithi === 15) return "🌕"; // Purnima (Full Moon)
  if (tithi > 0 && tithi < 8) return "🌒";
  if (tithi >= 8 && tithi < 15) return "🌔";
  if (tithi > 15 && tithi < 23) return "🌖";
  return "🌘";
}

// Alternate calendar view layout
function setCalendarView(view) {
  currentView = view;
  document.getElementById("btnListView").classList.toggle("active", view === "list");
  document.getElementById("btnGridView").classList.toggle("active", view === "grid");
  renderCalendar();
}

// Detailed day modal dialog populator
function openDayDetailModal(d) {
  const modal = document.getElementById("dayDetailModal");
  const t = translations[currentLang];
  
  // Format modal title date
  const fullDateStr = new Date(d.date.year, d.date.month - 1, d.date.day)
    .toLocaleDateString(currentLang === "en" ? "en-US" : "es-ES", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric"
    });

  document.getElementById("modalTitle").innerText = fullDateStr;
  
  // Populate astronomical details
  const tithiName = d.ekadashiName ? `${d.ekadashiName} (${getMoonPhaseIcon(d.astrodata.tithi)})` : `Tithi ${d.astrodata.tithi} ${getMoonPhaseIcon(d.astrodata.tithi)}`;
  const gaurabdaYear = d.astrodata.gaurabda_year;
  const masaName = getMasaName(d.astrodata.masa);
  const sunrise = d.astrodata.sun.rise.substring(0, 5);
  const sunset = d.astrodata.sun.set.substring(0, 5);
  const noon = d.astrodata.sun.noon.substring(0, 5);

  document.getElementById("modalAstroTitle").innerText = t.modalAstroTitle;
  document.getElementById("modalEventsTitle").innerText = t.modalEventsTitle;

  const astroBody = `
    <div class="modal-astro-item">
      <span>${t.tithiLabel}</span>
      <strong>${tithiName}</strong>
    </div>
    <div class="modal-astro-item">
      <span>${t.masaLabel}</span>
      <strong>${masaName}</strong>
    </div>
    <div class="modal-astro-item">
      <span>${t.gaurabdaLabel}</span>
      <strong>${gaurabdaYear}</strong>
    </div>
    <div class="modal-astro-item">
      <span>${t.sunriseLabel} / ${t.sunsetLabel}</span>
      <strong>☀️ ${sunrise} / 🌙 ${sunset}</strong>
    </div>
    <div class="modal-astro-item">
      <span>${t.noonLabel}</span>
      <strong>🕛 ${noon}</strong>
    </div>
  `;
  document.getElementById("modalAstroGrid").innerHTML = astroBody;

  // Populate events/festivals
  let eventsHtml = "";
  if (d.events && d.events.length > 0) {
    if (d.events.length > 1) {
      const eventsJson = encodeURIComponent(JSON.stringify(d.events));
      eventsHtml += `
        <div style="margin-bottom: 12px; display: flex; justify-content: flex-end;">
          <button class="secondary" onclick="addToGoogleCalendarAll('${d.date.year}', '${d.date.month}', '${d.date.day}', '${eventsJson}')" style="padding: 6px 12px; font-size: 12.5px; border-radius: 10px; width: 100%;">
            📅 ${t.addToGoogleAll || "Añadir todos a Google Calendar"}
          </button>
        </div>
      `;
    }
    d.events.forEach(e => {
      const isFast = e.text.toLowerCase().includes("fast");
      eventsHtml += `
        <div class="modal-event-item ${isFast ? "fast-item" : ""}">
          <div>${translateEventText(e.text)}</div>
          <div style="margin-top: 4px; display: flex; justify-content: flex-end;">
            <button class="secondary" onclick="addToGoogleCalendar('${d.date.year}', '${d.date.month}', '${d.date.day}', '${e.text.replace(/'/g, "\\'")}')" style="padding: 4px 8px; font-size: 11px; border-radius: 8px;">
              ➕ Google Calendar
            </button>
          </div>
        </div>
      `;
    });
  } else {
    eventsHtml = `<div style="color: var(--color-text-muted); font-style: italic;">No events on this day.</div>`;
  }
  document.getElementById("modalEventsList").innerHTML = eventsHtml;

  // Add event handlers to buttons in footer
  const footerContainer = document.getElementById("modalFooter");
  footerContainer.innerHTML = `
    <button class="secondary" onclick="exportarICSUnDia(${JSON.stringify(d).replace(/"/g, '&quot;')})">${t.exportBtn}</button>
    <button onclick="document.getElementById('dayDetailModal').close()">${t.closeModal}</button>
  `;

  modal.showModal();
}

// Convert masa ID to human-readable names
function getMasaName(masaId) {
  const masaNamesEs = [
    "Madhusudana", "Trivikrama", "Vamana", "Sridhara", "Hrisikesa", "Padmanabha",
    "Damodara", "Kesava", "Narayana", "Madhava", "Govinda", "Visnu", "Purusottama Adhika"
  ];
  const masaNamesEn = [
    "Madhusudana", "Trivikrama", "Vamana", "Sridhara", "Hrisikesa", "Padmanabha",
    "Damodara", "Kesava", "Narayana", "Madhava", "Govinda", "Visnu", "Purusottama Adhika"
  ];
  
  const names = currentLang === "en" ? masaNamesEn : masaNamesEs;
  return names[masaId] || `Masa ${masaId}`;
}

// Trigger quick date views
function mostrarHoy() {
  initDates();
  generarCalendario();
}

// Event live searching API caller
async function buscarEventoSiguiente() {
  if (!selectedCity) {
    alert(currentLang === "en" ? "Select a city first" : "Selecciona una ciudad primero");
    return;
  }

  const query = document.getElementById("searchQueryInput").value.trim();
  if (!query) {
    alert(currentLang === "en" ? "Please enter an event name" : "Por favor, escribe el nombre de un evento");
    return;
  }

  const count = parseInt(document.getElementById("searchCountSelect").value) || 5;
  const now = new Date();
  
  showLoader("loadingSearch");
  
  const url = `${BASE_URL}/search-event?city=${encodeURIComponent(selectedCity.city)}&country=${encodeURIComponent(selectedCity.country)}&query=${encodeURIComponent(query)}&count=${count}&year=${now.getFullYear()}&month=${now.getMonth() + 1}&day=${now.getDate()}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Search API error");
    const data = await response.json();
    
    renderSearchResults(data.matches);
  } catch (error) {
    console.error("Error searching event:", error);
    alert(translations[currentLang].errorSearch);
  } finally {
    hideLoader();
  }
}

// Render event search results
function renderSearchResults(matches) {
  const container = document.getElementById("searchResultsOutput");
  container.innerHTML = "";
  const t = translations[currentLang];

  if (!matches || !matches.length) {
    container.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--color-text-muted);">${t.noMatches}</div>`;
    return;
  }

  const panel = document.createElement("div");
  panel.className = "search-results-panel";

  matches.forEach(m => {
    const card = document.createElement("div");
    card.className = "search-match-card";
    
    if (m.ekadashiName) card.classList.add("ekadashi");
    if (m.fast) card.classList.add("fasting");

    const matchDate = new Date(m.date.year, m.date.month - 1, m.date.day);
    const dateStr = matchDate.toLocaleDateString(currentLang === "en" ? "en-US" : "es-ES", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric"
    });

    const otherEvents = m.events
      .filter(e => e.text !== m.matching_event)
      .map(e => translateEventText(e.text))
      .join(", ");

    let badgeHtml = "";
    if (m.ekadashiName) badgeHtml += `<span class="badge ekadashi-badge">${t.ekadashiBadge}</span>`;
    if (m.fast) badgeHtml += `<span class="badge fast">${t.fastingBadge}</span>`;

    card.innerHTML = `
      <div class="search-match-header">
        <span class="search-match-date">${dateStr}</span>
        <div class="badges-container">${badgeHtml}</div>
      </div>
      <div class="search-match-event-text">${translateEventText(m.matching_event)}</div>
      ${otherEvents ? `<div class="search-match-other-events"><i>Otros eventos:</i> ${otherEvents}</div>` : ""}
      <div class="search-match-actions">
        <button class="secondary" onclick="addToGoogleCalendar('${m.date.year}', '${m.date.month}', '${m.date.day}', '${m.matching_event.replace(/'/g, "\\'")}')">
          ➕ Google Calendar
        </button>
        <button onclick="exportarICSUnDia(${JSON.stringify(m).replace(/"/g, '&quot;')})">
          📥 ICS
        </button>
      </div>
    `;

    panel.appendChild(card);
  });

  container.appendChild(panel);
}

// Redirect helpers for Google Calendar
function addToGoogleCalendar(year, month, day, title, details = "Calculado según el Calendario Vaisnava.") {
  // Format values safely
  const y = String(year);
  const m = String(month).padStart(2, "0");
  const d = String(day).padStart(2, "0");
  
  const startDateStr = `${y}${m}${d}`;
  
  // All day event end date is exclusive (day + 1)
  const endDate = new Date(year, month - 1, parseInt(day) + 1);
  const ey = String(endDate.getFullYear());
  const em = String(endDate.getMonth() + 1).padStart(2, "0");
  const ed = String(endDate.getDate()).padStart(2, "0");
  const endDateStr = `${ey}${em}${ed}`;
  
  const text = translateEventText(title);
  
  const gcalUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(text)}&dates=${startDateStr}/${endDateStr}&details=${encodeURIComponent(translateEventText(details))}&sf=true&output=xml`;
  window.open(gcalUrl, "_blank");
}

function addToGoogleCalendarAll(year, month, day, eventsJson) {
  const events = JSON.parse(decodeURIComponent(eventsJson));
  const combinedTitle = currentLang === "en" ? "Vaishnava Festivals" : "Festivales Vaisnavas";
  const details = events.map((e, idx) => `${idx + 1}. ${translateEventText(e.text)}`).join("\n");
  addToGoogleCalendar(year, month, day, combinedTitle, details);
}

// Custom ICS exporter for calendar range
function exportarICS() {
  if (!lastCalendarData) {
    alert(currentLang === "en" ? "Generate a calendar first" : "Primero genera un calendario");
    return;
  }

  const incluirAlarmas = document.getElementById("icsIncludeAlarms").checked;
  const alarmaHoras = parseInt(document.getElementById("icsAlarmHours").value) || 15;
  const soloAyunosExport = document.getElementById("icsOnlyFasts").checked;

  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//GCAL Moderno//Calendario Vaisnava//ES",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH"
  ];

  const ahora = new Date().toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";

  lastCalendarData.days.forEach((d, index) => {
    // filter export list
    if (soloAyunosExport && !d.fast) return;
    if (!(d.fast || (d.events && d.events.length > 0))) return;

    const start = `${d.date.year}${String(d.date.month).padStart(2, "0")}${String(d.date.day).padStart(2, "0")}`;
    
    const nextDate = new Date(d.date.year, d.date.month - 1, d.date.day + 1);
    const end = `${nextDate.getFullYear()}${String(nextDate.getMonth() + 1).padStart(2, "0")}${String(nextDate.getDate()).padStart(2, "0")}`;

    let title = "Evento vaisnava";
    if (d.events && d.events.length > 0) {
      title = d.events[0].text;
    }
    if (d.fast && !d.ekadashiName && d.events && d.events.length > 0) {
      title = d.events[0].text.replace(", (Fast today)", "").replace("(Fast today)", "").trim();
    }
    if (d.fast && !d.ekadashiName && (!d.events || d.events.length === 0)) {
      title = "Ayuno vaisnava";
    }
    if (d.ekadashiName && d.fast) {
      title += ` — Ekādaśī: ${d.ekadashiName}`;
    }

    const description = d.events ? d.events.map(e => e.text).join(" | ") : "";

    lines.push(
      "BEGIN:VEVENT",
      `UID:gcal-moderno-${start}-${index}@local`,
      `DTSTAMP:${ahora}`,
      "X-APPLE-DEFAULT-ALARM:FALSE",
      `DTSTART;VALUE=DATE:${start}`,
      `DTEND;VALUE=DATE:${end}`,
      `SUMMARY:${limpiarTexto(translateEventText(title))}`,
      `DESCRIPTION:${limpiarTexto(translateEventText(description))}`
    );

    if (incluirAlarmas && d.fast) {
      lines.push(
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        `DESCRIPTION:${limpiarTexto("Recordatorio de Ayuno: " + translateEventText(title))}`,
        `TRIGGER;RELATED=START:-PT${alarmaHoras}H`,
        "END:VALARM"
      );
    }

    lines.push("END:VEVENT");
  });

  lines.push("END:VCALENDAR");

  const ics = lines.join("\r\n");
  descargarICSFile(ics, "VaisnavaCalendar.ics");
}

// Custom ICS exporter for a single day event
function exportarICSUnDia(d) {
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//GCAL Moderno//Calendario Vaisnava//ES",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH"
  ];

  const ahora = new Date().toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";
  const start = `${d.date.year}${String(d.date.month).padStart(2, "0")}${String(d.date.day).padStart(2, "0")}`;
  
  const nextDate = new Date(d.date.year, d.date.month - 1, d.date.day + 1);
  const end = `${nextDate.getFullYear()}${String(nextDate.getMonth() + 1).padStart(2, "0")}${String(nextDate.getDate()).padStart(2, "0")}`;

  let title = d.ekadashiName ? `Ekādaśī: ${d.ekadashiName}` : "Evento vaisnava";
  if (d.matching_event) {
    title = d.matching_event;
  } else if (d.events && d.events.length > 0) {
    title = d.events[0].text;
  }

  const description = d.events ? d.events.map(e => e.text).join(" | ") : (d.matching_event || "");

  lines.push(
    "BEGIN:VEVENT",
    `UID:gcal-single-${start}@local`,
    `DTSTAMP:${ahora}`,
    "X-APPLE-DEFAULT-ALARM:FALSE",
    `DTSTART;VALUE=DATE:${start}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${limpiarTexto(translateEventText(title))}`,
    `DESCRIPTION:${limpiarTexto(translateEventText(description))}`
  );

  if (d.fast) {
    lines.push(
      "BEGIN:VALARM",
      "ACTION:DISPLAY",
      `DESCRIPTION:${limpiarTexto("Recordatorio: " + translateEventText(title))}`,
      "TRIGGER;RELATED=START:-PT15H",
      "END:VALARM"
    );
  }

  lines.push("END:VEVENT", "END:VCALENDAR");

  const ics = lines.join("\r\n");
  descargarICSFile(ics, `${title.replace(/[^a-zA-Z0-9]/g, "_")}.ics`);
}

function descargarICSFile(icsContent, filename) {
  const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
}

function limpiarTexto(texto) {
  return String(texto || "")
    .replace(/\\/g, "\\\\")
    .replace(/\n/g, "\\n")
    .replace(/,/g, "\\,")
    .replace(/;/g, "\\;");
}

// Translations string switcher
function applyTranslations() {
  const t = translations[currentLang];

  document.getElementById("title").innerText = t.title;
  document.getElementById("searchCityLabel").innerText = t.searchCity;
  document.getElementById("cityInput").placeholder = t.searchPlaceholder;
  document.getElementById("selectedCityLabel").innerText = t.selectedCity;
  document.getElementById("saveDefaultBtn").innerText = t.saveDefaultBtn;
  document.getElementById("generateLabel").innerText = t.generate;
  document.getElementById("fastFilterText").innerText = t.fastFilter;
  document.getElementById("startDateLabel").innerText = t.startDate;
  document.getElementById("endDateLabel").innerText = t.endDate;
  document.getElementById("generateBtn").innerText = t.generateBtn;
  document.getElementById("todayBtn").innerText = t.todayBtn;
  document.getElementById("exportBtn").innerText = t.exportBtn;
  document.getElementById("resultLabel").innerText = t.result;

  // Tab translations
  document.getElementById("tabCalendar").innerText = t.generate;
  document.getElementById("tabSearchEvents").innerText = t.searchEventsTab;

  // Search Event elements
  document.getElementById("searchQueryLabel").innerText = t.searchQueryLabel;
  document.getElementById("searchQueryInput").placeholder = t.searchQueryPlaceholder;
  document.getElementById("searchCountLabel").innerText = t.searchCountLabel;
  document.getElementById("searchEventBtn").innerText = t.searchBtnLabel;

  // Export customization settings
  document.getElementById("toggleExportSettings").innerText = t.exportSettingsLabel;
  document.getElementById("labelIncludeAlarms").innerText = t.includeAlarmsLabel;
  document.getElementById("labelAlarmHours").innerText = t.alarmHoursLabel;
  document.getElementById("labelOnlyFastsExport").innerText = t.onlyFastsExportLabel;

  // Alarm select options
  const opt0 = document.getElementById("optAlarm0");
  const opt12 = document.getElementById("optAlarm12");
  const opt15 = document.getElementById("optAlarm15");
  const opt24 = document.getElementById("optAlarm24");
  if (opt0) opt0.text = t.hours0;
  if (opt12) opt12.text = t.hours12;
  if (opt15) opt15.text = t.hours15;
  if (opt24) opt24.text = t.hours24;

  // View selectors
  document.getElementById("btnListView").innerText = t.viewList;
  document.getElementById("btnGridView").innerText = t.viewGrid;

  // Active state lang buttons
  document.querySelectorAll(".language-buttons button").forEach(btn => {
    btn.classList.remove("active");
  });
  if (currentLang === "es") {
    document.querySelector(".language-buttons button:first-child").classList.add("active");
  } else {
    document.querySelector(".language-buttons button:last-child").classList.add("active");
  }

  // Reload lists if there is data
  if (lastCalendarData) renderCalendar();
}

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem("lang", lang);
  applyTranslations();
}

// Loader overlay operations
let loaderTimer = null;
let loaderSeconds = 0;

function showLoader(titleKey) {
  const t = translations[currentLang];
  document.getElementById("loadingTitle").innerText = t[titleKey] || "Loading...";
  
  const progressBar = document.getElementById("progressBar");
  const timerText = document.getElementById("timerText");
  
  progressBar.style.width = "0%";
  loaderSeconds = 0;
  timerText.innerText = t.elapsed.replace("{sec}", "0");
  
  document.getElementById("loadingOverlay").classList.add("active");
  
  clearInterval(loaderTimer);
  loaderTimer = setInterval(() => {
    loaderSeconds++;
    timerText.innerText = t.elapsed.replace("{sec}", loaderSeconds);
    const percentage = Math.min(90, (loaderSeconds / 50) * 100);
    progressBar.style.width = `${percentage}%`;
  }, 1000);
}

function hideLoader() {
  document.getElementById("loadingOverlay").classList.remove("active");
  clearInterval(loaderTimer);
  setTimeout(() => {
    document.getElementById("progressBar").style.width = "0%";
  }, 300);
}

// Event translation replacements
function translateEventText(text) {
  if (currentLang === "en") return text;
  let t = text;

  t = t.replaceAll("Lord ", "Sri ");
  t = t.replaceAll("Appearance", "Aparición");
  t = t.replaceAll("Disappearance", "Desaparición");
  t = t.replaceAll("Fasting for ", "Ayuno por ");
  t = t.replaceAll("Break fast", "Romper ayuno");
  t = t.replaceAll("Fast today", "Ayuno hoy");
  t = t.replaceAll("Fasting is done yesterday", "Ayuno realizado ayer");
  t = t.replaceAll("consort of ", "consorte de ");
  t = t.replaceAll("First day of ", "Primer día de ");
  t = t.replaceAll("Last day of ", "Último día de ");
  t = t.replaceAll("begins", "comienza");
  t = t.replaceAll("ends", "termina");
  t = t.replaceAll("fast for one month", "ayuno por un mes");
  t = t.replaceAll("green leafy vegetable", "vegetales de hoja verde");
  t = t.replaceAll("yogurt", "yogur");
  t = t.replaceAll("milk", "leche");

  return t;
}

// PWA Service worker registration
function initPWA() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js")
      .then(reg => console.log("PWA Service Worker registered", reg))
      .catch(err => console.error("PWA Service Worker registration failed", err));
  }
}
