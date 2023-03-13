import os
from os import listdir
from os.path import isfile, join
import sys
from typing import Dict
import csv
import json

from tqdm import tqdm

from dindex_store.discovery_index import DiscoveryIndex
from dindex_store.common import EdgeType


def load_dindex(config: Dict):

    dindex = DiscoveryIndex(config, load=True)
    return dindex


def build_dindex(input_data_path, config: Dict):

    # Create an instance of the discovery index
    dindex = DiscoveryIndex(config)

    # Initialize index
    dindex.initialize(config)

    # Check input data type
    if config["input_data_type"] != "json":
        # TODO
        print("Error: only json profiles supported")
        return

    profile_path = input_data_path + "/json/"
    text_path = input_data_path + "/text/"

    # Read profiles and populate index
    for file_path in os.listdir(profile_path):
        if os.path.isfile(file_path):
            with open(file_path) as f:
                profile = json.load(f)
                # Preprocessing minhash on profile
                if "minhash" in profile and profile["minhash"]:
                    profile["minhash"] = ",".join(map(str, profile["minhash"]))
                # add profile
                dindex.add_profile(profile)

    # Read text files and populate index
    onlyfiles = [f for f in listdir(text_path) if isfile(join(text_path, f))]
    for csv_file_path in tqdm(onlyfiles):
        csv_delimiter = config["text_csv_delimiter"]
        with open(csv_file_path) as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=csv_delimiter)
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                    continue
                profile_id, dbName, path, sourceName, columnName, data = int(row[0]), row[1], row[2], row[3], row[4], row[5]

                dindex.add_text_content(profile_id, dbName, path, sourceName, columnName, data)

    # Create content_similarity edges
    # TODO: this could be done incrementally, every time a new node is added, at a cost in efficiency
    profiles = dindex.get_minhashes()
    content_similarity_index = dindex.get_content_similarity_index()
    for profile in profiles:
        neighbors = content_similarity_index.query(profile['minhash'])
        for neighbor in neighbors:
            # TODO: Need to check that they are not from the same source
            # TODO: Replace with actual attributes
            dindex.add_undirected_edge(
                profile['id'], neighbor,
                EdgeType.ATTRIBUTE_SYNTACTIC_SIMILARITY, {'similar': 1})

    return dindex


if __name__ == "__main__":
    print("DIndex Builder")

    import config

    cnf = {setting: getattr(config, setting) for setting in dir(config) if setting.islower() and setting.isalpha()}

    def print_usage():
        print("USAGE: ")
        print("python dindex_builder.py load|build --input_path <path>")
        print("where opath must be writable by the process")
        exit()

    build = False
    load = False
    input_path = None
    if len(sys.argv) == 4 or len(sys.argv) == 2:
        mode = sys.argv[1]
        if mode == "load":
            load = True
        elif mode == "build":
            input_path = sys.argv[3]
            build = True
        else:
            print_usage()
    else:
        print_usage()

    if build:
        dindex = build_dindex(input_path, cnf)
    elif load:
        dindex = load_dindex(cnf)

    # TODO: notification
