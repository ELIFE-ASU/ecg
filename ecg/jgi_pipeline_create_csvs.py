"""
.. currentmodule:: data_pipeline.GatherRaw

Gathers the raw data from JGI.
"""
import json
import glob
from os.path import join
import sys
import os
import pandas as pd
from tqdm import tqdm

def load_json(path):
    """
    Loads jsons given a path.

    :param path: Path for file to be read.
    :type param: str.

    :return: Dictionary of data loaded from JSON file.
    """
    with open(path,mode='r',encoding='utf-8') as f:
        file = json.load(f)
    return file

def dump_json(json_dict,path,filename):
    """
    Dumps data to a json file given a filename.

    :param json_dict: Dictionary to be written as JSON file.
    :type: dict.

    :param path: Path for folder of file to be written.
    :type path: str.

    :param filename: Filename of file to be written.
    :type filename: str.
    """
    # Checks if folder exists.
    check_folder(path)

    # Writes json file to path using given filename.
    taxon_ids_path = os.path.join(path,filename+'.json')
    with open(taxon_ids_path,mode= 'w+',encoding='utf-8') as file:
        json.dump(json_dict, file)

def check_folder(path):
    """
    Checks if path exists and creates it if it does not.

    :param path: Path for folder.
    :type path: str
    """
    # Checks if folder exists.
    if not os.path.exists(path):
        # If folder does not exist it creates it.
        os.makedirs(path)

def traverse_files(path):
    """
    Gets a list of files in a given path and returns them as a list of filenames.

    :param path: Path for folder.
    :type path: str.

    :return: List of filenames in folder.
    """
    # Initializes empty list of filenames.
    filenames = []

    # Checks to see if path exists.
    if os.path.exists(path):
        # Iterates over all files and folders.
        for _dirpath, _dirnames, files in os.walk(path):
            # If files exist in path iterate over them.
            if files:
                # Adds the files to the list. I had to use extend instead of append as it gave a
                # list inside a list?
                filenames.extend(files)

    # Returns the list of filenames
    return filenames

def combine_files(path):
    """
    Combines .csv files into one .csv file.

    :param path: Path for files.
    :type path: str.
    """
    print('Combining all .csv files. This will take a few minutes.')
    all_files = glob.glob(join(path, '*.csv'))
    df_from_each_file = (pd.read_csv(f) for f in all_files)

    df = pd.concat(df_from_each_file, ignore_index=True, sort=True)

    if path == '../jgi_raw_metagenomes_oct2023/':
        df.to_csv('../data/Raw_Metagenome_Data_Combined.csv', index = False)
    else:
        df.to_csv('../data/Raw_Data_Combined.csv', index = False)

class GatherRaw:
    """
    A class to gather the raw data from a domain and create .csv files from the JSON files.

    :param name: Name of domain.
    :type name: str.

    :param jgi_path: Path where JGI data is stored.
    :type jgi_path: str.

    :param dump_path: Path to where .csv files will be written.
    :type dump_path: str.
    """
    def __init__(self,name,jgi_path,dump_path):

        # Sets name = name
        self.name = name

        # Sets path to the path of the json files for the domain.
        self.path = join(jgi_path,self.name,'taxon_ids')

        # Sets the dump path for the files.
        self.dump_path = dump_path

        # Checks if folder exists for dump_path.
        if not os.path.exists(self.dump_path):
            # If folder does not exist it creates it.
            os.makedirs(self.dump_path)

        # Creates a list of taxons.
        self.taxons = traverse_files(self.path)
        print('Pre-processing raw data')

        # Gets data
        self.get_data()

    def get_data(self):
        """
        Parses the taxon list to get statistics, enzyme, and metadata raw data.
        """

        # Creates progress bar based on total number of files in domain
        with tqdm(total=len(self.taxons),file=sys.stdout) as pbar:
            # Sets the progress bar description.
            pbar.set_description(f'Processing raw taxons ({self.name}):')

            # Iterates over every taxon in the domain list of taxons.
            for taxon_path in self.taxons:
                # Loads the individual .json file for the taxon.
                taxon = load_json(join(self.path,taxon_path))
                # Checks if taxon has enzymes data.
                if 'enzymes' in taxon.keys():
                    # Checks for empty enzyme value data.
                    if [v[1] for v in taxon['enzymes'].values()] != []:
                        # Only retrieves the following keys. There may be more keys that are
                        # needed, and can be added/subtracted here.
                        meta_keys = ['Organism Name', 'Taxon ID', 'NCBI Taxonomy Lineage', 'High Quality',
                                    'JGI Analysis Project Type' , 'JGI Analysis Product Name']
                        stats_keys = ['DNA, total number of bases','DNA coding number of bases',
                                    'DNA G+C number of bases', 'Genes total number',
                                    'Protein coding genes',
                                    'Protein coding genes with function prediction']

                        # Checks if any data is missing from above keys.
                        missing_meta = [k for k in meta_keys
                                       if k not in taxon['metadata'].keys()]
                        missing_stats = [k for k in stats_keys
                                        if k not in taxon['statistics'].keys()]

                        # Sets missing data to be null value so that keys are not missing.
                        if missing_meta != []:
                            for k in missing_meta:
                                taxon['metadata'][k] = ''

                        if missing_stats != []:
                            for k in missing_stats:
                                taxon['statistics'][k] = ''

                        # Retrieves data from JSON file.
                        data1 = [taxon['metadata']['Organism Name'],
                                taxon['metadata']['Taxon ID'],
                                taxon['metadata']['NCBI Taxonomy Lineage'].split(';')[0],
                                taxon['metadata']['NCBI Taxonomy Lineage'].split(';')[1].split()[0],
                                taxon['metadata']['NCBI Taxonomy Lineage'].split(';')[2].split()[0],
                                taxon['metadata']['NCBI Taxonomy Lineage'].split(';')[3].split()[0],
                                taxon['metadata']['NCBI Taxonomy Lineage'].split(';')[4].split()[0],
                                taxon['metadata']['NCBI Taxonomy Lineage'].split(';')[5].split()[0],
                                taxon['metadata']['NCBI Taxonomy Lineage'].split(';')[6],
                                taxon['metadata']['High Quality'],
                                taxon['metadata']['JGI Analysis Project Type'],
                                taxon['metadata']['JGI Analysis Product Name'],
                                taxon['statistics']['DNA, total number of bases'][0],
                                taxon['statistics']['DNA coding number of bases'][1].split()[0].strip('%'),
                                taxon['statistics']['DNA G+C number of bases'][1].split()[0].strip('%'),
                                taxon['statistics']['Genes total number'][0],
                                taxon['statistics']['Protein coding genes'][1].strip('%'),
                                taxon['statistics']['Protein coding genes with function prediction'][1].strip('%')]

                        # Sets column names to match data retrieved.
                        columns1 = ['Organism Name', 'Taxon ID', 'Domain', 'Phylum', 'Class',
                                    'Order', 'Family', 'Genus', 'Species', 'High Quality',
                                    'JGI Analysis Project Type', 'JGI Analysis Product Name',
                                    'DNA, total number of bases', 'DNA coding number of bases',
                                    'DNA G+C number of bases', 'Genes total number',
                                    'Protein coding genes',
                                    'Protein coding genes with function prediction']

                        # Retrieves all enzyme data.
                        data2 = [v[1] for v in taxon['enzymes'].values()]
                        # Removes 'EC:' from EC name.
                        columns2 = [k.strip('EC:') for k in taxon['enzymes'].keys()]

                        # Combines enzyme and metadata/statistics into one list.
                        data = [[*data1, *data2]]
                        # Combines column names and enzyme names into one list.
                        columns = [*columns1, *columns2]

                        # Creates Pandas DataFrame from data. Writes to a .csv file.
                        df = pd.DataFrame(data, columns = columns)
                        df.to_csv(join(self.dump_path,df['Taxon ID'][0] + '.csv'),index =False)

                # Updates progress bar
                pbar.update()

class GatherRawMetagenome(GatherRaw):
    """
    An inherited class to gather the raw data from metagenomes and create .csv files from the
    JSON files in a separate folder from the domain files.
    """
    def get_data(self):
        """
        Parses the metagenome taxon list to get statistics, enzyme, and metadata raw data.
        """

        # Creates progress bar based on total number of metagenome files.
        with tqdm(total=len(self.taxons),file=sys.stdout) as pbar:
            # Sets the progress bar description.
            pbar.set_description('Processing raw metagenomes:')

            # Iterates over every taxon in the metagenome list of taxons.
            for taxon_path in self.taxons:
                # Loads the individual .json file for metagenomes.
                taxon = load_json(join(self.path,taxon_path))
                # Checks if taxon has enzymes data.
                if 'assembled' in taxon:
                    # Checks for empty enzyme value data.
                    if [ec_value[1] for ec_value in taxon['assembled'].values()] != []:
                        # Only retrieves the following keys. There may be more keys that are
                        # needed, and can be added/subtracted here.
                        meta_keys = ['Add Date','Altitude In Meters', 'Annotation Method',
                                    'Chlorophyll Concentration', 'Cultured',
                                    'GOLD Analysis Project Type', 'GOLD Ecosystem',
                                    'GOLD Ecosystem Category', 'GOLD Ecosystem Subtype',
                                    'GOLD Ecosystem Type','GOLD Sequencing Depth',
                                    'GOLD Sequencing Quality', 'GOLD Sequencing Status',
                                    'GOLD Sequencing Strategy', 'GOLD Specific Ecosystem',
                                    'Geographic Location', 'Habitat',
                                    'IMG Release/Pipeline Version', 'Is Public', 'Is Published',
                                    'Isolation', 'Isolation Country', 'JGI Analysis Product Name',
                                    'JGI Analysis Project Type', 'Latitude', 'Longhurst Code',
                                    'Longitude', 'Modified Date', 'Nitrate Concentration',
                                    'Nitrite Concentration', 'Oxygen Concentration', 'pH',
                                    'Pressure', 'Proportal Isolation', 'Proportal Ocean',
                                    'Proportal WOA Dissolved Oxygen', 'Proportal WOA Nitrate',
                                    'Proportal WOA Phosphate', 'Proportal WOA Salinity',
                                    'Proportal WOA Silicate', 'Proportal WOA Temperature',
                                    'Salinity Concentration', 'Sample Body Site',
                                    'Sample Body Subsite', 'Sample Collection Date',
                                    'Sample Collection Temperature', 'Sample Name',
                                    'Sequencing Center', 'Sequencing Method', 'Sequencing Status',
                                    'Study Name (Proposal Name)', 'Submission Type',
                                    'Taxon Object ID']

                        stats_keys = ['Number of sequences', 'Number of bases', 'GC count',
                                     'Genes', 'RNA genes', 'rRNA genes', 'tRNA genes',
                                     'Protein coding genes', 'with Product Name']

                        # Sets list of keys to take percent and strip % from.
                        stats_keys_strip = ['GC count','with Product Name']

                        # Checks if any data is missing from above keys.
                        missing_meta = [key for key in meta_keys
                                       if key not in taxon['metadata']]

                        missing_stats = [key for key in stats_keys
                                        if key not in taxon['statistics']['assembled']]

                        # Sets missing data to be null value so that keys are not missing.
                        if missing_meta != []:
                            for key in missing_meta:
                                taxon['metadata'][key] = ''

                        if missing_stats != []:
                            for key in missing_stats:
                                taxon['statistics']['assembled'][key] = ['','']

                        # Retrieves data from JSON file.
                        taxon_stats = taxon['statistics']['assembled']
                        stats_data = [taxon_stats[key][0] if key not in stats_keys_strip
                                     else taxon_stats[key][1].strip('%') for key in stats_keys]

                        meta_data = [taxon['metadata'][key] if key != 'Annotation Method'
                                    else ' '.join(taxon['metadata']['Annotation Method'].split())
                                    for key in meta_keys]

                        ec_data = [ec_value[1] for ec_value in taxon['assembled'].values()]
                        ec_columns = [ec.strip('EC:') for ec in taxon['assembled']]

                        # Combines enzyme, metadata, and statistics into one list.
                        data = [[*ec_data, *stats_data, *meta_data]]
                        # Combines column names and enzyme names into one list.
                        columns = [*ec_columns, *stats_keys, *meta_keys]

                        # Creates Pandas DataFrame from data. Writes to a .csv file.
                        df = pd.DataFrame(data, columns = columns)
                        df.to_csv(join(self.dump_path, df['Taxon Object ID'][0] + '.csv'),index =False)

                # Updates progress bar
                pbar.update()

def main():
    """
    Calls the GatherRaw class for each domain to create initial .csv files.
    """
    jgi_path = '../../ecg/myjgi/'
    domain_path = '../jgi_raw_domains_oct2023/'
    meta_path = '../jgi_raw_metagenomes_oct2023/'

    GatherRaw('Archaea', jgi_path, domain_path)
    GatherRaw('Bacteria', jgi_path, domain_path)
    GatherRaw('Eukaryota', jgi_path, domain_path)
    combine_files(domain_path)

    # GatherRawMetagenome('Microbiome', jgi_path, meta_path)
    # combine_files(meta_path)

if __name__ == '__main__':
    main()
