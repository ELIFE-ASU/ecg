"""
WARNING. CLI HAS NOT BEEN TESTED YET.
DO I MAKE THIS A CLASS OR NOT? for gmls, i can just say: if rxn directory exists, use that. if not, run the reaction creation and then create gmls

Combine KEGG derived reaction data with JGI derived enzyme data to generate reaction lists (meta)genomes

Usage:
  ecg.py BIOSYSTEM_JSON write_biosystem_rxns EC_RXN_LINK_JSON [--outdir=<outdir>]

Arguments:
  BIOSYSTEM_JSON  Directory or file where JGI data is located
  EC_RXN_LINK_JSON    Json containing relationship between ec numbers and reactions
  write_biosystem_rxns   Download data from one or more (meta)genomes by URL

Options:
  --outdir=<outdir>   Path where biosystem reactions will be saved [default: "taxon_reactions"]

"""

import json
import glob
import os

class Ecg(object):

    def __init__(self,biosystem_json):
        self.__biosystem_json = biosystem_json
        self.__ec_rxn_link_json = None

    def __load_json(self,fname):
        """
        Wrapper to load json in single line

        :param fname: the filepath to the json file
        """
        with open(fname) as f:
            return json.load(f)

    def __write_json(self,data,fname):
        """
        Wrapper to write json in single line

        :param data: the data to write out
        :param fname: the filepath to write out
        """
        with open(fname, 'w') as outfile:
            json.dump(data, outfile)
    
    def _get_biosystem_eclist(self,biosystem_json):
        """
        Converts exhaustive JGI json to only a list of ECs
        """

        biosystem_json = self.__load_json(biosystem_json)
        
        ec_list = list()
        for d in biosystem_json['records']:
            ec_list.append(d['EnzymeID'].split("EC:")[1])
        
        return ec_list

    def _get_biosystem_rxnlist(self,ec_list,ec_rxn_link_json):
        """
        Converts list of ECs to list of reactions
        """
        if self.__ec_rxn_link_json == None:
            self.__ec_rxn_link_json = self.__load_json(ec_rxn_link_json)

        rxn_list = list()
        for ec in ec_list:
            ec_key = 'ec:'+ec
            if ec_key in self.__ec_rxn_link_json:
                rxn_list+=self.__ec_rxn_link_json[ec_key].split("rn:")[1]
            
        return rxn_list

    def _write_biosystem_rxns_from_jgi_json_file(self,infile,ec_rxn_link_json,outdir="taxon_reactions"):
        """
        Write a single biosystem's' reaction list (using the JGI json)
        """
        biosystem_json = self.__load_json(infile)
        ec_list = self._get_biosystem_eclist(biosystem_json)
        rxn_list = self._get_biosystem_rxnlist(ec_list,ec_rxn_link_json)
        outpath = os.path.join(outdir,os.path.basename(infile))
        self.__write_json(rxn_list,outpath)

    def _write_biosystem_rxns_from_jgi_json_dir(self,indir,ec_rxn_link_json,outdir="taxon_reactions"):
        """
        Write reaction lists from a directory of biosystems (all JGI jsons)
        """
        for fname in glob.glob(os.path.join(indir, '*.json')):
            self._write_biosystem_rxns_from_jgi_json_file(fname,ec_rxn_link_json,outdir)


    def write_biosystem_rxns(self,ec_rxn_link_json,outdir="taxon_reactions"):
        """
        Write reaction lists from either a single biosystem file or biosystem directory (all JGI jsons)
        """

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if os.path.isfile(self.__biosystem_json):
            self._write_biosystem_rxns_from_jgi_json_file(self.__biosystem_json,ec_rxn_link_json,outdir)
        
        elif os.path.isdir(self.__biosystem_json):
            self._write_biosystem_rxns_from_jgi_json_dir(self.__biosystem_json,ec_rxn_link_json,outdir)

    #######################################################################################################
    ### NX GRAPHS
    #######################################################################################################

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
            write_dir_to_outfpath=write_dir_to_outfpath, \
            write_dir_to_outfname=write_dir_to_outfname, \
            write_header_to_outfname=write_header_to_outfname, \
            write_fname_to_outfname=write_fname_to_outfname)
        
        ## Bipartite-directed-rxnsub needed for all graphs

        # print "outside ifs 2"
        # print graphtypes

        # if ('unipartite-directed-sub' or 'unipartite-undirected-subfromdirected') in graphtypes:
        #     print 'hello'

        genome_rxn_list, missing_ec_list = get_organism_rxn_list(genome_ec_list,ec_to_rxn_dict) ## Not outputting missing_ec_list right now
        B, rxns_missing_from_rxn_edges = create_bipartite_directed_rxn_sub_network(genome_rxn_list,rxn_edges,rxn_detailed_json_dir)

        if 'bipartite-directed-rxnsub' in graphtypes:

            print 'bipartite-directed-rxnsub'

            outfpath_final = gmldir+'bipartite-directed-rxnsub/'+outfpath+'.gml'
            
            create_dirs_for_path(outfpath_final)
            
            nx.write_gml(B,outfpath_final)

        if {'bipartite-undirected-rxnsub','unipartite-undirected-rxn','unipartite-undirected-sub'} & set(graphtypes):

            print '(bipartite-undirected-rxnsub or unipartite-undirected-rxn or unipartite-undirected-sub)'

            B_un = B.to_undirected()

            if 'bipartite-undirected-rxnsub' in graphtypes:

                print 'bipartite-undirected-rxnsub'

                outfpath_final = gmldir+'bipartite-undirected-rxnsub/'+outfpath+'.gml'

                create_dirs_for_path(outfpath_final)

                nx.write_gml(B_un,outfpath_final)

            if 'unipartite-undirected-rxn' in graphtypes:

                print 'unipartite-undirected-rxn'

                G_r = bipartite.projected_graph(B_un,[n for n in B_un.nodes() if n.startswith('R')])

                outfpath_final = gmldir+'unipartite-undirected-rxn/'+outfpath+'.gml'

                create_dirs_for_path(outfpath_final)

                nx.write_gml(G_r,outfpath_final)

            if 'unipartite-undirected-sub' in graphtypes:

                print 'unipartite-undirected-sub'

                G_c = bipartite.projected_graph(B_un, [n for n in B_un.nodes() if n.startswith('C')])

                outfpath_final = gmldir+'unipartite-undirected-sub/'+outfpath+'.gml'

                create_dirs_for_path(outfpath_final)

                nx.write_gml(G_c,outfpath_final)

        if {'unipartite-directed-sub','unipartite-undirected-subfromdirected'} & set(graphtypes):

            print '(unipartite-directed-sub or unipartite-undirected-subfromdirected)'

            G_cdir = bipartite.projected_graph(B, [n for n in B.nodes() if n.startswith('C')])

            if 'unipartite-directed-sub' in graphtypes:

                print 'unipartite-directed-sub'
                
                outfpath_final = gmldir+'unipartite-directed-sub/'+outfpath+'.gml'

                create_dirs_for_path(outfpath_final)

                nx.write_gml(G_cdir,outfpath_final)


            if 'unipartite-undirected-subfromdirected' in graphtypes:

                print 'unipartite-undirected-subfromdirected'

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

    def write_graphs_from_many_genomes_sampled(sample_size,fpathdir,gmldir,missingdir,graphtypes=['unipartite-undirected-subfromdirected'],write_dir_to_outfpath=True,write_dir_to_outfname=True,write_header_to_outfname=True,write_fname_to_outfname=True):
        """
        Writes multiple EC lists to one or more gml files.

        See `write_graphs_from_one_genome` docstring for details.

        :param fpathdir: the filepath to the directory of genomes
        :param sample_size: the number of graphs to make from a random selection of the ec_list
        """

        all_fpaths = [fpath for fpath in glob.glob(fpathdir+'*.dat')]

        gml_sample = random.sample(all_fpaths,sample_size)

        for fpath in gml_sample:

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




    # NEW PLAN
    # require master.json and enzyme_reaction_link.json 
    # if master.json isn't generated, tell user to generate it from the data they have using kegg.py
    # def get_omic_edges(master_json,ec_rxn_link_json,biosystem_json):
    #     """
    #     gets "reaction edges" from one or more genomes/metagenomes
    #     """


    # def write_graphs_from_many_genomes(fpathdir,gmldir,missingdir,graphtypes=['unipartite-undirected-subfromdirected'],write_dir_to_outfpath=True,write_dir_to_outfname=True,write_header_to_outfname=True,write_fname_to_outfname=True):
    #     """
    #     allows depreciating of convert_eclists_to_graphs.py
    #     allows user to turn their "reaction edges" (whether it's from all or kegg, a single organism, or many organisms)
    #     into a gml or networkx graph or whatever. ***not used for network expansion***
    #     """
    #     pass

    # OLD PLAN
    # takes as input either: 
    # master.json (master['reactions']['left'] and master['reactions']['right'])
    # and 
    # enzyme_reaction_link.json 
