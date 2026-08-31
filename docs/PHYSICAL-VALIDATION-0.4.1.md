# Validación física de RTFM 0.4.1

Fecha de cierre: 2026-08-31.

Este documento registra una validación física sanitizada sobre tres hosts Unraid `linux/amd64`.
Los nodos se identifican únicamente como `node-1`, `node-2` y `node-3`; no se incluyen nombres
reales, direcciones, usuarios, rutas privadas ni valores de credenciales. Las huellas se
truncan deliberadamente y no sustituyen a los manifiestos SHA-256 completos, conservados con
acceso exclusivo de `root` en cada host.

La prueba valida un snapshot privado aprobado como **prerelease 0.4.1**. Su OID, nombres
temporales y huellas completas permanecen únicamente en la evidencia root-only; este documento
público no crea tags, releases ni imágenes y no cambia `VERSION`.

## Candidato exacto

| Elemento | Evidencia sanitizada |
| --- | --- |
| Etiqueta temporal | única, efímera y no publicable |
| Archive Docker `amd64` | SHA-256 completo verificado en la evidencia privada |
| ID de imagen en Docker clásico | comparado de extremo a extremo sin publicarlo |
| Arquitectura y usuario | `linux/amd64`, `10001:10001` |
| Versión servida | `0.4.1` |
| Topología | red `host`, una VIP, un activo y dos pasivos |

El primer artefacto ensayado era un índice OCI con attestations. El almacén Docker clásico del
host reconocía el manifiesto de ejecución, pero no dejaba una etiqueta utilizable. Se detuvo la
puerta antes de tocar el servicio y se generó un archive `type=docker` sin provenance adicional,
con el mismo manifiesto y config de ejecución. Sólo ese segundo archive superó la comprobación
de etiqueta, ID, arquitectura, usuario, capas y labels antes del despliegue.

## Prepuerta y backups

Antes de cada parada se exigió exactamente un nodo activo, salud `ok`, versión esperada y rol
del objetivo. El orden de actualización fue pasivo, pasivo y, por último, el activo. El activo
se determinó de nuevo en cada frontera; no se supuso que fuese siempre el mismo host.

Cada nodo conserva un backup frío independiente y de acceso exclusivo de `root` con:

- `docker inspect` exacto y copia sanitizada;
- plantilla Unraid exacta y copia sanitizada;
- archive de la imagen anterior y prueba de lectura del tar;
- tar de `/data` con propietarios numéricos, modos, ACL y xattrs;
- inventario, ACL, hashes lógicos y manifiestos SHA-256;
- secretos de rollback separados y protegidos;
- ausencia comprobada de symlinks, sockets, dispositivos, pipes y montajes anidados.

En el antiguo activo se verificaron por SHA-256 tanto el snapshot frío de datos como el archive
de la imagen anterior. Un manifiesto privado agrupa todas las evidencias root-only. Los
contenedores anteriores quedaron conservados, detenidos y renombrados; no se eliminó ningún
backup ni candidato fallido.

## Migración de permisos y secretos

El árbol persistente de 0.4.0 pertenecía a `root:root`. Para 0.4.1 se migró íntegramente a
`10001:10001` y se verificó que no quedara ninguna entrada con otro UID/GID. El rollback
deliberado restauró tanto el contenido lógico como el propietario original antes de arrancar
0.4.0.

La instalación ya tenía una cuenta propietaria replicada y dos clientes API modernos válidos.
Por ello se retiró `APP_TOKEN`: el valor anterior recibe `401` y no aparece en el entorno del
contenedor. Los tres secretos que siguen activos se almacenan así:

- directorio `0500`, propietario `10001:10001`;
- tres ficheros `0400`, propietario `10001:10001`;
- un único bind mount de `/run/secrets` en modo `ro`;
- `SESSION_SECRET_FILE`, `REPLICATION_TOKEN_FILE` y `KEEPALIVED_API_KEY_FILE`;
- ningún valor secreto directo en `docker inspect` ni en la plantilla viva.

Los peers de esta instalación usan HTTP dentro de una LAN considerada confiable. Se estableció
de forma explícita `REPLICATION_ALLOW_INSECURE_HTTP=true`. El conector Keepalived usa localhost,
por lo que `KEEPALIVED_ALLOW_INSECURE_HTTP=false` permanece correcto. Esta excepción no autoriza
HTTP en redes no confiables; allí los peers deben usar HTTPS.

## Runtime aprobado

Los tres contenedores quedaron con el mismo contrato:

- mismo ID de imagen verificado de forma privada y proceso `10001:10001`;
- red `host`, reinicio `unless-stopped` e `init`;
- rootfs de sólo lectura y `/tmp` como `tmpfs` de 128 MiB;
- `cap-drop=ALL`, `no-new-privileges` y límite de 256 procesos;
- `/data` RW y `/run/secrets` RO;
- sin modo privilegiado ni puertos publicados adicionales;
- cero errores de permisos, rootfs o aplicación en los logs del periodo validado.

Las plantillas vivas se actualizaron después del laboratorio, sin recrear ni reiniciar los
contenedores. Cada cambio se hizo mediante fichero temporal y reemplazo atómico, con XML
validado por dos parsers, backup exacto root-only y comparación contra el `inspect` en ejecución.
Las huellas completas se compararon contra cada fichero vivo y se conservaron en privado:

| Nodo sanitizado | Plantilla comprobada | Reinicio |
| --- | --- | --- |
| `node-1` | SHA-256 privado válido | no |
| `node-2` | SHA-256 privado válido | no |
| `node-3` | SHA-256 privado válido | no |

La plantilla física apunta intencionadamente a la etiqueta temporal ya cargada en cada host.
La plantilla pública seguirá usando la referencia pública aprobada cuando exista; no debe
copiar esta etiqueta temporal.

## Actualización y rollback

`node-1` actuó como canario. Se desplegó 0.4.1, se validó, se ejecutó un rollback real completo
a 0.4.0 desde su tar, se comprobó contenido y propietario `root:root`, y se reimplantó 0.4.1
desde una restauración limpia.

En `node-2`, una primera creación del candidato no superó una puerta de portabilidad del host.
El mecanismo recuperó 0.4.0 sano y los propietarios originales; el candidato fallido quedó
conservado. El reintento eliminó la dependencia de Python del host, usó Bash/JQ, creó un snapshot
nuevo como autoridad y terminó correctamente. La réplica entrante posterior se observó a los
144 segundos.

Para el antiguo activo se capturó metadata en caliente, se detuvo únicamente RTFM y se esperó
la conmutación antes de tocar `/data`. La primera conmutación completa tardó 37,005 segundos.
El nuevo 0.4.1 recibió una réplica real a los 19 segundos y, tras el intervalo configurado de
300 segundos, confirmó sincronización saliente con ambos peers a los 607/608 segundos. El
rollback quedó preparado con snapshot propio, imagen, inspect y plantilla, pero no fue necesario
activarlo en este nodo.

## Permisos, escritura y HA

Se verificaron una cuenta propietaria activa, dos clientes API activos y dos bibliotecas
abiertas. Ambos clientes modernos tienen `full_control`, suficiente para crear, eliminar y
solicitar una sincronización manual.

La prueba funcional final produjo esta cronología:

| Operación | Resultado |
| --- | --- |
| Crear un documento único mediante la VIP | `201`, 298 ms |
| Replicar el documento a los dos peers | 3/3 nodos, 2,142 s |
| Intentar la misma clase de escritura directamente en un pasivo | `409`, sin persistencia |
| Eliminar mediante el activo | tombstone, 266 ms |
| Replicar eliminación y vault | 3/3 nodos, 2,016 s |
| Parar sólo RTFM en el activo | conmutación completa en 12,963 s |
| Reincorporar el nodo detenido | salud y rol válidos en 3,549 s |
| Recuperar la prioridad original | preemption completa en 58,874 s |
| Sincronización posterior a la reincorporación | dos peers, 1,846 s |

El artefacto sintético de prueba permanece deliberadamente sólo como tombstone y copia de
vault. En los tres nodos coinciden estado, reloj lógico, metadata, contenido del vault y
propietarios. La huella lógica completa y el número de ficheros permanecen en la evidencia
privada; las diferencias no funcionales se limitan a auditoría y estado regenerable.

El estado final es tres nodos `0.4.1` saludables, exactamente uno activo y dos pasivos. La VIP
responde desde el activo y dos clientes sintéticos leen el mismo conjunto esperado de
documentos y bibliotecas en la puerta previa al artefacto de tombstone; no se publican recuentos
del entorno validado.

## Puertas externas suplementarias

Después del laboratorio principal se repitió una auditoría de sólo lectura: 3/3 runtimes
seguían saludables y endurecidos, exactamente uno activo y dos pasivos, la VIP era única y no
había secretos directos en el entorno. Sobre un host físico `linux/amd64` se ejecutaron además
dos laboratorios efímeros, sin puertos publicados y sin montar datos del clúster vivo:

- un terminador TLS con CA efímera verificó nombre de servidor, TLS 1.2/1.3, HSTS, CSP,
  `X-Frame-Options`, `Cache-Control`, y una cookie `rtfm_session` con `Secure`, `HttpOnly` y
  `SameSite=Strict`; el proxy fue autorizado por su IP exacta y dos clientes reenviados
  conservaron contadores de login independientes;
- tres contenedores RTFM sembraron el mismo documento; `node-c` quedó detenido y atrasado,
  mientras `node-a` y `node-b` aceptaron escrituras simultáneas y divergentes en aislamiento.
  Tras volver a roles activo/pasivo y ejecutar dos ciclos autenticados, los tres convergieron
  byte a byte en contenido y versión al ganador de la tupla `(clock, timestamp, node)`.

Los mismos dos gates pasaron localmente con las imágenes `linux/amd64` y `linux/arm64`. Cada
ejecución eliminó sus contenedores, redes, volúmenes, PKI y credenciales sintéticas; el recuento
residual fue cero. El primer intento físico no llegó a la aplicación porque el directorio que
contenía los scripts públicos era `0700`; se corrigió a permisos de lectura para UID 10001 y se
repitió desde cero. No se relajaron permisos de datos ni secretos.

## Resultado y límites

La puerta física de actualización, permisos, backup, rollback, réplica, escritura, tombstone,
vault, failover, rejoin, preemption, HTTPS, proxy confiable y conflicto/reincorporación queda
**aprobada** para este candidato exacto.

Siguen fuera de alcance y, por tanto, abiertas:

- instalación desde repositorio e imagen públicos en una máquina limpia;
- validación en hardware físico `arm64`, no disponible en este entorno; la imagen y todos los
  gates equivalentes sí se ejecutaron bajo `linux/arm64` emulado por Docker Desktop;
- promoción, tag, release, SBOM y provenance públicos.

RTFM 0.4.1 continúa siendo prerelease de una serie experimental `0.x`; esta evidencia no la
declara apta para Internet ni autoriza su publicación.
