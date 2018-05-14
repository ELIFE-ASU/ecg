## parse_patric.py

import pandas as pd
import os
import glob

"""
Turns PATRIC's PATHWAY.tab files into master csv of ECs present in each genome.

write_boolean_genome_master_csv is the only function in the file meant to be called directly.
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
        dfs.append(pd.read_csv(fname, sep="\t", dtype={'genome_id': str}))

    # print dfs[0]

    return dfs


def create_genome_ec_dict(dfs):
    """
    Convert genomes into dicts,
    Also returns identifies union of all ECs across all genomes
    and list of degenerate genome_ids

    :param dfs: list of all genome dfs
    """
    genome_dict = {} # genome_id: {}, where {} is keyed by: 'ECs'[eIDs],genome_name,genome_name_with_id,duplicate
    all_ECs = set()
    genome_id_duplicates = []

    for df in dfs:

        if len(set(df['genome_id'])) == 1:

            genome_name = df['genome_name'][0]
            genome_id = df['genome_id'][0]
            ECs = set(df['ec_number'])
            genome_name_with_id = genome_name+' '+str(genome_id)

            genome_dict[genome_id] = {}
            genome_dict[genome_id]['genome_name'] = genome_name
            genome_dict[genome_id]['genome_name_with_id'] = genome_name+' '+str(genome_id)
            genome_dict[genome_id]['duplicate'] = 0
            
            if 'ECs' not in genome_dict[genome_id]:
                genome_dict[genome_id]['ECs'] = ECs 
                # genome_dict[genome_id] = ECs
            
            else:
                ## If more than 1 genome shares a name, create new name incorporating the genome_id
                # genome_name_with_id = genome_name+' '+str(genome_id)
                # genome_dict[genome_name_with_id] = ECs
                # print "genome_name: %s, id: %s already present in genome_dict. Creating new key: %s."%(genome_name,genome_id,genome_name_with_id)
                print "Warning-- genome_id: %s has multiple PATHWAY files"%genome_id
                genome_dict[genome_id]['duplicate'] = 1

            all_ECs.update(ECs)
                
        elif len(set(df['genome_id'])) > 1:
            raise ValueError("Warning, there is more than one genome_id in this file")
        elif len(set(df['genome_id'])) == 0:
            raise ValueError("Warning, there are no genome_ids in this file")
        else:
            raise ValueError("Something went horribly wrong. There is a negative or decimal amount of genome_ids in this file")

    return genome_dict, all_ECs

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
        boolean_genome_dict[genome_id]['genome_name'] = genome_dict[genome_id]['genome_name']
        boolean_genome_dict[genome_id]['genome_name_with_id'] = genome_dict[genome_id]['genome_name_with_id']
        boolean_genome_dict[genome_id]['duplicate'] = genome_dict[genome_id]['duplicate'] 

        for EC in all_ECs:
            if EC in genome_dict[genome_id]['ECs']:
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

    # print boolean_genome_df.head()

    col_list = list(boolean_genome_df)#.columns

    # print col_list
    col_list.remove('duplicate')
    col_list.remove('genome_name_with_id')
    col_list.remove('genome_name')

    boolean_genome_df['sum']=boolean_genome_df[col_list].sum(axis=1) # add column for sum

    ## Move sum column to front of dataframe
    cols = boolean_genome_df.columns.tolist()
    cols.insert(0, cols.pop(cols.index('sum')))
    cols.insert(0, cols.pop(cols.index('duplicate')))
    cols.insert(0, cols.pop(cols.index('genome_name_with_id')))
    cols.insert(0, cols.pop(cols.index('genome_name')))

    boolean_genome_df = boolean_genome_df.reindex(columns=cols)

    return boolean_genome_df

###############################################################
def write_boolean_genome_master_csv(dirname,subdir,outfile):
    """
    Turns PATRIC's PATHWAY.tab files into master csv of ECs present in each genome.
    This is the only function in the file meant to be called directly.

    :param dirname: the filepath to the PATRIC files
    :param subdir: True if the .tab files are within subdirectorys
    :param outfile: filename to write csv to
    """

    dfs = read_patric_files(dirname,subdir=subdir)
    genome_dict, all_ECs = create_genome_ec_dict(dfs)
    boolean_genome_dict = create_boolean_dict(genome_dict,all_ECs)
    boolean_genome_df = create_boolean_df(boolean_genome_dict)

    # print boolean_genome_df

    boolean_genome_df.to_csv(outfile,index_label='species') # write to csv


## Do i even use the master csv to create the invididual ec list csvs?



###############################################################
def main():

    ## parameters to change --------------------------
    dirname = 'userdata/PATRIC_Export_pathways' # folder with patric files
    subdir = True
    outfile = 'test_patric_parse.csv' # file to write
    ##------------------------------------------------

    write_boolean_genome_master_csv(dirname,subdir,outfile)

    


if __name__=='__main__':
    main()


