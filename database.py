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


def history_scraper_save_year_events(connection, events, year):
    if not connection or not connection.is_connected():
        print("Cannot save events: database connection is unavailable.")
        return False

    if not events:
        print("No events available to save.")
        return False

    event_records = []

    for event in events:
        if event.get("event_year") != year:
            continue

        event_date = event.get("event_date") or None

        event_records.append(
            (
                event.get("event_title"),
                event_date,
                event.get("event_year"),
                event.get("category"),
                event.get("description") or None,
                event.get("source_url"),
                event.get("source_name"),
                event.get("review_reason") or None
            )
        )

    if not event_records:
        print(f"No matching events found for {year}.")
        return False

    cursor = None

    try:
        cursor = connection.cursor()

        delete_query = """
            DELETE FROM historical_events
            WHERE event_year = %s
        """

        insert_query = """
            INSERT INTO historical_events (
                event_title,
                event_date,
                event_year,
                category,
                description,
                source_url,
                source_name,
                review_reason
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(delete_query, (year,))

        cursor.executemany(insert_query, event_records)

        saved_count = cursor.rowcount

        connection.commit()

        print(
            f"Successfully saved {saved_count} events "
            f"for {year} in MySQL."
        )

        return True

    except Error as error:
        connection.rollback()
        print(f"Could not save events to MySQL: {error}")
        return False

    finally:
        if cursor:
            cursor.close()


def history_scraper_close_database_connection(connection):
    try:
        if connection and connection.is_connected():
            connection.close()
            print("Database connection closed successfully.")

    except Error as error:
        print(f"Error closing database connection: {error}")
