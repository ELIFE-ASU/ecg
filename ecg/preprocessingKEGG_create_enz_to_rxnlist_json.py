import glob
import json
import copy
import os

"""
Creates a json containing all KEGG ECs, and the reactions each EC catalyzes.
Requires a directory containing a detailed json of each EC.
"""
def check_if_input_data_likely_valid(enz_dir):
    if not os.path.exists(enz_dir):
        raise KeyError("The directory \"%s\" does not exist"%enz_dir)

    if len(glob.glob(enz_dir+'*.json')) < 1:
        raise ValueError("\"%s\" does not contain any json files."%enz_dir)


def associate_enz_to_rxns(json_fname):
    with open(json_fname) as f:    
        ec_json = json.load(f)

    ec = ec_json[0]['entry_id']
    rxn_list = list()
    
    if ec_json[0]['kegg_reactions']:
        rxn_list += ec_json[0]['kegg_reactions'][0].split(' ')
    
    if ec_json[0]['iubmb_reactions']:
        rxn_list += ec_json[0]['iubmb_reactions'][0].split(' ')

    rxn_list = remove_non_rxn_items_from_rxn_list(rxn_list)

    return ec,list(set(rxn_list))

def remove_non_rxn_items_from_rxn_list(rxn_list):
    
    rxn_list_copy = copy.copy(rxn_list)
    for r in rxn_list_copy:
        if not r.startswith('R'):
            rxn_list.remove(r)

    return [r.strip("(G)") for r in rxn_list]

def create_enz_to_rxn_json(enz_dir,json_outfile):
    
    enz_to_rxns_dict = dict()
    
    for json_fname in glob.glob(enz_dir+'*.json'):
        ec,rxn_list = associate_enz_to_rxns(json_fname)
        enz_to_rxns_dict[ec] = rxn_list

    with open(json_outfile, 'w') as outfile:
        json.dump(enz_to_rxns_dict, outfile)

    print "%s has been written to drive."%json_outfile

def main():
    ## Input
    enz_dir = 'enzyme_jsons/'

    ## Output
    json_outfile = 'ec_to_rxnlist.json'

    check_if_input_data_likely_valid(enz_dir)    
    create_enz_to_rxn_json(enz_dir,json_outfile)

if __name__ == '__main__':
    main()