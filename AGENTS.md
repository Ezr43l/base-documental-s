# AGENTS.md

Este repositorio contiene RTFM, una plataforma documental instalable en entornos propios.

## Reglas permanentes

1. La documentación es contenido versionable; no se guarda únicamente en una base de datos.
2. No almacenar contraseñas, tokens ni claves reales en el repositorio, los documentos, el vault o la auditoría.
3. Todo cambio debe tener autor, fecha/hora, nodo de origen y operación identificable.
4. El nodo activo es el único que acepta escrituras de documentos.
5. Los nodos pasivos pueden informar de su estado y recibir sincronizaciones, pero deben rechazar escrituras de usuario.
6. Una eliminación es una operación versionada y deja tombstone; nunca se resuelve haciendo desaparecer el registro sin más.
7. Archivado y eliminación son estados distintos.
8. Las comprobaciones deben distinguir `ok`, `degraded` y `unknown`; no proclamar éxito sin verificarlo.
9. Los cambios de código siguen `VERSION` + `CHANGELOG.md`.
10. La aplicación no debe codificar en documentos en qué servidor debe vivir un servicio.
11. La estructura documental pertenece al usuario: no imponer bibliotecas, categorías ni profundidad desde el código.
12. Cada opción principal de navegación debe tener ruta y página propias; no simular páginas mediante anclas.
13. Una funcionalidad visual no está terminada hasta que su operación, error y estado vacío sean verificables.
14. La carpeta de trabajo entregada por el usuario es la raíz del proyecto; no crear una carpeta de nivel adicional dentro de ella.

## Estado de esta base

Todas las versiones `0.x` son experimentales. La sesión firmada, TOTP, la administración
multiusuario, los tres niveles globales, los clientes API independientes y Git están
integrados. Los permisos por biblioteca están implementados desde `0.4.1`. HTTPS y otras
validaciones operativas siguen pendientes antes de exponer la aplicación fuera de la LAN/VPN
o considerarla apta para producción.
