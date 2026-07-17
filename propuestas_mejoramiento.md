# Propuestas de Mejoramiento y Optimización

Este documento contiene un conjunto de recomendaciones para optimizar el rendimiento, mejorar la experiencia de usuario (UI/UX) y potenciar las funcionalidades del **Calendario Vaisnava**.

---

## 1. Optimización de Rendimiento y Alojamiento

### ⚡ Mitigación del Arranque en Frío (Cold Start)
Actualmente, el servidor de Render (en su plan gratuito) entra en suspensión después de 15 minutos de inactividad, lo que genera una espera de hasta 50 segundos para el primer usuario.
* **Propuesta**: Configurar un servicio de monitoreo externo gratuito (como *UptimeRobot*, *Better Uptime* o un *cron job* simple en GitHub Actions) que realice una solicitud `GET` ligera (por ejemplo, a `/countries` o un endpoint `/ping` nuevo) cada 14 minutos. Esto mantendrá activa la instancia de Render continuamente.

### 💾 Caché de Consultas en el Servidor
Los cálculos astrológicos son deterministas (para una misma ciudad y rango de fechas, el resultado nunca cambia).
* **Propuesta**: Implementar un sistema de caché en el backend (usando un diccionario simple en memoria con tiempo de expiración o *Flask-Caching* con almacenamiento en disco/SQLite) para almacenar las respuestas de los calendarios ya generados. Esto evitará recálculos costosos en la CPU de Python para consultas repetitivas de ciudades populares.

### 📥 Caché del Lado del Cliente (Navegador)
El cliente actualmente solicita los datos al servidor cada vez que se genera un calendario.
* **Propuesta**: Almacenar las respuestas de calendario generadas por el usuario en `localStorage` o `IndexedDB` indexadas por ciudad, año y rango de fechas. Si el usuario vuelve a buscar el mismo rango, se cargan de inmediato desde la caché local sin necesidad de realizar peticiones de red.

---

## 2. Mejoras de UI/UX (Diseño y Usabilidad)

### 📅 Vista de Calendario Mensual (Grid)
El diseño actual muestra una lista vertical continua de días. Aunque es funcional, a los usuarios les resulta más natural ver un mes completo en forma de cuadrícula.
* **Propuesta**: Añadir un selector de vista para alternar entre "Lista" y "Mensual (Cuadrícula)". En la vista de cuadrícula, cada celda representaría un día del mes, permitiendo identificar rápidamente los fines de semana y las fechas importantes de un vistazo.

### 🌟 Resaltado Visual para Ekādaśīs y Ayunos
Los días de Ekādaśī y ayunos son los eventos más importantes del calendario. Actualmente, solo se distinguen por texto como `(Ayuno)` o `— Ekādaśī`.
* **Propuesta**: 
  * Crear un diseño visual diferenciado para estos días (por ejemplo, una tarjeta con borde dorado, fondo degradado sutil en tonos ámbar/amarillo, o un "badge" o insignia vibrante que diga **AYUNO** o **EKĀDAŚĪ**).
  * Usar un icono de luna correspondiente a la fase lunar (creciente/menguante) para enriquecer el aspecto visual del día.

### 🔍 Buscador de Ciudades con Autocompletado (Live Search)
El flujo actual requiere escribir el nombre de la ciudad, hacer clic en "Buscar" y seleccionar el resultado correcto.
* **Propuesta**: Implementar un buscador predictivo que filtre y muestre sugerencias en un menú desplegable a medida que el usuario escribe (utilizando `<datalist>` o una lista flotante generada dinámicamente con un retraso tipo *debounce* para no saturar al servidor).

### 💬 Modales con Detalles de Eventos e Historias
Al hacer clic en un evento o en un día de Ekādaśī, el usuario podría querer saber más.
* **Propuesta**: Permitir que los elementos del calendario sean interactivos (hacer clic). Al pulsar sobre un Ekādaśī, se abriría un panel modal o cajón lateral con información adicional (reglas específicas de ayuno, el horario exacto de ruptura del ayuno y la historia espiritual asociada o *Mahatmya*).

### ⏱️ Ajustes Rápidos de Fecha (Presets)
Tener que usar selectores de fecha nativos para definir rangos amplios puede ser tedioso.
* **Propuesta**: Añadir botones de acceso rápido para establecer el rango de fechas con un solo clic, por ejemplo:
  * "Este mes"
  * "Mes siguiente"
  * "Año actual"
  * "Año Gaurabda actual" (según el calendario vaisnava)

---

## 3. Traducción e Internacionalización

### 🌍 Detección Automática de Idioma
El sitio se carga por defecto en español ("es") o en el último idioma guardado.
* **Propuesta**: En la carga inicial (si no hay preferencia guardada), detectar automáticamente el idioma del navegador mediante `navigator.language`. Si el código del navegador comienza con `en`, configurar por defecto inglés; de lo contrario, español.

### 🛠️ Sistema de Traducción Estructurado (Diccionario de Eventos)
La función `translateEventText` realiza reemplazos manuales con `.replaceAll`. Esto es propenso a fallos, traducciones incompletas o errores de concordancia gramatical.
* **Propuesta**: Estructurar los textos de eventos que devuelve el servidor. En lugar de procesar cadenas planas con reemplazos de texto, sería ideal que el servidor devolviera los eventos con códigos de identificador único (e.g., `EVENT_EKADASHI`, `EVENT_APPEARANCE`) y un mapa de variables (e.g., `personName`). Así, el cliente podrá renderizar la frase estructurada en el idioma seleccionado usando plantillas limpias.

---

## 4. Integraciones y Funcionalidades de Exportación

### 📅 Enlaces de Integración Directa ("Añadir a Google Calendar")
Actualmente se exporta un archivo `.ics` que el usuario debe descargar e importar de forma manual en su calendario.
* **Propuesta**: Añadir enlaces directos para servicios en la nube populares. Por ejemplo, se puede construir una URL para añadir un evento directamente a Google Calendar (`https://calendar.google.com/calendar/render?action=TEMPLATE&...`) para que el usuario guarde eventos clave en su cuenta sin descargar archivos.

### 🔔 Notificaciones Locales y PWA
El calendario es muy útil cuando avisa a tiempo sobre los ayunos.
* **Propuesta**: 
  * Convertir la aplicación en una PWA (Progressive Web App) completa con Service Worker para permitir el funcionamiento offline.
  * Usar la API de Notificaciones de la PWA para programar avisos locales en el dispositivo del usuario el día anterior al ayuno o la mañana del mismo, sin necesidad de tener la pestaña del navegador abierta.

### ⚙️ Personalización del Archivo `.ics`
El archivo `.ics` generado tiene alarmas integradas y fijadas de forma rígida a 15 horas antes y 8 horas después.
* **Propuesta**: Ofrecer al usuario un menú de configuración de exportación donde pueda elegir:
  * Si desea incluir alarmas.
  * Con cuántas horas de anticipación quiere la alarma (e.g., "1 día antes", "12 horas antes", "Solo el mismo día").
  * Si desea exportar todos los eventos o únicamente los días de ayuno.

---

## 5. Arquitectura de Código y Buenas Prácticas

### 📁 Separación de Archivos (Frontend Limpio)
Actualmente, `index.html` es un archivo monolítico de casi 1000 líneas que contiene HTML, CSS extenso y lógica Javascript mezclada.
* **Propuesta**: Separar el proyecto en una estructura limpia:
  * `web/index.html` (Solo estructura semántica)
  * `web/css/styles.css` (Toda la hoja de estilos, facilitando el uso de variables CSS y responsive design)
  * `web/js/app.js` (Toda la lógica de eventos, fetch y manipulación del DOM)

### 🏷️ Datos Estructurados (SEO & Rich Results)
Para que el sitio sea más visible en buscadores como Google.
* **Propuesta**: Implementar marcado de datos estructurados Schema.org (`JSON-LD`) dinámicamente para los festivales generados en el calendario (tipo `Event` o `Festival`). Esto permitiría que los eventos vaisnavas aparezcan como resultados enriquecidos en las búsquedas de Google.
