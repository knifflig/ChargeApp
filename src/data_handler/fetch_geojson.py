"""Module for converting kreis and geo data to GeoJSON format."""

import json
from data_handler import SQLiteFetcher

def data_to_geojson(kreis, geo):
    """
    Convert kreis and geometry data to GeoJSON features.

    Parameters:
        kreis (list): List of dictionaries containing kreis metadata.
        geo (list): List of dictionaries containing geometry data.

    Returns:
        list: A list of GeoJSON features.
    """
    # Initialize an empty list for features
    features = []

    for k_item, g_item in zip(kreis, geo):
        if k_item.get('KREISID') == g_item.get('KREISID'):
            feature = {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [g_item['geometry'].get('rings', [])]
                }
            }

            # Copy metadata to properties
            feature['properties'].update(k_item)

            features.append(feature)

    return features

def get_geojson(min_kreisid, max_kreisid):
    """
    Generate a GeoJSON object containing features for a range of kreisid values.

    Parameters:
        min_kreisid (int): The minimum kreisid value.
        max_kreisid (int): The maximum kreisid value.

    Returns:
        dict: A GeoJSON object.
    """
    # Initialize the GeoJSON object
    geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    try:
        # Loop over all desired kreisid values
        for kreisid in range(min_kreisid, max_kreisid):
            with SQLiteFetcher('../../ChargeApp.db', kreisid=kreisid) as fetcher:
                kreis = fetcher.fetch_kreise()
                geo = fetcher.fetch_geometry_data("geometry")
                geojson['features'].extend(data_to_geojson(kreis, geo))
    except Exception as error:# pylint: disable=W0718
        print(f"An error occurred: {error}")

    return geojson

# Usage
if __name__ == "__main__":
    GEOJSON_DATA = get_geojson(1, 402)

    with open("kreise.geojson", 'w', encoding='utf-8') as file:
        json.dump(GEOJSON_DATA, file, ensure_ascii=False, indent=4)
