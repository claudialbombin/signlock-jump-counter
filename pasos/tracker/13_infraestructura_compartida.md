# Paso 13 — Reutilizar infraestructura compartida (cámara y calibración)

## Rama
`feature/rope-jump-counter` (coordinación con `feature/sign-language-auth` y `feature/calibration`)

## Descripción
El bloque de seguridad ya ha construido, en `feature/sign-language-auth`, un wrapper de cámara reutilizable (`lse_auth/camera.py`, clase `Camera`) que aplica la corrección de distorsión de la calibración (`calibration/camera_params.npz`) y el espejado. Tu bloque necesita exactamente lo mismo (leer frames ya corregidos). **No lo reimplementes desde cero ni diverjas en cómo se aplica la calibración** — generaría dos formas distintas de leer la cámara en el mismo proyecto, y complicaría mucho la integración final.

## Cómo hacerlo
Dos formas de resolverlo, a decidir en equipo (dejarlo escrito aquí una vez decidido):

1. **Importar directamente `lse_auth.camera.Camera`** desde tu rama mientras desarrollas en aislado (puede dar warnings de "módulo no relacionado" pero funciona), y dejar que en `feature/integration` esa clase se mueva a un sitio neutral (p. ej. `core/camera.py`) que usen ambos bloques sin que ninguno "sea dueño" de la cámara.
2. **Mover `camera.py` y `calibration_io.py` a un paquete compartido `core/` ya en este Paso 13**, coordinado con la otra persona (puede ser un PR pequeño y rápido contra `main` o `feature/integration` que ambas ramas reciban por rebase/merge) — más limpio a largo plazo, pero requiere coordinarlo antes de que las dos ramas avancen mucho más, para no generar conflictos grandes luego.

En cualquier caso: usa `calibration/camera_params.npz` tal cual lo exporta `calibration_main.py` (rama `feature/calibration`, ya en `main`) — no recalcules la calibración por tu cuenta ni generes un segundo fichero de parámetros.

## Qué necesita estar hecho antes
Nada técnico de tu parte; es una decisión de coordinación. Idealmente resolverla antes de avanzar mucho en los Pasos 3-6, para no tener que reescribir la lectura de cámara más tarde.

## Entregable del paso
Decisión documentada aquí (opción 1 o 2, y por qué) + confirmación con la persona de `feature/sign-language-auth` de que está de acuerdo.
