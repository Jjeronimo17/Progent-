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
