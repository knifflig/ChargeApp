"""
kreis_find.py

Fetch data from the ArcGIS API and provide functionality to query by object ID or other parameters.
"""

import json
import requests
from requests.exceptions import RequestException

class ArcGISAPI:
    """
    A class used to interact with the ArcGIS API.
    """

    def __init__(self, base_url):
        self.base_url = base_url
        self.default_params = {
            "where": "1=1",
            "objectIds": "",
            "outFields": "*",
            "returnIdsOnly": "false",
            "returnCountOnly": "false",
            "spatial_rel": "",
            "geometry_type": "esriGeometryEnvelope",
            "inSR": "4326",
            "geometry": "",
            "returnGeometry": "false",
            "outSR": "4326",
            "f": "json"
        }

        self.allowed_out_fields = [
            '*',
            'ags',
            'gen',
            'bez',
            'ibz',
            'bem',
            'sn_l',
            'sn_r',
            'sn_k',
            'sn_v1',
            'sn_v2',
            'sn_g',
            'fk_s3',
            'nuts',
            'wsk',
            'ewz',
            'kfl',
            'Shape__Area',
            'Shape__Length'
            ]


    def fetch_data(self, **kwargs):
        """
        Fetch data from the ArcGIS API.

        :param object_id: The ID of the object to fetch.
        :param where: SQL-like where clause to filter features.
        :param out_fields: List of field names to include in the returned features.
        :param f_format: The format of the returned features.
        :param return_geometry: True to return the geometry, False otherwise.
        :param spatial_rel: Spatial relationship to apply to the input geometry.
        :param out_sr: Output spatial reference of the returned geometry.
        :param in_sr: Input spatial reference of the returned geometry.
        :param geometry: Geometry to apply as the spatial filter.
        :param geometry_type: The type of geometry specified in the geometry parameter.
        :return: List of features that meet the query criteria.
        """

        params = self.default_params.copy()
        params.update(kwargs)

        try:
            response = requests.get(self.base_url, params=params, timeout=10.0)
            response.raise_for_status()

            data_json = json.loads(response.text)

            if "error" in data_json:
                print(data_json)
                return None

            features = data_json.get("features", [])
            return features

        except RequestException as error:
            print(f"An error occurred while making the request: {error}")
            return None

def get_kreise(**kwargs):
    """
    A convenience function for fetching data from a specific ArcGIS API endpoint.

    :param object_id: The ID of the object to fetch.
    :param kwargs: Additional parameters to pass to the fetch_data function.
    :return: List of features that meet the query criteria.
    """
    base_url = (
    'https://services2.arcgis.com/jUpNdisbWqRpMo35/arcgis/'
    'rest/services/KRS_ew_20/FeatureServer/0/query'
)
    api = ArcGISAPI(base_url)
    return api.fetch_data(**kwargs)

def get_envelope(polygon):
    """
    Initialize variables to hold the min and max coordinates
    """
    xmin, ymin = float('inf'), float('inf')
    xmax, ymax = float('-inf'), float('-inf')

    # Loop through the points to update min and max coordinates
    for ring in polygon['rings']:
        for point in ring:
            x_axis, y_axis = point
            xmin = min(xmin, x_axis)
            ymin = min(ymin, y_axis)
            xmax = max(xmax, x_axis)
            ymax = max(ymax, y_axis)

    # Create and return the bounding rectangle
    #geometry = {xmin, ymin, xmax, ymax}
    geometry = f"{{{xmin}, {ymin}, {xmax}, {ymax}}}"

    return geometry

if __name__ == '__main__':
    try:
        ALL_DATA = get_kreise(object_id=1, return_geometry=True)
        print("All object data:")
        print(ALL_DATA)

    except Exception as err:  # pylint: disable=broad-except
        print(f"An error occurred: {err}")
