import networkx as nx
import json
import os
import glob
import cPickle as pickle

def combine_all_compound_jsons_into_single_dict(compound_directory):

    compound_dict = dict()

    for path in glob.glob(compound_directory+"*.json"):
        # print path
        # outpath = outdirname+os.path.basename(path)

        with open(path) as data_file:    
            data = json.load(data_file)[0] #dict of single compound

            data["entry_type"] = "compound"

            compound_dict[data["entry_id"]] = data

    return compound_dict

def combine_all_reaction_jsons_into_single_dict(reaction_directory):

    reaction_dict = dict()

    for path in glob.glob(reaction_directory+"*.json"):
        # print path
        # outpath = outdirname+os.path.basename(path)

        with open(path) as data_file:    
            data = json.load(data_file)[0] #dict of single reaction

            data["entry_type"] = "reaction"

            reaction_dict[data["entry_id"]] = data

    return reaction_dict

def combine_compound_and_reaction_dicts(compound_dict,reaction_dict):
    return dict(compound_dict.items() + reaction_dict.items())

def create_networkx_graphs_from_edgelist_json(edge_filepath,attribute_dict=None):

    with open(edge_filepath) as data_file:
        data = json.load(data_file)

    G = nx.Graph()

    G.add_nodes_from(data["substrates"])
    G.add_nodes_from(data["products"])

    ## Add edges
    for k, v in data["substrates"].items():
        G.add_edges_from(([(k, t) for t in v]))
    for k, v in data["products"].items():
        G.add_edges_from(([(k, t) for t in v]))

    if attribute_dict:
        nx.set_node_attributes(G, attribute_dict)

    return G

def load_json(fname):
    """
    Wrapper to load json in single line

    :param fname: the filepath to the json file
    """
    with open(fname) as f:
        return json.load(f)

def write_json(data,fname):
    """
    Wrapper to write json in single line

    :param data: the data to write out
    :param fname: the filepath to write out
    """
    with open(fname, 'w') as outfile:
        json.dump(data, outfile)

def get_org_enzlist_from_org_json(organism_json):

    org_json = load_json(organism_json)

    org_enzlist = list()
    for d in org_json['records']:
        org_enzlist.append(d['EnzymeID'].split("EC:")[1])

    return org_enzlist

def get_org_rxnlist_from_org_json(organism_json):

    org_enzlist = get_org_enzlist_from_org_json(organism_json)

    ec_to_rxndict = load_json("ec_to_rxnlist.json")

    org_rxnlist = list()
    missing_list = list()
    for ec in org_enzlist:
        try:
            org_rxnlist+=ec_to_rxndict[ec]
        except:
            missing_list.append(ec)

    return org_rxnlist, missing_list

def create_reaction_edges_json_subset(organism_json,edge_filepath,json_outpath):

    org_rxnlist,missing_list = get_org_rxnlist_from_org_json(organism_json)

    reaction_edges_json = load_json("reaction_edges.json")

    reaction_edges_json_subset = {"products":dict(),"substrates":dict()}

    skipped_rxns = set()
    for rid in org_rxnlist:
        try:
            reaction_edges_json_subset["products"][rid] = reaction_edges_json["products"][rid]
        except:
            skipped_rxns.add(rid)
        try:
            reaction_edges_json_subset["substrates"][rid] = reaction_edges_json["substrates"][rid]
        except:
            skipped_rxns.add(rid)

    write_json(reaction_edges_json_subset,json_outpath)

    # D = create_networkx_graphs_from_edgelist_json(edge_filepath,attribute_dict)

    # print skipped_rxns
    ## ok good, for ds-80 these seem to all have glycans.
    
    # for k in reaction_edges_json:
    #     print k

    # print "missing_list:"
    # print missing_list

    # print reaction_edges_json_subset

    # print len(reaction_edges_json_subset['products']), len(reaction_edges_json['products'])
    # print len(reaction_edges_json_subset['substrates']), len(reaction_edges_json['substrates'])









def main():
    # compound_directory = "newdata/20171201/compounds/"
    # reaction_directory = "newdata/20171201/reactions_detailed/"
    # edge_filepath = "newdata/20171201/reaction_edges.json"
    # outpath = "newdata/20171201/kegg_reaction_compound_graph_with_attributes.pkl"

    # compound_dict = combine_all_compound_jsons_into_single_dict(compound_directory)
    # reaction_dict = combine_all_reaction_jsons_into_single_dict(reaction_directory)
    # attribute_dict = combine_compound_and_reaction_dicts(compound_dict,reaction_dict)
    # G = create_networkx_graphs_from_edgelist_json(edge_filepath,attribute_dict)

    # print "Pickling networkx graph..."

    # nx.write_gpickle(G, outpath)

    ############################################################
    ## create DS-80 reaction edges (ONLY NEED TO DO THIS ONCE)
    ############################################################
    # organism_json = "Acidianus_sp_DS-80.json"
    # edge_filepath = "reaction_edges.json"
    # json_outpath = "reaction_edges_ds-80.json"
    # create_reaction_edges_json_subset(organism_json,edge_filepath,json_outpath)
    ############################################################

    compound_directory = "compounds/"
    reaction_directory = "reactions_detailed/"
    edge_filepath = "reaction_edges_ds-80.json"
    # outpath = "ds-80_reaction_compound_graph_with_attributes.pkl"
    outpath = "ds-80_reaction_compound_graph_without_attributes.pkl"

    compound_dict = combine_all_compound_jsons_into_single_dict(compound_directory)
    reaction_dict = combine_all_reaction_jsons_into_single_dict(reaction_directory)
    attribute_dict = combine_compound_and_reaction_dicts(compound_dict,reaction_dict)
    G = create_networkx_graphs_from_edgelist_json(edge_filepath)

    print "Pickling networkx graph..."

    nx.write_gpickle(G, outpath)


    ############



    # create_networkx_graphs_from_edgelist_json(edge_filepath)
    # add_substrates_products_stoichiometry_to_reaction_jsons(dirname,outdirname)
    # test_parsing(outdirname)


if __name__ == '__main__':
    main()