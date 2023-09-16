"""
This module provides a SQLite class to handle SQLite database operations.
"""

import sqlite3

class SQLite:
    """
    A class used to represent SQLite operations.
    """

    def __init__(self, db_name):
        """
        Initializes SQLite object with database name.

        Parameters:
        db_name (str): The name of the SQLite database.
        """
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """
        Enter method for context manager.
        """
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit method for context manager.
        """
        if self.conn:
            self.conn.close()

    def table_exists(self, table_name):
        """
        Checks if a table exists in the database.

        Parameters:
        table_name (str): The name of the table.

        Returns:
        bool: True if table exists, False otherwise.
        """
        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE \
                type='table' AND name='{table_name}';")
        except sqlite3.Error as err:
            print(f"An error occurred: {err}")
            return False
        return bool(self.cursor.fetchone())

    def prompt_to_drop_table(self, table_name):
        """
        Prompts the user whether to drop an existing table.

        Parameters:
        table_name (str): The name of the table.
        """
        while True:
            user_input = input(f"Table {table_name} already exists. \
                               All data will be deleted. Would you like to continue? (y/n): ")
            if user_input.lower() == 'y':
                self.drop_table(table_name)
                break
            if user_input.lower() == 'n':
                print("Operation cancelled.")
                return

            print("Invalid input. Please enter 'y' or 'n'.")

    def drop_table(self, table_name):
        """
        Drops a table from the database.

        Parameters:
        table_name (str): The name of the table to drop.
        """
        try:
            self.cursor.execute(f"DROP TABLE {table_name};")
            self.conn.commit()
            print(f"Table {table_name} deleted.")
        except sqlite3.Error as err:
            print(f"An error occurred: {err}")

    def create_table_query(self, table_name, columns):
        """
        Creates a SQL query string to create a new table.

        Parameters:
        table_name (str): The name of the new table.
        columns (dict): Dictionary containing column names and data types.

        Returns:
        str: SQL query string.
        """
        column_def = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
        return f"CREATE TABLE {table_name} ({column_def});"

    def execute_create_table(self, create_table_query):
        """
        Executes the SQL query to create a table.

        Parameters:
        create_table_query (str): The SQL query to execute.
        """
        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
        except sqlite3.Error as err:
            print(f"An error occurred: {err}")

    def create_table(self, table_name, columns):
        """
        Creates a table if it does not already exist.

        Parameters:
        table_name (str): The name of the table to create.
        columns (dict): The columns and their data types.
        """
        if self.table_exists(table_name):
            self.prompt_to_drop_table(table_name)
        else:
            create_table_query = self.create_table_query(table_name, columns)
            self.execute_create_table(create_table_query)
            print(f"Table {table_name} created.")

    def create_sub_table(self, table_name, columns, reference_key):
        """
        Creates a sub-table with a foreign key reference to another table.

        Parameters:
        table_name (str): The name of the sub-table.
        columns (dict): The columns and their data types.
        reference_key (dict): Information about the foreign key reference.
        """
        if not self.table_exists(reference_key['table']):
            print(f"Reference table {reference_key['table']} does not exist.")
            return
        columns.update({
            f"FOREIGN KEY ({reference_key['column']})": (
                f"REFERENCES {reference_key['table']}({reference_key['reference_column']})"
            )
        })
        self.create_table(table_name, columns)

    def add_column(self, table_name, column_name, data_type):
        """
        Adds a new column to an existing table.

        Parameters:
        table_name (str): The name of the table.
        column_name (str): The name of the new column.
        data_type (str): The data type of the new column.
        """
        if not self.table_exists(table_name):
            print(f"Table {table_name} does not exist.")
            return

        try:
            alter_table_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type};"
            self.cursor.execute(alter_table_query)
            self.conn.commit()
            print(f"Column {column_name} added to table {table_name}.")
        except sqlite3.Error as err:
            print(f"An error occurred: {err}")

    def check_and_filter_columns(self, table_name, data, strict):
        """
        Checks and filters columns based on their existence in the table schema.

        Parameters:
        table_name (str): The name of the table.
        data (dict): The data to insert or update.
        strict (bool): If True, raises an error for unrecognized columns.

        Returns:
        dict: Filtered data dictionary.
        """
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [column[1] for column in self.cursor.fetchall()]
        unrecognized_columns = [col for col in data.keys() if col not in existing_columns]

        if strict and unrecognized_columns:
            raise ValueError(f"Unrecognized column(s)\
                              {', '.join(unrecognized_columns)} found in strict mode.")

        if not strict:
            for col in unrecognized_columns:
                del data[col]
                print(f"Ignoring unrecognized column: {col}")

        return data

    def handle_data(self, table_name, key_column, data,
                    key_value=None, reference_key=None, strict=True):
        """
        Inserts or updates a row in the table based on the key.

        Parameters:
        table_name (str): The name of the table.
        key_column (str): The primary key column name.
        data (dict): The data to insert or update.
        key_value (str): The key value to use for the operation.
        reference_key (dict): Information about the foreign key reference.
        strict (bool): If True, raises an error for unrecognized columns.
        """
        if not self.table_exists(table_name):
            print(f"Table {table_name} does not exist.")
            return

        try:
            data = self.check_and_filter_columns(table_name, data, strict)

        except ValueError as value_error:
            print(f"Value error: {value_error}")
            return

        try:
            if reference_key:
                self.validate_foreign_key(reference_key, key_value)

            actual_key_value = self.determine_actual_key_value(key_column, data, key_value)
            existing_row = self.check_existing_row(table_name, key_column, actual_key_value)

            if existing_row is None:
                self.insert_new_row(table_name, data)
            else:
                self.update_existing_row(table_name, key_column, actual_key_value, data)

            self.conn.commit()
            print(f"Data inserted or updated in table {table_name}.")

        except sqlite3.Error as sql_error:
            print(f"SQLite error occurred: {sql_error}")


    def validate_foreign_key(self, reference_key, key_value=None):
        """
        Validates if the given foreign key exists in the reference table.

        Parameters:
            reference_key (dict): The foreign key details.
            key_value (Optional[Any]): The value of the foreign key.

        Returns:
            bool: True if valid, otherwise False.
        """
        try:
            if key_value is None:
                key_value = None
            query = f"SELECT * FROM {reference_key['table']}\
                WHERE {reference_key['reference_column']} = ?"

            self.cursor.execute(query, (key_value,))
            if self.cursor.fetchone() is None:
                print(f"No matching row in {reference_key['table']}\
                      for FOREIGN KEY {key_value}. Cannot insert into subtable.")
                return False
            return True

        except Exception as error:# pylint: disable=W0718
            print(f"An error occurred in validate_foreign_key: {error}")
            return False

    def determine_actual_key_value(self, key_column, data, key_value):
        """
        Determines the actual key value to use.

        Parameters:
            key_column (str): The name of the primary key column.
            data (dict): Data dictionary.
            key_value (Optional[Any]): Provided key value.

        Returns:
            Any: Actual key value.
        """
        try:
            if key_value is None and key_column not in data:
                raise ValueError("Key value must either be provided\
                                  as an argument or exist in the data dictionary.")
            if key_value is not None and key_column in data:
                raise ValueError("Key value should not be provided\
                                  both as an argument and in the data dictionary.")
            return key_value if key_value is not None else data[key_column]
        except ValueError as value_error:
            print(f"ValueError occurred: {value_error}")
            return None

    def check_existing_row(self, table_name, key_column, actual_key_value):
        """
        Checks if a row with the given key value exists in the table.

        Parameters:
            table_name (str): Table name.
            key_column (str): Primary key column name.
            actual_key_value (Any): Key value to check.

        Returns:
            Any: Row if exists, otherwise None.
        """

        try:
            query = f"SELECT * FROM {table_name} WHERE {key_column} = ?"
            self.cursor.execute(query, (actual_key_value,))
            return self.cursor.fetchone()

        except Exception as error:# pylint: disable=W0718
            print(f"An error occurred in check_existing_row: {error}")
            return None

    def insert_new_row(self, table_name, data):
        """
        Inserts a new row into a table.

        Parameters:
        table_name (str): The name of the table.
        data (dict): Data to be inserted.
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            self.cursor.execute(insert_query, list(data.values()))
        except sqlite3.Error as error:
            print(f"An error occurred: {error}")

    def update_existing_row(self, table_name, key_column, actual_key_value, data):
        """
        Updates an existing row in a table.

        Parameters:
        table_name (str): The name of the table.
        key_column (str): The name of the primary key column.
        actual_key_value: The value of the primary key.
        data (dict): Data to be updated.
        """
        try:
            update_pairs = ', '.join([f"{col} = ?" for col in data.keys()])
            update_query = f"UPDATE {table_name} SET {update_pairs} WHERE {key_column} = ?"
            self.cursor.execute(update_query, list(data.values()) + [actual_key_value])
        except sqlite3.Error as error:
            print(f"An error occurred: {error}")

    def insert_data(self, table_name, key_column, data,
                    key_value=None, reference_key=None, strict=True):
        """
        Inserts data into a table. Can handle single or multiple rows.

        Parameters:
        table_name (str): The name of the table.
        key_column (str): The name of the primary key column.
        data (Union[dict, list]): The data to be inserted.
        key_value (Optional[Any]): The value of the primary key.
        reference_key (Optional[dict]): The reference key details.
        strict (bool): If True, strict column matching is enforced.
        """
        try:
            if isinstance(data, list):
                for obj in data:
                    self.handle_data(table_name, key_column, obj, key_value, reference_key, strict)
            else:
                self.handle_data(table_name, key_column, data, key_value, reference_key, strict)

        except Exception as error:# pylint: disable=W0718
            print(f"An error occurred: {error}")
