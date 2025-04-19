from core.index import Index
from core._database import InternalDatabase, DatabaseBase


def get_context(
    query, index: Index, internal_db: InternalDatabase, source: DatabaseBase
):
    """
    Basic retrival to obtain most similar obtain generated documenation, and their source schema ( datatypes and so on.).
    """
    similars = index.retrieve(query)
    table_ids = [hit["metadata"]["table_id"] for hit in similars]
    column_ids = [hit["metadata"]["column_id"] for hit in similars]
    docs = internal_db.get_documenation(table_ids=table_ids, column_ids=column_ids)
    table_names = docs.table_name.unique().tolist()
    column_names = docs.column_name.unique().tolist()
    schemas = source.get_table_schema(table_name=table_names)
    schemas = schemas[schemas.column_name.isin(column_names)]
    context = docs.merge(schemas, on=["table_name", "column_name"])
    return context.to_dict(orient="records")
