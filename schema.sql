-- =============================================================================
-- SiteLog - Sistema móvil para la gestión y trazabilidad del Cuaderno de Obra digital
-- Script de Creación de Base de Datos y Datos Semilla para MySQL
-- Universidad Católica Santo Toribio de Mogrovejo (USAT) - 2026-II
-- =============================================================================

CREATE DATABASE IF NOT EXISTS `sitelog_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `sitelog_db`;

-- 1. TABLA: usuarios
CREATE TABLE IF NOT EXISTS `usuarios` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(120) NOT NULL,
    `correo` VARCHAR(120) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `rol` VARCHAR(50) NOT NULL, -- 'Residente', 'Supervisor', 'Administrador'
    `colegiatura` VARCHAR(50) NULL,
    `fcm_token` TEXT NULL,
    `activo` TINYINT(1) NOT NULL DEFAULT 1,
    INDEX `idx_usuario_correo` (`correo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. TABLA: obras
CREATE TABLE IF NOT EXISTS `obras` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `codigo_contrato` VARCHAR(50) NOT NULL UNIQUE,
    `nombre` VARCHAR(150) NOT NULL,
    `ubicacion_lat` DOUBLE NOT NULL,
    `ubicacion_lon` DOUBLE NOT NULL,
    `radio_metros` DOUBLE NOT NULL DEFAULT 50.0,
    `estado` VARCHAR(50) NOT NULL DEFAULT 'En ejecución',
    `id_residente` INT NULL,
    `id_supervisor` INT NULL,
    FOREIGN KEY (`id_residente`) REFERENCES `usuarios`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`id_supervisor`) REFERENCES `usuarios`(`id`) ON DELETE SET NULL,
    INDEX `idx_obra_codigo` (`codigo_contrato`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. TABLA: frentes_obra
CREATE TABLE IF NOT EXISTS `frentes_obra` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_obra` INT NOT NULL,
    `nombre_sector` VARCHAR(100) NOT NULL,
    `latitud` DOUBLE NOT NULL,
    `longitud` DOUBLE NOT NULL,
    FOREIGN KEY (`id_obra`) REFERENCES `obras`(`id`) ON DELETE CASCADE,
    INDEX `idx_frente_obra` (`id_obra`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. TABLA: asientos_cuaderno
CREATE TABLE IF NOT EXISTS `asientos_cuaderno` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_obra` INT NOT NULL,
    `id_frente` INT NULL,
    `numero_correlativo` INT NOT NULL,
    `tipo` VARCHAR(50) NOT NULL, -- 'Consulta', 'Notificación', 'Instrucción', 'Modificación'
    `titulo` VARCHAR(150) NOT NULL,
    `descripcion` TEXT NOT NULL,
    `lat_registro` DOUBLE NOT NULL,
    `lon_registro` DOUBLE NOT NULL,
    `fecha_registro` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `estado` VARCHAR(50) NOT NULL DEFAULT 'Emitido', -- 'Emitido', 'Pendiente de Absolución', 'Absuelto', 'Observado', 'Concluido'
    `codigo_qr_verificacion` VARCHAR(100) NULL UNIQUE,
    `id_usuario` INT NOT NULL,
    FOREIGN KEY (`id_obra`) REFERENCES `obras`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`id_frente`) REFERENCES `frentes_obra`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id`) ON DELETE RESTRICT,
    INDEX `idx_asiento_obra_correlativo` (`id_obra`, `numero_correlativo`),
    INDEX `idx_asiento_qr` (`codigo_qr_verificacion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. TABLA: respuestas_asiento
CREATE TABLE IF NOT EXISTS `respuestas_asiento` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_asiento` INT NOT NULL,
    `id_supervisor` INT NOT NULL,
    `descripcion` TEXT NOT NULL,
    `fecha_respuesta` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`id_asiento`) REFERENCES `asientos_cuaderno`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`id_supervisor`) REFERENCES `usuarios`(`id`) ON DELETE RESTRICT,
    INDEX `idx_respuesta_asiento` (`id_asiento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. TABLA: incidencias_obra
CREATE TABLE IF NOT EXISTS `incidencias_obra` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_asiento` INT NOT NULL,
    `tipo_incidencia` VARCHAR(100) NOT NULL,
    `descripcion` TEXT NOT NULL,
    `impacto_contractual` VARCHAR(100) NOT NULL,
    `fecha_registro` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`id_asiento`) REFERENCES `asientos_cuaderno`(`id`) ON DELETE CASCADE,
    INDEX `idx_incidencia_asiento` (`id_asiento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. TABLA: evidencias
CREATE TABLE IF NOT EXISTS `evidencias` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_asiento` INT NULL,
    `id_incidencia` INT NULL,
    `ruta_archivo` VARCHAR(255) NOT NULL,
    `tipo` VARCHAR(50) NOT NULL DEFAULT 'IMAGEN',
    `fecha` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`id_asiento`) REFERENCES `asientos_cuaderno`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`id_incidencia`) REFERENCES `incidencias_obra`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. TABLA: historial_cambios
CREATE TABLE IF NOT EXISTS `historial_cambios` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_asiento` INT NOT NULL,
    `estado_anterior` VARCHAR(50) NULL,
    `estado_nuevo` VARCHAR(50) NOT NULL,
    `comentario` TEXT NULL,
    `id_usuario` INT NOT NULL,
    `fecha` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`id_asiento`) REFERENCES `asientos_cuaderno`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id`) ON DELETE RESTRICT,
    INDEX `idx_historial_asiento` (`id_asiento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. TABLA: notificaciones_log
CREATE TABLE IF NOT EXISTS `notificaciones_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `id_usuario` INT NOT NULL,
    `id_asiento` INT NULL,
    `tipo` VARCHAR(50) NOT NULL,
    `mensaje` TEXT NOT NULL,
    `fcm_result` TEXT NULL,
    `fecha` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`id_usuario`) REFERENCES `usuarios`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`id_asiento`) REFERENCES `asientos_cuaderno`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
