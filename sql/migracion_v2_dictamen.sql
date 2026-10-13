-- =============================================================================
-- Migración SiteLog - Versión 2 (Conforme al Dictamen del Equipo Docente)
-- 1. Ciclo de vida oficial de 5 estados para asientos
-- 2. Integridad y autenticidad con hash_contenido SHA-256
-- 3. Precisión GPS (accuracy_registro) y radio en frentes_obra
-- =============================================================================

USE `sitelog_db`;

-- 1. Agregar radio_metros a frentes_obra si no existe
ALTER TABLE `frentes_obra`
  ADD COLUMN `radio_metros` DOUBLE NOT NULL DEFAULT 50.0 AFTER `longitud`;

-- 2. Agregar accuracy_registro y hash_contenido a asientos_cuaderno
ALTER TABLE `asientos_cuaderno`
  ADD COLUMN `accuracy_registro` DOUBLE NULL AFTER `lon_registro`,
  ADD COLUMN `hash_contenido` VARCHAR(64) NULL AFTER `estado`;

-- 3. Modificar columna estado a los 5 estados oficiales
ALTER TABLE `asientos_cuaderno`
  MODIFY COLUMN `estado` ENUM('PENDIENTE_SINCRONIZACION', 'EMITIDO', 'OBSERVADO', 'ABSUELTO', 'CONCLUIDO') 
  NOT NULL DEFAULT 'EMITIDO';
