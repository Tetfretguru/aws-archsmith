# QA Test Plan

## Objetivo

Definir un plan de pruebas para `aws-archsmith` alineado a `INSTRUCTIONS.md`, priorizando el principio **validation before rendering** y el flujo iterativo de diseño arquitectónico.

## Alcance

- Flujo local end-to-end (sin CI).
- Artefacto principal: XML `.drawio` en `architecture/raw/`.
- Validación estructural y de layout con `scripts/validate_drawio.py`.
- Renderizado de salidas en `architecture/rendered/`.

## Dependencias y precondiciones

Validar disponibilidad de:

- `python3`
- `docker`
- `docker compose`
- `make` (recomendado; usar scripts directos si no está)

Precondiciones:

- Directorios inicializados (`architecture/raw`, `architecture/rendered`, `architecture/specs`).
- Permisos de ejecución en scripts cuando aplique.

## Estrategia de prueba

1. Verificar entorno (preflight).
2. Ejecutar flujo feliz E2E (generar -> validar -> renderizar).
3. Probar contrato de validación con casos negativos y positivos.
4. Verificar diseño iterativo incremental sobre el mismo diagrama.
5. Confirmar gate de validación antes de render.
6. Probar rutas de fallback ante fallos de herramientas.

## Casos de prueba

### TP-01 Preflight de entorno

**Objetivo**

Confirmar que el runtime requerido está disponible.

**Pasos**

1. Ejecutar `python3 --version`.
2. Ejecutar `docker --version`.
3. Ejecutar `docker compose version`.
4. Ejecutar `make --version`.

**Resultado esperado**

- Todas las herramientas responden versión válida.
- Si falta `make`, el flujo continúa con comandos directos.

---

### TP-02 Inicialización de estructura

**Objetivo**

Verificar estructura base de carpetas del proyecto.

**Pasos**

1. Ejecutar `make init`.
2. Si `make` no existe, ejecutar `mkdir -p architecture/raw architecture/rendered architecture/specs`.

**Resultado esperado**

- Existen las 3 carpetas esperadas.

---

### TP-03 Flujo E2E feliz con Makefile

**Objetivo**

Validar el flujo estándar completo con validación obligatoria antes del render.

**Pasos**

1. Ejecutar `make generate NAME=qa-baseline PROMPT="public ALB, ECS service, RDS postgres"`.
2. Ejecutar `make validate`.
3. Ejecutar `make render`.

**Resultado esperado**

- Se crea `architecture/raw/qa-baseline.drawio`.
- `make validate` pasa sin errores.
- Se genera `architecture/rendered/qa-baseline.png`.

---

### TP-04 Flujo E2E sin Make (fallback)

**Objetivo**

Asegurar operatividad sin `make`.

**Pasos**

1. Ejecutar `python3 scripts/generate_xml.py --name "qa-fallback" --prompt "public ALB, ECS service, RDS postgres"`.
2. Ejecutar `python3 scripts/validate_drawio.py architecture/raw`.
3. Ejecutar `docker compose -f docker/compose.yml run --rm renderer`.

**Resultado esperado**

- XML generado correctamente.
- Validación exitosa.
- PNG exportado correctamente.

---

### TP-05 Contrato de validación: estructura XML

**Objetivo**

Comprobar que fallan estructuras inválidas.

**Pasos**

1. Crear archivo `.drawio` con root distinto de `<mxfile>`.
2. Ejecutar `python3 scripts/validate_drawio.py architecture/raw`.

**Resultado esperado**

- Falla con mensaje indicando root inválido.
- No se debe ejecutar render para ese estado.

---

### TP-06 Contrato de validación: IDs base

**Objetivo**

Validar requerimiento de celdas base `0` y `1`.

**Pasos**

1. Usar un XML sin una o ambas IDs base.
2. Ejecutar validador.

**Resultado esperado**

- Falla explícita por IDs base faltantes.

---

### TP-07 Contrato de validación: geometría

**Objetivo**

Validar obligatoriedad de geometría numérica y positiva.

**Pasos**

1. Crear vértice sin `mxGeometry`.
2. Crear vértice con `width`/`height` no numéricos.
3. Crear vértice con `width <= 0` o `height <= 0`.
4. Ejecutar validador.

**Resultado esperado**

- Cada caso falla con error correspondiente.

---

### TP-08 Contrato de validación: solapamiento entre siblings

**Objetivo**

Comprobar detección de overlap entre vértices con mismo `parent`.

**Pasos**

1. Ajustar dos vértices con intersección y mismo `parent`.
2. Ejecutar validador.

**Resultado esperado**

- Falla con mensaje de overlap detectado.

---

### TP-09 Contrato de validación: edges ortogonales

**Objetivo**

Comprobar enforcement de `edgeStyle=orthogonalEdgeStyle`.

**Pasos**

1. Modificar una arista quitando la propiedad ortogonal.
2. Ejecutar validador.

**Resultado esperado**

- Falla indicando edge sin estilo ortogonal.

---

### TP-10 Gate de render condicionado a validación

**Objetivo**

Verificar que no se renderiza si hay errores de validación.

**Pasos**

1. Introducir un error de validación conocido en un `.drawio`.
2. Ejecutar `make render` (o flujo manual validación+render).

**Resultado esperado**

- Render bloqueado por validación fallida.
- No se generan imágenes nuevas para estado inválido.

---

### TP-11 Iteración conversacional incremental

**Objetivo**

Verificar que cada prompt incremental aplica solo el delta sobre el mismo archivo.

**Pasos**

1. Partir de un diagrama base en `architecture/raw/`.
2. Aplicar cambio incremental (ej. agregar SQS).
3. Revalidar.
4. Renderizar preview.
5. Aplicar segundo cambio (ej. reconectar ECS -> SQS -> RDS).
6. Revalidar y renderizar nuevamente.

**Resultado esperado**

- Se mantiene el mismo archivo objetivo.
- Se preservan componentes no solicitados para eliminación.
- Cada iteración reporta: cambios, XML, estado de validación y PNG.

---

### TP-12 Fallback sin Docker

**Objetivo**

Asegurar continuidad del trabajo cuando no es posible renderizar.

**Pasos**

1. Simular/confirmar indisponibilidad de Docker.
2. Ejecutar generación y validación.
3. Omitir render y registrar estado pendiente.

**Resultado esperado**

- XML generado y validado.
- Reporte explícito: render pendiente por dependencia faltante.

## Criterios de aceptación

- El flujo base cumple `generate -> validate -> render`.
- Ningún render se ejecuta con validación fallida.
- El validador cubre y detecta todos los contratos definidos en `INSTRUCTIONS.md`.
- El proceso iterativo conserva continuidad de sesión y aplica cambios incrementales.
- Existen rutas de fallback claras para ausencia de `make` o Docker.

## Evidencia y reporte por ejecución

En cada corrida registrar:

- Fecha/hora.
- Comandos ejecutados.
- Archivo XML afectado (`architecture/raw/...`).
- Resultado de validación (pass/fail + mensaje).
- Artefactos generados (`architecture/rendered/...`).
- Incidencias y remediación aplicada.

## Riesgos y notas

- Sin Docker operativo no se puede cerrar cobertura de render.
- Cambios manuales en XML pueden romper IDs/estructura y afectar diffs deterministas.
- Al agregar nuevos servicios o reglas, este plan debe actualizarse junto con `README.md` e `INSTRUCTIONS.md`.
