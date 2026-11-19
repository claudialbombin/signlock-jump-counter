# Paso 6 — Clasificador por reglas (H / O / L / A / ninguna)

## Rama
`feature/sign-language-auth`

## Descripción
Con la tabla de valores por clase del Paso 5 delante, escribir un clasificador basado en reglas (si-entonces, sin machine learning) que convierta el vector de características en una etiqueta. Es deliberadamente simple e interpretable — encaja con el espíritu "visión clásica" del proyecto y es fácil de explicar y justificar en el informe.

## Cómo hacerlo
1. Mirar la tabla de valores reales del dataset (no solo la teoría del Paso 1) y fijar umbrales concretos, por ejemplo (ajustar con tus propios números):
   - Si `has_hole` → **O**.
   - Si no, y `n_defects == 0` y `solidity` alta → **A**.
   - Si no, y hay 1 defecto con ángulo grande (~80-100°) → **L**.
   - Si no, y hay 1 defecto con ángulo pequeño (<40°) y dedos paralelos → **H**.
   - Si nada encaja con suficiente margen → **ninguna/desconocida** (mejor no forzar una clasificación dudosa).
2. Implementarlo como una función pura `classify(features) -> str` fácil de testear unitariamente con los vectores del Paso 5.
3. Añadir una pequeña "zona muerta" (umbral con margen) alrededor de cada frontera de decisión para evitar que el sistema parpadee entre dos letras cuando el valor está justo en el límite.
4. Documentar en el propio código (comentario) la justificación de cada umbral — se reutiliza casi literal en el informe.

## Qué necesita estar hecho antes
Paso 5, y preferiblemente haber corrido `extract_features` sobre las ~15-20 imágenes por clase del Paso 2 para tener números reales, no solo intuición.

## Entregable del paso
Función `classify(features: dict) -> str` en `lse_auth/classifier.py`, con un pequeño test manual que recorre el dataset de referencia y muestra una matriz de confusión simple (aciertos por clase).
