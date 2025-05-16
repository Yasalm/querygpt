SELECT
    database AS table_schema,
    table AS table_name,
    name AS column_name,
    type AS data_type,
    default_kind AS default_type,
    default_expression AS default_expression
FROM
    system.columns
WHERE
    database not in ('system', 'information_schema', 'INFORMATION_SCHEMA')
ORDER BY
    database ASC,
    table ASC,
    name ASC;