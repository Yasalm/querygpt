CREATE SEQUENCE IF NOT EXISTS table_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS column_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS question_metadata_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS questions_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS tag_id_sequence START 1;


-- Probably need better namings for all :(
CREATE TABLE IF NOT EXISTS table_metadata (
    id INTEGER DEFAULT nextval('table_id_sequence'),
    table_name VARCHAR,
    bussines_summary VARCHAR,
    possible_usages VARCHAR,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS column_metadata (
    id INTEGER DEFAULT nextval('column_id_sequence'),
    table_id INTEGER,
    column_name VARCHAR,
    column_details_summary VARCHAR,
    bussines_summary VARCHAR,
    possible_usages VARCHAR,
    tags VARCHAR[],
    PRIMARY KEY (id)
);


-- CREATE TABLE IF NOT EXISTS question_metadata (
--     id INTEGER DEFAULT nextval('question_metadata_id_sequence'),
--     question_title VARCHAR,
--     question VARCHAR,
--     question_outcome VARCHAR,
--     PRIMARY KEY (id)
-- );

-- CREATE TABLE IF NOT EXISTS questions (
--     id INTEGER DEFAULT nextval('questions_id_sequence'),
--     question_metadata_id INTEGER,
--     table_id INTEGER,
--     column_id INTEGER,
--     PRIMARY KEY (id)
-- );