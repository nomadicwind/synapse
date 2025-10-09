import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    """Create the synapse database and user if they don't exist"""
    try:
        # Connect to PostgreSQL as superuser (usually 'postgres')
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",  # Default superuser
            password=""  # No password by default for local development
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname='synapse'")
        user_exists = cursor.fetchone()
        
        if not user_exists:
            print("Creating user 'synapse'...")
            cursor.execute("CREATE USER synapse WITH PASSWORD 'synapse'")
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='synapse'")
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print("Creating database 'synapse'...")
            cursor.execute("CREATE DATABASE synapse OWNER synapse")
        
        cursor.close()
        conn.close()
        print("Database setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        print("Please make sure PostgreSQL is running and you have superuser access.")
        raise

if __name__ == "__main__":
    create_database()
