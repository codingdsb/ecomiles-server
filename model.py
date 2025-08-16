import osmnx as ox
import networkx as nx
import numpy as np
import joblib
from scipy.spatial import cKDTree
from shapely.geometry import LineString, Point


def get_route(start_lat, start_lon, end_lat, end_lon, date, hour, month, weekday, weekend):

    G=ox.load_graphml("my_graph.graphml")
    station_tree=joblib.load("kdtree.pkl")

    def predict_pollution(lat_lon_list, station_coord, date, hour, month, weekday, weekend ):
        lon, lat = station_coord
        station_id = lat_lon_list.index((lon, lat)) + 1 
        
        model=joblib.load("PM25_model.joblib")
        date_early=0
        date_mid=0
        date_late=0
        if date <= 10:
            date_early=1
        elif date <= 20:
            date_mid=1
        else:
            date_late=1
        month_spring=0
        month_winter=0
        month_summer=0
        if month in [11, 12, 1]:
            month_winter=1
        elif month in [2, 3, 4]:
            month_spring=1
        else:
            month_summer=1
        if 6 <= hour < 12:
            y_pred = model.predict([[station_id, weekday,weekend, 0, 0,1,0,np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12), date_early, date_late, date_mid, month_spring, month_summer, month_winter ]])
        elif 12 <= hour < 17:
            y_pred = model.predict([[station_id, weekday,weekend, 0, 0,0,1,np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12), date_early, date_late, date_mid, month_spring, month_summer, month_winter]])
        elif 17 <= hour < 21:
            y_pred = model.predict([[station_id, weekday,weekend, 1, 0,0 ,0,np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12), date_early, date_late, date_mid, month_spring, month_summer, month_winter]])
        else:
            y_pred = model.predict([[station_id, weekday,weekend, 0, 1,0,0,np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12), date_early, date_late, date_mid, month_spring, month_summer, month_winter]])

        pollution_score = (y_pred[0][0])
        return pollution_score

    src = ox.distance.nearest_nodes(G, start_lon, start_lat)
    dst = ox.distance.nearest_nodes(G, end_lon, end_lat)

    shortest_route = nx.shortest_path(G, src, dst, weight="length")

    route_coords = [(G.nodes[n]["x"], G.nodes[n]["y"]) for n in shortest_route]
    route_line = LineString(route_coords)

    nodes_gdf = ox.graph_to_gdfs(G, edges=False)
    buffer_meters = 200
    buffer_deg = buffer_meters / 111000
    route_buffer = route_line.buffer(buffer_deg)
    likely_nodes = nodes_gdf[nodes_gdf.geometry.within(route_buffer)].index.tolist()

    likely_nodes = list(likely_nodes)

    station_pollution_cache = {}

    node_pollution = {}

    lat_lon_list=joblib.load("lat_lon_list.pkl")

    for i, node in enumerate(likely_nodes, 1):
        node_lat = G.nodes[node]['y']
        node_lon = G.nodes[node]['x']

        dist, station_idx = station_tree.query([node_lon, node_lat])

        if station_idx not in station_pollution_cache:
            station_coord = lat_lon_list[station_idx]
            pollution_val = predict_pollution(lat_lon_list, station_coord, date, hour, month, weekday, weekend)
            station_pollution_cache[station_idx] = pollution_val
        else:
            pollution_val = station_pollution_cache[station_idx]

        node_pollution[node] = pollution_val

    default_pollution = 40
    for u, v, key, data in G.edges(keys=True, data=True):
        p_u = node_pollution.get(u, default_pollution)
        p_v = node_pollution.get(v, default_pollution)
        avg_pollution = (p_u + p_v) / 2
        data['pollution'] = data['length'] * 5*(avg_pollution)

    least_pollution_route = nx.shortest_path(G, src, dst, weight='pollution')

    route_latlon = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in least_pollution_route]
    return route_latlon