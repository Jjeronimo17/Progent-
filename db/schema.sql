-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema Progent_Usuarios
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema Progent_Usuarios
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `Progent_Usuarios` DEFAULT CHARACTER SET utf8mb3 ;
USE `Progent_Usuarios` ;

-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Usuarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Usuarios` (
  `Correos` VARCHAR(200) NOT NULL,
  `SALT` VARCHAR(32) NULL,
  `Hashed` VARCHAR(100) NULL DEFAULT NULL,
  PRIMARY KEY (`Correos`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`informacion_usuarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`informacion_usuarios` (
  `Correos` VARCHAR(200) NOT NULL,
  `Nombre` VARCHAR(60) NOT NULL,
  `Edad` INT NULL,
  `Telefono` VARCHAR(50) NULL,
  `Correo_contacto` VARCHAR(200) NOT NULL,
  `Ubicacion` VARCHAR(100) NOT NULL,
  `Ocupacion` LONGTEXT NOT NULL,
  PRIMARY KEY (`Correos`),
  CONSTRAINT `Correos`
    FOREIGN KEY (`Correos`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Experiencia`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Experiencia` (
  `ID` INT NOT NULL AUTO_INCREMENT,
  `Correos_experiencia` VARCHAR(200) NOT NULL,
  `Nombre_empresa` VARCHAR(100) NOT NULL,
  `Sector_industria` VARCHAR(100) NULL,
  `Tamaño_empresa` BIGINT NULL,
  `Titulo_puesto` VARCHAR(100) NOT NULL,
  `Nivel_seniority` VARCHAR(100) NULL,
  `Fecha_inicio` DATE NOT NULL,
  `Fecha_finalizacion` DATE NULL,
  `Descripcion_funciones` LONGTEXT NOT NULL,
  `Logros` LONGTEXT NULL,
  `Habilidades` LONGTEXT NOT NULL,
  `Ubicacion_empresa` VARCHAR(100) NULL,
  `Tipo_contrato` VARCHAR(100) NULL,
  `Modalidad_trabajo` ENUM('Hibrido', 'Presencial', 'Virtual') NULL,
  PRIMARY KEY (`ID`),
  INDEX `Correos_idx` (`Correos_experiencia` ASC) VISIBLE,
  CONSTRAINT `Correos_experiencia`
    FOREIGN KEY (`Correos_experiencia`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Educacion`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Educacion` (
  `Id_educacion` INT NOT NULL AUTO_INCREMENT,
  `Correos_educacion` VARCHAR(200) NOT NULL,
  `Institucion_educativa` VARCHAR(100) NOT NULL,
  `Tipo_institucion` VARCHAR(250) NULL,
  `Titulo_Carrera_Grado` VARCHAR(200) NOT NULL,
  `Nivel_educacion` VARCHAR(150) NULL,
  `Campo_estudio` VARCHAR(200) NULL,
  `Fecha_inicio` DATE NOT NULL,
  `Fecha_final` DATE NULL,
  `Estado_estudio` ENUM('Cursando', 'Graduado', 'Aplazado', 'Incompleto') NOT NULL,
  `Logros` LONGTEXT NULL,
  PRIMARY KEY (`Id_educacion`),
  INDEX `Correos_idx` (`Correos_educacion` ASC) VISIBLE,
  CONSTRAINT `Correos_educacion`
    FOREIGN KEY (`Correos_educacion`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`archivos_usuarios`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`archivos_usuarios` (
  `Correos_usuarios` VARCHAR(200) NOT NULL,
  `nombre_archivo` VARCHAR(300) NOT NULL,
  `tipo` VARCHAR(100) NOT NULL,
  `archivo_bytes` LONGBLOB NOT NULL,
  PRIMARY KEY (`Correos_usuarios`),
  CONSTRAINT `Correos_usuarios`
    FOREIGN KEY (`Correos_usuarios`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Vacantes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Vacantes` (
  `Id_vacante` INT NOT NULL AUTO_INCREMENT,
  `Cargo` VARCHAR(150) NOT NULL,
  `Empresa` VARCHAR(150) NOT NULL,
  `Ubicacion` VARCHAR(100) NOT NULL,
  `Descripcion` LONGTEXT NOT NULL,
  `Requisitos` LONGTEXT NOT NULL,
  `Estado` ENUM('Abierta', 'Cerrada') NOT NULL DEFAULT 'Abierta',
  `Fecha_publicacion` DATE NOT NULL,
  `Salario` INT NULL,
  `Modalidad` ENUM('Hibrido', 'Presencial', 'Virtual') NULL,
  PRIMARY KEY (`Id_vacante`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Postulaciones`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Postulaciones` (
  `Id_postulacion` INT NOT NULL AUTO_INCREMENT,
  `Correos_postulacion` VARCHAR(200) NOT NULL,
  `Id_vacante_postulacion` INT NOT NULL,
  `Fecha_postulacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Estado` ENUM('Postulado', 'En revision', 'Entrevista', 'Oferta', 'Rechazado', 'Retirado') NOT NULL DEFAULT 'Postulado',
  `Fecha_actualizacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_postulacion`),
  UNIQUE INDEX `Usuario_vacante_UNIQUE` (`Correos_postulacion` ASC, `Id_vacante_postulacion` ASC) VISIBLE,
  INDEX `Id_vacante_idx` (`Id_vacante_postulacion` ASC) VISIBLE,
  CONSTRAINT `Correos_postulacion`
    FOREIGN KEY (`Correos_postulacion`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `Id_vacante_postulacion`
    FOREIGN KEY (`Id_vacante_postulacion`)
    REFERENCES `Progent_Usuarios`.`Vacantes` (`Id_vacante`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Criterios_busqueda`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Criterios_busqueda` (
  `Correos_criterios` VARCHAR(200) NOT NULL,
  `Cargo_deseado` VARCHAR(150) NULL,
  `Modalidad` ENUM('Hibrido', 'Presencial', 'Virtual') NULL,
  `Ciudad` VARCHAR(100) NULL,
  PRIMARY KEY (`Correos_criterios`),
  CONSTRAINT `Correos_criterios`
    FOREIGN KEY (`Correos_criterios`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Recomendaciones`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Recomendaciones` (
  `Id_recomendacion` INT NOT NULL AUTO_INCREMENT,
  `Correos_recomendacion` VARCHAR(200) NOT NULL,
  `Id_vacante_recomendacion` INT NOT NULL,
  `Decision` ENUM('Interesa', 'Descartada') NOT NULL,
  `Motivo` LONGTEXT NULL,
  `Fecha_decision` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_recomendacion`),
  UNIQUE INDEX `Usuario_vacante_recomendacion_UNIQUE` (`Correos_recomendacion` ASC, `Id_vacante_recomendacion` ASC) VISIBLE,
  INDEX `Id_vacante_recomendacion_idx` (`Id_vacante_recomendacion` ASC) VISIBLE,
  CONSTRAINT `Correos_recomendacion`
    FOREIGN KEY (`Correos_recomendacion`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `Id_vacante_recomendacion`
    FOREIGN KEY (`Id_vacante_recomendacion`)
    REFERENCES `Progent_Usuarios`.`Vacantes` (`Id_vacante`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Vacantes_guardadas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Vacantes_guardadas` (
  `Id_guardada` INT NOT NULL AUTO_INCREMENT,
  `Correos_guardada` VARCHAR(200) NOT NULL,
  `Id_vacante_guardada` INT NOT NULL,
  `Fecha_guardada` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_guardada`),
  UNIQUE INDEX `Usuario_vacante_guardada_UNIQUE` (`Correos_guardada` ASC, `Id_vacante_guardada` ASC) VISIBLE,
  INDEX `Id_vacante_guardada_idx` (`Id_vacante_guardada` ASC) VISIBLE,
  CONSTRAINT `Correos_guardada`
    FOREIGN KEY (`Correos_guardada`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `Id_vacante_guardada`
    FOREIGN KEY (`Id_vacante_guardada`)
    REFERENCES `Progent_Usuarios`.`Vacantes` (`Id_vacante`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Alertas`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Alertas` (
  `Correos_alerta` VARCHAR(200) NOT NULL,
  `Palabra_clave` VARCHAR(100) NULL,
  `Ubicacion` VARCHAR(100) NULL,
  `Salario_minimo` INT NULL,
  `Modalidad` ENUM('Hibrido', 'Presencial', 'Virtual') NULL,
  `Ultima_vacante_revisada` INT NOT NULL DEFAULT 0,
  `Fecha_creacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Correos_alerta`),
  CONSTRAINT `Correos_alerta`
    FOREIGN KEY (`Correos_alerta`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Notificaciones`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Notificaciones` (
  `Id_notificacion` INT NOT NULL AUTO_INCREMENT,
  `Correos_notificacion` VARCHAR(200) NOT NULL,
  `Id_vacante_notificacion` INT NOT NULL,
  `Fecha_notificacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Leida` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`Id_notificacion`),
  UNIQUE INDEX `Usuario_vacante_notificacion_UNIQUE` (`Correos_notificacion` ASC, `Id_vacante_notificacion` ASC) VISIBLE,
  INDEX `Id_vacante_notificacion_idx` (`Id_vacante_notificacion` ASC) VISIBLE,
  CONSTRAINT `Correos_notificacion`
    FOREIGN KEY (`Correos_notificacion`)
    REFERENCES `Progent_Usuarios`.`Usuarios` (`Correos`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `Id_vacante_notificacion`
    FOREIGN KEY (`Id_vacante_notificacion`)
    REFERENCES `Progent_Usuarios`.`Vacantes` (`Id_vacante`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Cartas_presentacion`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Cartas_presentacion` (
  `Id_postulacion_carta` INT NOT NULL,
  `Nombre_archivo` VARCHAR(300) NOT NULL,
  `Tipo` VARCHAR(100) NOT NULL,
  `Archivo_bytes` LONGBLOB NOT NULL,
  `Fecha_carga` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_postulacion_carta`),
  CONSTRAINT `Id_postulacion_carta`
    FOREIGN KEY (`Id_postulacion_carta`)
    REFERENCES `Progent_Usuarios`.`Postulaciones` (`Id_postulacion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Respuestas_formulario`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Respuestas_formulario` (
  `Id_respuesta` INT NOT NULL AUTO_INCREMENT,
  `Id_postulacion_respuesta` INT NOT NULL,
  `Orden` INT NOT NULL,
  `Pregunta` LONGTEXT NOT NULL,
  `Respuesta` LONGTEXT NOT NULL,
  `Fecha_confirmacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_respuesta`),
  INDEX `Id_postulacion_respuesta_idx` (`Id_postulacion_respuesta` ASC) VISIBLE,
  CONSTRAINT `Id_postulacion_respuesta`
    FOREIGN KEY (`Id_postulacion_respuesta`)
    REFERENCES `Progent_Usuarios`.`Postulaciones` (`Id_postulacion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `Progent_Usuarios`.`Cv_postulacion`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `Progent_Usuarios`.`Cv_postulacion` (
  `Id_postulacion_cv` INT NOT NULL,
  `Nombre_archivo` VARCHAR(300) NOT NULL,
  `Tipo` VARCHAR(100) NOT NULL,
  `Archivo_bytes` LONGBLOB NOT NULL,
  `Fecha_asociacion` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`Id_postulacion_cv`),
  CONSTRAINT `Id_postulacion_cv`
    FOREIGN KEY (`Id_postulacion_cv`)
    REFERENCES `Progent_Usuarios`.`Postulaciones` (`Id_postulacion`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

USE `Progent_Usuarios` ;

-- -----------------------------------------------------
-- procedure verificar_usuario
-- -----------------------------------------------------

DELIMITER $$
USE `Progent_Usuarios`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `verificar_usuario`(IN Correo VARCHAR(200), OUT mensaje ENUM('Usuario Disponible', 'Usuario No Disponible'))
BEGIN
IF EXISTS (SELECT 1 FROM usuarios WHERE Correos = Correo) THEN
SET mensaje = 'Usuario No Disponible';
ELSE
SET mensaje = 'Usuario Disponible';
END IF;
END$$

DELIMITER ;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- -----------------------------------------------------
-- Data for table `Progent_Usuarios`.`Vacantes`
-- Vacantes de prueba (empresas y datos inventados)
-- -----------------------------------------------------
SET NAMES utf8mb4;
START TRANSACTION;
USE `Progent_Usuarios`;
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (1, 'Desarrollador Backend Python', 'Andina Software S.A.S.', 'Medellín', 'Desarrollo y mantenimiento de servicios REST para la plataforma de pagos de la empresa. Trabajo en un equipo ágil con despliegues semanales.', 'Dos años de experiencia con Python. Conocimientos de Django o FastAPI, MySQL y Git.', 'Abierta', '2026-11-03', 6500000, 'Hibrido');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (2, 'Analista de Datos Junior', 'Cafetal Analytics', 'Bogotá', 'Construcción de tableros e informes para clientes del sector agrícola a partir de bases de datos de producción.', 'Profesional o estudiante de último semestre en Ingeniería o Estadística. SQL y Excel avanzado; Power BI deseable.', 'Abierta', '2026-11-05', 3200000, 'Presencial');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (3, 'Practicante de Desarrollo de Software', 'Nodo Ingeniería', 'Medellín', 'Apoyo al equipo de desarrollo en la construcción de módulos internos y en pruebas manuales.', 'Estudiante de Ingeniería de Sistemas a partir de sexto semestre. Bases de programación orientada a objetos.', 'Abierta', '2026-11-07', 1600000, 'Presencial');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (4, 'Ingeniero DevOps', 'Cordillera Cloud', 'Remoto', 'Administración de la infraestructura en la nube, automatización de despliegues y monitoreo de servicios.', 'Tres años de experiencia en Linux, Docker y CI/CD. Experiencia con AWS o Azure.', 'Abierta', '2026-11-08', 9000000, 'Virtual');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (5, 'Desarrollador Frontend', 'Pixel Valle Estudio', 'Cali', 'Maquetación e implementación de interfaces web para tiendas en línea de clientes nacionales.', 'Experiencia con HTML, CSS y JavaScript. React deseable. Portafolio de proyectos.', 'Abierta', '2026-11-10', 4500000, 'Hibrido');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (6, 'Auxiliar Contable', 'Contadores Asociados del Caribe', 'Barranquilla', 'Registro de facturas, conciliaciones bancarias y apoyo en el cierre contable mensual.', 'Técnico o tecnólogo en contabilidad. Un año de experiencia y manejo de software contable.', 'Abierta', '2026-11-11', 2200000, 'Presencial');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (7, 'Diseñador UX/UI', 'Pixel Valle Estudio', 'Remoto', 'Diseño de flujos y prototipos para aplicaciones móviles, en conjunto con el equipo de producto.', 'Dos años de experiencia en diseño de producto digital. Manejo de Figma y pruebas con usuarios.', 'Abierta', '2026-11-12', NULL, 'Virtual');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (8, 'Ejecutivo Comercial', 'Seguros La Montaña', 'Bogotá', 'Venta y seguimiento de pólizas a clientes corporativos en la zona norte de la ciudad.', 'Experiencia comercial de un año. Excelente comunicación. Vehículo propio deseable.', 'Abierta', '2026-11-13', 2800000, 'Presencial');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (9, 'Tester QA Manual', 'Andina Software S.A.S.', 'Medellín', 'Diseño y ejecución de casos de prueba para la aplicación móvil de la empresa y reporte de defectos.', 'Un año de experiencia en pruebas de software. Conocimiento de Jira y de metodologías ágiles.', 'Abierta', '2026-11-14', 3800000, 'Hibrido');
INSERT IGNORE INTO `Progent_Usuarios`.`Vacantes` (`Id_vacante`, `Cargo`, `Empresa`, `Ubicacion`, `Descripcion`, `Requisitos`, `Estado`, `Fecha_publicacion`, `Salario`, `Modalidad`) VALUES (10, 'Soporte Técnico Nivel 1', 'Nodo Ingeniería', 'Medellín', 'Atención de solicitudes de soporte de los usuarios internos por teléfono y correo.', 'Técnico en sistemas. Conocimientos básicos de redes y de Windows.', 'Cerrada', '2026-10-20', 1900000, 'Presencial');

COMMIT;
