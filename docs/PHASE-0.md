# Fase 0 — Contrato de producto y arquitectura

Estado: aprobado como base de diseño · versión de trabajo `0.0.4` · aplicación en desarrollo

## Propósito

Convertir la base funcional en un producto documental privado, estructurado,
auditable, replicable y consumible por otras aplicaciones. Esta fase no pretende
declarar la aplicación madura ni lista para producción: fija las decisiones que
evitan rehacer el núcleo en las fases siguientes.

## Decisiones de base

1. La aplicación seguirá distribuida como un contenedor por nodo.
2. Solo el nodo que posee la IP flotante acepta escrituras de usuario.
3. Los nodos pasivos sirven lectura, estado de sincronización y recepción de
   operaciones; nunca aceptan mutaciones externas.
4. El almacenamiento local objetivo será transaccional y consultable. Se adopta
   SQLite como primera opción para mantener el contenedor único, pero la
   replicación será lógica por operaciones, nunca copia ciega del fichero de base
   de datos.
5. Markdown, adjuntos y exportaciones Git serán proyecciones portables del modelo,
   no la única fuente de verdad para usuarios, permisos y relaciones.
6. Todas las mutaciones tendrán identidad de autor, fecha UTC, nodo, resultado y
   referencia de operación.
7. Las eliminaciones serán tombstones; el contenido recuperable vivirá en el vault
   durante la retención configurada.
8. La API pública estable comenzará en `/api/v1`. Las rutas `/api/*` actuales son
   prototipo y no constituyen todavía un contrato de producción.

## Fuera de esta fase

- autenticación funcional;
- rediseño completo de la interfaz;
- migración de los datos actuales;
- compatibilidad Git operativa;
- 2FA y registro de aplicaciones;
- pruebas de failover destructivas.

Estos elementos quedan condicionados por los contratos de esta fase.

## Entregables

- modelo de datos: `DATA-MODEL.md`;
- contrato API: `API-CONTRACT.md`;
- seguridad: `SECURITY-MODEL.md`;
- replicación y HA: `REPLICATION-CONTRACT.md`;
- criterios verificables: `ACCEPTANCE-PHASE-0.md`.
