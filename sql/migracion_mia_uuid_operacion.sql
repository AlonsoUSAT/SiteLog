-- Migración Bloque 2 (Mia): idempotencia offline + correlativo único por obra
-- Ejecutar UNA SOLA VEZ en la base sitelog_db si ya la tenías creada (phpMyAdmin > SQL).
-- Alternativa: borra la base y vuelve a ejecutar "flask init-db" y "flask seed-db".

ALTER TABLE `asientos_cuaderno`
  ADD COLUMN `uuid_operacion` VARCHAR(64) NULL AFTER `id_usuario`,
  ADD UNIQUE KEY `uq_asiento_uuid_operacion` (`uuid_operacion`),
  ADD UNIQUE KEY `uq_obra_correlativo` (`id_obra`, `numero_correlativo`);
