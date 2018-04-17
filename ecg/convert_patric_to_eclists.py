## parse_patric.py

import pandas as pd
import os
import glob

"""
Turns PATRIC's PATHWAY.tab files into master csv of ECs present in each genome.
Turns master csv into individual EC lists.
"""

def read_patric_files(dirname,subdir = False):
    """
    Turn PATRIC PATHWAY.tab files into list of dataframes.

    :param dirname: the filepath to the PATRIC files
    :param subdir: True if the .tab files are within subdirectorys
    """

    if subdir == True:
        subdirnames = glob.glob(dirname+'/*')

        fnames = []
        for subdir in subdirnames:
            fnames+=glob.glob(subdir+'/*.tab')

    else:
        ## Read in filenames
        fnames = glob.glob(dirname+'*.tab')
    
    fnames.sort()
    
    ## Convert all files to dataframes
    dfs = []
    for fname in fnames:
        dfs.append(pd.read_csv(fname, sep="\t"))

    return dfs


def create_genome_ec_dict(dfs):
    """
    Convert genomes into dicts,
    Also returns identifies union of all ECs across all genomes
    and list of degenerate genome_ids

    :param dfs: list of all genome dfs
    """
    genome_dict = {} # genome_name:[eIDs]
    all_ECs = set()
    genome_id_duplicates = []

    for df in dfs:

        if len(set(df['genome_id'])) == 1:
            genome_name = df['genome_name'][0]
            genome_id = df['genome_id'][0]
            ECs = set(df['ec_number'])
            
            if genome_id not in genome_id:
                genome_dict[genome_id] = ECs
            
            else:
                ## If more than 1 genome shares a name, create new name incorporating the genome_id
                # genome_name_with_id = genome_name+' '+str(genome_id)
                # genome_dict[genome_name_with_id] = ECs
                # print "genome_name: %s, id: %s already present in genome_dict. Creating new key: %s."%(genome_name,genome_id,genome_name_with_id)
                print "Warning-- genome_id: %s has multiple PATHWAY files"%s
                genome_id_duplicates.append(genome_id)

            all_ECs.update(ECs)
                
        elif len(set(df['genome_id'])) > 1:
            raise ValueError("Warning, there is more than one genome_id in this file")
        elif len(set(df['genome_id'])) == 0:
            raise ValueError("Warning, there are no genome_ids in this file")
        else:
            raise ValueError("Something went horribly wrong. There is a negative or decimal amount of genome_ids in this file")

    return genome_dict, all_ECs, genome_id_duplicates

def create_boolean_dict(genome_dict,all_ECs):
    """
    Create new dict of dicts to store genome names

    :param genome_dict: dict of key=genome_id, value=dict of genome's name, id, ec_numbers
    :param all_ECs: set of all ECs found across all genomes
    """
    ## new format: key=genome, value={EC:0 or 1}
    ## This makes it easy to write to file with pandas
    boolean_genome_dict = {}
    for genome_id in genome_dict:
        boolean_genome_dict[genome_id] = {}
        for EC in all_ECs:
            if EC in genome_dict[genome_id]:
                boolean_genome_dict[genome_id][EC] = 1
            else:
                boolean_genome_dict[genome_id][EC] = 0

    return boolean_genome_dict

def create_boolean_df(boolean_genome_dict):
    """
    Converts boolean_genome_dict to dataframe 

    :param boolean_genome_dict: dict of presence/absence of each EC for all genomes
    """

    boolean_genome_df = pd.DataFrame(boolean_genome_dict) # convert back to pandas df

    boolean_genome_df = boolean_genome_df.T # transpose to get in same format as 1k and 21k

    boolean_genome_df['sum']=boolean_genome_df.sum(axis=1) # add column for sum

    ## Move sum column to front of dataframe
    cols = boolean_genome_df.columns.tolist()
    cols.insert(0, cols.pop(cols.index('sum')))
    boolean_genome_df = boolean_genome_df.reindex(columns=cols)

    return boolean_genome_df

def boolean_df_to_ec_lists(boolean_genome_df):

    

###############################################################
def main():

    ## parameters to change --------------------------
    dirname = 'Archaea' # folder with patric files
    outfile = 'archaea_genomes.csv' # file to write
    ##------------------------------------------------

    dfs = read_patric_files(dirname,subdir=True)
    genome_dict, all_ECs = create_genome_ec_dict(dfs)
    boolean_genome_dict = create_boolean_dict(genome_dict,all_ECs)
    boolean_genome_df = create_boolean_df(boolean_genome_dict)

    boolean_genome_df.to_csv(outfile,index_label='species') # write to csv


if __name__=='__main__':
    main()


