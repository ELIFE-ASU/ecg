## parse_patric.py

import pandas as pd
import os
import glob

"""
Turns PATRIC's PATHWAY.tab files into EC lists of ECs present in each genome.
Turns PATRIC's PATHWAY.tab files into master csv of ECs present in each genome.
Turns JGI .json files into EC lists of ECs present in each genome or metagenome.
Turns JGI .json files into master csv of ECs present in each genome or metagenome.

Functions meant to be called directly:
- write_patric_ec_lists_from_tabs
- write_patric_boolean_csv_from_tabs
- write_jgi_ec_lists_from_jsons
- write_jgi_boolean_csv_from_jsons
"""
###############################################################################
## PATRIC (not directly called)
###############################################################################
def read_patric_files(tab_dir,subdir = False):
    """
    Turn PATRIC PATHWAY.tab files into list of dataframes.

    :param tab_dir: the filepath to the PATRIC files
    :param subdir: True if the .tab files are within subdirectorys
    """

    if subdir == True:
        subdirnames = glob.glob(tab_dir+'/*')

        fnames = []
        for subdir in subdirnames:
            fnames+=glob.glob(subdir+'/*.tab')

    else:
        ## Read in filenames
        fnames = glob.glob(tab_dir+'*.tab')
    
    fnames.sort()
    
    ## Convert all files to dataframes
    dfs = []
    for fname in fnames:
        dfs.append(pd.read_csv(fname, sep="\t", dtype={'genome_id': str}))

    # print dfs[0]

    return dfs


def create_patric_ec_dict(dfs):
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

def create_patric_boolean_dict(genome_dict,all_ECs):
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

def create_patric_boolean_df(boolean_genome_dict):
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

###############################################################################
## JGI (not directly called)
###############################################################################
def create_jgi_ec_dict(json_dir):

    all_eukarya_dict = dict()
    for json_file in glob.glob(json_dir+'/*'):
        
        with open(json_file) as f:
            eukaryote_id = json_file.split('/')[-1].split('.json')[0]
            all_eukarya_dict[eukaryote_id] = dict()
            
            json_data = json.load(f)

            for EC in natsorted(json_data['genome']):
                EC_number = EC.split(':')[1]
                EC_count = int(json_data['genome'][EC][1])
                all_eukarya_dict[eukaryote_id][EC_number] = EC_count

    return all_eukarya_dict

###############################################################################
## Functions to directly call (JGI and PATRIC)
###############################################################################

def write_patric_ec_lists_from_tabs(tab_dir,subdir,output_dir):
    """
    Turns PATRIC's PATHWAY.tab files into EC lists of ECs present in each genome.

    :param tab_dir: the filepath to the PATRIC files
    :param subdir: True if the .tab files are within subdirectorys
    :param output_dir: dir to write output ec lists
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    dfs = read_patric_files(tab_dir,subdir=subdir)
    genome_dict, all_ECs = create_patric_ec_dict(dfs)
    boolean_genome_dict = create_patric_boolean_dict(genome_dict,all_ECs)

    for genome_id in boolean_genome_dict:
        with open(output_dir+'/'+genome_id+'.dat','w') as f:
            f.write("# %s\n" %genome_id)
            for EC in natsorted(boolean_genome_dict[genome_id]):
                if boolean_genome_dict[genome_id][EC] == 1:
                    f.write("%s\n" %EC)

def write_patric_boolean_csv_from_tabs(tab_dir,subdir,outfile):
    """
    Turns PATRIC's PATHWAY.tab files into master csv of ECs present in each genome.

    :param tab_dir: the filepath to the PATRIC files
    :param subdir: True if the .tab files are within subdirectorys
    :param outfile: filename to write csv to
    """

    dfs = read_patric_files(tab_dir,subdir=subdir)
    genome_dict, all_ECs = create_patric_ec_dict(dfs)
    boolean_genome_dict = create_patric_boolean_dict(genome_dict,all_ECs)
    boolean_genome_df = create_patric_boolean_df(boolean_genome_dict)

    boolean_genome_df.to_csv(outfile,index_label='species') # write to csv

def write_jgi_ec_lists_from_jsons(json_dir,output_dir):
    """
    Turns JGI's .json files into EC lists of ECs present in each meta/genome.

    :param json_dir: filepath to the jgi json files
    :param output_dir: dir to write output ec lists
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    all_eukarya_dict = create_jgi_ec_dict(json_dir)

    for eukaryote_id in all_eukarya_dict:
        with open(output_dir+'/'+eukaryote_id+'.dat','w') as f:
            f.write("# %s\n" %eukaryote_id)
            for EC in natsorted(all_eukarya_dict[eukaryote_id]):
                f.write("%s\n" %EC)

def write_jgi_boolean_csv_from_jsons(json_dir,outfile):
    """
    Turns JGI's .json files into master csv of ECs present in each meta/genome.

    :param json_dir: filepath to the jgi json files
    :param outfile: filename to write csv to
    """

    all_eukarya_dict = create_jgi_ec_dict(json_dir)

    eukarya_df = pd.DataFrame.from_dict(all_eukarya_dict)

    eukarya_df = eukarya_df.T

    eukarya_df = eukarya_df.fillna(0).astype(int)

    eukarya_df.to_csv(outfile)  


###############################################################
def main():

    ## PATRIC
    ## parameters to change --------------------------
    tab_dir = 'userdata/PATRIC_Export_pathways' 
    subdir = True
    outfile = 'test_patric_boolean_csv.csv' # file to write
    ## OR---------------------------------------------
    output_dir = 'userdata/domain_ec_lists/PATRIC'
    ## -----------------------------------------------

    write_patric_boolean_csv_from_tabs(tab_dir,subdir,outfile)
    write_patric_ec_lists_from_tabs(tab_dir,subdir,output_dir)

    ##################################################

    ## JGI
    ## parameters to change --------------------------
    json_dir = 'userdata/jgi_eukarya_jsons_20180403'
    output_dir = 'userdata/domain_ec_lists/individual_eukarya'
    ## OR---------------------------------------------
    outfile = 'test_jgi_boolean_csv.csv' # file to write
    ## -----------------------------------------------

    write_jgi_ec_lists_from_jsons(json_dir,output_dir)
    write_jgi_boolean_csv_from_jsons(json_dir,outfile)

    


if __name__=='__main__':
    main()


