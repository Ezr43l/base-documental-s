# Criterios de aceptación — Fase 0

La fase se considera cerrada cuando:

- existe un modelo explícito para documentos, estructura, etiquetas, referencias,
  fragmentos, usuarios, 2FA, API, logs y auditoría;
- existe contrato versionado para `/api/v1`, paginación, errores, idempotencia y
  exportación de logs;
- se distingue autenticación web de credenciales de aplicaciones;
- se han definido roles, permisos y alcances sin depender del rol HA;
- las eliminaciones, tombstones, vault y retención están especificados;
- la réplica se define por operaciones idempotentes y no por copiar ficheros;
- se ha fijado la decisión de SQLite local con réplica lógica como arquitectura
  inicial de contenedor único;
- los documentos actuales indican claramente qué partes son prototipo y cuáles
  son contrato futuro;
- todos los entregables están versionados en el repositorio configurado para el proyecto;
- no hay secretos en los entregables ni en el historial Git.

El cierre de esta fase no significa que la aplicación sea apta para producción.
Significa únicamente que las siguientes fases pueden implementarse sin cambiar
arbitrariamente el núcleo de seguridad, datos o sincronización.
