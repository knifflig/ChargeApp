# pylint: disable=import-error
"""
This script loads and processes data about geographical entities (kreise)
and charging stations, storing them in an SQLite database.
"""

import json
from kreis_loader import get_envelope, get_kreise
from stations_loader import stations_find, filter_stations
from data_handler import SQLite, SQLiteFetcher

def main():
    """Main function that handles the data loading and processing."""

    kreise = get_kreise(returnGeometry=True)

    for kreis in kreise:
        kreis["attributes"]['KREISID'] = kreis["attributes"].pop('OBJECTID')

    # Define the columns for the kreis table
    kreis_columns = {
            'KREISID': 'INTEGER PRIMARY KEY NOT NULL',
            'ags': 'TEXT',
            'gen': 'TEXT',
            'bez': 'TEXT',
            'ibz': 'INTEGER',
            'bem': 'TEXT',
            'sn_l': 'TEXT',
            'sn_r': 'TEXT',
            'sn_k': 'TEXT',
            'sn_v1': 'TEXT',
            'sn_v2': 'TEXT',
            'sn_g': 'TEXT',
            'fk_s3': 'TEXT',
            'nuts': 'TEXT',
            'wsk': 'TEXT', 
            'ewz': 'INTEGER',
            'kfl': 'REAL',
            'Shape__Area': 'REAL',
            'Shape__Length': 'REAL'
        }

    # Create the kreis table
    with SQLite('ChargeApp.db') as db_conn:
        db_conn.create_table("kreis_table", kreis_columns)

    # Define the columns for the geometry table
    geometry_columns = {
            'KREISID': 'INTEGER PRIMARY KEY NOT NULL',
            'GeoData': 'BLOB',
        }
    geometry_reference_key = {
            'table': 'kreis_table',
            'column': 'KREISID',
            'reference_column': 'KREISID'
        }

    # Create the geometry table
    with SQLite('ChargeApp.db') as db_conn:
        db_conn.create_sub_table("geometry", geometry_columns, geometry_reference_key)

    # Define the columns for the station table
    station_columns = {
            'OBJECTID': 'INTEGER PRIMARY KEY NOT NULL',
            'KREISID': 'INTEGER',
            'Betreiber': 'TEXT',
            'Straße': 'TEXT',
            'Hausnummer': 'TEXT',
            'Adresszusatz': 'TEXT',
            'Postleitzahl': 'INTEGER',
            'Ort': 'TEXT',
            'Bundesland': 'TEXT',
            'Kreis_kreisfreie_Stadt': 'TEXT',
            'Breitengrad': 'REAL',
            'Längengrad': 'REAL',
            'Inbetriebnahmedatum': 'TEXT',
            'Anschlussleistung': 'REAL',
            'Art_der_Ladeeinrichung': 'TEXT',
            'Anzahl_Ladepunkte': 'INTEGER',
            'Steckertypen1': 'TEXT',
            'P1__kW_': 'INTEGER',
            'Public_Key1': 'TEXT',
            'Steckertypen2': 'TEXT',
            'P2__kW_': 'REAL',
            'Public_Key2': 'TEXT',
            'Steckertypen3': 'TEXT',
            'P3__kW_': 'INTEGER',
            'Public_Key3': 'TEXT',
            'Steckertypen4': 'TEXT',
            'P4__kW_': 'INTEGER',
            'Public_Key4': 'TEXT'
        }
    station_reference_key = {
            'table': 'kreis_table',
            'column': 'KREISID',
            'reference_column': 'KREISID'
        }

    # Create the station table
    with SQLite('ChargeApp.db') as db_conn:
        db_conn.create_sub_table("stations", station_columns, station_reference_key)

    for kreis in kreise:
        handle_kreis_data(kreis)

def handle_kreis_data(kreis):
    """Handles the data for a single kreis."""

    kreis_id = kreis["attributes"].get('KREISID')

    # Insert Kreise data
    with SQLite('ChargeApp.db') as db_conn:
        db_conn.insert_data("kreis_table", "KREISID", kreis["attributes"])

    polygon = kreis.get("geometry", None)

    # Insert geometry data
    if polygon:
        handle_geometry_data(polygon, kreis_id)

    # Insert envelope data
    envelope = get_envelope(polygon)
    if envelope:
        handle_envelope_data(envelope, kreis_id)

        # Insert stations data
        stations = stations_find(geometry=envelope)
        stations_filtered = filter_stations(polygon, stations)
        handle_station_data(stations_filtered, kreis_id)

def handle_geometry_data(polygon, kreis_id):
    """Handles the geometry data for a single kreis."""

    with SQLite('ChargeApp.db') as db_conn:
        db_conn.insert_data(
                table_name="geometry",
                key_column="KREISID",
                data={'GeoData': json.dumps(polygon)},
                key_value=kreis_id,
                reference_key={
                    'table': 'kreis_table',
                    'column': 'KREISID',
                    'reference_column': 'KREISID'
                }
            )

def handle_envelope_data(envelope, kreis_id):
    """Handles the envelope data for a single kreis."""

    with SQLite('ChargeApp.db') as db_conn:
        db_conn.add_column("kreis_table", "envelope", "TEXT")

        db_conn.insert_data(
                table_name="kreis_table",
                key_column="KREISID",
                data={"envelope": envelope},
                key_value=kreis_id
            )

def handle_station_data(stations_filtered, kreis_id):
    """Handles the stations data for a single kreis."""

    for station in stations_filtered:
        station['KREISID'] = kreis_id

    with SQLite('ChargeApp.db') as db_conn:
        db_conn.insert_data(
            "stations", "OBJECTID", stations_filtered,
            reference_key={
                'table': 'kreis_table',
                'column': 'OBJECTID',
                'reference_column': 'KREISID'
            },
            strict=False
        )

for ID in list(range(400)):

    with SQLiteFetcher('../../ChargeApp.db', kreisid=ID) as fetcher:
        kreis = fetcher.fetch_rows('kreis_table')[0]
        stations = fetcher.fetch_rows('stations')

    with SQLite('../../ChargeApp.db') as db_conn:
        db_conn.add_column("kreis_table", "stations", "INT")

        db_conn.insert_data(
                table_name="kreis_table",
                key_column="KREISID",
                data={"stations": len(stations)},
                key_value=ID
            )



if __name__ == "__main__":
    main()
