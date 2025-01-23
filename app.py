import streamlit as st
import pandas as pd
from logic import *
import folium
from streamlit_folium import st_folium
from shapely import wkt

st.set_page_config(page_title="Railway journey planner 🚂", layout="wide")

st.title("Railway journey planner 🚂")

if "selected_points" not in st.session_state:
    st.session_state.selected_points = []

if "lines" not in st.session_state:
    st.session_state.lines = []

if "endpoints" not in st.session_state:
    st.session_state.endpoints = []

if "ready" not in st.session_state:
    st.session_state.ready = False

if "routes" not in st.session_state:
    st.session_state.routes = None

if "route_with_change" not in st.session_state:
    st.session_state.route_with_change = None

if "filtered_routes" not in st.session_state:
    st.session_state.filtered_routes = None

if "no_results" not in st.session_state:
    st.session_state.no_results = False

if "alternative_lines" not in st.session_state:
    st.session_state.alternative_lines = []

if st.session_state.ready and st.session_state.routes:
    st.sidebar.write("### Filtering")
    st.sidebar.write("#### Maximum walking distance")
    max_walking_distance = st.sidebar.slider("Distance (km)", 0.0, 10.0, 10.0, 0.1)

    st.sidebar.write("#### Stations")
    start_stations = sorted(
        set(route["start_station"] for route in (st.session_state.routes or []))
    )
    end_stations = sorted(
        set(route["end_station"] for route in (st.session_state.routes or []))
    )
    operators = sorted(
        set(
            route["operator"]
            for route in (st.session_state.routes or [])
            if route["operator"]
        )
    )

    start_station_filter = st.sidebar.selectbox(
        "Start station", ["All"] + start_stations
    )
    end_station_filter = st.sidebar.selectbox("End station", ["All"] + end_stations)

    st.sidebar.write("#### Operators")
    selected_operators = []
    for operator in operators:
        if operator:
            if st.sidebar.checkbox(operator, value=True):
                selected_operators.append(operator)

    other = st.sidebar.checkbox("Other (no operator)", value=True)

    st.sidebar.write("#### Other")
    unique_routes_only = st.sidebar.checkbox(
        "Show only one route per start-end station pair", value=False
    )
    unique_route_names_only = st.sidebar.checkbox(
        "Show only the option with the closest stations for a given route", value=False
    )

    if st.sidebar.button("Filter"):
        if st.session_state.routes is not None:
            filtered_routes = [
                route
                for route in st.session_state.routes
                if (
                    route["total_distance"] <= max_walking_distance
                    and (
                        start_station_filter == "All"
                        or start_station_filter == route["start_station"]
                    )
                    and (
                        end_station_filter == "All"
                        or end_station_filter == route["end_station"]
                    )
                    and (
                        route.get("operator") in selected_operators
                        or (other and not route.get("operator"))
                    )
                )
            ]

        if unique_routes_only:
            filtered_routes = get_unique_routes(filtered_routes)
        if unique_route_names_only:
            filtered_routes = get_unique_routes_by_name(filtered_routes)

        if not filtered_routes:
            st.session_state.no_results = True
        else:
            st.session_state.no_results = False

        st.session_state.filtered_routes = filtered_routes

    if st.sidebar.button("Clear filters"):
        st.session_state.filtered_routes = None
        st.session_state.no_results = False


def handle_map_click(lat_, lon_):
    if len(st.session_state.selected_points) < 2:
        st.session_state.selected_points.append({"lat": lat_, "lon": lon_})
        st.rerun()
    else:
        st.warning("You can only select two points. Clear the points to reset.")


st.sidebar.write("### Add points manually")
lat = st.sidebar.number_input("Latitude", value=0.0, format="%.6f")
lon = st.sidebar.number_input("Longitude", value=0.0, format="%.6f")
if st.sidebar.button("Add Point"):
    handle_map_click(lat, lon)

if st.session_state.selected_points:
    st.sidebar.write("### Selected points")
    for idx, point in enumerate(st.session_state.selected_points):
        st.sidebar.write(
            f"Point {idx + 1}:\n\n Latitude {round(point['lat'], 3)}, Longitude {round(point['lon'], 3)}"
        )

if st.sidebar.button("Clear selected points"):
    st.session_state.selected_points = []
    st.session_state.lines = []
    st.session_state.endpoints = []
    st.session_state.ready = False
    st.session_state.routes = None
    st.session_state.no_results = False
    st.session_state.filtered_routes = None
    st.session_state.alternative_lines = []

m = folium.Map(location=[52.228, 21.0], zoom_start=10)

for point in st.session_state.selected_points:
    folium.Marker([point["lat"], point["lon"]], tooltip="Selected Point").add_to(m)

for point in st.session_state.endpoints:
    folium.CircleMarker(
        [point[0], point[1]],
        tooltip=point[2],
        radius=10,
        color="red",
        fill=True,
        fill_color="red",
        fill_opacity=0.7,
    ).add_to(m)

for line_coords in st.session_state.alternative_lines:
    folium.PolyLine(line_coords, color="blue", weight=3).add_to(m)

for line_coords in st.session_state.lines:
    folium.PolyLine(line_coords, color="red", weight=3).add_to(m)

if "route_lines" in st.session_state:
    colors = ["blue", "green", "orange"]
    for idx, (route_name, lines) in enumerate(st.session_state.route_lines.items()):
        color = colors[idx % len(colors)]
        for line in lines:
            folium.PolyLine(
                line, color=color, weight=3, tooltip=f"Route: {route_name}"
            ).add_to(m)

if len(st.session_state.selected_points) < 2:
    m.add_child(folium.ClickForMarker(popup=None))

map_data = st_folium(m, width=1000, height=550)

if map_data and map_data.get("last_clicked") is not None:
    lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
    if {"lat": lat, "lon": lon} not in st.session_state.selected_points:
        handle_map_click(lat, lon)

if len(st.session_state.selected_points) == 2 and not st.session_state.ready:
    lat1, lon1 = (
        st.session_state.selected_points[0]["lat"],
        st.session_state.selected_points[0]["lon"],
    )
    lat2, lon2 = (
        st.session_state.selected_points[1]["lat"],
        st.session_state.selected_points[1]["lon"],
    )

    try:
        common_routes = find_common_routes(lat1, lon1, lat2, lon2)
        st.session_state.ready = True

        if common_routes:
            closest_route = common_routes[0]
            geometry_wkt = get_route_geometry(closest_route["route"])
            geometry = wkt.loads(geometry_wkt)

            if geometry.geom_type == "GeometryCollection":
                for geom in geometry.geoms:
                    if geom.geom_type == "LineString":
                        coordinates = [(point[1], point[0]) for point in geom.coords]
                        st.session_state.lines.append(coordinates)

            start_station_geometry = wkt.loads(closest_route["start_station_geometry"])
            end_station_geometry = wkt.loads(closest_route["end_station_geometry"])

            if start_station_geometry.geom_type == "Point":
                st.session_state.endpoints.append(
                    (
                        start_station_geometry.y,
                        start_station_geometry.x,
                        closest_route["start_station"],
                    )
                )

            if end_station_geometry.geom_type == "Point":
                st.session_state.endpoints.append(
                    (
                        end_station_geometry.y,
                        end_station_geometry.x,
                        closest_route["end_station"],
                    )
                )

            st.session_state.routes = common_routes
            st.rerun()
        else:
            possible_routes = find_routes_with_change(lat1, lon1, lat2, lon2)
            if possible_routes:
                st.session_state.route_with_change = possible_routes

                for i, possible_route in enumerate(possible_routes):
                    route_a = possible_route["route_a"]
                    route_b = possible_route["route_b"]
                    change_station = possible_route["change"]
                    station_a_name = possible_route["station_name_a"]
                    station_b_name = possible_route["station_name_b"]
                    station_a_geometry = possible_route["station_geometry_a"]
                    station_b_geometry = possible_route["station_geometry_b"]

                    geometry_route_a = get_route_geometry(route_a)
                    geometry_route_b = get_route_geometry(route_b)

                    for geometry_wkt in [geometry_route_a, geometry_route_b]:
                        geometry = wkt.loads(geometry_wkt)
                        if geometry.geom_type == "GeometryCollection":
                            for geom in geometry.geoms:
                                if geom.geom_type == "LineString":
                                    coordinates = [
                                        (point[1], point[0]) for point in geom.coords
                                    ]
                                    if i == 0:
                                        st.session_state.lines.append(coordinates)
                                    else:
                                        st.session_state.alternative_lines.append(
                                            coordinates
                                        )

                    change_station_geometry = get_route_geometry(change_station)
                    change_station_geometry = wkt.loads(change_station_geometry)

                    if change_station_geometry.geom_type == "Point":
                        st.session_state.endpoints.append(
                            (
                                change_station_geometry.y,
                                change_station_geometry.x,
                                "Change here",
                            )
                        )

                    if i == 0:
                        start_station_geometry = wkt.loads(station_a_geometry)
                        end_station_geometry = wkt.loads(station_b_geometry)

                        if start_station_geometry.geom_type == "Point":
                            st.session_state.endpoints.append(
                                (
                                    start_station_geometry.y,
                                    start_station_geometry.x,
                                    station_a_name,
                                )
                            )

                        if end_station_geometry.geom_type == "Point":
                            st.session_state.endpoints.append(
                                (
                                    end_station_geometry.y,
                                    end_station_geometry.x,
                                    station_b_name,
                                )
                            )
            st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {e}")

if st.session_state.ready:
    if st.session_state.routes is not None:
        closest_route = st.session_state.routes[0]

        st.write("### Recommended route")
        st.write(f"Route: {closest_route['route_name']}")
        st.write(f"From: {closest_route['start_station']}")
        st.write(f"To: {closest_route['end_station']}")
        st.write(f"Total distance to stations: {closest_route['total_distance']} km")

        if st.checkbox("Display station details", value=False):
            st.session_state.routes[0]["details_start"] = get_station_details(
                closest_route["start_station"]
            )
            st.session_state.routes[0]["details_end"] = get_station_details(
                closest_route["end_station"]
            )

            st.write("#### Stations details")
            st.write("##### Start station details")
            (
                st.write(pd.DataFrame(closest_route["details_start"]))
                if closest_route["details_start"]
                else "No details found"
            )
            st.write("##### End station details")
            (
                st.write(pd.DataFrame(closest_route["details_end"]))
                if closest_route["details_end"]
                else "No details found"
            )

        st.write("### All direct train routes found")
        if not st.session_state.filtered_routes and st.session_state.no_results:
            st.write("No results matching the filter criteria were found.")
        else:
            column_mapping = {
                "route_name": "Route",
                "start_station": "Start station",
                "end_station": "End station",
                "operator": "Operator",
                "total_distance": "Walking distance (km)",
            }

            routes_to_display = (
                st.session_state.filtered_routes or st.session_state.routes
            )
            st.write(
                pd.DataFrame(routes_to_display)[
                    [
                        "route_name",
                        "start_station",
                        "end_station",
                        "operator",
                        "total_distance",
                    ]
                ].rename(columns=column_mapping)
            )

            if 0 < len(routes_to_display) <= 3:
                if st.button("Show all routes on the map"):
                    route_lines = {}
                    for route in routes_to_display:
                        geometry_wkt = get_route_geometry(route["route"])
                        geometry = wkt.loads(geometry_wkt)

                        lines = []
                        if geometry.geom_type == "GeometryCollection":
                            for geom in geometry.geoms:
                                if geom.geom_type == "LineString":
                                    coordinates = [
                                        (point[1], point[0]) for point in geom.coords
                                    ]
                                    lines.append(coordinates)
                        elif geometry.geom_type == "LineString":
                            coordinates = [
                                (point[1], point[0]) for point in geometry.coords
                            ]
                            lines.append(coordinates)

                        route_lines[route["route_name"]] = lines

                    st.session_state.route_lines = route_lines
                    st.rerun()

    elif st.session_state.route_with_change:
        st.write("### Possible routes with changes")

        routes_with_change_df = pd.DataFrame(st.session_state.route_with_change).rename(
            columns={
                "route_a": "First route",
                "route_b": "Second route",
                "route_name_a": "First route name",
                "route_name_b": "Second route name",
                "change": "Change station",
                "change_name": "Change station name",
                "station_name_a": "Start station",
                "station_name_b": "End station",
                "station_geometry_a": "Start station geometry",
                "station_geometry_b": "End station geometry",
            }
        )

        st.write(
            pd.DataFrame(routes_with_change_df)[
                [
                    "First route name",
                    "Second route name",
                    "Start station",
                    "End station",
                    "Change station",
                ]
            ]
        )
    else:
        st.write("No routes found between the selected points.")
