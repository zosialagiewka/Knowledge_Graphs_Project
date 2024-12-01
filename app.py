import streamlit as st
import pandas as pd
from logic import *
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Railway journey planner", layout="wide")

st.title("Railway journey planner")

if "selected_points" not in st.session_state:
    st.session_state.selected_points = []


def handle_map_click(lat, lon):
    if len(st.session_state.selected_points) < 2:
        st.session_state.selected_points.append({"lat": lat, "lon": lon})
        st.rerun()
    else:
        st.warning("You can only select two points. Clear the points to reset.")


c1, c2 = st.columns(2)
with c1:
    st.write("### Add Points Manually")
    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=0.0, format="%.6f")
        lon = st.number_input("Longitude", value=0.0, format="%.6f")
    if st.button("Add Point"):
        handle_map_click(lat, lon)

    if st.button("Clear Selected Points"):
        st.session_state.selected_points = []

    if st.session_state.selected_points:
        st.write("### Selected Points")
        for idx, point in enumerate(st.session_state.selected_points):
            st.write(f"Point {idx + 1}: Latitude {point['lat']}, Longitude {point['lon']}")

with c2:
    st.write("### Map View")
    m = folium.Map(location=[52.22, 21.0], zoom_start=10)
    for point in st.session_state.selected_points:
        folium.Marker([point['lat'], point['lon']], tooltip="Selected Point").add_to(m)

    if len(st.session_state.selected_points) < 2:
        m.add_child(folium.ClickForMarker(popup=None))

    map_data = st_folium(m, width=700, height=500)

if map_data and map_data.get('last_clicked') is not None:
    lat, lon = map_data['last_clicked']['lat'], map_data['last_clicked']['lng']
    if {"lat": lat, "lon": lon} not in st.session_state.selected_points:
        handle_map_click(lat, lon)

if len(st.session_state.selected_points) == 2:
    lat1, lon1 = st.session_state.selected_points[0]["lat"], st.session_state.selected_points[0]["lon"]
    lat2, lon2 = st.session_state.selected_points[1]["lat"], st.session_state.selected_points[1]["lon"]

    st.write("### Train Routes")
    try:
        # train_routes = find_train_route(lat1, lon1, lat2, lon2)
        train_routes = get_routes_between_two_places(lat1, lon1, lat2, lon2)
        if train_routes:
            st.write(train_routes)
        else:
            st.write("No train routes found between the selected points.")
    except Exception as e:
        st.error(f"An error occurred while fetching train routes: {e}")
else:
    st.info("Please select or add coordinates for two points to find a train route.")
