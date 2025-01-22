# **Railway Journey Planner 🚂**

## **Table of Contents**
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Data Sources](#data-sources)
6. [License](#license)

---

## **Project Overview**

**Description**:  
This project involves creating a simple railway journey planner using OpenStreetMap (OSM) data represented as a knowledge graph, powered by a Qlever SPARQL endpoint. The planner focuses on route relationships between railway stations across different countries, without considering train schedules or waiting times.

## Key Features
- **Find Route** Select two points on the map and find a train relation connecting those two places
- **Find Route with change** Find a route with change (algorithm limited to one station change)
- **Visualize Route** Visualize the geometry of the connection between two stations (visualize the change station if present)
- **Walking Distance** Calculate a walking distance from a selected point to the stations
- **Route Filtering**: Filter routes by railway operators (e.g., avoid Intercity, use Koleje Mazowieckie only).
- **Detailed Route Information**: Display comprehensive route details sourced from OSM and Wikidata queries.
- **Amenities around the station** Provide information about amenities close to the station

---

## **Installation**

### Prerequisites
This project relies on specific versions of key libraries to ensure compatibility and functionality. The requirements include `folium` for interactive maps, `pandas` for data manipulation, `SPARQLWrapper` 
for querying SPARQL endpoints, `streamlit` for building the user interface, `streamlit_folium` for embedding Folium maps into Streamlit apps, 
and `shapely` for handling geometric operations. These exact versions have been used:

- `folium==0.18.0`: Used for creating interactive maps.
- `pandas==2.0.3`: For data manipulation and analysis.
- `SPARQLWrapper==2.0.0`: Enables querying SPARQL endpoints for extracting data.
- `streamlit==1.40.2`: A framework for building interactive web applications.
- `streamlit_folium==0.23.2`: Integrates Folium maps into Streamlit apps.
- `shapely==2.0.4`: Used for geometric operations and spatial analysis.

These versions are defined in the `requirements.txt` file, which allows for easy setup of the project environment


### Installation

#### Steps

1. Install requirements:
```bash
pip install -r requirements.txt
```
2. Clone the repository:
```bash
git clone https://github.com/zosialagiewka/Knowledge_Graphs_Project.git
cd knowledge-graph-project
```

---

### Usage

The repository is organized in following manner:

- `app.py` - a streamlit application (user interface)
- `logic.py` - contains a logic of the application, including the algorithms to find routes and SPARQL queries 

To run the application use:
```bash
streamlit run app.py
```
---

### Data sources

## 1. OpenStreetMap Endpoint

- **Endpoint**: [https://qlever.cs.uni-freiburg.de/osm-planet](https://qlever.cs.uni-freiburg.de/osm-planet)
- Used to query geographic and location-based data, in case of this project find stations, relations and it's geometries

## 2. Wikidata Endpoint

- **Endpoint**: [https://query.wikidata.org/sparql](https://query.wikidata.org/sparql)
- Used to query structured data from the Wikidata knowledge base, in case of this project more detailed informations about stations


---

### License

This project is licensed under the [WTFPL License](http://www.wtfpl.net/). You are free to do whatever you want with this code — no restrictions, no conditions. 

---




