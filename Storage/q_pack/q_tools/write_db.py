import psycopg2

def write_db_single(conn, data_dict, table, return_col=""):
    cols= data_dict.keys()
    cols_val_list=['%('+i+')s' for i in cols]
    cols_val=", ".join(cols_val_list)
    cols=", ".join(cols)

    cur = conn.cursor()
    if return_col:
        sql="""INSERT INTO """+table+"""("""+cols+""") VALUES ("""+cols_val+""") RETURNING """+return_col
    else:
        sql="""INSERT INTO """+table+"""("""+cols+""") VALUES ("""+cols_val+""")"""
    cur.executemany(sql,[data_dict])
    cur.execute('SELECT LASTVAL()')
    db_run_id = cur.fetchall()[0][0] # fetching the value returned by ".....RETURNING ___"
    conn.commit()
    if db_run_id:
        return db_run_id

def write_db_dataframe(df, conn, table):    
    list_of_lists = df.values.tolist()  
    tuples_data = [tuple(x) for x in list_of_lists]
    column_str = ','.join(df.columns)
    insert_str = ("%s, " * len(df.columns))[:-2]
    query = "INSERT INTO %s (%s) VALUES (%s)" % (table, column_str, insert_str)
    cur = conn.cursor()
    cur.executemany(query, tuples_data)
    conn.commit()  
