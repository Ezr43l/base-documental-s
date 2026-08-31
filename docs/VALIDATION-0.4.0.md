# Validación local de RTFM 0.4.0

Fecha: 2026-08-30.

> Evidencia histórica supersedida por
> [`VALIDATION-0.4.1.md`](VALIDATION-0.4.1.md). Los bloqueos funcionales y de
> licencia enumerados aquí describen el estado de 0.4.0 y no el candidato actual.

Esta validación se ha ejecutado sobre el árbol privado de desarrollo. No supone una
publicación ni sustituye las puertas pendientes de la primera release pública.

## Resultado comprobado

| Comprobación | Resultado |
| --- | --- |
| Versión en código, paquete web, Compose y plantilla | `0.4.0` |
| Build local `linux/arm64` | correcto |
| Build cruzado `linux/amd64` | correcto |
| Pruebas obligatorias embebidas en cada build | 47/47 |
| TypeScript y frontend de producción | correctos |
| Usuario final de ambas imágenes | `10001:10001` |
| Fuente OCI prevista | `Ezr43l/base-documental-s` |
| Plantilla Unraid | XML válido y sin marcadores de sustitución |
| Docker Compose | configuración válida |
| Gitleaks 8.30.1 sobre el árbol actual | sin secretos detectados |
| `npm audit --omit=dev` | 0 vulnerabilidades conocidas |
| `pip-audit` sobre dependencias exactas | 0 vulnerabilidades conocidas |
| Auditoría de nombres, nodos e IP del entorno original | sin coincidencias en el árbol actual |

La prueba de arranque limpio confirmó además:

- salud y versión `0.4.0`;
- estado público mínimo y estado detallado protegido con `401` antes del login;
- creación inicial de la cuenta propietaria;
- creación de una biblioteca y conservación tras reiniciar el contenedor;
- sesión firmada válida tras el reinicio;
- filesystem de sólo lectura y proceso ejecutado como UID/GID `10001:10001`.

Los contenedores y volúmenes efímeros de esa prueba se eliminaron al finalizar.

## Bloqueos que tenía esta candidata histórica

- elegir la licencia, añadir `LICENSE` y configurar `LICENSE_SPDX`; `NOASSERTION` es sólo la
  declaración OCI honesta mientras no exista una decisión;
- decidir el nombre público definitivo entre `base-documental-s` y un renombrado previo del
  repositorio privado a `rtfm`, que produciría `rtfm-s`;
- completar permisos por biblioteca o aprobar expresamente que la versión mantenga roles
  globales;
- validar HTTPS, proxy de confianza, cookie segura, backup y restauración en un host real;
- completar un laboratorio HA multinodo con VIP, réplica, conflictos, tombstones, vault,
  failover, nodo atrasado, actualización y rollback;
- exportar un árbol con historial nuevo, repetir los escaneos y probar las URLs y la imagen
  pública desde una máquina limpia.

Por tanto, `0.4.0` quedó como candidata experimental y no se publica. La corrección
`0.4.1` es la única versión promovible de esta línea.
