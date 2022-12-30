-- CREATE DATABASE hormone_levels;
USE hormone_levels;

CREATE TABLE levels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hdl FLOAT,
    ldl FLOAT,
    luteinizing_hormone FLOAT,
    total_testosterone FLOAT,
    shbg FLOAT,
    free_testosterone FLOAT,
    igf1 FLOAT
);
