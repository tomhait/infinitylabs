CREATE DATABASE oulad_db;
USE oulad_db;

CREATE TABLE courses (
    code_module VARCHAR(10),
    code_presentation VARCHAR(10),
    module_presentation_length INTEGER,
    PRIMARY KEY (code_module, code_presentation)
);

CREATE TABLE assessments (
    code_module VARCHAR(10),
    code_presentation VARCHAR(10),
    id_assessment INTEGER PRIMARY KEY,
    assessment_type VARCHAR(5),
    date INTEGER,
    weight NUMERIC(5,2),
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

CREATE TABLE vle (
    id_site INTEGER PRIMARY KEY,
    code_module VARCHAR(10),
    code_presentation VARCHAR(10),
    activity_type VARCHAR(50),
    week_from INTEGER,
    week_to INTEGER,
    FOREIGN KEY (code_module, code_presentation) REFERENCES courses(code_module, code_presentation)
);

CREATE TABLE student_info (
    code_module VARCHAR(10),
    code_presentation VARCHAR(10),
    id_student INTEGER,
    gender CHAR(1),
    region VARCHAR(50),
    highest_education VARCHAR(50),
    imd_band VARCHAR(10),
    age_band VARCHAR(10),
    num_of_prev_attempts INTEGER,
    studied_credits INTEGER,
    disability CHAR(1),
    final_result VARCHAR(20),
    PRIMARY KEY (id_student, code_module, code_presentation)
);

CREATE TABLE student_registration (
    code_module VARCHAR(10),
    code_presentation VARCHAR(10),
    id_student INTEGER,
    date_registration INTEGER,
    date_unregistration INTEGER,
    FOREIGN KEY (id_student, code_module, code_presentation) REFERENCES student_info(id_student, code_module, code_presentation)
);

CREATE TABLE student_assessment (
    id_assessment INTEGER,
    id_student INTEGER,
    date_submitted INTEGER,
    is_banked BOOLEAN,
    score INTEGER,
    PRIMARY KEY (id_assessment, id_student),
    FOREIGN KEY (id_assessment) REFERENCES assessments(id_assessment)
);

CREATE TABLE student_vle (
    code_module VARCHAR(10),
    code_presentation VARCHAR(10),
    id_student INTEGER,
    id_site INTEGER,
    date INTEGER,
    sum_click INTEGER,
    FOREIGN KEY (id_site) REFERENCES vle(id_site),
    FOREIGN KEY (id_student, code_module, code_presentation) REFERENCES student_info(id_student, code_module, code_presentation)
);
