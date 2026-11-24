# Paso 10 — Integración con el bloque siguiente (tracker del compañero)

## Rama
`feature/sign-language-auth` → se fusiona en `feature/integration`

## Descripción
Según el diagrama de bloques del guion, el "Sistema de seguridad" (tu parte: detector de patrones + decodificador) debe "garantizar o bloquear el paso al siguiente bloque". Aquí se define y se deja lista la interfaz con la que el resto del equipo (bloque Tracker / Sistema Propuesto, rama `feature/rope-jump-counter` u otra) engancha su módulo.

## Cómo hacerlo
1. Exponer una función/objeto único y simple, por ejemplo `lse_auth.run_security_block(cap) -> bool` o, mejor para un bucle de vídeo en vivo, una clase con `.is_unlocked` consultable en cada iteración del bucle principal.
2. Acordar con el resto del equipo el contrato exacto: ¿el bloque de seguridad bloquea la ejecución (bucle propio hasta desbloquear) o corre en paralelo y el bucle principal simplemente no activa el tracker hasta que `is_unlocked` sea `True`? Dejarlo escrito en este fichero una vez decidido.
3. Evitar acoplar `lse_auth/` a detalles del tracker — el módulo de seguridad no debería necesitar saber nada de lo que hace el bloque siguiente, solo informar de `True`/`False`.
4. Probar manualmente el enganche en una rama de integración local antes de abrir PR contra `feature/integration`, para no romper el trabajo de las otras personas.

## Qué necesita estar hecho antes
Paso 8 y 9 funcionando de forma aislada (puedes probarlos con un `main` de prueba propio, p. ej. `lse_auth/demo_standalone.py`, sin depender todavía del resto del equipo).

## Entregable del paso
Interfaz pública documentada (docstring + ejemplo de uso) en `lse_auth/__init__.py`, y confirmación por escrito (issue o mensaje al equipo) del contrato acordado con quien lleve el bloque siguiente.

## Implementación (23/11)
### Contrato decidido
El bloque de seguridad **bloquea la ejecución**: `main.py` llama primero al desbloqueo y, **solo cuando se ha deletreado H-O-L-A**, llama al tracker. No corren en paralelo. Mientras el sistema está bloqueado no hay nada más que hacer, y así el tracker no gasta tiempo de proceso ni baja los FPS del desbloqueo.

```python
# main.py
with Camera() as cam:
    grabber = FrameGrabber(cam)               # un solo hilo de cámara para los dos bloques
    if run_unlock(grabber, WINDOW):           # bloqueante: True al desbloquear, False si se sale con q
        run_tracker(grabber, WINDOW)          # bloque de Tere
```

**Lo que recibe el tracker** (`run_tracker(grabber, window)`):
- `grabber.read()` devuelve el frame más reciente, BGR, 1280×720, **ya sin distorsión** (calibración) y **en espejo**. Devuelve `None` si la cámara se para.
- `window` es la ventana de OpenCV donde dibujar, la misma del desbloqueo, para que el cambio no abra otra ventana.
- Termina cuando el usuario sale (q / ESC). La cámara la abre y la cierra `main.py`.
- Si el tracker necesita la imagen **sin espejo**, basta con `cv2.flip(frame, 1)`.

Mientras el tracker no esté hecho, `run_tracker` en `main.py` es un sustituto que muestra "ACCESO CONCEDIDO" sobre la cámara. **Lo único que tiene que cambiar Tere es el cuerpo de esa función** (o una llamada a su módulo desde ella).

### Código
- `lse_auth/security.py`:
  - **`SecurityBlock`** junta los Pasos 3–9 para un frame. `update(frame) -> bool` dice si está desbloqueado y `draw(view)` pinta la interfaz del Paso 9. Sirve para quien quiera meter el desbloqueo dentro de otro bucle.
  - **`run_unlock(grabber, window, code, log_path) -> bool`** es el bucle bloqueante que usa `main.py`. Al empezar da 2 s para sacar la mano ("Saca la mano del recuadro (2)") y aprende el fondo. Luego espera el código y, al desbloquear, deja "DESBLOQUEADO" 1,5 s en pantalla antes de devolver `True`. Muestra siempre los **FPS**, que el vídeo exige. Teclas: `f` (fondo nuevo), `r` (bloquear y empezar de cero), `q` (salir).
- `lse_auth/__init__.py` exporta `SecurityBlock` y `run_unlock`. El bloque de seguridad no importa nada del tracker.
- `lse_auth/camera.py`: `FrameGrabber` pasa aquí desde el preview, para que lo compartan `main.py` y el preview.
- `main.py` es el punto de entrada:
  ```
  python main.py                 # H-O-L-A y después el tracker
  python main.py --log           # además guarda cada evento del desbloqueo (Paso 11)
  python main.py --code HO       # código más corto para probar rápido
  ```

### Registro para el Paso 11
Con `--log`, cada evento del decodificador se añade a `pasos/lse/pruebas/sesion_<fecha>.csv` con las columnas `wall_time, t, event, letter, progress`. Los eventos son `correct`, `wrong`, `restart`, `timeout`, `unlocked` y `reset`. Con eso se calculan los intentos, los desbloqueos, los fallos y el tiempo hasta desbloquear sin apuntar nada a mano.

### Pruebas
- `python -m pytest tests/test_security.py`: 4 tests con fotos reales del dataset (fondo `bg_06`, A y una mano abierta) y un código de una letra, `A`, sin cámara.
  - La A desbloquea y queda registrada en el CSV.
  - La mano abierta no desbloquea.
  - Se dibuja en todas las fases.
  - `lock()` vuelve a bloquear.
- Simulación de `run_unlock` con una cámara falsa: cuenta atrás → fondo → A → DESBLOQUEADO → devuelve `True` a los 5,5 s (2 s de margen + 1 s de fondo + 0,5 s de confirmación + 1,5 s de cartel), a ~30–40 FPS.
- Falta probarlo con la cámara real y engancharlo al tracker cuando esté.
