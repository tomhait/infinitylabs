USE oulad_db;

# Load Courses
LOAD DATA INFILE '/var/lib/mysql-files/data/courses.csv'
INTO TABLE courses
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;

# Load Assessments
LOAD DATA INFILE '/var/lib/mysql-files/data/assessments.csv'
INTO TABLE assessments
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(code_module, code_presentation, id_assessment, assessment_type, @vdate, weight)
SET date = NULLIF(@vdate, '');

# Load Student Info
LOAD DATA INFILE '/var/lib/mysql-files/data/studentInfo.csv'
INTO TABLE student_info
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;

# Load VLE
LOAD DATA INFILE '/var/lib/mysql-files/data/vle.csv'
INTO TABLE vle
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(id_site, code_module, code_presentation, activity_type, @week_from, @week_to)
SET week_from = NULLIF(@week_from, ''),
	week_to = NULLIF(@week_to, '');

# Load Student Assessments
LOAD DATA INFILE '/var/lib/mysql-files/data/studentAssessment.csv'
INTO TABLE student_assessment
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(id_assessment, id_student, date_submitted, is_banked, @score)
SET score = NULLIF(@score, '');


# Load Student Registration
LOAD DATA INFILE '/var/lib/mysql-files/data/studentRegistration.csv'
INTO TABLE student_registration
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS
(code_module, code_presentation, id_student, @date_registration, @date_unregistration)
SET date_unregistration = NULLIF(@date_unregistration, ''),
	date_registration = NULLIF(@date_registration, '');

# Load Student VLE
SET FOREIGN_KEY_CHECKS = 0;

LOAD DATA INFILE '/var/lib/mysql-files/data/studentVle.csv'
INTO TABLE student_vle
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 ROWS;

SET FOREIGN_KEY_CHECKS = 1;
