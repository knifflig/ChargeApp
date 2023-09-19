"""Module for converting kreis and geo data to GeoJSON format."""

from typing import List, Dict, Union, Optional, Any
from data_handler import SQLiteFetcher

def fetch_obj(kreisid: int,
              out: str = "kreis",
              link: Optional[str] = '../../ChargeApp.db'
              ) -> Dict[str, Any]:
    """Fetches data based on the given parameters.
    
    Args:
        kreisid: A single integer representing the Kreis ID.
        out: Specifies the type of output desired (kreis, geometry, stations).
        link: The SQLite database link, can be None.

    Returns:
        A dictionary containing the fetched data.

    Raises:
        ValueError: If the 'out' parameter is invalid.
    """

    if out not in ["kreis", "geometry", "stations"]:
        raise ValueError("Invalid value for 'out'. Choose from ['kreis', 'geometry', 'stations']")

    obj = None

    if kreisid < 1:
        raise ValueError("kreisid must be greater than 0")

    try:
        with SQLiteFetcher(link, kreisid=kreisid) as sql_fetcher:
            if out == "kreis":
                kreis = sql_fetcher.fetch_kreise()
                if kreis:
                    obj = kreis[0]
                else:
                    raise ValueError("No data found for 'kreis'")

            elif out == "geometry":
                geometry = sql_fetcher.fetch_geometry_data("geometry")
                if geometry and "geometry" in geometry[0]:
                    obj = geometry[0]["geometry"]
                else:
                    raise ValueError("No geometry data found")

            elif out == "stations":
                stations = sql_fetcher.fetch_stations()
                if stations:
                    obj = stations
                else:
                    raise ValueError("No station data found")

    except Exception as error:# pylint: disable=W0718
        print(f"An error occurred: {error}")
        return None  # Return None to indicate failure

    return obj

def list_obj(
        kreisids: Union[int, List[int]] = range(1, 402),
        out: str = "kreis",
        link: Optional[str] = '../../ChargeApp.db'
            ) -> List[List[Dict[str, Any]]]:
    """Fetches data based on the given parameters.
    
    Args:
        kreisids: Either a single integer or a list of integers.
        out: Specifies the type of output desired (kreis, geometry, stations).
        link: The SQLite database link.

    Returns:
        A list of dictionaries with fetched data.
    """
    # Ensure kreisids is a list
    if isinstance(kreisids, int):
        kreisids = [kreisids]

    fetched_data = []
    for kreisid in kreisids:
        if kreisid < 1:
            raise ValueError("kreisid must be greater than 0")

        fetched_obj = fetch_obj(kreisid, out=out, link=link)
        fetched_data.append(fetched_obj)

    return fetched_data

def featurise_obj(
        kreis: Dict[str, Any],
        geo: Dict[str, Any] = None
        ) -> List[Dict[str, Any]]:
    """Converts 'kreis' and 'geo' dictionaries into GeoJSON-like feature format.

    Args:
        kreis (Dict[str, Any]): Dictionary containing kreis information.
        geo (Dict[str, Any]): Dictionary containing geometry information.

    Raises:
        ValueError: Raised if the first attribute of kreis is not 'KREISID'
        ValueError: Raised if the first attribute of geo is not 'rings'

    Returns:
        List[Dict[str, Any]]: A list containing the GeoJSON-like feature.
    """
    # Check that the first attribute of kreis is "KREISID"
    if list(kreis.keys())[0] != "KREISID":
        raise ValueError("The first attribute of the kreis dictionary must be 'KREISID'.")

    if geo is not None:
        # Check that the first attribute of geo is "rings"
        if list(geo.keys())[0] != "rings":
            raise ValueError("The first attribute of the geo dictionary must be 'rings'.")
    else:
        geo = {}

    feature = {
        "type": "Feature",
        "properties": kreis,
        "geometry": {
            "type": "Polygon",
            "coordinates": geo.get('rings', [])
        }
    }
    return [feature]

def list_features(
        kreis_list: Union[Dict[str, Any] ,List[Dict[str, Any]]],
        link: Optional[str] = '../../ChargeApp.db'
        ) -> Dict[str, Any]:
    """Fetches data based on the given list of kreise.
    
    Args:
        kreis_list: Either a single Dict or a list of Dicts.

    Returns:
        A list of features with fetched data.
    """

    # Ensure kreis_list is a list
    if isinstance(kreis_list, Dict):
        kreis_list = [kreis_list]

    feature_list = []
    for kreis in kreis_list:
        # Check that the first attribute of kreis is "KREISID"
        if list(kreis.keys())[0] != "KREISID":
            raise ValueError("The first attribute of the kreis dictionary must be 'KREISID'.")

        kreis_id = kreis["KREISID"]

        geometry = fetch_obj(kreis_id, out = "geometry", link = link)

        feature = featurise_obj(kreis, geometry)
        feature_list.append(feature[0])

    return feature_list

def export_geojson(feature_list):
    """Export as GeoJson"""
    return {
        "type": "FeatureCollection",
        "features": feature_list
    }
