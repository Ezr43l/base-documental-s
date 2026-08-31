# Validación local de RTFM 0.4.1

Fecha: 2026-08-30.

Esta validación se ha ejecutado sobre el árbol privado de desarrollo. No publica artefactos ni
autoriza por sí sola la promoción a `Ezr43l/base-documental-s`.

## Resultado comprobado

| Comprobación | Resultado |
| --- | --- |
| Versión en código, paquete web, Compose y plantilla | `0.4.1` |
| Licencia de código y documentación | `Apache-2.0` |
| Pruebas unitarias | 50/50 |
| TypeScript y frontend de producción | correctos |
| Build local de la imagen completa `linux/arm64` | correcto; 50/50 pruebas embebidas |
| Build local de la imagen completa `linux/amd64` | correcto; 50/50 pruebas embebidas |
| Base de ejecución | Alpine 3.24, fijada por digest |
| Trivy 0.74.0, HIGH/CRITICAL corregidas y sin corregir | 0 en arm64; 0 en amd64 |
| Auditoría Python (`pip-audit`) y web (`npm audit --omit=dev`) | 0 vulnerabilidades conocidas |
| Escaneo de secretos con Gitleaks 8.30.1 | sin hallazgos |
| Lock Python regenerado en contenedor contra PyPI | idéntico byte a byte en AMD64 |
| Avisos npm/Python y textos GPL incluidos | idénticos en AMD64 y ARM64; legibles por UID 10001 |
| Fuentes Alpine recíprocas | recetas, parches y distfiles verificados; archive reproducible |
| Recorrido integral de roles globales y permisos por biblioteca | correcto |
| Suite de seis recorridos smoke aislados y limpieza etiquetada | correcta; 0 recursos residuales |
| Ciclo documental, auditoría, editor, imagen privada y Mermaid | correcto |
| Orden manual/alfabético y favoritos | correcto |
| Perfil, cambio de contraseña y ciclo TOTP | correcto |
| Actualización real con volumen `0.4.0` → `0.4.1` | datos y acceso conservados |
| Laboratorio físico de tres nodos Unraid `amd64` | aprobado; actualización pasivo/pasivo/activo |
| Backup frío y rollback real `0.4.1` → `0.4.0` → `0.4.1` | contenido, permisos y acceso conservados |
| Réplica, VIP, escritura y rechazo directo al pasivo | correcto; `201` vía VIP y `409` en pasivo |
| Tombstone y vault | idénticos en 3/3 nodos |
| Failover, rejoin y preemption | 12,963 s; 3,549 s; 58,874 s |
| Plantillas físicas persistidas | XML válido, equivalentes al runtime y sin reinicio |
| HTTPS y proxy de confianza | TLS/CA/HSTS/cookie segura y clientes reenviados aislados |
| Conflicto concurrente y nodo atrasado | convergencia determinista 3/3; local en ambas arquitecturas y host físico AMD64 |
| Fuente OCI prevista | `Ezr43l/base-documental-s` |

El recorrido de permisos verificó con personas, clientes API y la credencial heredada:

- biblioteca abierta compatible y biblioteca restringida con concesiones individuales;
- rol global como techo, sin elevación de lector a operador;
- ocultación mediante `404` de bibliotecas y documentos no autorizados;
- comprobación de biblioteca de origen y destino al mover contenido;
- aislamiento de categorías, imágenes privadas, favoritos, búsqueda y etiquetas;
- métricas filtradas y actividad transversal omitida para no administradores;
- registros y exportaciones reservados a cuentas humanas con control total;
- política administrativa protegida por CSRF, contraseña y 2FA cuando corresponde;
- política versionada, auditada y replicada dentro del esquema HA 6.

La prueba de actualización creó una biblioteca y un documento con la imagen `0.4.0`, sustituyó
el contenedor por `0.4.1` conservando exactamente el volumen y confirmó contenido, identidad y
rol efectivo. La ausencia histórica de `access` se interpretó como `open` sin reescritura
destructiva.

La imagen Debian inicialmente ensayada quedó descartada al actualizar la base de datos de
Trivy: Git arrastraba paquetes Perl con hallazgos HIGH/CRITICAL todavía sin paquete corregido.
La imagen final usa Alpine 3.24, conserva Git e `iproute2`, ejecuta como `10001:10001` y no
presenta hallazgos HIGH/CRITICAL en ninguna de las dos arquitecturas. La CI rechaza también
vulnerabilidades sin corrección; no usa `--ignore-unfixed`.

La validación física posterior se documenta, sin identificadores de infraestructura ni
credenciales, en [`PHYSICAL-VALIDATION-0.4.1.md`](PHYSICAL-VALIDATION-0.4.1.md). Verificó tres
nodos `amd64`, migración completa a UID/GID 10001, tres secretos activos mediante ficheros
`0400`, retirada de `APP_TOKEN`, backups root-only, rollback real, réplica autenticada,
tombstones, vault, conmutación HA, TLS terminado en proxy y conflicto/reincorporación. Las
huellas completas del candidato permanecen únicamente en los manifiestos privados de
validación.

## Puertas que siguen abiertas

- configurar `LICENSE_SPDX=Apache-2.0` en el futuro repositorio público;
- crear el repositorio público únicamente cuando se apruebe la promoción;
- probar las URLs y la imagen pública desde una máquina limpia después de publicarlas.

`0.4.1` resuelve el bloqueo funcional de permisos por biblioteca y queda congelada como
versión correctiva publicable de la línea experimental `0.x`. No se declara estable ni apta
para producción por pertenecer a una serie experimental. Esta evidencia
local tampoco afirma que el repositorio, el tag o la imagen públicos existan: esos hechos se
registran únicamente después de superar sus puertas externas.
