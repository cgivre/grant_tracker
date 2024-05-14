import logging
import sqlite3

from millify import millify
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine


class Utils:
    DATABASE_PATH = 'static/data/database.db'

    def __init__(self):
        # Check and see if the database file is there, and create one if not.

        if not Path(self.DATABASE_PATH).is_file():
            self.conn = sqlite3.connect(self.DATABASE_PATH, isolation_level=None)
            self.__create_database()
        else:
            self.conn = sqlite3.connect(self.DATABASE_PATH, isolation_level=None)

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

    def create_grant(self, grant_name: str, grant_description: str,
                     grant_start_date: str, grant_end_date: str,
                     grant_amount: float, grant_categories: list) -> bool:
        """
        Adds a grant to the Grant Tracker Database
        :param grant_name: The grant name
        :param grant_description: A description of the grant.
        :param grant_start_date: The grant start date in yyyy-MM-dd format
        :param grant_end_date: The grant end date in yyyy-MM-dd format
        :param grant_amount: The grant amount
        :param grant_categories: A list of categories for the grant.
        :return:
        """
        # Validate Grant info
        if grant_amount <= 0:
            raise ValueError('Grant amount must be greater than zero')
        elif grant_name == "" or grant_description == "":
            raise ValueError('Grant name or description cannot be empty')
        elif grant_start_date == "" or grant_end_date == "":
            raise ValueError('Grant start date and end date cannot be empty')

        # Insert grant into database
        category_list = ', '.join(grant_categories)
        sql = (
            f"INSERT INTO grants (grant_name, grant_description, grant_start_date, grant_end_date, grant_amount, grant_categories) "
            f"VALUES ('{grant_name}','{grant_description}', '{grant_start_date}', '{grant_end_date}', '{grant_amount}','{category_list}')")
        logging.debug(sql)

        try:
            self.conn.execute(sql)
        except Exception as e:
            raise e

        return True

    def get_grants(self) -> pd.DataFrame:
        sql = "SELECT * FROM grants"

        result = pd.read_sql(sql, self.conn)
        return result

    def get_total_available_grants(self):
        sql = "SELECT SUM(grant_amount) as total FROM grants"
        result = pd.read_sql(sql, self.conn)
        total = result['total'].values[0]
        return millify(total, precision=0)



if __name__ == '__main__':
    utils = Utils()
    utils.close_connection()
