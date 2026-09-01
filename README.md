# RTFM

**RTFM (Read The Fucking Manual)** es una aplicación privada para organizar y conservar
documentación técnica, procedimientos, diagramas y conocimiento operativo. Cada instancia
incluye la interfaz, la API, almacenamiento documental, auditoría, historial Git y réplica.

La estructura pertenece al usuario: puede crear cualquier número de bibliotecas y árboles de
categorías, sin nombres ni profundidad impuestos por la aplicación. Los documentos admiten
Markdown, Mermaid, imágenes privadas, etiquetas, favoritos, archivado y eliminación con vault
y tombstone.

La versión `0.x` es experimental y no debe publicarse fuera de una red de confianza sin HTTPS
y una revisión específica de la instalación.

El desarrollo canónico continúa en un repositorio privado no exportable. Las versiones que
superan todas las puertas de publicación se distribuyen, sin el historial privado, en
`Ezr43l/base-documental-s`; el sufijo `-s` significa *shared*. La versión de aplicación es
idéntica en ambos repositorios.

## Modos de instalación

RTFM funciona de dos formas:

- **un solo servidor**: `ROLE_MODE=active`, sin IP flotante ni réplica;
- **alta disponibilidad**: una instancia por nodo, `ROLE_MODE=auto`, una IP reclamada a
  Keepalived y una lista configurable de pares.

En alta disponibilidad, solo el nodo que posee la VIP acepta mutaciones. Los pasivos sirven
estado, reciben réplicas y enlazan a la dirección flotante. Si el rol no se puede verificar,
RTFM usa `unknown` y bloquea escrituras.

```text
                       IP flotante
                            │
              ┌─────────────┴─────────────┐
              │                           │
         nodo activo                 nodos pasivos
      interfaz + escritor          estado + réplicas
              │                           │
              └──── réplica lógica ──────┘
```

## Conector autenticado de Keepalived

Al arrancar, cada nodo envía la misma reclamación idempotente:

```http
POST /api/claims
Authorization: Bearer fip_…
Idempotency-Key: provision:rtfm:identificador-de-instalacion
Content-Type: application/json
```

```json
{
  "servicio": "rtfm",
  "descripcion": "RTFM",
  "puertos": [7400],
  "chequeo": {"puerto": 7400, "ruta": "/api/health"}
}
```

Keepalived devuelve la VIP asignada. Todos los nodos comparten el nombre de servicio, la clave
de idempotencia y la credencial, por lo que obtienen la misma dirección sin consumir varias.
RTFM confirma periódicamente la reclamación y muestra su estado en **Ajustes → Configuración**.

La credencial necesita el scope `claims:write`. Debe crearse una clave distinta para cada
instalación o entorno y guardarse como secreto. El conector usa `Authorization: Bearer`; no
incluye la clave en respuestas, errores ni auditoría.

Una parada individual **no libera** la reclamación porque las demás réplicas siguen usándola.
Al retirar una instalación completa, la reclamación se libera de forma explícita en
Keepalived mediante `DELETE /api/claims/{Idempotency-Key}`.

`http://127.0.0.1:6060` está permitido porque el Bearer no abandona el servidor. HTTP hacia
otro host se bloquea salvo que se active `KEEPALIVED_ALLOW_INSECURE_HTTP=true`; para redes no
confiables se debe usar HTTPS y, si procede, `KEEPALIVED_CA_FILE`.

`FLOATING_IP` continúa disponible como configuración manual o recuperación. Si no se define
`FLOATING_URL`, RTFM la construye con `PUBLIC_SCHEME`, la VIP y `PORT`.

## Instalación con Docker Compose

1. Copiar [`.env.example`](.env.example) a `.env`.
2. Generar valores distintos y aleatorios para `APP_TOKEN`, `SESSION_SECRET` y
   `REPLICATION_TOKEN`. Este último sólo es necesario con varios nodos.
3. Pegar en `KEEPALIVED_API_KEY` la clave creada para esta instalación.
4. Configurar `NODE_NAME`, `PEERS` y una `KEEPALIVED_CLAIM_ID` diferente por entorno.
5. Construir y arrancar:

   ```bash
   docker compose up --build -d
   ```

Compose usa red `host`, necesaria para que el modo automático observe la VIP del servidor.
Para una instalación aislada, usar `ROLE_MODE=active`; `KEEPALIVED_API_URL` y
`KEEPALIVED_API_KEY` pueden quedar vacíos.

La imagen se ejecuta como UID/GID `10001`. Los volúmenes Docker nuevos heredan los permisos
correctos; un directorio enlazado desde el host debe permitir escritura a ese usuario antes
del arranque. Los cuatro secretos admiten alternativamente `*_FILE`; Compose monta
`RTFM_SECRETS_PATH` como `/run/secrets` sin incluirlo en Git. Cada secreto debe ser un fichero
regular de hasta 64 KiB y un único enlace: en Unraid se recomienda propietario `10001:10001`
y modo `0400` o `0600`; también se admiten los secretos Docker root-owned de solo lectura.

Tras crear la cuenta propietaria y comprobar que está disponible en todos los nodos, vacía
`APP_TOKEN` para desactivar el Bearer heredado. Conserva `SESSION_SECRET`: cambiarlo sin un
procedimiento de rotación invalida sesiones, tokens API y secretos TOTP cifrados.

Si un reverse proxy termina TLS, configura `PUBLIC_SCHEME=https` y
`SESSION_COOKIE_SECURE=true`. `FORWARDED_ALLOW_IPS` debe contener únicamente las IPs o redes
desde las que el proxy conecta realmente con RTFM; su valor seguro predeterminado es
`127.0.0.1`. Nunca uses `*`: permitiría que cualquier origen falsificara
`X-Forwarded-For` y debilitara el limitador de login por cliente.

## Instalación en Unraid

El procedimiento completo, incluidos creación de ficheros, permisos, bootstrap, retirada de
`APP_TOKEN`, migración segura de un volumen previo a UID/GID `10001`, rollback y
verificaciones de `docker inspect`, está en
[`docs/UNRAID-INSTALLATION.md`](docs/UNRAID-INSTALLATION.md).

La plantilla preparada es [`unraid/my-RTFM.xml`](unraid/my-RTFM.xml). No contiene marcadores
ni valores de la infraestructura original. Una plantilla Unraid no construye la imagen:
descarga exactamente `ghcr.io/ezr43l/base-documental-s:0.4.4`. Compose conserva la ruta de
construcción local desde código para validar una copia nueva o trabajar antes de publicar el
artefacto.

La plantilla:

- instala el contenedor como `RTFM` en red `host`;
- guarda los datos nuevos en `/mnt/user/appdata/rtfm/data`;
- monta los cuatro secretos desde ficheros del host, individualmente y en modo `ro`, y sólo
  pasa sus rutas internas mediante `*_FILE`;
- permite configurar cualquier topología, nodo, URL, CA, puerto y política sin editar la
  imagen;
- conserva `FLOATING_IP` como fallback opcional.

Las rutas host predeterminadas bajo `/mnt/user/appdata/rtfm/secrets/` son genéricas y
editables. Los ficheros deben pertenecer a `10001:10001` y usar modo `0400`; los secretos
opcionales existen vacíos. Una instalación nueva usa `app-token` sólo para crear la primera
cuenta y lo vacía en todos los nodos después de cambiar la contraseña y verificar la réplica.
La plantilla no define campos directos para `APP_TOKEN`, `SESSION_SECRET`,
`REPLICATION_TOKEN` ni `KEEPALIVED_API_KEY`, por lo que sus valores no aparecen en
`docker inspect`.

Para actualizar desde “Base Documental”, se debe conservar el montaje de datos anterior o
mover su contenido de forma controlada antes de cambiarlo. Crear el nuevo directorio vacío
parecería una pérdida de datos aunque el original siguiera intacto.

El cambio de `<Name>` hace que Unraid pueda tratar RTFM como otro contenedor. Detén primero
`Base-Documental`, instala `RTFM` reutilizando exactamente su montaje persistente y verifica
contenido, cuentas y Git antes de retirar la definición antigua. No ejecutes ambos a la vez:
usan el mismo puerto y no deben escribir sobre el mismo volumen simultáneamente.

Si la VIP antigua fue creada manualmente en Keepalived, también hay que migrar su registro
antes de activar el conector: liberar la asignación antigua, apartar esa misma dirección para
el servicio `rtfm` y arrancar primero un solo nodo con la nueva reclamación. Una entrada
manual no contiene `Idempotency-Key` y la API no la adopta implícitamente. Arrancar sin este
paso podría tomar otra dirección libre; después de confirmar que RTFM recibió la VIP esperada
se pueden actualizar las demás réplicas.

## Variables principales

El runtime mantiene las cuatro variables directas para migraciones heredadas, pero Unraid
usa exclusivamente sus equivalentes `*_FILE`. Nunca se deben configurar ambos mecanismos
para el mismo secreto.

| Variable | Función | Predeterminado |
|---|---|---|
| `RTFM_LICENSE_SPDX` | licencia declarada en los metadatos OCI | `Apache-2.0` |
| `DATA_DIR` | almacenamiento persistente | `/data` |
| `PORT` | interfaz y API | `7400` |
| `NODE_NAME` | identidad única del nodo | `local` |
| `ROLE_MODE` | `auto`, `active`, `passive` o `unknown` | `auto` |
| `KEEPALIVED_API_URL` | base del panel que asigna la VIP | vacío |
| `KEEPALIVED_API_KEY` | Bearer `fip_…` con `claims:write` | vacío |
| `KEEPALIVED_SERVICE` | nombre de la reclamación | `rtfm` |
| `KEEPALIVED_DESCRIPTION` | texto visible en Keepalived | `RTFM` |
| `KEEPALIVED_CLAIM_ID` | idempotencia única compartida por la instalación | vacío |
| `KEEPALIVED_HEALTH_PATH` | ruta local comprobada | `/api/health` |
| `KEEPALIVED_SERVICE_PORTS` | puertos adicionales, separados por comas | vacío |
| `KEEPALIVED_TIMEOUT_SECONDS` | espera por petición, entre 1 y 30 s | `5` |
| `KEEPALIVED_ALLOW_INSECURE_HTTP` | acepta HTTP hacia otro host | `false` |
| `KEEPALIVED_CA_FILE` | CA privada PEM para HTTPS | vacío |
| `FLOATING_IP` | VIP manual o de recuperación | vacío |
| `FLOATING_URL` | URL canónica opcional | derivada de la VIP |
| `PUBLIC_SCHEME` | esquema para la URL derivada | `http` |
| `FORWARDED_ALLOW_IPS` | orígenes de reverse proxy autorizados por Uvicorn | `127.0.0.1` |
| `PEERS` | pares `nombre=url`, separados por comas | vacío |
| `APP_TOKEN` | credencial de alta inicial y API heredada | vacío |
| `SESSION_SECRET` | firma de sesión y cifrado de cuenta | `APP_TOKEN` sólo por compatibilidad heredada |
| `*_FILE` | ruta de fichero para cada uno de los cuatro secretos; vía recomendada | vacío |
| `SESSION_HOURS` | duración de sesión | `12` |
| `SESSION_COOKIE_SECURE` | cookie exclusiva de HTTPS | `false` |
| `LOGIN_MAX_ATTEMPTS` | fallos antes del bloqueo temporal | `5` |
| `LOGIN_WINDOW_SECONDS` | ventana del límite de login | `300` |
| `PASSWORD_MIN_LENGTH` | longitud mínima de contraseña | `12` |
| `TOTP_ISSUER` | nombre mostrado por la aplicación 2FA | `RTFM` |
| `REPLICATION_TOKEN` | credencial entre nodos | vacío |
| `REPLICATION_ALLOW_INSECURE_HTTP` | acepta réplica HTTP remota | `false` |
| `REPLICATION_CA_FILE` | CA privada para pares HTTPS | vacío |
| `MAX_REPLICATION_MB` | límite por bundle | `512` |
| `RETENTION_DAYS` | retención del vault | `90` |
| `SYNC_INTERVAL_SECONDS` | reclamación y réplica periódicas | `300` |
| `MAX_IMAGE_SIZE_MB` | límite por imagen privada | `10` |
| `GIT_ENABLED` | proyección Git documental | `false` |
| `GIT_REPO_DIR` | repositorio persistente | `/data/git` |
| `GIT_AUTHOR_NAME` | identidad técnica de commits | `RTFM` |
| `GIT_AUTHOR_EMAIL` | correo técnico de commits | `rtfm@localhost` |

## API de RTFM

La API de producto usa `/api/v1` y ofrece sesiones personales, usuarios, clientes API,
bibliotecas, categorías, documentos, imágenes, favoritos, búsqueda, registros, estado y
réplica. Los clientes registrados presentan tokens `rtfm_…`; las credenciales históricas
`bdapi_…` siguen siendo válidas hasta que se roten.

`/api/v1/public-status`, `/api/version`, `/api/health` y el alias `/api/status` ofrecen sólo
el estado mínimo necesario antes del login. `/api/v1/status` exige identidad y contiene la
topología y métricas completas. `/api/internal/*` exige el token de réplica. `/api/health`
distingue `ok`, `degraded` y `unknown`; devuelve `503` cuando no puede establecer un rol seguro.

## Permisos por biblioteca

Cada persona y cliente API conserva un rol global (`reader`, `operator` o `full_control`) que
actúa como techo. Una biblioteca puede permanecer abierta para todas las identidades
autenticadas o restringirse mediante concesiones individuales. Una concesión nunca eleva el
rol global: un lector global seguirá siendo lector aunque se le asigne control total local.

Las bibliotecas creadas antes de `0.4.1` se interpretan como abiertas para que la actualización
no bloquee instalaciones existentes. Las cuentas humanas con control total conservan acceso de
recuperación a todas las bibliotecas. Sólo esas cuentas pueden cambiar la política, tras
reconfirmar contraseña y 2FA cuando esté habilitado. Los clientes API y el token heredado no
disponen de ese bypass.

La autorización se aplica en la API a catálogos, documentos, imágenes, favoritos, búsqueda,
etiquetas, archivado, papelera y métricas. Los registros completos se reservan a administradores
humanos porque pueden contener contexto transversal de varias bibliotecas.

## Persistencia y seguridad

Los documentos son Markdown versionable y los metadatos se escriben de forma atómica. Cada
operación conserva actor, fecha UTC, nodo, identificador, revisión y resultado. Las
eliminaciones crean tombstone y vault; archivar y eliminar siguen siendo estados distintos.

Las contraseñas usan `scrypt`, TOTP se cifra con una clave derivada de `SESSION_SECRET`, las
cookies son `HttpOnly` y `SameSite=Strict`, y las mutaciones web exigen CSRF. Los tokens API,
claves de Keepalived, contraseñas y secretos de réplica no deben entrar en Git, documentos,
capturas ni registros.

El login limita intentos por usuario y origen. La réplica rechaza HTTP remoto salvo opt-in,
acota petición y respuesta, verifica esquema y exige que el nodo emisor esté declarado en
`PEERS`. Para una red no confiable, los pares deben usar HTTPS.

## Verificación

```bash
./build-image.sh
```

El build ejecuta las pruebas Python, el typecheck TypeScript y el build de producción antes
de producir la imagen. Para publicar multi-arquitectura se usa explícitamente
`PUBLISH=true IMAGE_REPOSITORY=ghcr.io/ezr43l/base-documental-s ./build-image.sh` únicamente
después de aprobar la release.

La documentación técnica ampliada vive en [`docs/`](docs/). El procedimiento para producir
el futuro árbol público sin historial ni contenido ignorado está en
[`docs/DEVELOPMENT-ENVIRONMENT.md`](docs/DEVELOPMENT-ENVIRONMENT.md).

## Licencia

RTFM se distribuye bajo [Apache License 2.0](LICENSE). La licencia cubre el código y la
documentación del repositorio; las dependencias conservan sus licencias respectivas. El
inventario, los textos incluidos en la imagen y la disponibilidad de fuentes se describen en
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

Cada release pública incorpora dos SBOM SPDX, inventarios y textos de licencia npm/Python,
así como las fuentes Alpine correspondientes verificadas para `linux/amd64` y `linux/arm64`.
La publicación falla de forma cerrada si falta cualquiera de esos artefactos.
