from psycopg2 import sql


def get_col_names(cur, table_name):
    col_names_str = "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE "
    col_names_str += "table_name = '{}';".format(table_name)
    cur.execute(col_names_str)

    sql_object = sql.SQL(
        # pass SQL statement to sql.SQL() method
        col_names_str
    ).format(
        # pass the identifier to the Identifier() method
        sql.Identifier(table_name)
    )

    # execute the SQL string to get list with col names in a tuple
    cur.execute(sql_object)

    # get the tuple element from the list
    col_names = (cur.fetchall())

    # return column names as a list of strings, rather than list of tuples
    new_names = [name[0] for name in col_names]
    # print("Column names:", new_names)
    return new_names

