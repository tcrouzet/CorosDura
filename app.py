import os
import json
import subprocess
from pathlib import Path
import osmium
import math

os.system('clear')


class BoundsHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.min_lat = float('inf')
        self.max_lat = float('-inf')
        self.min_lon = float('inf')
        self.max_lon = float('-inf')

    def node(self, n):
        self.min_lat = min(self.min_lat, n.location.lat)
        self.max_lat = max(self.max_lat, n.location.lat)
        self.min_lon = min(self.min_lon, n.location.lon)
        self.max_lon = max(self.max_lon, n.location.lon)



class AreaExtractor(osmium.SimpleHandler):
    def __init__(self, min_lat, max_lat, min_lon, max_lon):
        osmium.SimpleHandler.__init__(self)
        self.min_lat = min_lat
        self.max_lat = max_lat
        self.min_lon = min_lon
        self.max_lon = max_lon
        self.writer = None
        self.needed_nodes = set()  # Initialisation de needed_nodes
    
    def set_writer(self, writer):
        self.writer = writer

    def is_in_bounds(self, location):
        if not location.valid():
            return False
        return (self.min_lat <= location.lat <= self.max_lat and 
                self.min_lon <= location.lon <= self.max_lon)

    def way(self, w):
        nodes_in_area = False
        for n in w.nodes:
            if self.is_in_bounds(n.location):
                nodes_in_area = True
                # Marquer tous les nœuds de ce way
                for way_node in w.nodes:
                    self.needed_nodes.add(way_node.ref)
                break
        
        if nodes_in_area:
            # print(f"Way {w.id} within bounds, adding to writer.")
            self.writer.add_way(w)

    def node(self, n):
        if self.writer and (self.is_in_bounds(n.location) or n.id in self.needed_nodes):
            # print(f"Node {n.id} within bounds or needed, adding to writer.")
            self.writer.add_node(n)

    def relation(self, r):
        if any(m.type == 'w' for m in r.members):
            # print(f"Relation {r.id} related to needed ways, adding to writer.")
            self.writer.add_relation(r)



def get_map_bounds(osm_file):
    """
    Obtient les limites géographiques d'un fichier OSM, avec mise en cache.
    
    Args:
        osm_file (str): Chemin vers le fichier OSM
        
    Returns:
        dict: Dictionnaire contenant min_lat, max_lat, min_lon, max_lon
    """
    # Nom du fichier cache basé sur le nom du fichier OSM
    cache_file = Path('_' + osm_file).with_suffix('.bounds.json')
    
    # Si le cache existe et que le fichier OSM n'a pas été modifié depuis
    if cache_file.exists() and Path(osm_file).stat().st_mtime < cache_file.stat().st_mtime:
        try:
            print("Utilisation du cache des limites...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                bounds = json.load(f)
                print(f"Limites chargées du cache : {bounds}")
                return bounds
        except json.JSONDecodeError:
            print("Cache corrompu, recalcul des limites...")
            cache_file.unlink()  # Supprimer le cache corrompu
    
    # Calculer les bounds
    print("Calcul des nouvelles limites...")
    handler = BoundsHandler()
    handler.apply_file(osm_file)
    
    bounds = {
        'min_lat': handler.min_lat,
        'max_lat': handler.max_lat,
        'min_lon': handler.min_lon,
        'max_lon': handler.max_lon
    }
    
    # Sauvegarder dans le cache avec une indentation lisible
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(bounds, f, indent=4)
    
    print(f"Limites de la carte trouvées : {bounds}")
    return bounds


def create_segment(input_file, min_lat, max_lat, min_lon, max_lon, output_file):
    # Ajouter une marge autour de la zone
    margin = 0.2
    writer = osmium.SimpleWriter(str(output_file))
    handler = AreaExtractor(
        min_lat - margin,  # Étendre la zone vers le sud
        max_lat + margin,  # Étendre la zone vers le nord
        min_lon - margin,  # Étendre la zone vers l'ouest
        max_lon + margin   # Étendre la zone vers l'est
    )
    handler.set_writer(writer)  # Définir le writer avant d'appeler apply_file
    print(f"Création du segment {output_file}")  # Debug
    handler.apply_file(input_file, locations=True, idx='flex_mem')
    writer.close()


def segment_map(input_osm, output_base_dir):
    # Obtenir les limites de la carte
    bounds = get_map_bounds(input_osm)

    min_lat = math.floor(bounds['min_lat'])
    max_lat = math.ceil(bounds['max_lat'])
    min_lon = math.floor(bounds['min_lon'])
    max_lon = math.ceil(bounds['max_lon'])

    # Pour chaque degré de latitude/longitude
    map_number = 63240001  # Numéro de départ pour les cartes
    for lat in range(min_lat, max_lat):
        for lon in range(min_lon, max_lon):

            # Déterminez le préfixe pour la latitude et la longitude
            lat_prefix = '0' if lat >= 0 else '1'
            lon_prefix = '0' if lon >= 0 else '1'

            # Format du numéro de région
            lat_str2 = f"{abs(lat):02d}"
            lat_str = f"{abs(lat):03d}"
            lon_str = f"{abs(lon):04d}"

            # Nom du fichier selon convention Dura
            segment_file = f'C{lat_str}{lon_str}'

            # Structure de dossiers selon Dura
            segment_dir = Path(output_base_dir) / 'CM' / lon_prefix / lat_str2 / lat_prefix
            segment_dir.mkdir(parents=True, exist_ok=True)

            osm_file = segment_dir / f'{segment_file}.osm'

            # Convertir .oms en .img avec mkgmap
            try:

                create_segment(input_osm, lat, lat+1, lon, lon+1, osm_file)

                subprocess.run([
                    'java', '-jar', 'mkgmap/mkgmap.jar',
                    '--output-dir=' + str(segment_dir),
                    '--mapname=' + f'{map_number:08d}',  # Doit être un nombre à 8 chiffres
                    '--description=OSM tcrouzet',
                    '--country-name=France',
                    '--country-abbr=FR',
                    '--family-id=42',
                    '--product-id=1',
                    '--series-name=OSM Coros tcrouzet',
                    '--family-name=OSM',
                    '--route',  # Pour le réseau routier
                    '--net',    # Pour le réseau de base
                    '--draw-priority=20',
                    '--add-pois-to-areas',
                    '--preserve-element-order',
                    '--style-file=styles/mystyle',
                    '--verbose',
                    str(osm_file)
                ], check=True)  # Ajouter check=True pour détecter les erreurs

                # Renommer .img en .csm seulement si la conversion a réussi
                img_file = segment_dir / f'{map_number:08d}.img'
                if img_file.exists():
                    csm_file = segment_dir / f'{segment_file}.csm'
                    print("CMS FILE:",csm_file)
                    os.rename(img_file, csm_file)

               # Nettoyer les fichiers temporaires
                if osm_file.exists():
                    os.remove(osm_file)
                
                # Supprimer les autres fichiers temporaires
                for temp_file in segment_dir.glob('ovm_*.img'):
                    os.remove(temp_file)
                for temp_file in segment_dir.glob('osmmap.*'):
                    os.remove(temp_file)

                map_number += 1  # Incrémenter le numéro de carte

            except subprocess.CalledProcessError as e:
                print(f"Erreur détaillée : {e.stderr}")  # Afficher l'erreur complète
                print(f"Erreur lors de la conversion de {segment_file}: {e}")
                exit()



if __name__ == "__main__":
    input_file = "maison.osm"
    output_dir = "_output"

    # Gérer le répertoire de sortie
    output_path = Path(output_dir)
    if output_path.exists():
        import shutil
        shutil.rmtree(output_path)
    output_path.mkdir(exist_ok=True)  # Créer le répertoire de sortie

    segment_map(input_file, output_dir)