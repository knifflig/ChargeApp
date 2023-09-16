import sqlite3
import pandas as pd

class SQLite:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def table_exists(self, table_name):
        self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        return bool(self.cursor.fetchone())

    def prompt_to_drop_table(self, table_name):
        while True:
            user_input = input(f"Table {table_name} already exists. All data will be deleted. Would you like to continue? (y/n): ")
            if user_input.lower() == 'y':
                self.drop_table(table_name)
                break
            else:
                print("Operation cancelled.")
                return

    def drop_table(self, table_name):
        self.cursor.execute(f"DROP TABLE {table_name};")
        self.conn.commit()
        print(f"Table {table_name} deleted.")

    def create_table_query(self, table_name, columns):
        column_def = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
        return f"CREATE TABLE {table_name} ({column_def});"

    def execute_create_table(self, create_table_query):
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def create_table(self, table_name, columns):
        if self.table_exists(table_name):
            self.prompt_to_drop_table(table_name)

        create_table_query = self.create_table_query(table_name, columns)
        self.execute_create_table(create_table_query)
        print(f"Table {table_name} created.")

    def create_sub_table(self, table_name, columns, reference_key):
        if not self.table_exists(reference_key['table']):
            print(f"Reference table {reference_key['table']} does not exist.")
            return

        columns.update({f"FOREIGN KEY ({reference_key['column']})": f"REFERENCES {reference_key['table']}({reference_key['reference_column']})"})
        self.create_table(table_name, columns)

    def add_column(self, table_name, column_name, data_type):
        if not self.table_exists(table_name):
            print(f"Table {table_name} does not exist.")
            return

        # Check if column already exists
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [column[1] for column in self.cursor.fetchall()]
        if column_name in existing_columns:
            print(f"Column {column_name} already exists in table {table_name}.")
            return

        # If column does not exist, add it
        try:
            alter_table_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type};"
            self.cursor.execute(alter_table_query)
            self.conn.commit()
            print(f"Column {column_name} added to table {table_name}.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def check_and_filter_columns(self, table_name, data, strict):
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [column[1] for column in self.cursor.fetchall()]
        unrecognized_columns = [col for col in data.keys() if col not in existing_columns]

        if strict and unrecognized_columns:
            raise ValueError(f"Unrecognized column(s) {', '.join(unrecognized_columns)} found in strict mode.")
        
        if not strict:
            for col in unrecognized_columns:
                del data[col]
                print(f"Ignoring unrecognized column: {col}")

        return data

    def handle_data(self, table_name, key_column, data, key_value=None, reference_key=None, strict=True):
        if not self.table_exists(table_name):
            print(f"Table {table_name} does not exist.")
            return

        try:
            data = self.check_and_filter_columns(table_name, data, strict)

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
            
        except Exception as e:
            print(f"An error occurred: {e}")

    def validate_foreign_key(self, reference_key, key_value=None):
        if key_value is None:
            key_value = None 

        self.cursor.execute(
            f"SELECT * FROM {reference_key['table']} WHERE {reference_key['reference_column']} = ?",
            (key_value,)
        )

        if self.cursor.fetchone() is None:
            print(f"No matching row in {reference_key['table']} for FOREIGN KEY {key_value}. Cannot insert into subtable.")
            return False
        return True

    def determine_actual_key_value(self, key_column, data, key_value):
        if key_value is None and key_column not in data:
            raise ValueError("Key value must either be provided as an argument or exist in the data dictionary.")
        if key_value is not None and key_column in data:
            raise ValueError("Key value should not be provided both as an argument and in the data dictionary.")
        
        return key_value if key_value is not None else data[key_column]

    def check_existing_row(self, table_name, key_column, actual_key_value):
        self.cursor.execute(f"SELECT * FROM {table_name} WHERE {key_column} = ?", (actual_key_value,))
        return self.cursor.fetchone()

    def insert_new_row(self, table_name, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        self.cursor.execute(insert_query, list(data.values()))

    def update_existing_row(self, table_name, key_column, actual_key_value, data):
        update_pairs = ', '.join([f"{col} = ?" for col in data.keys()])
        update_query = f"UPDATE {table_name} SET {update_pairs} WHERE {key_column} = ?"
        self.cursor.execute(update_query, list(data.values()) + [actual_key_value])

    def insert_data(self, table_name, key_column, data, key_value=None, reference_key=None, strict=True):
        if isinstance(data, list):
            for obj in data:
                self.handle_data(table_name, key_column, obj, key_value, reference_key, strict)
        else:
            self.handle_data(table_name, key_column, data, key_value, reference_key, strict)
