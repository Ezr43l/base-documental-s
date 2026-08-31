# Entorno de desarrollo y despliegue

RTFM no presupone nombres de servidores, rangos de red, registros, repositorios ni rutas de
una instalación. Esos datos pertenecen a la configuración de cada entorno.

Un repositorio privado no exportable es el origen de desarrollo. Una versión aprobada se
exportará con árbol e historial limpios a `Ezr43l/base-documental-s`; no existe sincronización
automática entre ambos y la versión de aplicación debe coincidir.

Práctica requerida:

- validar código, frontend e imagen antes de promover una versión;
- mantener el árbol de trabajo y el historial en el repositorio elegido por el operador;
- no guardar contraseñas, claves privadas, tokens API ni secretos de réplica en Git;
- usar el panel de IP flotantes como autoridad de la reclamación y de su colocación;
- usar una clave de Keepalived diferente por aplicación y entorno, con scopes mínimos;
- mantener una `KEEPALIVED_CLAIM_ID` estable dentro de la instalación y diferente entre
  producción, pruebas e instalaciones independientes;
- conservar aislado el estado de cada servicio; dos imágenes iguales no convierten sus
  volúmenes en réplicas;
- documentar el servidor o sistema usado para la validación sin convertirlo en un valor
  predeterminado de la aplicación.

`requirements.txt` fija las versiones y `requirements.lock` fija además los hashes de todos
los artefactos publicados. El lock se regenera exclusivamente contra PyPI, dentro de la imagen
Python fijada y en `linux/amd64`, para que no dependa del Python, índice o arquitectura del
equipo del desarrollador:

```bash
bash scripts/update-requirements-lock.sh --write
bash scripts/update-requirements-lock.sh --check
```

CI y la release ejecutan `--check` y fallan si el resultado deja de ser byte a byte
reproducible.

## Exportación al repositorio público

Nunca se copia el directorio privado con `cp`, `rsync`, un ZIP del escritorio ni un clon que
conserve `.git`. La entrega se genera con el exportador versionado, desde un árbol cuyo
contenido versionado esté limpio:

```bash
git status --short
EXPORT_PARENT="$(mktemp -d)"
python3 scripts/export-public-release.py "$EXPORT_PARENT/base-documental-s"
```

El exportador captura el árbol inmutable de `HEAD` después de exigir que tanto el worktree
versionado como el índice estén limpios. Enumera y lee únicamente los blobs de ese objeto Git,
no los ficheros ignorados o sin seguimiento; por ello un cambio concurrente posterior en el
índice no altera los bytes seleccionados. Falla ante enlaces simbólicos, submódulos, punteros
LFS, rutas de datos/evidencias, ficheros de secretos, credenciales reconocibles, direcciones de
infraestructura no pública, nombres privados o rutas locales de una estación de trabajo.
También rechaza un destino dentro del repositorio o ya existente.

El árbol resultante no contiene historial y añade `PUBLIC_EXPORT_SHA256SUMS`. Si un repositorio
público limpio ya contiene ese manifiesto, se ignora como entrada y se regenera, de modo que
pueda reexportarse sin una excepción manual. Los modos proceden del árbol Git (`0644` o `0755`)
y las fechas se normalizan; dos ejecuciones sobre el mismo `HEAD` producen los mismos bytes,
modos y fechas. El manifiesto enumera todos los ficheros exportados salvo el propio manifiesto
y se comprueba así:

```bash
cd "$EXPORT_PARENT/base-documental-s"
sha256sum --check PUBLIC_EXPORT_SHA256SUMS
test ! -e .git
test ! -e .codex-artifacts
test ! -e 'tests;C'
gitleaks detect --source=. --no-git --redact --exit-code=1
```

La detección incorporada es una barrera conservadora, no sustituye el escaneo de secretos ni
la revisión humana. Antes del primer push se revisan también nombres, enlaces, plantillas y
documentación; después se crea un repositorio Git nuevo dentro de este árbol y su primer
commit. No se incorpora ningún commit, remoto, reflog, tag ni identificador del historial
privado. La CI debe quedar verde en ese repositorio público antes de crear `v0.4.2`.

La activación final usa una operación atómica *no-replace*: `renameat2(RENAME_NOREPLACE)` en
Linux y el contrato no-clobber de `rename` en Windows. Si el sistema o filesystem no puede
garantizarlo, el exportador falla cerrado y conserva cualquier destino que haya aparecido
durante la generación.
