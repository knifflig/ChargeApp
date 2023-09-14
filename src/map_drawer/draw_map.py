import matplotlib.pyplot as plt
import matplotlib.patches as patches
from kreis_loader import get_kreise

class DrawMap:
    def __init__(self, arcgis_data_list):
        self.arcgis_data_list = arcgis_data_list

    def plot_region(self):
        plt.figure(figsize=(10, 10))
        plt.title("Map of Regions")
        
        for arcgis_data in self.arcgis_data_list:
            geometry = arcgis_data['geometry']['rings']
            attributes = {key: arcgis_data[key] for key in arcgis_data.keys() if key != 'geometry'}
            
            for ring in geometry:
                x, y = zip(*ring)
                plt.fill(x, y, 'b-', alpha=0.4)
                plt.plot(x, y, 'k-')
        
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")

        return plt

def base_map(arcgis_data):
    dm = DrawMap(arcgis_data)
    return dm.plot_region()

def add_envelope(map_obj, envelope):
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

    # Create the rectangle
    rect = patches.Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, linewidth=2, edgecolor='black', facecolor='none')
    
    # Add the rectangle to the Axes
    map_obj.gca().add_patch(rect)

def add_stations(map_obj, stations):
    """
    Adds points to a Matplotlib Axes object.

    Parameters:
    map_obj (Axes): Matplotlib Axes object where the map is plotted.
    data_list (list): List of dictionaries containing 'Breitengrad' and 'Längengrad' keys.
    """
    
    # Extract the latitude and longitude coordinates from the data list
    latitudes = [entry['Breitengrad'] for entry in stations]
    longitudes = [entry['Längengrad'] for entry in stations]
    
    # Plot the points on the map
    map_obj.scatter(longitudes, latitudes, c='red', marker='o')


# Example usage:
if __name__ == '__main__':
    arcgis_data = get_kreise(object_id=[1,12], return_geometry=True)

    base_map(arcgis_data)
    