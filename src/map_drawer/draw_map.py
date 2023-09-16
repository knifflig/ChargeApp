"""
DrawMap Class
-------------
This class provides functionalities for plotting regions, envelopes, and stations on a map.
"""
import plotly.graph_objects as go
import numpy as np
from kreis_loader import get_kreise  # Assuming kreis_loader is another Python file you have

class DrawMap:
    """Draw geographical regions on a map."""

    def __init__(self, map_fig=None):
        """
        Initialize DrawMap object.
        
        Parameters:
        map_fig (object): An existing Plotly Figure object (default is None).
        """
        self.fig = go.Figure() if map_fig is None else map_fig
        self.lons = []
        self.lats = []

    def calculate_zoom_level(self, min_lon, max_lon, min_lat, max_lat):
        """
        Calculate the zoom level for the map.

        Parameters:
        min_lon (float): Minimum longitude.
        max_lon (float): Maximum longitude.
        min_lat (float): Minimum latitude.
        max_lat (float): Maximum latitude.
        
        Returns:
        float: Zoom level.
        """
        try:
            lon_diff = max_lon - min_lon
            lat_diff = max_lat - min_lat
            zoom_factor = max(lon_diff, lat_diff)
            zoom_level = 10 - zoom_factor * 1.1
            return max(1, zoom_level)  # Ensure zoom level is at least 1
        except TypeError as error:
            print(f"An error occurred: {error}")
            return 1  # Default zoom level

    def base_map(self):
        """
        Create a basic map.

        Returns:
        object: A Plotly Scattermapbox object.
        """
        self.fig = go.Scattermapbox()
        return self.fig

    def plot_region(self, arcgis_data_object):
        """
        Plot a region on the map.

        Parameters:
        arcgis_data_object (dict): ArcGIS data as a dictionary.
        
        Returns:
        object: Updated Plotly Figure object.
        """
        try:
            polygon = arcgis_data_object['geometry']['rings']
        except KeyError:
            print("Invalid ArcGIS data object format.")
            return self.fig

        for point in polygon:
            x_axis, y_axis = zip(*point)
            self.lons.extend(x_axis)
            self.lats.extend(y_axis)
            self.fig.add_trace(go.Scattermapbox(
                mode="lines",
                lon=x_axis,
                lat=y_axis,
                fill='toself',
                fillcolor='rgba(0, 128, 128, 0.2)',
                line=dict(width=2, color='black')
            ))

        if self.lons and self.lats:
            min_lon, max_lon = min(self.lons), max(self.lons)
            min_lat, max_lat = min(self.lats), max(self.lats)
            zoom_level = self.calculate_zoom_level(min_lon, max_lon, min_lat, max_lat)

            self.fig.update_layout(
                mapbox=dict(
                    style="carto-positron",
                    center=dict(
                        lon=np.mean([min_lon, max_lon]),
                        lat=np.mean([min_lat, max_lat])
                    ),
                    zoom=zoom_level
                ),
                showlegend=False,
            )
        return self.fig

    def plot_regions(self, arcgis_data_list):
        """
        Plot multiple regions on the map.

        Parameters:
        arcgis_data_list (list): List of ArcGIS data as dictionaries.
        
        Returns:
        object: Updated Plotly Figure object.
        """
        if not isinstance(arcgis_data_list, (list, dict)):
            print("Input must be a list or dictionary.")
            return self.fig

        if isinstance(arcgis_data_list, dict):
            arcgis_data_list = [arcgis_data_list]

        for arcgis_data_object in arcgis_data_list:
            self.plot_region(arcgis_data_object)

        return self.fig

    def add_envelope(self, envelope):
        """
        Adds a rectangle to the map.

        Parameters:
        envelope (str): Coordinates defining the rectangle as a string.

        Returns:
        object: Updated Plotly Figure object.
        """
        try:
            clean_str = envelope.strip("{}")
            str_values = clean_str.split(", ")
            envelope = [float(x) for x in str_values]
        except (ValueError, TypeError):
            print("Invalid envelope format. Expected a string with comma-separated float values.")
            return self.fig

        xmin, ymin, xmax, ymax = envelope

        self.fig.add_trace(
            go.Scattermapbox(
                lat=[ymin, ymax, ymax, ymin, ymin],
                lon=[xmin, xmin, xmax, xmax, xmin],
                mode='lines',
                line=dict(width=2, color='red'),
            )
        )
        return self.fig

    def add_stations(self, stations):
        """
        Adds points (flags) to the map.

        Parameters:
        stations (list):
        List of dictionaries containing 'Breitengrad' (latitude) and 'Längengrad' (longitude) keys.

        Returns:
        object: Updated Plotly Figure object.
        """
        try:
            latitudes = [entry['Breitengrad'] for entry in stations]
            longitudes = [entry['Längengrad'] for entry in stations]
        except (KeyError, TypeError):
            print("Invalid format. Expected a list of dicts with 'Breitengrad'/'Längengrad'.")
            return self.fig

        self.fig.add_trace(
            go.Scattermapbox(
                mode="markers",
                lon=longitudes,
                lat=latitudes,
                marker=dict(
                    size=5,
                    color='red',
                )
            )
        )
        return self.fig

if __name__ == '__main__':
    arcgis_data = get_kreise(object_id=[1], return_geometry=True)
    draw_map_instance = DrawMap()
    draw_map_instance.plot_regions(arcgis_data[0])
