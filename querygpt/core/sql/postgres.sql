SELECT
    col.table_schema,
    col.table_name,
    col.column_name,
    col.data_type,
    col.is_nullable,
    col.character_maximum_length,
    col.numeric_precision,
    col.numeric_scale,
    CASE
        WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY'
        WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY'
        ELSE 'NO CONSTRAINT'
    END AS constraint_type,
    CASE
        WHEN fk.column_name IS NOT NULL THEN
            fk_ref.referenced_table || '.' || fk_ref.referenced_column
        ELSE
            NULL
    END AS foreign_key_reference
FROM
    information_schema.columns col
LEFT JOIN (
    SELECT
        kcu.table_schema,
        kcu.table_name,
        kcu.column_name
    FROM
        information_schema.key_column_usage kcu
    JOIN information_schema.table_constraints tc
        ON kcu.constraint_name = tc.constraint_name
    WHERE
        tc.constraint_type = 'PRIMARY KEY'
) pk
    ON col.table_schema = pk.table_schema
    AND col.table_name = pk.table_name
    AND col.column_name = pk.column_name
LEFT JOIN (
    SELECT
        kcu.table_schema,
        kcu.table_name,
        kcu.column_name
    FROM
        information_schema.key_column_usage kcu
    JOIN information_schema.table_constraints tc
        ON kcu.constraint_name = tc.constraint_name
    WHERE
        tc.constraint_type = 'FOREIGN KEY'
) fk
    ON col.table_schema = fk.table_schema
    AND col.table_name = fk.table_name
    AND col.column_name = fk.column_name
LEFT JOIN (
    SELECT
        kcu.table_schema,
        kcu.table_name AS referencing_table,
        kcu.column_name AS referencing_column,
        ccu.table_name AS referenced_table,
        ccu.column_name AS referenced_column
    FROM
        information_schema.key_column_usage kcu
    JOIN information_schema.table_constraints tc
        ON kcu.constraint_name = tc.constraint_name
    JOIN information_schema.constraint_column_usage ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE
        tc.constraint_type = 'FOREIGN KEY'
) fk_ref
    ON fk.table_schema = fk_ref.table_schema
    AND fk.table_name = fk_ref.referencing_table
    AND fk.column_name = fk_ref.referencing_column
WHERE
    col.table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY
    col.table_schema,
    col.table_name,
    col.column_name;