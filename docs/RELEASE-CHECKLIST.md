# Checklist de publicación de RTFM 0.4.3

Un repositorio privado no exportable sigue siendo el origen canónico. Sólo una versión
correctiva aprobada se exporta con historial limpio a `Ezr43l/base-documental-s`.
La publicación de `0.4.3` no cambia el carácter experimental de toda la serie `0.x`.

## Bloqueos antes de la primera release

- [ ] Ejecutar externamente `PUT` + `GET /repos/{owner}/{repo}/immutable-releases`
  con permisos de administración y, solo tras confirmar `enabled=true`, fijar
  `IMMUTABLE_RELEASES_ENABLED=true`. El workflow no almacena ningún PAT y
  comprueba de nuevo `immutable=true` tras publicar.

- [x] Adoptar Apache-2.0 y añadir el texto canónico en `LICENSE`.
- [ ] Configurar `LICENSE_SPDX=Apache-2.0` en el repositorio público; el workflow
  bloquea la publicación mientras la variable falte o sea distinta.
- [ ] Crear el repositorio público aprobado `Ezr43l/base-documental-s`.
- [x] Completar permisos por biblioteca, interfaz administrativa, migración compatible y
  pruebas de aislamiento para personas, clientes API y credencial heredada.
- [x] Validar el contrato genérico de cuatro secretos para bootstrap y, en la instalación
  física ya inicializada, retirar `APP_TOKEN` y montar sólo los tres secretos activos como
  ficheros `0400` mediante un único directorio de sólo lectura, sin valores directos en
  `docker inspect` ni en las plantillas vivas.
- [x] Verificar backup frío, restauración y rollback real en una instalación de tres nodos.
- [x] Validar HTTPS, CA, proxy de confianza, HSTS, cookie segura y limitación por cliente en
  Docker local AMD64/ARM64 y en un host físico AMD64 sin exponer puertos del laboratorio.
- [x] Ejecutar el núcleo del laboratorio HA multinodo: VIP, réplica, escritura, rechazo en
  pasivo, tombstones, vault, failover, rejoin, preemption, actualización y rollback.
- [x] Completar un laboratorio HA de tres nodos con conflicto concurrente deliberado, nodo
  mantenido atrasado, reconciliación determinista y limpieza total de recursos.
- [x] Exportador público determinista basado sólo en el snapshot inmutable de `HEAD`, con
  política de rechazo, manifiesto SHA-256 regenerable y pruebas que excluyen historial,
  evidencias y ficheros ignorados.
- [ ] Confirmar que GHCR permite pull anónimo y que plantilla, icono y enlaces son públicos.
- [ ] Escanear árbol exportado e historial nuevo para secretos e identificadores privados.
- [ ] Instalar únicamente con la guía y artefactos públicos desde una máquina limpia.

## Contrato de artefactos

1. `VERSION`, changelog, paquete web, Compose, plantilla e imagen contienen la misma versión.
2. El tag anotado y protegido es `v<version>`, nace en el repositorio público `-s` y sólo se
   promociona tras una CI correcta sobre el mismo commit.
3. El workflow construye y escanea `linux/amd64` y `linux/arm64`, publica dos SBOM, avisos y
   textos de licencia, fuentes Alpine correspondientes, sumas SHA-256 y procedencia firmada
   en `ghcr.io/ezr43l/base-documental-s:<version>`.
4. La release registra el digest multi-arquitectura; la guía no depende de `latest`.
5. Se verifican backup, restauración, actualización y rollback antes de declarar la versión
   apta para producción.

Una plantilla Unraid no construye la imagen: descarga el valor de `<Repository>`. Compose sí
puede construir desde un source release porque incluye `build:` y el Dockerfile. Para una
entrega sencilla deben existir tanto el source público como la imagen GHCR verificable.

El árbol que inicia el repositorio público se crea siguiendo
[`DEVELOPMENT-ENVIRONMENT.md`](DEVELOPMENT-ENVIRONMENT.md); queda prohibido copiar `.git` o
construir la entrega desde una lista manual de archivos.
