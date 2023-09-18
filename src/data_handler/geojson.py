"""Module for converting kreis and geo data to GeoJSON format."""

from data_handler import SQLiteFetcher
from ipyleaflet import GeoJSON

class GeoJsonFeatureCollection:
    """Handles GeoJsonFeatureCollection"""

    def __init__(self, features):
        self.features = features
        self.filter_and_calculate()
        self.calculate_opacities()

    @classmethod
    def import_geojson(cls, geojson_dict):
        """Import from GeoJson"""
        if geojson_dict.get('type') == 'FeatureCollection' and 'features' in geojson_dict:
            return cls(geojson_dict['features'])
        elif 'type' not in geojson_dict and isinstance(geojson_dict, list):
            # Assume the list contains only features
            return cls(geojson_dict)
        else:
            raise ValueError("Invalid GeoJSON dictionary or features list")

    def export_geojson(self):
        """Export as GeoJson"""
        return {
            "type": "FeatureCollection",
            "features": self.features
        }

    def filter_and_calculate(self):
        """Filter features from geojson and calculate ewz_sta.

        This method filters out features with None or missing 'stations' or 'ewz'
        values, and then calculates the 'ewz_sta' for each remaining feature.

        Args:
            geojson (dict): The GeoJSON object containing features.

        Raises:
            Exception: An error occurred during filtering or calculation.
        """
        filtered_features = []
        for feature in self.features:
            try:
                if feature['properties'].get('stations') and feature['properties'].get('ewz'):
                    stations = feature['properties']['stations']
                    ewz = feature['properties']['ewz']
                    ewz_sta = ewz / stations if stations else None
                    feature['properties']['ewz_sta'] = ewz_sta
                    filtered_features.append(feature)
            except Exception as error:# pylint: disable=W0718
                print(f"An error occurred: {error}")
        self.features = filtered_features

    def calculate_opacities(self):
        """Calculate and assign opacity values to each feature based on its properties.

        This method updates each feature in self.features with new properties that
        indicate the opacity of the feature based on 'stations' and 'ewz_sta'.

        Raises:
            Exception: An error occurred during the calculation of opacities.
        """
        min_stations = min(
            [feature['properties']['stations'] for feature in self.features]
            )
        max_stations = max(
            [feature['properties']['stations'] for feature in self.features]
            )
        min_ewz_sta = min(
            [feature['properties']['ewz_sta'] for feature in self.features
             if feature['properties']['ewz_sta'] is not None]
            )
        max_ewz_sta = max(
            [feature['properties']['ewz_sta'] for feature in self.features
             if feature['properties']['ewz_sta'] is not None]
            )

        for feature in self.features:
            try:
                stations = feature['properties']['stations']
                ewz_sta = feature['properties']['ewz_sta']
                feature['properties']['opac_sta'] = GeoJsonHandler.\
                    lerp_opac(min_stations, max_stations, stations, reverse=False)
                feature['properties']['opac_ewz_sta'] = GeoJsonHandler.\
                    lerp_opac(min_ewz_sta, max_ewz_sta, ewz_sta, reverse=True)
            except Exception as error:# pylint: disable=W0718
                print(f"An error occurred: {error}")

    def export_layer(self,
                     name="Layer", style=None,
                     hover=None, point_style=None, style_callback=None,
                     on_click=None, on_hover=None):
        """
        Exports the feature collection as an ipyleaflet GeoJSON object.

        Parameters:
            name (str): Name of the layer.
            style (dict): Base style for the layer.
            hover (dict): Style to be applied on hover.
            point_style (dict): Style for point features.
            style_callback (callable): Function to compute the style.
            on_click (callable): Function to be called when a feature is clicked.
            on_hover (callable): Function to be called when mouse hovers over a feature.

        Returns:
            ipyleaflet.GeoJSON: The GeoJSON layer.
        """
        layer = GeoJSON(
            data=self.export_geojson(),
            name=name,
            style=style,
            hover_style=hover,
            point_style=point_style,
            style_callback=style_callback,
            on_click=on_click,
            on_hover=on_hover
        )
        return layer

class GeoJsonHandler:
    """Handles the conversion and manipulation of geoJSON data."""

    def __init__(self, min_kreisid, max_kreisid):
        self.min_kreisid = min_kreisid
        self.max_kreisid = max_kreisid

    @staticmethod
    def lerp_opac(minval, maxval, val, reverse=False):
        """Linearly interpolate opacity based on a given value within a range.

        This method calculates the relative opacity of a value within a specified
        range (minval to maxval). Optionally, the opacity can be reversed.

        Args:
            minval (float): The minimum value in the range.
            maxval (float): The maximum value in the range.
            val (float): The value for which opacity needs to be calculated.
            reverse (bool, optional): Whether to reverse the direction of opacity.
                                    Defaults to False.

        Returns:
            float or None: The calculated opacity value between 0 and 1, or None if
                        input conditions are not met.

        Note:
            Returns 0 if val is None and reverse is False, returns 1 if val is None
            and reverse is True.
        """
        if val is None:
            return 0 if not reverse else 1
        if maxval == minval or val < minval or val > maxval:
            return None
        rel_val = (val - minval) / (maxval - minval)
        if reverse:
            rel_val = 1 - rel_val
        return rel_val

    @staticmethod
    def fetch_data(kreis, geo):
        """
        Convert kreis and geometry data to GeoJSON features, including only specified items.

        Parameters:
            kreis (list): List of dictionaries containing kreis metadata.
            geo (list): List of dictionaries containing geometry data.

        Returns:
            list: A list of GeoJSON features.
        """
        features = []
        items_to_include = ['KREISID', 'ags', 'gen', 'bez', 'ewz', 'nuts', 'stations']
        for k_item, g_item in zip(kreis, geo):
            if k_item.get('KREISID') == g_item.get('KREISID'):
                feature = {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": g_item['geometry'].get('rings', [])
                    }
                }
                for key in items_to_include:
                    if key in k_item:
                        feature['properties'][key] = k_item[key]
                features.append(feature)
        return features

    def get_collection(self):
        """
        Generate a GeoJsonFeatureCollection containing features for a range of kreisid values.

        Parameters:
            min_kreisid (int): The minimum kreisid value.
            max_kreisid (int): The maximum kreisid value.

        Returns:
            dict: A GeoJsonFeatureCollection.
        """
        geojson = {"type": "FeatureCollection", "features": []}
        try:
            for kreisid in range(self.min_kreisid, self.max_kreisid):
                with SQLiteFetcher('../../ChargeApp.db', kreisid=kreisid) as fetcher:
                    kreis = fetcher.fetch_kreise()
                    geo = fetcher.fetch_geometry_data("geometry")
                    geojson['features'].extend(self.fetch_data(kreis, geo))
        except Exception as error:# pylint: disable=W0718
            print(f"An error occurred: {error}")
        return GeoJsonFeatureCollection(geojson['features'])


def import_geojson(geojson_dict):
    """Import from GeoJson"""
    return GeoJsonFeatureCollection.import_geojson(geojson_dict)

# Usage
if __name__ == "__main__":
    geojson_handler = GeoJsonHandler(1, 402)
    geojson_data = geojson_handler.get_collection()
