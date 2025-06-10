CREATE SEQUENCE IF NOT EXISTS table_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS column_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS question_metadata_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS questions_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS tag_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS trace_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS tracestep_id_sequence START 1;
CREATE SEQUENCE IF NOT EXISTS toolcall_id_sequence START 1;


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

CREATE TABLE IF NOT EXISTS trace (
    id VARCHAR PRIMARY KEY,
    task TEXT NOT NULL,
    enhanced_task TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds DOUBLE,
    final_answer TEXT,
    total_steps INTEGER,
    system_prompt TEXT
);

CREATE TABLE IF NOT EXISTS tracestep (
    id VARCHAR PRIMARY KEY,
    trace_id VARCHAR,
    step_number INTEGER,
    step_type TEXT NOT NULL,

    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds DOUBLE,

    -- Action step specific fields
    model_input TEXT,
    model_output TEXT,
    tool_calls TEXT[],       -- JSON stored as TEXT
    observations TEXT,
    error TEXT,
    action_output TEXT,    -- JSON stored as TEXT

    -- Planning step specific fields
    plan TEXT,

    FOREIGN KEY (trace_id) REFERENCES trace(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tracestep_trace_id ON tracestep(trace_id);
CREATE INDEX IF NOT EXISTS idx_tracestep_step_number ON tracestep(trace_id, step_number);
