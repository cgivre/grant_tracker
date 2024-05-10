import sqlite3
from pathlib import Path


class Utils:
    DATABASE_PATH = '../static/data/database.db'

    def __init__(self):
        # Check and see if the database file is there, and create one if not.

        if not Path(self.DATABASE_PATH).is_file():
            self.conn = sqlite3.connect(self.DATABASE_PATH)
            self.__create_database()
        else:
            self.conn = sqlite3.connect(self.DATABASE_PATH)

    def close_connection(self):
        self.conn.close()

    def __create_database(self) -> bool:
        """
        Initializes the database with the correct tables and columns
        :return: False if anything goes wrong, True otherwise
        """
        grant_table_query = """
        CREATE TABLE IF NOT EXISTS grants (
            grant_id INTEGER PRIMARY KEY AUTOINCREMENT,
            grant_name TEXT,
            grant_description TEXT,
            grant_start_date TEXT,
            grant_end_date TEXT,
            grant_amount NUMERIC(10,2),
            grant_categories TEXT
        );
        """
        cursor = self.conn.cursor()
        cursor.execute(grant_table_query)

        # Now create the invoice table
        invoice_table_query = """
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            grant_id INTEGER,
            vendor_name TEXT,
            invoice_date TEXT,
            invoice_amount NUMERIC(10,2),
            invoice_categories TEXT,
            invoice_description TEXT,
            invoice_receipt_location TEXT,
            FOREIGN KEY(grant_id) REFERENCES grants(grant_id)
                ON DELETE CASCADE
        );
        """
        cursor.execute(invoice_table_query)
        return True


if __name__ == '__main__':
    utils = Utils()
    utils.close_connection()
