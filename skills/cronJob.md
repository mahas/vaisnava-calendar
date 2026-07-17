<!--
Este archivo sirve como una "Skill" o guía de instrucciones automatizadas (runbook) para que el agente de IA administre el workflow de Keep-Alive en GitHub Actions.
Cuando el usuario pida seguir estas instrucciones, el agente debe preguntar si desea activar, desactivar o modificar el intervalo del cron, realizar los cambios en el archivo YAML de workflow y subirlos a GitHub.
-->

# Skill: Administración del Workflow de Keep-Alive

Este archivo contiene instrucciones precisas que tú (el agente de IA) debes seguir de manera interactiva para modificar el intervalo de tiempo o activar/desactivar el servicio keep-alive (que evita que el servidor gratuito de Render entre en suspensión).

## Instrucciones para el Agente (Runbook)

Cuando el usuario te solicite "seguir las instrucciones de `skills/cronJob.md`", debes ejecutar los siguientes pasos de forma secuencial:

### Paso 1: Interactuar con el usuario para determinar la acción
Pregúntale al usuario a través del chat qué desea realizar. Presenta las siguientes opciones:
1. **Activar el servicio** (Descomentar el disparador cron en el archivo del workflow).
2. **Desactivar el servicio** (Comentar el disparador cron en el archivo del workflow).
3. **Cambiar el intervalo de tiempo** (Modificar los minutos de ejecución del cron).

### Paso 2: Leer el archivo de configuración del workflow
Abre y lee el contenido del archivo de workflow localizado en:
`/.github/workflows/keep-alive.yml`

### Paso 3: Modificar el archivo según la opción elegida

#### Caso A: Activar el servicio
Asegúrate de que la sección `schedule` y su respectiva regla `cron` estén descomentadas. El archivo debe quedar con esta estructura en la parte superior:
```yaml
on:
  schedule:
    # Runs every X minutes to keep the Render free-tier container active
    - cron: '*/12 * * * *'
  workflow_dispatch:
```
*(Si no estaba comentada, avísale al usuario que ya se encontraba activa).*

#### Caso B: Desactivar el servicio
Desactiva las líneas del programador automático agregando el símbolo `#` al inicio de la sección `schedule` y del `cron`. Debe quedar con esta estructura:
```yaml
on:
  # schedule:
  #   # Runs every X minutes to keep the Render free-tier container active
  #   - cron: '*/12 * * * *'
  workflow_dispatch:
```
*(De esta forma, el cron automático no se ejecuta, pero se mantiene la opción `workflow_dispatch` para permitir dispararlo manualmente si se desea).*

#### Caso C: Cambiar el intervalo de tiempo
1. Pregúntale al usuario por el intervalo en minutos que desea (ej. 14 minutos).
2. Modifica el valor dentro del cron en el archivo YAML:
   `- cron: '*/<MINUTOS> * * * *'` (ejemplo: `- cron: '*/14 * * * *'`).
3. Asegúrate de que las líneas no estén comentadas para que el cambio surta efecto de inmediato.

### Paso 4: Validar la sintaxis YAML
Asegúrate de que el formato de indentación y espaciado del archivo `.github/workflows/keep-alive.yml` siga siendo válido tras tu edición.

### Paso 5: Confirmar y subir a GitHub
Una vez realizados los cambios en el archivo local:
1. Corre `git status` para verificar la modificación de `.github/workflows/keep-alive.yml`.
2. Ejecuta `git add .github/workflows/keep-alive.yml`.
3. Haz un commit con un mensaje claro en español o inglés, según corresponda (ejemplo: `"ci: update keep-alive cron job schedule to 14 minutes"` o `"ci: disable keep-alive cron job schedule"`).
4. Sube los cambios mediante `git push origin main`.
5. Confirma en el chat que el cambio se ha subido exitosamente.
