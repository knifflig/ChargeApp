from kreis_loader import get_envelope
from stations_loader import stations_find, filter_stations
from map_drawer import DrawMap as dm
import json

# Open the file for reading
with open('kreise.json', 'r') as json_file:
    kreise = json.load(json_file)

# Create an instance of DrawMap
dm = dm()

for kreis in kreise:
    station_map = dm.plot_regions(kreis)

    polygon = kreis.get("geometry", None)  # Using get() to avoid KeyError
    if polygon is not None:
        # Compute the envelope and add it to the kreis
        envelope = get_envelope(polygon)
        kreis['envelope'] = envelope
    
    stations = stations_find(geometry = envelope)
    kreis['stations'] = stations

    stations_filtered = filter_stations(polygon, stations)
    kreis['stations_filtered'] = stations_filtered
    station_map = dm.add_stations(kreis["stations_filtered"])

station_map
