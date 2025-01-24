# Coros Dura

Projet to generate Coros Dura map from OSM on MacOS. Not working at that time.

Set input_file in app.py.

pip install osmium

python app.py

results in _output

### Donwload OSM

https://download.openstreetmap.fr/extracts/europe/france/

https://extract.bbbike.org/

### Decompress osm.pbf file

brew install osmosis
osmosis --read-pbf file="my.osm.pbf" --write-xml file="my.osm"
