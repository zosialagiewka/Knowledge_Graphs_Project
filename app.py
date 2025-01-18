import streamlit as st
import pandas as pd
from logic import *
import folium
from streamlit_folium import st_folium
from shapely import wkt
from shapely.geometry import GeometryCollection

st.set_page_config(page_title="Railway journey planner", layout="wide")

st.title("Railway journey planner 🚂🗓️")

if "selected_points" not in st.session_state:
    st.session_state.selected_points = []

if "lines" not in st.session_state:
    st.session_state.lines = []

if "endpoints" not in st.session_state:
    st.session_state.endpoints = []


def handle_map_click(lat, lon):
    if len(st.session_state.selected_points) < 2:
        st.session_state.selected_points.append({"lat": lat, "lon": lon})
        st.rerun()
    else:
        st.warning("You can only select two points. Clear the points to reset.")


c1, c2 = st.columns(2)
with c1:
    st.write("### Add points manually")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=0.0, format="%.6f")
        lon = st.number_input("Longitude", value=0.0, format="%.6f")
    if st.button("Add Point"):
        handle_map_click(lat, lon)

    if st.button("Clear selected points"):
        st.session_state.selected_points = []
        st.session_state.lines = []
        st.session_state.endpoints = []

    if st.session_state.selected_points:
        st.write("### Selected points")
        for idx, point in enumerate(st.session_state.selected_points):
            st.write(
                f"Point {idx + 1}: Latitude {point['lat']}, Longitude {point['lon']}"
            )

with c2:
    st.write("### Map view")
    m = folium.Map(location=[52.228, 21.0], zoom_start=14)

    for point in st.session_state.selected_points:
        folium.Marker([point["lat"], point["lon"]], tooltip="Selected Point").add_to(m)

    for point in st.session_state.endpoints:
        folium.CircleMarker(
            [point[0], point[1]],
            tooltip=point[2],
            radius=12,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.7,
        ).add_to(m)

    for line_coords in st.session_state.lines:
        folium.PolyLine(line_coords, color="red", weight=2.5).add_to(m)

    if len(st.session_state.selected_points) < 2:
        m.add_child(folium.ClickForMarker(popup=None))

    map_data = st_folium(m, width=700, height=500)

if map_data and map_data.get("last_clicked") is not None:
    lat, lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
    if {"lat": lat, "lon": lon} not in st.session_state.selected_points:
        handle_map_click(lat, lon)

if len(st.session_state.selected_points) == 2:
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

        if common_routes:
            closest_route = common_routes[0]
            st.write("### Closest Route")

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

            st.write(f"Route: {closest_route['route_name']}")
            st.write(
                f"From: {closest_route['start_station']} to {closest_route['end_station']}"
            )
            st.write(
                f"Total distance to stations: {closest_route['total_distance']} km"
            )

            st.write("### All direct train routes found")
            st.write(pd.DataFrame(common_routes))
        else:
            st.write("No routes found between the selected points.")

    except Exception as e:
        st.error(f"An error occurred: {e}")

else:
    st.info("Please select or add coordinates for two points to find a train route.")
