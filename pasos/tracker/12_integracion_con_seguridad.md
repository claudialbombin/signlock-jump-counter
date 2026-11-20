# Paso 12 — Integración con el bloque de seguridad (desbloqueo LSE)

## Rama
`feature/rope-jump-counter` → se fusiona en `feature/integration`

## Descripción
Según el diagrama de bloques del guion, el tracker (tu bloque) solo debe arrancar cuando el bloque de seguridad ha dado el OK. El bloque de seguridad (rama `feature/sign-language-auth`, desbloqueo deletreando H-O-L-A en LSE) ya tiene pensada una interfaz para esto en su propio `pasos/lse/10_integracion_con_tracker.md` — no la dupliques ni inventes otra desde cero, coordínate con esa persona antes de dar esto por cerrado.

## Cómo hacerlo
1. Revisar `lse_auth/__init__.py` y el `pasos/lse/10_integracion_con_tracker.md` de la rama `feature/sign-language-auth` (están pensando en algo del tipo `lse_auth.run_security_block(cap) -> bool`, o una clase con `.is_unlocked` consultable en el bucle principal) — usar exactamente esa interfaz, sea cual sea la forma final que acordéis entre los dos.
2. En `jump_tracker/`, el contador de saltos (Pasos 6-11) debe quedar "dormido" (sin procesar frames, o procesándolos pero sin contar ni mostrar overlay) hasta que `is_unlocked` sea `True`. Decidir juntos si eso significa que el bloque de seguridad consume los frames hasta desbloquear y luego "pasa el testigo", o si ambos bloques corren en paralelo y el bucle principal simplemente no activa el tracker todavía.
3. Igual que pide el Paso 10 del otro bloque: `jump_tracker/` no debería necesitar saber nada de cómo funciona la detección de LSE por dentro — solo leer un booleano.
4. Probar el enganche conjunto en una rama de integración local (o directamente en `feature/integration`) antes de dar por cerrados los dos bloques por separado.

## Qué necesita estar hecho antes
Pasos 1-11 de este documento (tracker + contador funcionando de forma aislada, con su propio `demo_standalone.py`) y que el bloque de seguridad tenga ya su interfaz pública decidida (su Paso 10).

## Entregable del paso
Punto de entrada único, p. ej. `jump_tracker.run(cap, is_unlocked_fn)` o clase equivalente, documentado con docstring y ejemplo de uso, más confirmación escrita (issue o mensaje al equipo) del contrato acordado con la persona del bloque de seguridad.
