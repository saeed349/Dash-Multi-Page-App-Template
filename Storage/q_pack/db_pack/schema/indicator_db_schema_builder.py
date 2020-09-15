

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import q_credentials.db_indicator_cred as db_indicator_cred
# import q_credentials.db_indicator_cloud_cred as db_indicator_cred


def create_db(db_credential_info):
    """
    create a new database if it does not exist in the PostgreSQL database
    will use method 'check_db_exists' before creating a new database
    args:
        db_credential_info: database credentials including host, user, password and db name, type array
    returns:
        NoneType
    """
    db_host, db_user, db_password, db_name = db_credential_info
    
    
    if check_db_exists(db_credential_info):
        pass
    else:
        print('Creating new database.')
        # Here we are connecting to the existing DB to create a new DB
        conn = psycopg2.connect(host=db_host, database='postgres', user=db_user, password=db_password)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("CREATE DATABASE %s  ;" % db_name)
        cur.close()

        
def check_db_exists(db_credential_info):
    """
    checks to see if a database already exists in the PostgreSQL database
    args:
        db_credential_info: database credentials including host, user, password and db name, type array
    returns:
        boolean value (True or False)
    """
    db_host, db_user, db_password, db_name = db_credential_info
    try:
        conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)
        cur = conn.cursor()
        cur.close()
        print('Database exists.')
        return True
    except:
        print("Indicator Database does not exist.")
        return False

       
def create_mkt_tables(db_credential_info):
    """
    create table in designated PostgreSQL database
    will use method 'check_db_exists' before creating table
    args:
        db_credential_info: database credentials including host, user, password and db name, type array
    returns:
        NoneType
    """
    db_host, db_user, db_password, db_name = db_credential_info
    conn = None
    
    if check_db_exists(db_credential_info):
        commands = (
                    """
                    CREATE TABLE indicator (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        period INTEGER NULL,
                        created_date TIMESTAMP NOT NULL,
                        last_updated_date TIMESTAMP NOT NULL
                        )
                    """,
                    """
                    CREATE TABLE symbol (
                        id SERIAL PRIMARY KEY,
                        ticker TEXT NOT NULL,
                        instrument TEXT NOT NULL,
                        name TEXT NOT NULL,
                        currency VARCHAR(64) NULL,
                        created_date TIMESTAMP NOT NULL
                        )
                    """,
                    """
                    CREATE TABLE m1_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE m5_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE m15_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE m30_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE h1_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE h4_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE d_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE w_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """,
                    """
                    CREATE TABLE m_data (
                        id SERIAL PRIMARY KEY,
                        indicator_id INTEGER NOT NULL,
                        symbol_id INTEGER NOT NULL,
                        created_date TIMESTAMP NOT NULL,
                        date_price TIMESTAMP,
                        value json NULL,
                        FOREIGN KEY (indicator_id) REFERENCES indicator(id),
                        FOREIGN KEY (symbol_id) REFERENCES symbol(id)
                        )
                    """)
        try:
            for command in commands:
                print('Building tables.')
                conn = psycopg2.connect(host=db_host,database=db_name, user=db_user, password=db_password)
                cur = conn.cursor()
                cur.execute(command)
                # need to commit this change
                conn.commit()
                cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            cur.close()
        finally:
            if conn:
                conn.close()
    else:
        pass

    



def main():
    db_host=db_indicator_cred.dbHost 
    db_user=db_indicator_cred.dbUser
    db_password=db_indicator_cred.dbPWD
    db_name=db_indicator_cred.dbName
    
    # first lets create our database from postgres
    create_db([db_host, db_user, db_password, db_name])
    
    # second lets create our tables for our new database
    create_mkt_tables([db_host, db_user, db_password, db_name])

    
if __name__ == "__main__":
    main()