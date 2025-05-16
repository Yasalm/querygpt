select col.owner as table_schema,
       col.table_name,
       col.column_name,
       col.data_type,
       col.nullable,
       col.data_length,
       col.data_precision,
       col.data_scale,
       case
          when pk.constraint_type = 'P' then
             'PRIMARY KEY'
          when fk.constraint_type = 'R' then
             'FOREIGN KEY'
          else
             'NO CONSTRAINT'
       end as constraint_type,
       case
          when fk.constraint_type = 'R' then
             fk_ref.r_owner
             || '.'
             || fk_ref.r_table_name
             || '.'
             || fk_ref.r_column_name
          else
             null
       end as foreign_key_reference
  from all_tab_columns col
  left join (
   select acc.owner,
          acc.table_name,
          acc.column_name,
          ac.constraint_type
     from all_constraints ac
     join all_cons_columns acc
   on ac.constraint_name = acc.constraint_name
      and ac.owner = acc.owner
    where ac.constraint_type = 'P'
) pk
on col.owner = pk.owner
   and col.table_name = pk.table_name
   and col.column_name = pk.column_name
  left join (
   select acc.owner,
          acc.table_name,
          acc.column_name,
          ac.constraint_type,
          ac.constraint_name
     from all_constraints ac
     join all_cons_columns acc
   on ac.constraint_name = acc.constraint_name
      and ac.owner = acc.owner
    where ac.constraint_type = 'R'
) fk
on col.owner = fk.owner
   and col.table_name = fk.table_name
   and col.column_name = fk.column_name
  left join (
   select ac.owner,
          acc.table_name,
          acc.column_name,
          ccu.owner as r_owner,
          ccu.table_name as r_table_name,
          ccu.column_name as r_column_name
     from all_constraints ac
     join all_cons_columns acc
   on ac.constraint_name = acc.constraint_name
      and ac.owner = acc.owner
     join all_cons_columns ccu
   on ac.r_constraint_name = ccu.constraint_name
      and ac.owner = ccu.owner
    where ac.constraint_type = 'R'
) fk_ref
on col.owner = fk_ref.owner
   and col.table_name = fk_ref.table_name
   and col.column_name = fk_ref.column_name
 where col.owner not in ( 'SYS',
                          'SYSTEM',
                          'C##DBA_YAA',
                          'CTXSYS',
                          'DBSNMP',
                          'DVSYS',
                          'GSMADMIN_INTERNAL',
                          'LBACSYS',
                          'MDSYS',
                          'OLAPSYS',
                          'ORDDATA',
                          'ORDDATA',
                          'ORDSYS',
                          'OUTLN',
                          'WMSYS',
                          'XDB' )
 order by col.owner,
          col.table_name,
          col.column_name