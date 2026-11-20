# Índice general — `pasos/`

Planes de trabajo del equipo, repartidos por bloque del sistema (ver diagrama de bloques del
guion del proyecto). Cada subcarpeta tiene su propio `00_indice.md` con el detalle paso a paso.

| Subcarpeta | Bloque | Rama de trabajo | Responsable |
|---|---|---|---|
| [`lse/`](lse/00_indice.md) | Sistema de seguridad — desbloqueo deletreando H-O-L-A en LSE | `feature/sign-language-auth` (y sub-ramas `feature/lse-00-setup`, `feature/lse-01-alphabet`, `feature/lse-02-dataset`...) | Claudia |
| [`tracker/`](tracker/00_indice.md) | Sistema propuesto — contador de saltos por tracking de un zapato negro | `feature/rope-jump-counter` | tu compañera |

Los dos bloques son independientes hasta la integración final en `feature/integration`
(ver el Paso 10 de `lse/` y el Paso 12 de `tracker/`, que son los puntos de contacto entre
ambos: la interfaz de desbloqueo y la reutilización de la cámara/calibración).
