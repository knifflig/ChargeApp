import plotly.graph_objects as go
import numpy as np
from kreis_loader import get_kreise

class DrawMap:
    def __init__(self, map_fig=None):
        if map_fig is None:
            self.fig = go.Figure()
        else:
            self.fig = map_fig
        self.lons = []
        self.lats = []

    def calculate_zoom_level(self, min_lon, max_lon, min_lat, max_lat):
        # Calculate the difference in longitude and latitude
        lon_diff = max_lon - min_lon
        lat_diff = max_lat - min_lat
        
        # Calculate zoom level based on the larger range (latitude or longitude)
        zoom_factor = max(lon_diff, lat_diff)
        zoom_level = 10 - zoom_factor * 1.1
        
        return max(1, zoom_level)  # Make sure zoom is at least 1
    
    def base_map(self):
        self.fig = go.Scattermapbox()
        
        return self.fig
    
    def plot_region(self, arcgis_data_object):
        polygon = arcgis_data_object['geometry']['rings']
        
        for point in polygon:
            x, y = zip(*point)
            self.lons.extend(x)
            self.lats.extend(y)
            self.fig.add_trace(go.Scattermapbox(
                mode="lines",
                lon=x,
                lat=y,
                fill='toself',
                fillcolor='rgba(0, 128, 128, 0.2)',
                line=dict(width=2, color='black')
            ))
        
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

        # Ensure the input is a list of dictionaries
        if isinstance(arcgis_data_list, dict):
            arcgis_data_list = [arcgis_data_list]

        for arcgis_data_object in arcgis_data_list:
            self.plot_region(arcgis_data_object)
        
        return self.fig
    
    def add_envelope(self, envelope):
        """
        Adds a rectangle to a Matplotlib Axes object.
        
        Parameters:
        envelope (tuple): Coordinates defining the rectangle.
        """
        clean_str = envelope.strip("{}")
        str_values = clean_str.split(", ")

        # Convert each substring to a float
        envelope = [float(x) for x in str_values]

        xmin, ymin, xmax, ymax = envelope

        # Rectangle coordinates
        coords = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}

        self.fig.add_trace(
            go.Scattermapbox(
                lat=[coords['ymin'], coords['ymax'], coords['ymax'], coords['ymin'], coords['ymin']],
                lon=[coords['xmin'], coords['xmin'], coords['xmax'], coords['xmax'], coords['xmin']],
                mode='lines',
                line=dict(width=2, color='red'),
            )
        )

        return self.fig
    
    def add_stations(self, stations):
        """
        Adds points (flags) to a Plotly Figure object.
        
        Parameters:
        stations (list): List of dictionaries containing 'Breitengrad' (latitude) and 'Längengrad' (longitude) keys.
        """

        # Extract the latitude and longitude coordinates from the data list
        latitudes = [entry['Breitengrad'] for entry in stations]
        longitudes = [entry['Längengrad'] for entry in stations]

        # Add the flags (points) to the map
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


# Example usage:
if __name__ == '__main__':
    arcgis_data = get_kreise(object_id=[1], return_geometry=True)

    # Create an instance of DrawMap
    draw_map_instance = DrawMap()

    # Plot regions using the instance of DrawMap
    draw_map_instance.plot_regions(arcgis_data[0])

    