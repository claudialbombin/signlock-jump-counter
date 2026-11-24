# Paso 11 — Pruebas, ajuste de umbrales y medición de robustez

## Rama
`feature/sign-language-auth`

## Descripción
Antes de dar por cerrado tu bloque, conviene medir qué tan fiable es en condiciones reales (no solo con el dataset de referencia controlado del Paso 2), y dejar constancia de ello — el informe pide justificar el método de detección, y tener números de precisión ayuda mucho.

## Cómo hacerlo
1. Probar el sistema completo (Pasos 3-9 encadenados) en vivo, con distinta iluminación (luz natural vs. artificial) y, si es posible, con otra persona haciendo las señas (no solo tú) para comprobar que los umbrales no están sobreajustados a tu propia mano/mano de cámara.
2. Hacer una tabla sencilla: nº de intentos de secuencia completa H-O-L-A, nº de desbloqueos correctos, nº de falsos resets, nº de letras mal clasificadas individualmente — esto es directamente el contenido de la sección "Resultados" del informe para tu bloque.
3. Volver a los Pasos 3 (umbrales de piel) y 6 (umbrales del clasificador) si los resultados son pobres, y repetir la medición.
4. Anotar casos límite conocidos (p. ej. confusión H/L si los dedos no están bien juntos, fallos si hay otra zona de piel visible en el ROI) — esto alimenta directamente la sección "Futuros Desarrollos" del informe.

## Qué necesita estar hecho antes
Pasos 3 a 9 integrados y funcionando de punta a punta en un demo propio (no hace falta esperar a la integración completa del Paso 10 para esta medición).

## Entregable del paso
Tabla de resultados (puede ser un `.md` o `.csv` dentro de `pasos/`) con las métricas de la prueba, y lista corta de casos límite/limitaciones conocidas.

---

## Cómo se mide (implementado el 24/11)

### Sesión de prueba
```bash
python main.py --trials --log --tag natural     # luz natural, Claudia
python main.py --trials --log --tag artificial  # luz artificial
python main.py --trials --log --tag tere        # otra persona
```
- `--trials` no abre el tracker: cada vez que se desbloquea vuelve a bloquear, aprende el fondo otra vez (2 s para sacar la mano) y espera el código de nuevo. `q` termina la sesión.
- `--log` guarda cada evento del decodificador en `pasos/lse/pruebas/sesion_<fecha>_<tag>.csv`. El `tag` es la condición de la prueba y es la fila de la tabla.
- Protocolo: en cada intento se intenta deletrear H-O-L-A entero, sin hacer letras de otras a propósito. Así cualquier letra que no sea la esperada es una letra mal leída por el sistema. Si una vez te equivocas tú, pulsa `r`: ese intento queda como abortado y no cuenta.
- Objetivo: unos 20 intentos por condición.

### Tabla
```bash
python -m lse_auth.trial_report                                   # todas las sesiones
python -m lse_auth.trial_report --out pasos/lse/pruebas/resultados.md
```
Cuenta, por condición y en total:

| Columna | Qué es |
|---|---|
| Intentos | Desde la primera letra correcta hasta `unlocked`, `wrong`, `restart` o `timeout`. Los abortados con `r` no cuentan. |
| Desbloqueos y tasa | Intentos que terminan en `unlocked`. |
| Falsos resets | Intentos perdidos porque se leyó una letra que no era la esperada (`wrong` o `restart`). |
| Timeouts | 30 s sin letra correcta. |
| Letras mal leídas | Cada `wrong`/`restart`, con el par esperada→leída (p. ej. O->H), que dice qué regla del Paso 6 hay que revisar. |
| Tiempo medio / mediana | Segundos desde la H hasta el desbloqueo. |

Los tests (`tests/test_trial_report.py`) comprueban el recuento con logs escritos a mano.

### Limitación
El log solo ve las letras que el estabilizador confirma. Una letra que nunca llega a confirmarse (la mano no se reconoce) no aparece como error: se nota en el tiempo hasta desbloquear o acaba en timeout.

## Resultados

Pendiente de las sesiones en vivo.
