import logging
import sqlite3

from millify import millify
import pandas as pd
from pathlib import Path
import streamlit as st

streamlit_root_logger = logging.getLogger(st.__name__)


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
        streamlit_root_logger.debug(sql)

        try:
            self.conn.execute(sql)
        except Exception as e:
            streamlit_root_logger.error(e)
            raise False

        return True

    def create_invoice(self, grant_name: str,
                       vendor_name: str,
                       invoice_categories: str,
                       invoice_date: str,
                       invoice_amount: float,
                       invoice_description: str,
                       invoice_image: str) -> bool:

        # Get the grant id
        grant_id = self.get_grant_id(grant_name)
        sql = (f"INSERT INTO invoices (grant_id, vendor_name, invoice_date, invoice_amount, invoice_categories, invoice_description, invoice_receipt_location) "
               f"VALUES({grant_id},'{vendor_name}','{invoice_date}','{invoice_amount}','{invoice_categories}','{invoice_description}', '{invoice_image}')")
        streamlit_root_logger.debug(sql)

        try:
            self.conn.execute(sql)
        except Exception as e:
            streamlit_root_logger.error(e)
            return False
        return True

    def get_grants(self) -> pd.DataFrame:
        sql = """SELECT grant_name, grant_amount, grant_categories,
                   grant_description, grant_start_date, grant_end_date,
                   COALESCE(invoice_count,0) AS invoice_count, COALESCE(invoiced_total,0) AS invoiced_total
                FROM grants
                LEFT JOIN (
                    SELECT grant_id, COALESCE(SUM(invoice_amount),0) AS invoiced_total, COUNT(*) AS invoice_count
                    FROM invoices
                    GROUP BY grant_id
                ) AS invoice_stats ON invoice_stats.grant_id = grants.grant_id"""
        result = pd.read_sql(sql, self.conn)

        # Convert Dates to Date objects
        result['grant_start_date'] = pd.to_datetime(result['grant_start_date'])
        result['grant_end_date'] = pd.to_datetime(result['grant_end_date'])
        result['days_remaining'] = (result['grant_end_date'] - pd.to_datetime('today')).dt.days

        return result

    def get_grant_id(self, grant_name: str) -> int:
        sql = f"SELECT grant_id FROM grants WHERE grant_name = '{grant_name}'"
        result = pd.read_sql(sql, self.conn)
        return result['grant_id'].values[0]

    def get_invoices(self, grant_id: int) -> pd.DataFrame:
        sql = f"SELECT * FROM invoices WHERE grant_id = {grant_id}"
        result = pd.read_sql(sql, self.conn)
        return result

    def get_total_available_grants(self) -> str:
        sql = "SELECT SUM(grant_amount) as total FROM grants"
        result = pd.read_sql(sql, self.conn)
        total = result['total'].values[0]
        return millify(total, precision=0)

    def get_available_funding(self) -> float:
        sql = """SELECT SUM(grant_amount) - SUM(invoice_amount) AS remaining_funding
            FROM grants
            LEFT JOIN invoices ON invoices.grant_id = grants.grant_id"""

        result = pd.read_sql(sql, self.conn)
        return result['remaining_funding'].values[0]

    @staticmethod
    def list_to_string(the_list: list) -> str:
        if the_list is None:
            return ""

        return ','.join(the_list)
