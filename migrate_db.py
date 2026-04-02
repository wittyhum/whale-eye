import mysql.connector
from config import Settings
import logging

def migrate():
    s = Settings.from_env()
    try:
        conn = mysql.connector.connect(
            host=s.db_host,
            port=s.db_port,
            user=s.db_user,
            password=s.db_password,
            database=s.db_name
        )
        cursor = conn.cursor()
        try:
            cursor.execute('ALTER TABLE whales ADD COLUMN last_active_at TIMESTAMP NULL AFTER tx_count')
            conn.commit()
            print('Column last_active_at added successfully')
        except mysql.connector.Error as err:
            if err.errno == 1060:
                print('Column last_active_at already exists')
            else:
                print(f'Error: {err}')
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print(f'Connection failed: {e}')

if __name__ == "__main__":
    migrate()
