-- MySQL Workbench Synchronization
-- Generated: 2026-10-13 12:55
-- Model: New Model
-- Version: 1.0
-- Project: Name of the project
-- Author: kaosj

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

ALTER TABLE `progent_usuarios`.`Educacion` 
DROP FOREIGN KEY `Correos`;

ALTER TABLE `progent_usuarios`.`Experiencia` 
ADD INDEX `Correos_idx` (`Correos` ASC) VISIBLE,
DROP INDEX `Correos_idx` ;
;

ALTER TABLE `progent_usuarios`.`Educacion` 
ADD INDEX `Correos_idx` (`Correos` ASC) VISIBLE,
DROP INDEX `Correos_idx` ;
;

ALTER TABLE `progent_usuarios`.`informacion_usuarios` 
ADD CONSTRAINT `Correos`
  FOREIGN KEY (`Correos`)
  REFERENCES `progent_usuarios`.`Usuarios` (`Correos`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;

ALTER TABLE `progent_usuarios`.`Experiencia` 
ADD CONSTRAINT `Correos`
  FOREIGN KEY (`Correos`)
  REFERENCES `progent_usuarios`.`Usuarios` (`Correos`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;

ALTER TABLE `progent_usuarios`.`Educacion` 
ADD CONSTRAINT `Correos`
  FOREIGN KEY (`Correos`)
  REFERENCES `progent_usuarios`.`Usuarios` (`Correos`)
  ON DELETE CASCADE
  ON UPDATE CASCADE;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
