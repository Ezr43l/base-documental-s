# Instalación segura de RTFM en Unraid

Esta guía describe la instalación recomendada de RTFM `0.4.2` mediante la plantilla
`unraid/my-RTFM.xml`. Los secretos no se escriben en campos de tipo variable: se guardan en
ficheros del host y se montan en el contenedor como solo lectura. Por tanto, `docker inspect`
expone las rutas, pero no los valores de `APP_TOKEN`, `SESSION_SECRET`, `REPLICATION_TOKEN` ni
`KEEPALIVED_API_KEY`.

## Mapa de ficheros

| Contenido | Ruta host predeterminada | Ruta interna | Obligación del contenido |
|---|---|---|---|
| Credencial inicial | `/mnt/user/appdata/rtfm/secrets/app-token` | `/run/secrets/app-token` | Solo durante el bootstrap; vacío después |
| Secreto de sesiones | `/mnt/user/appdata/rtfm/secrets/session-secret` | `/run/secrets/session-secret` | Siempre, 32 caracteres o más |
| Token de réplica | `/mnt/user/appdata/rtfm/secrets/replication-token` | `/run/secrets/replication-token` | En HA; vacío en un solo nodo |
| Clave de Keepalived | `/mnt/user/appdata/rtfm/secrets/keepalived-api-key` | `/run/secrets/keepalived-api-key` | Con el conector; vacío en modo aislado |

Las rutas host son convenciones genéricas de Unraid y pueden cambiarse. Las cuatro rutas
internas son el contrato de la plantilla y no deben cambiarse salvo que también se modifique
su campo `*_FILE`. Los cuatro ficheros deben existir, aunque un secreto opcional quede vacío.

## 1. Decidir el modo antes de crear secretos

- En un solo servidor usa `ROLE_MODE=active`, deja `PEERS` vacío y deja vacíos
  `replication-token` y `keepalived-api-key`.
- En HA usa `ROLE_MODE=auto`; todos los nodos del mismo grupo comparten `session-secret`,
  `replication-token`, la clave de Keepalived y, solo mientras dure el alta, `app-token`.
- Una instalación que restaura datos con una cuenta propietaria existente no necesita
  `APP_TOKEN`: crea `app-token` vacío desde el principio.

Cada secreto debe ser distinto de los demás. No reutilices valores entre instalaciones,
entornos o productos.

## 2. Crear directorios y ficheros en cada host

Ejecuta como `root` en la terminal de Unraid:

```bash
RTFM_ROOT=/mnt/user/appdata/rtfm

install -d -o 10001 -g 10001 -m 0750 "$RTFM_ROOT/data"
install -d -o 10001 -g 10001 -m 0700 "$RTFM_ROOT/secrets"

for name in app-token session-secret replication-token keepalived-api-key; do
  install -o 10001 -g 10001 -m 0400 /dev/null "$RTFM_ROOT/secrets/$name"
done
```

La imagen se ejecuta como UID/GID `10001:10001`. El directorio `data` debe permitirle
escritura; el directorio de secretos solo necesita búsqueda y lectura por ese usuario. Los
ficheros permanecen `0400` y los mounts de Docker añaden una segunda barrera de solo lectura.

No uses symlinks para estos cuatro ficheros. Tampoco los coloques dentro del directorio de
datos que RTFM puede modificar.

## 3. Generar los valores

Para una instalación nueva, genera dos valores independientes:

```bash
openssl rand -base64 36 > "$RTFM_ROOT/secrets/app-token"
openssl rand -hex 32 > "$RTFM_ROOT/secrets/session-secret"
```

`app-token` será la contraseña usada una única vez para crear la primera cuenta. Si ya existe
una cuenta en los datos restaurados, mantenlo vacío:

```bash
: > "$RTFM_ROOT/secrets/app-token"
```

En HA, genera `replication-token` una vez y transfiere ese mismo valor a cada nodo por un
canal seguro. En modo de un solo nodo se mantiene vacío:

```bash
# Ejecutar una vez para un grupo HA nuevo.
openssl rand -hex 32 > "$RTFM_ROOT/secrets/replication-token"

# Alternativa para un único nodo.
: > "$RTFM_ROOT/secrets/replication-token"
```

Si se usa el conector autenticado, introduce la clave `fip_...` emitida por Keepalived sin
incluirla en el historial del shell:

```bash
read -rsp 'Clave de Keepalived: ' RTFM_KEEPALIVED_KEY
printf '\n'
printf '%s\n' "$RTFM_KEEPALIVED_KEY" > "$RTFM_ROOT/secrets/keepalived-api-key"
unset RTFM_KEEPALIVED_KEY
```

En una instalación aislada:

```bash
: > "$RTFM_ROOT/secrets/keepalived-api-key"
```

Restaura propietario y modos después de copiar cualquier valor:

```bash
chown 10001:10001 "$RTFM_ROOT/secrets/"*
chmod 0400 "$RTFM_ROOT/secrets/"*
stat -c '%u:%g %a %n' "$RTFM_ROOT/data" "$RTFM_ROOT/secrets" \
  "$RTFM_ROOT/secrets/"*
```

La salida esperada para cada secreto es `10001:10001 400`. No uses `cat`, `echo` ni una
captura de pantalla para comprobar su contenido.

## 4. Completar la plantilla

Instala `unraid/my-RTFM.xml` y revisa, como mínimo:

1. `Datos de RTFM`: `/mnt/user/appdata/rtfm/data` o la ruta persistente ya existente.
2. Los cuatro campos `Fichero ... (host)`: la ruta real de cada fichero creado antes.
3. Los cuatro campos avanzados `Ruta interna ...`: conserva sus valores
   `/run/secrets/...`.
4. `NODE_NAME`: único por nodo.
5. Un solo nodo: `ROLE_MODE=active`, `PEERS` vacío y sin reclamación de Keepalived.
6. HA: `ROLE_MODE=auto`, `PEERS`, `KEEPALIVED_CLAIM_ID` y el resto del conector.
7. HTTPS: activa `PUBLIC_SCHEME=https` y `SESSION_COOKIE_SECURE=true` solo cuando el acceso sea
   exclusivamente HTTPS.
8. Reverse proxy: deja `FORWARDED_ALLOW_IPS=127.0.0.1` si conecta por loopback; en otro caso
   escribe únicamente sus IPs o redes de origen, separadas por comas. Nunca uses `*`.

La plantilla define estas variables no secretas:

```text
APP_TOKEN_FILE=/run/secrets/app-token
SESSION_SECRET_FILE=/run/secrets/session-secret
REPLICATION_TOKEN_FILE=/run/secrets/replication-token
KEEPALIVED_API_KEY_FILE=/run/secrets/keepalived-api-key
FORWARDED_ALLOW_IPS=127.0.0.1
```

No añadas simultáneamente `APP_TOKEN`, `SESSION_SECRET`, `REPLICATION_TOKEN` o
`KEEPALIVED_API_KEY`: RTFM rechaza de forma deliberada que un secreto llegue a la vez por valor
directo y por fichero.

`FORWARDED_ALLOW_IPS` no contiene una credencial. Limita qué conexiones pueden imponer
`X-Forwarded-For` y `X-Forwarded-Proto`; debe coincidir con el origen que RTFM observa, no con
las direcciones de los navegadores. Tras aplicar HTTPS, bloquea el acceso directo HTTP al
puerto de RTFM mediante la red o el firewall y comprueba que la respuesta externa incluye
HSTS y que `rtfm_session` lleva `Secure`, `HttpOnly` y `SameSite=Strict`.

## 5. Primera puesta en marcha

1. Aplica la plantilla primero en un solo nodo.
2. Comprueba `/api/health` y abre la interfaz.
3. Si no hay usuarios, inicia sesión con el nombre deseado para la cuenta propietaria y el
   valor temporal de `app-token`. Ese primer login crea la cuenta.
4. Cambia inmediatamente su contraseña por otra distinta del token de bootstrap y configura
   2FA.
5. En HA, arranca los otros nodos y confirma que la cuenta propietaria se ha replicado antes
   de retirar el bootstrap.
6. Comprueba backups y acceso antes de retirar cualquier instalación anterior.

## 6. Retirar APP_TOKEN después del bootstrap

`APP_TOKEN` se carga al iniciar el proceso. Para deshabilitar tanto el bootstrap como el
Bearer heredado hay que vaciar el fichero y reiniciar todos los nodos:

1. Verifica que la cuenta propietaria existe y puede iniciar sesión con su nueva contraseña en
   todos los nodos.
2. Detén todos los contenedores RTFM del grupo.
3. En cada host ejecuta:

   ```bash
   : > /mnt/user/appdata/rtfm/secrets/app-token
   chown 10001:10001 /mnt/user/appdata/rtfm/secrets/app-token
   chmod 0400 /mnt/user/appdata/rtfm/secrets/app-token
   ```

4. Arranca los nodos y verifica login, réplica y salud.
5. Confirma sin mostrar contenido:

   ```bash
   test ! -s /mnt/user/appdata/rtfm/secrets/app-token \
     && echo 'APP_TOKEN retirado'
   ```

Mantener montado el fichero vacío evita que una actualización de la plantilla reactive o
rompa la configuración. Si se elimina el mount por completo, también debe vaciarse
`APP_TOKEN_FILE`; ambos cambios deben aplicarse juntos con el contenedor detenido.

## 7. Comprobar que Docker no conserva valores directos

Esta comprobación imprime solo nombres y rutas, nunca el contenido de los ficheros:

```bash
docker inspect RTFM --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep -E '^(APP_TOKEN|SESSION_SECRET|REPLICATION_TOKEN|KEEPALIVED_API_KEY)(_FILE)?='
```

Solo deben aparecer los cuatro nombres terminados en `_FILE`. Para comprobar que los mounts
son de solo lectura:

```bash
docker inspect RTFM --format '{{range .Mounts}}{{println .Destination "rw=" .RW}}{{end}}' \
  | grep '^/run/secrets/'
```

Los cuatro destinos deben mostrar `rw=false`. Desde el contenedor se puede validar lectura
sin revelar datos:

```bash
docker exec RTFM sh -c '
  for file in app-token session-secret replication-token keepalived-api-key; do
    test -f "/run/secrets/$file" && test -r "/run/secrets/$file" || exit 1
  done
'
```

## Migración segura de un volumen existente a UID/GID 10001

Este procedimiento sirve cuando `/data` ya contiene una instalación anterior cuyo
propietario no es `10001:10001`. No se ejecuta con RTFM escribiendo. En HA se declara una
ventana de mantenimiento, se detienen **todos** los nodos antes del primer backup y se respalda
cada volumen persistente independiente. Cambiar sólo un nodo mientras otro sigue replicando
impide demostrar que el backup sea consistente.

La autoridad ejecutable de esta operación es `scripts/migrate-data-uid.sh`. No copies una
selección de órdenes `find`, `tar`, `chown` o `mv`: el script conserva en un directorio `0700`
la identidad exacta del contenedor, imagen, almacenamiento, backup y fase. Además, antes de
cada lectura o mutación recursiva vuelve a comprobar ruta, contenedores locales, mounts
anidados, symlinks, hardlinks y tipos especiales. El rollback consume ese mismo estado sin
depender de variables de una shell anterior.

El script admite exclusivamente el bind mount que crea la plantilla Unraid. Un volumen Docker
con nombre requiere otro procedimiento: restaurar en un volumen nuevo mediante un contenedor
aislado y después cambiar el mount. Nunca se renombra, vacía ni modifica directamente `_data`
bajo el directorio interno de Docker. La migración automática falla antes de escribir si
detecta ese tipo de almacenamiento.

### 1. Detener el grupo y ejecutar la migración transaccional

Detén todos los nodos RTFM del grupo desde Unraid. Comprueba en cada host que el contenedor
objetivo figura detenido y que no queda otro contenedor apuntando al mismo almacenamiento.
Después ejecuta en cada host, usando un directorio de estado nuevo y distinto:

```bash
set -euo pipefail
RTFM_CONTAINER=RTFM
RTFM_ALLOWED_ROOT=/mnt/user/appdata
RTFM_STATE_PARENT=/mnt/user/backups/rtfm
RTFM_STATE_DIR="$RTFM_STATE_PARENT/uid-10001-$(date -u +%Y%m%dT%H%M%SZ)"

install -d -o 0 -g 0 -m 0700 -- "$RTFM_STATE_PARENT"
test "$(docker inspect "$RTFM_CONTAINER" --format '{{.State.Running}}')" = false

# Esta confirmación significa que también se han detenido los demás nodos remotos.
export RTFM_ALL_NODES_STOPPED=yes
bash scripts/migrate-data-uid.sh migrate \
  --container "$RTFM_CONTAINER" \
  --allowed-root "$RTFM_ALLOWED_ROOT" \
  --state-dir "$RTFM_STATE_DIR"
```

El script sólo admite el bind mount de la plantilla Unraid. Falla antes del backup si detecta
otro escritor local, una ruta fuera de la raíz aprobada, un submount, cualquier tipo distinto
de directorio/fichero regular o un fichero con más de un hardlink. Un hardlink aparentemente
interno podría compartir inode con una ruta externa y hacer que `chown` alterase otro servicio.
Si una puerta falla, se documenta y resuelve la ambigüedad; nunca se evita con `chown -R`.

### 2. Backup frío y estado durable

El backup contiene documentos, cuentas y auditoría. El script exige GNU tar, lo crea fuera de
`/data`, conserva propietario numérico, modos, ACL y atributos extendidos, fija modo `0600` y
valida tanto su SHA-256 como su índice antes del primer `chown`. Los ficheros de estado son
también `0600`; no los edites ni muevas por separado.

No continúes si el comando no termina con `rtfm-uid-migration: OK`. Conserva la ruta exacta de
`RTFM_STATE_DIR`, pero nunca añadas el estado, tar o checksum al repositorio o a un diagnóstico.

### 3. Cambio de propietario y prueba aislada

La misma ejecución vuelve a pasar todas las puertas justo antes de `chown`, cambia únicamente
UID/GID —no aplica `chmod` recursivo— y confirma que no queda ninguna entrada con otro dueño.
Finalmente crea y elimina un marcador usando el ID exacto de la imagen previa, como
`10001:10001`, sin red, rootfs escribible, capacidades ni privilegios adicionales.

Si algo falla después de `phase=backup-ready`, no repitas la migración sobre el árbol parcial:
ejecuta el rollback con el directorio de estado exacto.

### 4. Arrancar y verificar antes de aceptar la migración

```bash
set -euo pipefail
RTFM_MAINTENANCE_STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RTFM_CONTAINER=RTFM
docker start "$RTFM_CONTAINER"
docker inspect "$RTFM_CONTAINER" --format 'usuario={{.Config.User}} estado={{.State.Status}}'
docker logs --since "$RTFM_MAINTENANCE_STARTED" "$RTFM_CONTAINER"
```

La identidad configurada debe ser `10001:10001` y no debe haber errores de permisos. Comprueba
además `/api/health`, login, lectura de un documento y un ciclo controlado de crear/editar. En
HA, arranca primero un nodo, valida su estado y replica antes de incorporar los demás. Mantén
el backup hasta superar una ventana de observación y otra restauración ensayada.

### 5. Rollback conservando ambos árboles

Si falla la validación, vuelve a detener todos los escritores. En un bind mount restaura el
backup en un directorio hermano nuevo; no extraigas encima del árbol fallido y no lo borres.

```bash
set -euo pipefail
RTFM_CONTAINER=RTFM
RTFM_STATE_DIR=/mnt/user/backups/rtfm/uid-10001-AAAAMMDDTHHMMSSZ

# Detén antes todos los nodos del grupo y verifica el contenedor local.
docker stop "$RTFM_CONTAINER"
export RTFM_ALL_NODES_STOPPED=yes
bash scripts/migrate-data-uid.sh rollback --state-dir "$RTFM_STATE_DIR"
```

El rollback no arranca el contenedor. Verifica el mensaje final, arráncalo manualmente y
comprueba salud, login, documentos y propietarios esperados de la versión anterior. El árbol
`.failed-*`, estado y backup se conservan hasta confirmar el rollback; sólo entonces se decide
su retirada mediante un procedimiento separado y con las rutas absolutas revisadas.

## Migración desde variables directas

El runtime `0.4.2` conserva las variables directas únicamente para actualizar instalaciones
anteriores. Esa vía muestra el valor en `docker inspect` y no es la configuración recomendada.
La plantilla nueva no incluye campos directos ni secretos predeterminados.

Para migrar:

1. Detén RTFM y conserva un backup de los datos y de la configuración actual.
2. Crea los cuatro ficheros con propietario `10001:10001` y modo `0400`.
3. Copia cada valor actual a su fichero correspondiente mediante entrada silenciosa o un
   gestor de secretos; deja vacíos los opcionales que no se utilicen.
4. En la edición del contenedor, elimina las cuatro variables directas heredadas y añade los
   cuatro mounts y los cuatro `*_FILE` de la plantilla actual.
5. Antes de arrancar, confirma que no queda ningun secreto configurado por ambos mecanismos.
6. Arranca un nodo, valida login y salud y continúa con los demás.

No hay valor de compatibilidad predeterminado. Una variable directa solo debe mantenerse el
tiempo imprescindible para completar una migración controlada.

## Rotación y recuperación

- No cambies `SESSION_SECRET` durante una actualización ordinaria: invalida sesiones y afecta
  a TOTP y tokens protegidos. Su rotación exige detener todos los nodos y un procedimiento de
  recuperación probado.
- Rota `REPLICATION_TOKEN` de forma coordinada en todo el grupo; no mezcles valores durante
  una conmutación.
- Rota la clave de Keepalived primero en el emisor y después en todos los nodos dentro de una
  ventana controlada.
- Incluye `session-secret` en un backup cifrado y de acceso restringido. Nunca incluyas estos
  cuatro ficheros en Git, diagnósticos, capturas ni paquetes de soporte.
