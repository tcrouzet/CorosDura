# Coros Dura

Python to generate Coros Dura maps from OSM on MacOS, using [Mkgmap](https://www.mkgmap.org.uk/). Not working at that time.

### How to use

In app.py, set input_file to your OSM file (input_file = "my.osm" for exemple)

pip install osmium

python app.py

results in _output

### Download OSM

https://download.openstreetmap.fr/extracts/europe/france/

https://extract.bbbike.org/

### Decompress osm.pbf file

brew install osmosis
osmosis --read-pbf file="my.osm.pbf" --write-xml file="my.osm"

### Mount Dura disk on Mac

brew install --cask openmtp

### Inspiration

https://panaetius.github.io/swiss-topo-maps-on-coros/

### Comments in French on my blog


