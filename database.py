import os
import mysql.connector
from mysql.connector import Error


def history_scraper_open_database_connection():
    try:
        password = os.getenv("MYSQL_PASSWORD")

        if not password:
            print("MySQL password not found.")
            print("Set the MYSQL_PASSWORD environment variable first.")
            return None

        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password=password,
            database="world_history_db"
        )

        if connection.is_connected():
            print("Connected to World History database successfully!")
            return connection

    except Error as error:
        print(f"Database connection failed: {error}")

    return None


def history_scraper_close_database_connection(connection):
    try:
        if connection and connection.is_connected():
            connection.close()
            print("Database connection closed successfully.")

    except Error as error:
        print(f"Error closing database connection: {error}")