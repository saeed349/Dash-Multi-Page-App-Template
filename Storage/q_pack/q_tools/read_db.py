import psycopg2

def read_db_single(sql,conn):
    cur = conn.cursor()
    cur.execute(sql)
    results = cur.fetchall()
    try:
        results = results[0][0]
        return results
    except: 
        return ""