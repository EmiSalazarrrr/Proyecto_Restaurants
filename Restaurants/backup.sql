-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Versión del servidor:         10.4.32-MariaDB - mariadb.org binary distribution
-- SO del servidor:              Win64
-- HeidiSQL Versión:             12.15.0.7171
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Volcando estructura para tabla restaurants.alimentosbebidas
CREATE TABLE IF NOT EXISTS `alimentosbebidas` (
  `id_alimentosbebidas` int(11) NOT NULL AUTO_INCREMENT,
  `descripcion` varchar(200) NOT NULL,
  `costo` decimal(10,2) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_alimentosbebidas`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.alimentosbebidas: ~0 rows (aproximadamente)

-- Volcando estructura para tabla restaurants.cliente
CREATE TABLE IF NOT EXISTS `cliente` (
  `nombre_usuario` varchar(20) NOT NULL,
  `numero_celular` varchar(15) NOT NULL,
  `nombre` varchar(30) NOT NULL,
  `apellido_Paterno` varchar(30) NOT NULL,
  `apellido_materno` varchar(30) DEFAULT NULL,
  `contraseña` varchar(255) NOT NULL,
  `id_tipo_de_usuario` int(11) DEFAULT 1,
  PRIMARY KEY (`nombre_usuario`),
  UNIQUE KEY `numero_celular` (`numero_celular`),
  KEY `fk_perfiles_cliente` (`id_tipo_de_usuario`),
  CONSTRAINT `fk_perfiles_cliente` FOREIGN KEY (`id_tipo_de_usuario`) REFERENCES `perfiles` (`id_tipo_de_usuario`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.cliente: ~0 rows (aproximadamente)

-- Volcando estructura para tabla restaurants.detalleticket
CREATE TABLE IF NOT EXISTS `detalleticket` (
  `id_ticket` int(11) DEFAULT NULL,
  `id_productopedido` int(11) DEFAULT NULL,
  KEY `fk_ticket_detalleticket` (`id_ticket`),
  KEY `fk_productopedido_detalleticket` (`id_productopedido`),
  CONSTRAINT `fk_productopedido_detalleticket` FOREIGN KEY (`id_productopedido`) REFERENCES `productopedido` (`id_productopedido`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_ticket_detalleticket` FOREIGN KEY (`id_ticket`) REFERENCES `ticket` (`id_ticket`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.detalleticket: ~0 rows (aproximadamente)

-- Volcando estructura para tabla restaurants.perfiles
CREATE TABLE IF NOT EXISTS `perfiles` (
  `id_tipo_de_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_de_usuario` varchar(50) NOT NULL,
  PRIMARY KEY (`id_tipo_de_usuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.perfiles: ~0 rows (aproximadamente)

-- Volcando estructura para tabla restaurants.productopedido
CREATE TABLE IF NOT EXISTS `productopedido` (
  `id_productopedido` int(11) NOT NULL AUTO_INCREMENT,
  `id_alimentosbebidas` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_productopedido`),
  KEY `fk_alimentosbebidas_productopedido` (`id_alimentosbebidas`),
  CONSTRAINT `fk_alimentosbebidas_productopedido` FOREIGN KEY (`id_alimentosbebidas`) REFERENCES `alimentosbebidas` (`id_alimentosbebidas`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.productopedido: ~0 rows (aproximadamente)

-- Volcando estructura para tabla restaurants.promocion
CREATE TABLE IF NOT EXISTS `promocion` (
  `id_promocion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(200) NOT NULL,
  `porcentaje_a_reducir` decimal(5,2) NOT NULL,
  `id_restriccion` int(11) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_promocion`),
  UNIQUE KEY `nombre` (`nombre`),
  KEY `fk_restriccion_promocion` (`id_restriccion`),
  CONSTRAINT `fk_restriccion_promocion` FOREIGN KEY (`id_restriccion`) REFERENCES `restricciones` (`id_restriccion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.promocion: ~0 rows (aproximadamente)

-- Volcando estructura para tabla restaurants.restricciones
CREATE TABLE IF NOT EXISTS `restricciones` (
  `id_restriccion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(25) NOT NULL,
  `consumo_minimo_para_aplicar` int(11) NOT NULL,
  PRIMARY KEY (`id_restriccion`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.restricciones: ~0 rows (aproximadamente)

-- Volcando estructura para tabla restaurants.ticket
CREATE TABLE IF NOT EXISTS `ticket` (
  `id_ticket` int(11) NOT NULL AUTO_INCREMENT,
  `precio_final` decimal(10,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `canjeado` tinyint(1) DEFAULT 0,
  `id_promocion` int(11) DEFAULT NULL,
  `nombre_usuario` varchar(20) DEFAULT NULL,
  `codigounico` int(11) NOT NULL,
  PRIMARY KEY (`id_ticket`),
  UNIQUE KEY `codigounico` (`codigounico`),
  KEY `fk_promocion_ticket` (`id_promocion`),
  KEY `fk_cliente_ticket` (`nombre_usuario`),
  CONSTRAINT `fk_cliente_ticket` FOREIGN KEY (`nombre_usuario`) REFERENCES `cliente` (`nombre_usuario`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_promocion_ticket` FOREIGN KEY (`id_promocion`) REFERENCES `promocion` (`id_promocion`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Volcando datos para la tabla restaurants.ticket: ~0 rows (aproximadamente)

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
