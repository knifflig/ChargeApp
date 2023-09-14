"""
Module for finding stations
"""

import json
import requests
from requests.exceptions import RequestException
from shapely.geometry import Point, Polygon

class StationsFinder:
    """
    Class for station finding
    """
    def __init__(self, base_url):
        self.base_url = base_url
        self.default_params = {
            "where": "1=1",
            "objectIds": "",
            "outFields": "*",
            "returnGeometry": "false",
            "returnIdsOnly": "false",
            "returnCountOnly": "false",
            "inSR": "4326",
            "outSR": "4326",
            "f": "json"
        }

        self.allowed_out_fields = [
            '*',
            'Betreiber',
            'Straße',
            'Hausnummer',
            'Ort',
            'Bundesland',
            'Kreis_kreisfreie_Stadt',
            'Breitengrad',
            'Längengrad',
            'Inbetriebnahmedatum',
            'Anschlussleistung',
            'Art_der_Ladeeinrichung',
            'Anzahl_Ladepunkte',
            'Steckertypen1',
            'P1__kW_',
            'Public_Key1',
            'Steckertypen2',
            'P2__kW_',
            'Public_Key2',
            'Steckertypen3',
            'P3__kW_',
            'Public_Key3',
            'Steckertypen4',
            'P4__kW_',
            'Public_Key4'
        ]

    def fetch_data(self, object_ids=None, **kwargs):
        """
        Fetch data from API
        """
        if object_ids:
            object_ids = ",".join(map(str, object_ids))

        params = self.default_params.copy()
        params['objectIds'] = object_ids
        params.update(kwargs)

        try:
            response = requests.get(self.base_url, params=params, timeout=10.0)
            response.raise_for_status()

            data_json = json.loads(response.text)
            if "error" in data_json:
                print(data_json)
                return None

            features = data_json.get("features", [])

            formatted_data = [
                {
                    **feature.get("attributes", {}),
                    "geometry": feature.get("geometry", {})
                }
                for feature in features
            ]

            return formatted_data

        except RequestException as error:
            print(f"An error occurred: {error}")
            return None

def stations_find(object_ids=None, **kwargs):
    """
    Function for retrieving stations
    """
    base_url = (
    'https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/'
    'rest/services/Ladesaeulen_in_Deutschland/FeatureServer/0/query'
)
    api= StationsFinder(base_url)
    return api.fetch_data(object_ids, **kwargs)

def filter_stations(polygon, data_list):
    """
    Filters a list of dictionaries to keep only specific keys ('OBJECTID', 'Breitengrad', 'Längengrad') and
    checks if the coordinates are within the given polygon.
    
    Parameters:
    data_list (list): The original list of dictionaries.
    polygon (dict): Dictionary containing the polygon coordinates.
    
    Returns:
    list: A new list of filtered dictionaries.
    """
    # Create a Shapely Polygon object from the 'rings' coordinates
    poly = Polygon(polygon['rings'][0])
    
    # Define the keys we want to keep
    keys_to_keep = ['OBJECTID', 'Breitengrad', 'Längengrad']
    
    # Initialize an empty list to store the filtered dictionaries
    filtered_list = []
    
    # Loop through the original data list
    for entry in data_list:
        # Create a Point object from the coordinates
        point = Point(entry['Längengrad'], entry['Breitengrad'])
        
        # Check if the point is within the polygon
        if point.within(poly):
            # Create a filtered dictionary containing only the keys to keep
            filtered_dict = {key: entry[key] for key in keys_to_keep}
            
            # Append the filtered dictionary to the filtered list
            filtered_list.append(filtered_dict)
    
    return filtered_list

if __name__ == '__main__':
    try:
        ALL_STATIONS = stations_find()
        print("All station data:")
        print(ALL_STATIONS)

    except Exception as err:  # pylint: disable=broad-except
        print(f"An error occurred: {err}")
