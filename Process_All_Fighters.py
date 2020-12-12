import json
import pandas as pd
from os import listdir, getcwd, makedirs
from os.path import isfile, join, exists


def process_jsons_into_csv():
    """ Load event data from jsons, process into matchups, then store all matchups in a single CSV file.

    Returns
    -------
    None
    """

    all_fighters_dir = getcwd() + '/UFCStats_Dicts/All_Fighters/'
    processed_fighters_dir = getcwd() + '/UFCStats_Dicts/Processed/'
    if not exists(processed_fighters_dir):
        makedirs(processed_fighters_dir)
    processed_filename = 'All_Fighters.csv'
    only_files = \
        [f for f in listdir(all_fighters_dir) if isfile(join(all_fighters_dir, f)) and not f.startswith('.')]

    dfs = []  # an empty list to store the data frames
    for fighter_filename in only_files:
        data = pd.read_json(join(all_fighters_dir, fighter_filename), orient='index')
        dfs.append(data)  # append the data frame to the list
    df = pd.concat(dfs, ignore_index=True)

    df.to_csv(join(processed_fighters_dir, processed_filename), index=False)


if __name__ == '__main__':
    process_jsons_into_csv()
