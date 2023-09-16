"""SQLiteFetcher: A Python class to fetch data from SQLite tables."""

import sqlite3
from typing import List, Dict, Any, Optional
import json

class SQLiteFetcher:
    """SQLiteFetcher class for handling SQLite queries."""

    def __init__(self, db_name: str, kreisid: Optional[List[Any]] = None):
        """
        Initialize SQLiteFetcher object.

        Parameters:
            db_name (str): The name of the SQLite database.
            kreisid (List[Any], optional): The list of 'kreisid' values.
        """
        self.db_name = db_name
        self.kreisid = self._process_kreisid(kreisid)
        self.conn = None
        self.cursor = None

    def _process_kreisid(self, kreisid: Optional[List[Any]]) -> List[str]:
        """Converts 'kreisid' to a list of strings."""
        if kreisid is None:
            return []
        if not isinstance(kreisid, list):
            kreisid = [kreisid]
        return [str(k) for k in kreisid]

    def __enter__(self):
        """Create SQLite connection and cursor on entering the context."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as error:
            print(f"SQLite error occurred: {error}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close SQLite connection on exiting the context."""
        if self.conn:
            self.conn.close()

    def table_exists(self, table_name: str) -> bool:
        """Check if the table exists in the database."""
        try:
            self.cursor.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"
            )
            return bool(self.cursor.fetchone())
        except sqlite3.Error as error:
            print(f"SQLite error occurred: {error}")
            return False

    def fetch_kreise(self, **kwargs: Any) -> List[Any]:
        """Fetch rows from 'kreis_table' based on given conditions."""

        where_clauses = []
        values = []

        for key, value in kwargs.items():
            if isinstance(value, tuple):
                operator, actual_value = value
                where_clauses.append(f"{key} {operator} ?")
                values.append(actual_value)
            else:
                where_clauses.append(f"{key} = ?")
                values.append(value)

        if self.kreisid:
            kreisid_conditions = ", ".join(["?" for _ in self.kreisid])
            where_clauses.append(f"KREISID IN ({kreisid_conditions})")
            values.extend(self.kreisid)

        where_clause = " AND ".join(where_clauses)
        query = "SELECT * FROM kreis_table"

        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            self.cursor.execute(query, tuple(values))
            rows = self.cursor.fetchall()

            # Fetch column names from the cursor description
            columns = [col[0] for col in self.cursor.description]
        except sqlite3.Error as error:
            print(f"SQLite error occurred: {error}")
            return []

        # Transform rows into list of dictionaries
        return [dict(zip(columns, row)) for row in rows]

    def fetch_geometry_data(self, table_name: str = 'geometry') -> List[Dict[str, Any]]:
        """
        Fetch geometry data from a specified table based on the object's kreisid attribute.

        Args:
            table_name (str): Name of the table to fetch data from. Defaults to 'geometry'.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing KREISID and associated GeoData.
        """
        query = f"SELECT KREISID, GeoData FROM {table_name}"

        values = []
        where_clause = ""

        if self.kreisid:
            kreisid_conditions = ", ".join(["?" for _ in self.kreisid])
            where_clause = f" WHERE KREISID IN ({kreisid_conditions})"
            values.extend(self.kreisid)

        query += where_clause

        try:
            self.cursor.execute(query, tuple(values))
            rows = self.cursor.fetchall()
        except sqlite3.Error as sqlite_error:
            print(f"SQLite error occurred: {sqlite_error}")
            return []

        polygons = [{"KREISID": row[0], "geometry": json.loads(row[1])} for row in rows]

        return polygons

    def fetch_stations(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Fetch rows from 'stations' based on given conditions and return as list of dicts."""

        where_clauses = []
        values = []

        for key, value in kwargs.items():
            if isinstance(value, tuple):
                operator, actual_value = value
                where_clauses.append(f"{key} {operator} ?")
                values.append(actual_value)
            else:
                where_clauses.append(f"{key} = ?")
                values.append(value)

        if self.kreisid:
            kreisid_conditions = ", ".join(["?" for _ in self.kreisid])
            where_clauses.append(f"KREISID IN ({kreisid_conditions})")
            values.extend(self.kreisid)

        where_clause = " AND ".join(where_clauses)
        query = "SELECT * FROM stations"

        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            self.cursor.execute(query, tuple(values))
            rows = self.cursor.fetchall()

            # Fetch column names from the cursor description
            columns = [col[0] for col in self.cursor.description]
        except sqlite3.Error as error:
            print(f"SQLite error occurred: {error}")
            return []

        # Transform rows into list of dictionaries
        return [dict(zip(columns, row)) for row in rows]

    def fetch_rows(self, table_name: str, **kwargs: Any) -> List[Dict[str, Any]]:
        """Fetch rows from a table based on given conditions and return as list of dicts."""

        where_clauses = []
        values = []

        for key, value in kwargs.items():
            if isinstance(value, tuple):
                operator, actual_value = value
                where_clauses.append(f"{key} {operator} ?")
                values.append(actual_value)
            else:
                where_clauses.append(f"{key} = ?")
                values.append(value)

        if self.kreisid and table_name == 'stations':
            kreisid_conditions = ", ".join(["?" for _ in self.kreisid])
            where_clauses.append(f"KREISID IN ({kreisid_conditions})")
            values.extend(self.kreisid)

        where_clause = " AND ".join(where_clauses)

        query = f"SELECT * FROM {table_name}"
        if where_clause:
            query += f" WHERE {where_clause}"

        try:
            self.cursor.execute(query, tuple(values))
            rows = self.cursor.fetchall()

            # Fetch column names from the cursor description
            columns = [col[0] for col in self.cursor.description]
        except sqlite3.Error as error:
            print(f"SQLite error occurred: {error}")
            return []

        # Transform rows into list of dictionaries
        return [dict(zip(columns, row)) for row in rows]
