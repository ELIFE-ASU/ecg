"""
.. currentmodule:: data_pipeline.FilterRaw

Filters the processed data from JGI and KEGG.
"""
import json
from os.path import join
import pandas as pd

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

class FilterRaw:
    """
    A class to filter the combined .csv data. Filters are from the enzyme scaling paper.

    :param path: Path of raw combined .csv.
    :type path: str.
    """
    def __init__(self,path):
        # Path to raw combined .csv.
        self.path = path

        # Path to processed kegg enzyme data.
        self.kegg_path = '../Processed_data/enzyme_primary.json'

        # List of enzymes in KEGG data.
        self.kegg_list = self._create_kegg_list()

        # Loads the combined raw data for the three domains.
        self.data = pd.read_csv(self.path)

        # Filters the data.
        self._prune_data()

        # Saving filtered data.
        self._save_data()

    def _create_kegg_list(self):
        """
        Takes the Pandas DataFrame and removes enzyme columns not found in pruned kegg data.

        :return: List of enzymes in KEGG data.
        """

        # Loads the kegg json for enzymes with glycan data removed.
        kegg_enzymes = load_json(self.kegg_path)
        # Removes all entries for EC 7.
        seven_enzymes = [key for key in kegg_enzymes.keys() if key.startswith('7')]
        # Creates list of enzymes with EC 7 removed.
        kegg_enzymes_list = [k for k in kegg_enzymes.keys() if k not in seven_enzymes]

        return kegg_enzymes_list

    def _prune_data(self):
        """
        Prunes the data in the DataFrame by:
            1. Removing enzymes with partial names (example: 1.1.1.-).
            2. Removing enyzmes not found in kegg (associated with glycans).
            3. Removing fungal annotated entries in eukaryotes as they are suspect.
            4. Removing entries that are at extremes of percent functional coding genes
               (<10% | > 90%).
            5. Removing entries that are below the minimal gene size:
               1364 for prokaryotes,4718 for eukaryotes.
        """

        # Loads the combined raw data for the three domains.
        self.data = pd.read_csv(self.path, low_memory= False)

        # Prunes the data.
        self._remove_partial_enzymes()
        self._remove_glycan_enzymes()
        self._remove_fungal_entries()
        self._remove_outlier_coding()
        self._remove_minimal_genes()

    def _remove_partial_enzymes(self):
        """
        Takes the Pandas DataFrame and removes partial enzyme columns.
        """

        # Finds the enzyme columns.
        enzyme_columns = [col for col in self.data.columns if not col[0].isalpha()]

        # Finds columns in enzyme column list to prune
        partial_columns = [col for col in enzyme_columns if '-' in col]

        # Prints status of removed items.
        print(f'Removed {len(partial_columns)} partial enzyme columns with .-.')

        # Prunes the columns.
        self.data.drop(partial_columns, axis = 1, inplace = True)

    def _remove_glycan_enzymes(self):
        """
        Takes the Pandas DataFrame and removes enzyme columns not found in pruned kegg data.
        """

        # Finds the prunable columns.
        prune_columns = [col for col in self.data.columns
                        if (col not in self.kegg_list) & ( not col[0].isalpha())]

        # Prints status of removed items.
        print(f'Removed {len(prune_columns)} non-Kegg enzyme columns.')

        # Prunes the columns.
        self.data.drop(prune_columns, axis = 1, inplace = True)

    def _remove_fungal_entries(self):
        """
        Takes the Pandas DataFrame and removes fungal entries.
        """

        # Finds indexes of fungal annotation.
        drop_index = self.data[self.data['JGI Analysis Product Name'] == 'Fungal Annotation'].index

        # Prints status of removed items.
        print(f'Removed {len(drop_index)} Fungal Annotation entries.')

        # Prunes the indexes.
        self.data.drop(drop_index, inplace = True)

    def _remove_outlier_coding(self, min_coding = 10, max_coding = 90):
        """
        Takes the Pandas DataFrame and removes entries outside percent coding boundaries.

        :param min_coding: Minimum coding percentage (Default = 10)
        :type min_coding: int.

        :param max_coding: Maximum coding percentage (Default = 90)
        :type max_coding: int.
        """

        # Finds indexes outside coding boundaries.
        drop_index = self.data[
                     (self.data['Protein coding genes with function prediction'] > max_coding) |
                     (self.data['Protein coding genes with function prediction'] < min_coding)
                     ].index

        # Prints status of removed items.
        print(f'Removed {len(drop_index)} percent coding outliers')

        # Prunes the indexes.
        self.data.drop(drop_index, inplace = True)

    def _remove_minimal_genes(self, prokaryote_min = 1354, eukaryote_min = 4718):
        """
        Takes the Pandas DataFrame and removes entries that are below minimal gene size for a
        living organism.

        :param prokaryote_min: Minimum gene size for prokaryote. (Bacteria and Archaea)
                               (Default = 1354)
        :type prokaryote_min: int.

        :param eukaryote_min: Minimum gene size for eukaryote (Default = 4718)
        :type eukaryote_min: int.
        """

        # Finds the indexes of prokaryotes below minimum gene size.
        drop_pro_index = self.data[((self.data['Domain'] == 'Bacteria') |
                                  (self.data['Domain'] == 'Archaea')) &
                                  (self.data['Genes total number'] < prokaryote_min)].index

        # Prints status of removed items.
        index_size = len(drop_pro_index)
        print(f'Removed {index_size} prokaryote entries with less than minimal gene size.')

        # Prunes prokaryote indexes below minimum size.
        self.data.drop(drop_pro_index, inplace = True)

        # Finds the indexes of eukaryotes below minimum gene size.
        drop_euk_index = self.data[(self.data['Domain'] == 'Eukaryota') &
                                   (self.data['Genes total number'] < eukaryote_min)].index

        # Prints status of removed items.
        index_size = len(drop_euk_index)
        print(f'Removed {index_size} eukaryote entries with less than minimal gene size.')

        # Prunes eukaryote indexes below minimum size.
        self.data.drop(drop_euk_index, inplace = True)

    def _save_data(self):
        print('Printing Filtered Combined Data: CSV')
        self.data.to_csv('../Clean_Data_Combined.csv', index = False)

class FilterRawMetagenome(FilterRaw):
    """
    A class to filter the combined .csv data. Filters are from the enzyme scaling paper.

    :param path: Path of raw combined .csv.
    :type path: str.
    """

    def _prune_data(self):
        """
        Prunes the data in the DataFrame by:
            1. Removing enzymes with partial names (example: 1.1.1.-).
            2. Removing enyzmes not found in kegg (associated with glycans).
            3. Removing entries that are at extremes of percent functional coding genes
               (<10% | > 90%).
            4. Removing entries that are below the minimal gene size: 27280.
        """

        # Loads the combined raw data for metagenomes. These columns have mixed types and throw
        # up errors when imported. I think that they have some weird makeup with non-number values
        # inside them. In any case, they do not have many entries and I may delete them after
        # talking with Pilar.
        dtypes = {'Chlorophyll Concentration': "string",
                  'GOLD Sequencing Depth' : "string",
                  'Nitrate Concentration' : "string",
                  'Oxygen Concentration' : "string",
                  'Pressure' : "string",
                  'Proportal Isolation' : "string",
                  'Proportal Ocean' : "string",
                  'Salinity Concentration' : "string",
                  'pH' : "string"}
        self.data = pd.read_csv(self.path, dtype=dtypes, low_memory=False)
        #self.data = pd.read_csv(self.path)

        # Prunes the data.
        self._remove_partial_enzymes()
        self._remove_glycan_enzymes()
        self._remove_outlier_coding()
        self._remove_minimal_genes()

    def _remove_outlier_coding(self, min_coding = 10, max_coding = 90):
        """
        Takes the Pandas DataFrame and removes entries outside percent coding boundaries for
        metagenomes. Metagenomes have different coding percentage entries in statistics.

        :param min_coding: Minimum coding percentage (Default = 10)
        :type min_coding: int.

        :param max_coding: Maximum coding percentage (Default = 90)
        :type max_coding: int.
        """
 
        # Finds indexes outside coding boundaries.
        drop_index = self.data[
                    (self.data['with Product Name'] > max_coding) |
                    (self.data['with Product Name'] < min_coding)].index

        # Prints status of removed items.
        print(f'Removed {len(drop_index)} percent coding outliers')

        # Prunes the indexes.
        self.data.drop(drop_index, inplace = True)

    def _remove_minimal_genes(self, metagenome_min = 13540):
        """
        Takes the Pandas DataFrame and removes entries that are below minimal gene size for
        a metagenome. Assumption is that there are at least 20 free living prokaryotes, which
        gives a minimum size of (10*1354) = 13540

        :param metagenome_min: Minimum gene size for metagenome. (Default = 13540)
        :type metagenome_min: int.
        """

        # Finds the indexes of metagenomes below minimum gene size.
        drop_metagenome_index = self.data[self.data['Protein coding genes'] < metagenome_min].index

        # Prints status of removed items.
        index_size = len(drop_metagenome_index)
        print(f'Removed {index_size} metagenome entries with less than minimal gene size.')

        # Prunes eukaryote indexes below minimum size.
        self.data.drop(drop_metagenome_index, inplace = True)

    def _save_data(self):
        print('Printing Filtered Combined Metagenome Data: CSV')
        self.data.to_csv('../Clean_Metagenome_Data_Combined.csv', index = False)

def main():
    """
    Calls the FilterRaw class to filter the combined .csv file.
    """
    FilterRaw('../Raw_Data_Combined.csv')
    FilterRawMetagenome('../Raw_Metagenome_Data_Combined.csv')

if __name__ == '__main__':
    main()
