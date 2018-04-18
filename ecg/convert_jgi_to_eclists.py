import json
import csv
import os
import glob
import pandas as pd
from collections import OrderedDict
from natsort import natsorted

"""
Turns PATRIC's PATHWAY.tab files into master csv of ECs present in each genome.
Turns master csv into individual EC lists.
"""

def main():

    dat_dir = 'userdata/test_eukarya_ec_lists/'

    if not os.path.exists(dat_dir):
        os.makedirs(dat_dir)

    all_eukarya_dict = dict()
    for json_file in glob.glob('userdata/jgi_eukarya_jsons/*'):
        with open(json_file) as f:
            eukaryote_id = json_file.split('/')[-1].split('.json')[0]
            all_eukarya_dict[eukaryote_id] = dict()
            
            json_data = json.load(f)
    #         for EC in json_data['genome']:
    #         for EC in sorted(json_data['genome'], key=json_data['genome'].get):
    #         for EC in OrderedDict(sorted(json_data['genome'].items(), key=lambda x: x[1])):
            for EC in natsorted(json_data['genome']):
                EC_number = EC.split(':')[1]
                EC_count = int(json_data['genome'][EC][1])
                all_eukarya_dict[eukaryote_id][EC_number] = EC_count

        with open(dat_dir+eukaryote_id+'.dat','w') as f:
            f.write("# %s\n" %eukaryote_id)
            for EC in natsorted(all_eukarya_dict[eukaryote_id]):
                f.write("%s\n" %EC)

    eukarya_df = pd.DataFrame.from_dict(all_eukarya_dict)

    eukarya_df = eukarya_df.T

    eukarya_df = eukarya_df.fillna(0).astype(int)

    eukarya_df.to_csv('test_json_eukarya_parsed.csv')

if __name__=='__main__':
    main()