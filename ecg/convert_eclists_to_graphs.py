import glob
import json
import os
from os.path import dirname, abspath, realpath, join
import networkx as nx
from networkx.algorithms import bipartite

"""
Turns EC lists into uniparite and biparite gml files.

Does this by looping through all directories of domains, and all EC lists therein.
Requires ec_to_rxnlist.json, rxn_edges.json, and a directory of all reaction .json
files.
"""

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

def get_header(line):
    """
    Returns string stripped of comment characters, or False
    if no comment characters present

    :param fname: the filepath to write out
    """
    if line.startswith("#"):
        return line.strip('# ')
    else:
        return False

def create_dirs_for_path(outfpath):
    dirpath = os.path.dirname(outfpath)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

def get_organism_ec_list(fpath,write_dir_to_outfpath=True,write_dir_to_outfname=True,write_header_to_outfname=True,write_fname_to_outfname=True):
    """
    The ec_list file must be organized as a single column,
    with or without a header.

    :param fpath: the filepath to the ec_list file
    :param write_dir_to_outfpath: if True, use parent dir for outfpath
    :param write_header_to_outfname: if True, use header row in outfile name
    :param write_dir_to_outfname: if True, use parent dir in outfile name
    :param write_fname_to_outfname: if True, use fpath basename in outfile name
    
    :raises Warning: if all optional arguments are False
    :raises ValueError: if ``write_dir_to_outfname`` is True, but no valid parent directory is detected
    :raises ValueError: if ``write_header_to_outfname`` is True, but no header is detected
    """
    outfname = []
    outfpath = ''

    with open(fpath) as f:
        lines = [line.rstrip('\n') for line in f]

        header = get_header(lines[0])

        ## Get genome_ec_list
        if header:
            genome_ec_list = lines[1:]

        else:
            genome_ec_list = lines[:]

        ## Get outfname
        if write_dir_to_outfname:
            if fpath.count('/') < 2:
                raise ValueError("gmls/ does not contain any subdirectories")
            else:
                parentdir=fpath.split('/')[-2]
                outfname.append(parentdir)
                outfpath+=(parentdir+'/')

        if write_header_to_outfname:
            if not header:
                raise ValueError("no header detected")

            else:
                outfname.append(header)

        if write_fname_to_outfname:
            
            outfname.append(fpath.split('/')[-1])

        else:
            raise Warning("when write_fname_to_outfname==False, \
                the outfname is not guaranteed to be unique, \
                and thus may overwrite existing files.")

        if (write_dir_to_outfname==False) and \
           (write_header_to_outfname==False) and \
           (write_fname_to_outfname==False):
           raise ValueError("all arguments cannot be False. No filename!")

    outfname=';'.join(outfname)
    outfpath=outfpath+outfname
    return outfpath, genome_ec_list

def get_organism_rxn_list(genome_ec_list,ec_to_rxn_dict):
    """
    Returns string stripped of comment characters, or False
    if no comment characters present

    :param fname: the filepath to write out
    """

    rxn_list = list()
    missing_ec_list = list()

    for ec in genome_ec_list:
        if ec in ec_to_rxn_dict:
            rxn_list += ec_to_rxn_dict[ec]
        else:
            missing_ec_list.append(ec)

    return rxn_list,missing_ec_list 

def create_bipartite_directed_rxn_sub_network(genome_rxn_list,rxn_edges,rxn_detailed_json_dir):
    """
    Create single bipartite-directed-rxnsub graph 

    :param genome_rxn_list: list of all reactions for a (meta)genome 
    :param rxn_edges: loaded json of all possible rxn edges in KEGG 
    :param rxn_detailed_json_dir: path to directory containing json files of all reactions 
    """
    G = nx.DiGraph()
    
    rxns_missing_from_rxn_edges = list()
    for rxn in genome_rxn_list:
        ## rxn nodes
        G.add_node(rxn,bipartite=0,type=0)

        if (rxn in rxn_edges['substrates']) and (rxn in rxn_edges['products']):
            ## compound nodes
            G.add_nodes_from(rxn_edges['products'][rxn],bipartite=1,type=1)
            G.add_nodes_from(rxn_edges['substrates'][rxn],bipartite=1,type=1)
            ## edges
            G.add_edges_from([(rxn,product) for product in rxn_edges['products'][rxn]])
            G.add_edges_from([(substrate,rxn) for substrate in rxn_edges['substrates'][rxn]])

        ## Check if any non-glycan reactions are missing
        else:
            rxn_json = load_json(rxn_detailed_json_dir+rxn+'.json')
            if rxn_json[0]['glycans'] == False:
                rxns_missing_from_rxn_edges.append(rxn)

    return G, rxns_missing_from_rxn_edges

def write_graphs_from_one_genome(fpath,gmldir,missingdir,graphtypes=['unipartite-undirected-subfromdirected'],write_dir_to_outfpath=True,write_dir_to_outfname=True,write_header_to_outfname=True,write_fname_to_outfname=True):
    """
    Write single EC list to one or more gml files.
    Steps:
    -create directed bipartite graph
    -project if needed
    -undirect if needed

    :param fpath: the filepath to the ec_list file
    :param gmldir: the dir to store gml files and subdirs in 
    :param graphtypes: which types of graphs to write to gml files. see notes
                       below for description of possible inputs.
    :param write_dir_to_outfpath: if True, use parent dir for outfpath
    :param write_header_to_outfname: if True, use header row in outfile name
    :param write_dir_to_outfname: if True, use parent dir in outfile name
    :param write_fname_to_outfname: if True, use fpath basename in outfile name

    ------------------------------------------
    Notes: 
    ------------------------------------------
    Implemented
    --------------------
    bipartite-directed-rxnsub
    bipartite-undirected-rxnsub
    unipartite-undirected-rxn
    unipartite-directed-sub
    unipartite-undirected-sub
    unipartite-undirected-subfromdirected --same connection rules used in 
                                            "Universal Scaling" paper
    --------------------
    Not yet implemented
    --------------------
    rxn-enz (bi directed/undirected)
            rxn-rxn (uni)
            enz-enz (uni)
    enz-sub (bi directed/undirected)
        enz-enz (uni)
        sub-sub (uni)
        sub-sub-restricted (uni)  
    ------------------------------------------
    Scratch notes:
    ------------------------------------------
        rxn-sub (bi directed/undirected)
            rxn-rxn (uni)
            sub-sub (uni)
            sub-sub-restricted (uni)
        rxn-enz (bi directed/undirected)
            rxn-rxn (uni)
            enz-enz (uni)
        enz-sub (bi directed/undirected)
            enz-enz (uni)
            sub-sub (uni)
            sub-sub-restricted (uni)    

    """

    ## Package data THESE SHOULD ALL BE FIXED INTERNALLY
    datapath = os.path.join(os.path.dirname(os.path.abspath(os.path.realpath(__file__))), "data")

    ec_to_rxn_dict = load_json(os.path.join(datapath,'ec_to_rxnlist.json'))
    rxn_edges = load_json(os.path.join(datapath,'reaction_edges.json'))
    rxn_detailed_json_dir = os.path.join(datapath,'reaction_detailed_jsons/')
    
    ## User data
    outfpath, genome_ec_list = get_organism_ec_list(fpath, \
        write_dir_to_outfname=write_dir_to_outfname, \
        write_header_to_outfname=write_header_to_outfname, \
        write_fname_to_outfname=write_fname_to_outfname)
    
    ## Bipartite-directed-rxnsub needed for all graphs

    genome_rxn_list, missing_ec_list = get_organism_rxn_list(genome_ec_list,ec_to_rxn_dict) ## Not outputting missing_ec_list right now
    B, rxns_missing_from_rxn_edges = create_bipartite_directed_rxn_sub_network(genome_rxn_list,rxn_edges,rxn_detailed_json_dir)

    if 'bipartite-directed-rxnsub' in graphtypes:

        outfpath_final = gmldir+'bipartite-directed-rxnsub/'+outfpath+'.gml'
        
        create_dirs_for_path(outfpath_final)
        
        nx.write_gml(B,outfpath_final)

    if ('bipartite-undirected-rxnsub' or 'unipartite-undirected-rxn' or 'unipartite-undirected-sub') in graphtypes:

        B_un = B.to_undirected()

        if 'bipartite-undirected-rxnsub' in graphtypes:

            outfpath_final = gmldir+'bipartite-undirected-rxnsub/'+outfpath+'.gml'

            create_dirs_for_path(outfpath_final)

            nx.write_gml(B_un,outfpath_final)

        if 'unipartite-undirected-rxn' in graphtypes:
            G_r = bipartite.projected_graph(B_un,[n for n in B_un.nodes() if n.startswith('R')])

            outfpath_final = gmldir+'unipartite-undirected-rxn/'+outfpath+'.gml'

            create_dirs_for_path(outfpath_final)

            nx.write_gml(G_r,outfpath_final)

        if 'unipartite-undirected-sub' in graphtypes:
            G_c = bipartite.projected_graph(B_un, [n for n in B_un.nodes() if n.startswith('C')])

            outfpath_final = gmldir+'unipartite-undirected-sub/'+outfpath+'.gml'

            create_dirs_for_path(outfpath_final)

            nx.write_gml(G_c,outfpath_final)

    if ('unipartite-directed-sub' or 'unipartite-undirected-subfromdirected') in graphtypes:

        G_cdir = bipartite.projected_graph(B, [n for n in B.nodes() if n.startswith('C')])

        if 'unipartite-directed-sub' in graphtypes:
            
            outfpath_final = gmldir+'unipartite-directed-sub/'+outfpath+'.gml'

            create_dirs_for_path(outfpath_final)

            nx.write_gml(G_cdir,outfpath_final)


        if 'unipartite-undirected-subfromdirected' in graphtypes:

            G_cun = G_cdir.to_undirected()

            outfpath_final = gmldir+'unipartite-undirected-subfromdirected/'+outfpath+'.gml'

            create_dirs_for_path(outfpath_final)

            nx.write_gml(G_cun,outfpath_final)

    ## Write ECs in genome missing from KEGG (if not empty)
    if missing_ec_list:
        missing_ec_list_outpath = missingdir+'genomes_containing_ecs_missing_from_kegg/'+outfpath
        create_dirs_for_path(missing_ec_list_outpath)
        write_json(missing_ec_list, missing_ec_list_outpath+'.json')
    
    ## Write rxns in genome missing from KEGG (if not empty)
    if rxns_missing_from_rxn_edges:
        rxns_missing_from_edges_outpath = missingdir+'genomes_containing_rxns_missing_from_kegg/'+outfpath
        create_dirs_for_path(rxns_missing_from_edges_outpath)
        write_json(rxns_missing_from_rxn_edges, rxns_missing_from_edges_outpath+'.json')

def write_graphs_from_many_genomes(fpathdir,gmldir,missingdir,graphtypes=['unipartite-undirected-subfromdirected'],write_dir_to_outfpath=True,write_dir_to_outfname=True,write_header_to_outfname=True,write_fname_to_outfname=True):
    """
    Writes multiple EC lists to one or more gml files.

    See `write_graphs_from_one_genome` docstring for details.

    :param fpathdir: the filepath to the directory of genomes
    """
    for fpath in glob.glob(fpathdir+'*.dat'):

        print "Creating gml from: %s ..."%fpath

        write_graphs_from_one_genome(
            fpath,
            gmldir,
            missingdir,
            graphtypes=graphtypes, 
            write_dir_to_outfpath=write_dir_to_outfpath,
            write_dir_to_outfname=write_dir_to_outfname,
            write_header_to_outfname=write_header_to_outfname,
            write_fname_to_outfname=write_fname_to_outfname)


def main():
    #------------------------------------
    # Single genome
    #------------------------------------
    # ## Paths to user directories
    # fpath = 'userdata/domain_ec_lists/ecosystem_JGI/effective_ec_ecosystem_JGI-1.dat'
    # gmldir = 'userdata/gmls/'
    # missingdir = 'userdata/missingdata/'
    
    # ## Input
    # graphtypes = ['bipartite-directed-rxnsub']
    # write_dir_to_outfpath=True
    # write_dir_to_outfname=True
    # write_header_to_outfname=True
    # write_fname_to_outfname=True

    # write_graphs_from_one_genome(
    #     fpath,
    #     gmldir,
    #     missingdir,
    #     graphtypes=graphtypes, 
    #     write_dir_to_outfpath=write_dir_to_outfpath,
    #     write_dir_to_outfname=write_dir_to_outfname,
    #     write_header_to_outfname=write_header_to_outfname,
    #     write_fname_to_outfname=write_fname_to_outfname)

    #------------------------------------
    # Many genomes
    #------------------------------------
    ## Paths to user directories
    fpathdir = 'userdata/domain_ec_lists/ecosystem_JGI/'
    gmldir = 'userdata/gmls/'
    missingdir = 'userdata/missingdata/'
    
    ## Input
    graphtypes = ['bipartite-directed-rxnsub']
    write_dir_to_outfpath=True
    write_dir_to_outfname=True
    write_header_to_outfname=True
    write_fname_to_outfname=True

    write_graphs_from_many_genomes(
        fpathdir,
        gmldir,
        missingdir,
        graphtypes=graphtypes, 
        write_dir_to_outfpath=write_dir_to_outfpath,
        write_dir_to_outfname=write_dir_to_outfname,
        write_header_to_outfname=write_header_to_outfname,
        write_fname_to_outfname=write_fname_to_outfname)

    ## Need to write a script which matches the PATRIC IDs to the species names

# def loop_through_domain_directories(domain_dir,gml_dir,ec_to_rxnlist,rxn_edges,rxn_detailed_json_dir):

#     for ec_path in glob.glob(domain_dir+'*'):
#         print "looping through %s ..."%ec_path

#         loop_through_ec_lists(ec_path,gml_dir,ec_to_rxnlist,rxn_edges,rxn_detailed_json_dir)




# def main():
    
#     get_organism_ec_list('domain_ec_lists/ecosystem_JGI/effective_ec_ecosystem_JGI-1.dat')

#     # ## Inputs
#     domain_dir = 'data/domain_ec_lists/'
#     rxn_detailed_json_dir = 'data/reaction_detailed_jsons/'
#     ec_to_rxnlist = load_json('data/ec_to_rxnlist.json')
#     rxn_edges = load_json('data/reaction_edges.json')

#     # ## Outputs
#     gml_dir = 'gmls/'

    # loop_through_domain_directories(domain_dir,gml_dir,ec_to_rxnlist,rxn_edges,rxn_detailed_json_dir)




## todo:
## - add test cases for all functions




if __name__ == '__main__':
    main()