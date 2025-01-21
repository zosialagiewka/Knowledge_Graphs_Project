import time
import matplotlib.pyplot as plt
from SPARQLWrapper import SPARQLWrapper, JSON

# SPARQL endpoint URL (replace with the appropriate endpoint)
SPARQL_ENDPOINT = "https://qlever.cs.uni-freiburg.de/osm-planet"

# Define the SPARQL query
QUERY = """
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
PREFIX osm: <https://www.openstreetmap.org/>
PREFIX osmkey: <https://www.openstreetmap.org/wiki/Key:>
PREFIX osm2rdfmember: <https://osm2rdf.cs.uni-freiburg.de/rdf/member#>
PREFIX osmrel: <https://www.openstreetmap.org/relation/>
PREFIX osmway: <https://www.openstreetmap.org/way/>
PREFIX ogc: <http://www.opengis.net/rdf#>

SELECT ?station1 ?stationName WHERE {
            osmrel:13249292 ogc:sfContains ?station1 .
            ?station1 osmkey:name ?stationName .
            
            osmrel:13249294 ogc:sfContains ?station2 .
            ?station2 osmkey:name ?stationName .
            
            ?station1 osmkey:railway "stop" .
        }
        GROUP BY ?stationName ?station1
        LIMIT 1
"""

# Initialize the SPARQL wrapper
sparql = SPARQLWrapper(SPARQL_ENDPOINT)
sparql.setQuery(QUERY)
sparql.setReturnFormat(JSON)

# Benchmark execution time
execution_times = []
num_iterations = 100  # Number of repetitions for benchmarking

for i in range(num_iterations):
    start_time = time.time()
    sparql.query().convert()
    end_time = time.time()
    execution_times.append(end_time - start_time)

# Calculate the average execution time
average_time = sum(execution_times) / len(execution_times)

# Plot the histogram
plt.figure(figsize=(10, 6))
plt.hist(execution_times, bins=50, alpha=0.7, edgecolor='black')
plt.axvline(average_time, color='red', linestyle='dashed', linewidth=2, label=f'Average: {average_time:.2f} seconds')
plt.title('SPARQL Query Execution Time Benchmark (get_intersections (relation 13249292 and 13249294))')
plt.xlabel('Execution Time (seconds)')
plt.ylabel('Frequency')
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
