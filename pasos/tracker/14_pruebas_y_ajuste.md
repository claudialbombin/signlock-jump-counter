# Paso 14 — Pruebas, ajuste de umbrales y medición de precisión

## Rama
`feature/rope-jump-counter`

## Descripción
Medir qué tan fiable es el contador en condiciones reales (no solo con los vídeos de referencia del Paso 2) y dejar constancia de ello — el informe pide justificar el método y sus resultados.

## Cómo hacerlo
1. Probar el sistema completo (Pasos 3-11 encadenados) en vivo, variando: ritmo de salto (lento/rápido), distancia a la cámara, iluminación, y si es posible otra persona saltando (para comprobar que los umbrales de color/altura no están sobreajustados a tu propio zapato y tu propia altura de salto).
2. Comparar el conteo automático contra el conteo real anotado a mano (igual que en el Paso 9, pero ahora en vivo y con más variedad de condiciones) en una tabla: nº de saltos reales vs. contados, falsos positivos (saltos contados de más) y falsos negativos (saltos no detectados).
3. Volver a los Pasos 3 (umbral de color) y 9/10 (umbral de altura y tiempo mínimo) si los resultados son pobres, y repetir la medición.
4. Anotar casos límite conocidos (zapato parcialmente tapado por el pantalón, saltos muy pequeños que no superan `H_MIN`, confusión con otra zona oscura del encuadre) — alimenta la sección "Futuros Desarrollos" del informe.

## Qué necesita estar hecho antes
Pasos 3 a 11 integrados y funcionando de punta a punta.

## Entregable del paso
Tabla de resultados (`.md` o `.csv` en `pasos/tracker/`) con las métricas de la prueba, y lista corta de casos límite/limitaciones conocidas.
