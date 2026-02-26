
# Proyecto Hackaton

## La Idea
La idea es crear un juego de consola basado en el clásico buscaminas, pero con un 'twist'.

En vez de una cuadrícula e ir marcando las minas con el ratón, el jugador tendrá un avatar en el mapa, con visión limitada, y deberá usar un sistema de radar para localizar donde están las minas.

## Detalles
### Mapa
El mapa será una cuadrícula, el tamaño base será de 33x33, pero podrá variar según la dificultad elegida. El número de minas se calculará multiplicando el número de cuadrados totales (1089) por 0.05, de forma que cada cuadrado tiene una probabilidad del 5% de contener una mina (54 minas para 1089 cuadrados). Las minas se colocarán aleatoriamente por todo el mapa al empezar la partida, con la única excepción del cuadrado central (porque será el punto de aparición del jugador). 

### Gameplay

El jugador se podra mover por el mapa con las flechas del teclado. Y podrá marcar posibles minas en una cuadricula 9x9 alrededor suya, usando las teclas Q W E D C X Z A (cada una representando una posición alrededor del judador, si el jugador estuviera en la tecla S).

De forma similar al buscaminas original, todo cuadrado sin ninguna mina en un area de 9x9 alrededor suya al que el jugador tenga acceso directo, aparecerá de color blanco para el jugador