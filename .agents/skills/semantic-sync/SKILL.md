---
name: semantic-sync
description: Sync new semantic entities between BhaktiLib and Vaishnava Calendar using toAdd.md
---
# Semantic Sync Skill

Esta skill guía al agente sobre cómo sincronizar nuevos elementos semánticos añadidos a BhaktiLib e integrarlos en el Calendario Vaisnava utilizando los archivos `toAdd.md` y `pending-entities.md`.

## Flujo de Trabajo para el Agente

Cuando un usuario solicite sincronizar nuevos elementos o cuando detectes que `toAdd.md` tiene líneas añadidas bajo la sección `---`:

1. **Leer la lista en `toAdd.md`**:
   - Extraer cada línea que represente un nuevo elemento, junto con cualquier metadato provisto.

2. **Soporte de Formato en `toAdd.md`**:
   - **Formato Simple**:
     ```
     Nombre del Concepto
     ```
     *(El agente buscará en `import-output.php` o en la base de datos de BhaktiLib el slug correcto)*.
   
   - **Formato con URL Directa**:
     ```
     Nombre del Concepto
     Link: https://bhaktilib.com/reader/?id=93&cfi=epubcfi(...)
     ```
     *(El agente extraerá los parámetros `id` del libro y la coordenada `cfi` para crear un enlace directo al lector en español/inglés/francés)*.
     
   - **Formato Multilingüe (Múltiples Idiomas)**:
     ```
     Nombre del Concepto
     es: https://bhaktilib.com/reader/?id=93&cfi=epubcfi(...)
     en: https://bhaktilib.com/reader/?id=104&cfi=epubcfi(...)
     ```
     *(El agente asociará el enlace del lector de forma dinámica según el idioma activo del usuario en la interfaz del Calendario)*.

3. **Determinar la entidad en BhaktiLib**:
   > [!IMPORTANT]
   > **Normalización Conceptual (Crucial)**: Para eventos del calendario que contienen detalles circunstanciales o técnicos (por ejemplo, `"First month of Caturmasya begins [PURNIMA SYSTEM]"`), el agente **no debe** intentar buscar ni mapear la frase completa. Debe identificar la **entidad semántica o concepto central** (en este caso, `"Caturmasya"` o `"caturmasya"`) que tenga una ficha temática o biográfica correspondiente en BhaktiLib.
   
   > [!NOTE]
   > **Mapeos Duales (Autor vs. Pasatiempo)**: En apariciones de avatares o deidades (por ejemplo, `"Lord Balarama -- Appearance"`), el enlace puede apuntar a la ficha de CPT `autor` en BhaktiLib (ej: `/autor/sri-balarama/`) o directamente a la lectura del pasatiempo de su aparición en los libros a través de una CFI. El agente debe comprobar si existe una sección del lector idónea o preguntar al usuario el destino preferido.

4. **Integrar en `web/js/app.js`**:
   - Añadir la entidad al mapa `SEMANTIC_ENTITIES` (o al mapa correspondiente de pasatiempos si es un enlace directo a libro).
   - Por ejemplo: `"vyasa purnima"` o `"guru purnima"` ➔ `{ type: "tema", slug: "guru-vyasa-purnima" }`.

5. **Actualizar y limpiar los archivos**:
   - Borrar la línea correspondiente y sus metadatos del archivo `toAdd.md`.
   - Buscar el elemento coincidente en `pending-entities.md` y remover su línea (o marcarlo como completado) de forma que el listado de pendientes se mantenga limpio y actualizado.
   - Guardar los cambios.

6. **Verificar**:
   - Ejecutar pruebas para verificar que el nuevo enlace semántico funciona en la UI del calendario y redirige correctamente a BhaktiLib sin romper nada.
