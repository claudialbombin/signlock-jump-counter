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
