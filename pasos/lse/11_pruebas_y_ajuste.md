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
