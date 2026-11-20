# Paso 1 — Definición del objetivo: qué cuenta como "salto"

## Rama
`feature/rope-jump-counter`

## Descripción
Antes de escribir código, fijar con precisión qué va a contar el sistema. El guion pide un "Sistema Propuesto" de aplicación libre con un tracker que siga una zona de interés con una bounding box — aquí la zona de interés es un zapato (negro) y la aplicación es un contador de saltos (de comba o a la pata coja, a decidir).

Hay que decidir y documentar:
- **Qué zapato**: uno concreto (el pie dominante) o cualquiera de los dos que esté más centrado/visible. Empezar por uno solo simplifica mucho el Paso 4-5.
- **Qué trayectoria define un salto válido**: subida del centroide del zapato por encima de un umbral de altura (en píxeles o en mm si se usa la escala de la calibración) seguida de una bajada de vuelta cerca del suelo. No vale contar cualquier vibración de la imagen como salto.
- **Encuadre esperado**: cámara fija, usuario de cuerpo entero o solo de cintura para abajo, distancia aproximada a la cámara (afecta al tamaño en píxeles del zapato y por tanto a los umbrales de área del Paso 4).
- **Qué zapato NO cuenta**: calcetines, zapatillas de otro color, el pie descalzo — el sistema solo debe reaccionar a la silueta negra del zapato acordado.

## Cómo hacerlo
1. Grabar 2-3 vídeos cortos de prueba (cámara fija, tú saltando) para tener material real con el que decidir estos puntos, no solo teoría.
2. Medir aproximadamente cuántos píxeles sube el zapato en un salto normal, a la distancia de cámara que vais a usar — ese número orienta el umbral del Paso 9.
3. Escribir aquí mismo las decisiones tomadas (zapato, encuadre, criterio de salto válido) para que el resto de pasos no tengan que volver a discutirlo.

## Qué necesita estar hecho antes
Nada técnico; es el punto de partida, igual que el Paso 1 del bloque de seguridad (`pasos/lse/01_definicion_alfabeto_lse.md` en `feature/sign-language-auth`). Conviene tener ya aprobado por el profesor el planteamiento general del proyecto (seguridad por LSE + contador de saltos), como pide el guion.

## Entregable del paso
Este fichero ampliado con las decisiones concretas (zapato, encuadre, criterio de salto) + los 2-3 vídeos de prueba guardados en `pasos/tracker/videos_referencia/`.
