-- This script will update all foreign key constraints in your MySQL database to use ON DELETE CASCADE
-- for all constraints that should be CASCADE according to your Django models.
-- Run this after all migrations are applied and the schema is up to date.

SET @db = DATABASE();

-- Find all constraints that are not CASCADE but should be
SELECT
  CONCAT('ALTER TABLE `', kcu.TABLE_NAME, '` DROP FOREIGN KEY `', kcu.CONSTRAINT_NAME, '`;') AS drop_stmt,
  CONCAT('ALTER TABLE `', kcu.TABLE_NAME, '` ADD CONSTRAINT `', kcu.CONSTRAINT_NAME, '` FOREIGN KEY (`', kcu.COLUMN_NAME, '`)' ,
         ' REFERENCES `', kcu.REFERENCED_TABLE_NAME, '`(`', kcu.REFERENCED_COLUMN_NAME, '`) ON DELETE CASCADE;') AS add_stmt
FROM information_schema.KEY_COLUMN_USAGE kcu
JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
  ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME AND kcu.TABLE_NAME = rc.TABLE_NAME
WHERE kcu.TABLE_SCHEMA = @db
  AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
  AND kcu.REFERENCED_TABLE_NAME != ''
  AND kcu.REFERENCED_COLUMN_NAME IS NOT NULL
  AND kcu.REFERENCED_COLUMN_NAME != ''
  AND kcu.CONSTRAINT_NAME NOT LIKE 'django%'
  AND rc.DELETE_RULE != 'CASCADE';

-- Copy the output, review, and run the ALTER statements to enforce ON DELETE CASCADE.
-- You can automate this in a shell script if you wish.
