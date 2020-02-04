import json
import glob
import os
import networkx as nx
from networkx.algorithms import bipartite
import argparse

class Ecg(object):

    def __init__(self):
        self.__ec_rxn_link_json = None
        self.__master_json = None

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
            json.dump(data, outfile, indent=2)
    
    #######################################################################################################
    ### RXN JSONS
    #######################################################################################################
    
    def _get_biosystem_eclist(self,biosystem_json):
        """
        Converts exhaustive JGI json to only a list of ECs
        """

        biosystem_json = self.__load_json(biosystem_json)
        
        ec_list = list()
        try:
            for ec in biosystem_json["enzymes"]:
                try:
                    ec_list.append(ec.split("EC:")[1])
                except:
                    pass
        except:
            pass
        
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
                for rxn in self.__ec_rxn_link_json[ec_key]:
                    rxn_list.append(rxn.split("rn:")[1])
            
        return rxn_list

    def _write_biosystem_rxns_from_jgi_json_file(self,infile,ec_rxn_link_json,outdir="taxon_reactions"):
        """
        Write a single biosystem's' reaction list (using the JGI json)
        """
        ec_list = self._get_biosystem_eclist(infile)
        rxn_list = self._get_biosystem_rxnlist(ec_list,ec_rxn_link_json)
        outpath = os.path.join(outdir,os.path.basename(infile))
        self.__write_json(rxn_list,outpath)

    def _write_biosystem_rxns_from_jgi_json_dir(self,indir,ec_rxn_link_json,outdir="taxon_reactions"):
        """
        Write reaction lists from a directory of biosystems (all JGI jsons)
        """
        for fname in glob.glob(os.path.join(indir, '*.json')):
            self._write_biosystem_rxns_from_jgi_json_file(fname,ec_rxn_link_json,outdir)


    def write_biosystem_rxns(self,biosystem_json,ec_rxn_link_json,outdir="taxon_reactions"):
        """
        Write reaction lists from either a single biosystem file or biosystem directory (all JGI jsons)
        """

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if os.path.isfile(biosystem_json):
            self._write_biosystem_rxns_from_jgi_json_file(biosystem_json,ec_rxn_link_json,outdir)
        
        elif os.path.isdir(biosystem_json):
            self._write_biosystem_rxns_from_jgi_json_dir(biosystem_json,ec_rxn_link_json,outdir)

    #######################################################################################################
    ### NX GRAPHS
    #######################################################################################################
    def __create_base_network(self,biosys_rxn_json,master_json):
        """
        Create single bipartite-directed-rxnsub graph, used to create all subsequent graphs

        :param biosys_rxn_json: loaded json of all reactions for a (meta)genome
        :param master_json: loaded json of all possible rxn edges and detailed data in KEGG 
        """
        G = nx.DiGraph()

        rxn_list = self.__load_json(biosys_rxn_json)
        if self.__master_json == None:
            self.__master_json = self.__load_json(master_json)
        
        rxns_missing_from_rxn_edges = list()
        for rxn in rxn_list:
            ## rxn nodes
            G.add_node(rxn,bipartite=0,type=0)

            if rxn in self.__master_json["reactions"]:
                ## compound nodes- this is needed to assign bipartite type
                G.add_nodes_from(self.__master_json["reactions"][rxn]["left"],bipartite=1,type=1)
                G.add_nodes_from(self.__master_json["reactions"][rxn]["right"],bipartite=1,type=1)
                ## edges
                G.add_edges_from([(rxn,cpd) for cpd in self.__master_json["reactions"][rxn]["right"]])
                G.add_edges_from([(cpd,rxn) for cpd in self.__master_json["reactions"][rxn]["left"]])

            ## Check if any non-glycan reactions are missing
            else:
                # if self.__master_json["reactions"][rxn]['glycans'] == False:
                rxns_missing_from_rxn_edges.append(rxn)

        return G, rxns_missing_from_rxn_edges

    def _write_biosystem_graphs_from_json_file(self,
                                               biosys_rxn_json,
                                               master_json,
                                               graphtypes=["unipartite-undirected-subfromdirected"],
                                               outdir="graphs",
                                               missingdir="taxon_with_rxns_missing_from_kegg",
                                               verbose=True):
        """
        Write single biosystem's reaction json to one or more gml files.

        :param biosys_rxn_json: the filepath to the biosystem reaction json file
        :param master_json: the filepath to the json with details information about all KEGG reactions
        :param graphtypes: which types of graphs to write to gml files. see notes
                           below for description of possible inputs.
        :param outdir: the dir to store subdirs for each graph type, and subsequent gml files
        :param missingdir: the dir to store reactions which are missing from biosystems as jsons
        :param verbose: if True, prints the graph types as they're created

        ---------------------------------------------------------------------------------
        Notes: 
        ---------------------------------------------------------------------------------
        Steps involved:
        1. Creates directed bipartite graph
        2. Projects graph if needed
        3. Undirects graph if needed

        These steps allow for less overhead when wishing to produce multiple graph types.

        ------------------------
        Implemented graphtypes:
        ------------------------
        bipartite-directed-rxnsub
        bipartite-undirected-rxnsub
        unipartite-undirected-rxn
        unipartite-directed-sub
        unipartite-undirected-sub
        unipartite-undirected-subfromdirected --same connection rules used in 
                                                "Universal Scaling" paper
        """

        B, rxns_missing_from_rxn_edges = self.__create_base_network(biosys_rxn_json,master_json)
        biosys_id = os.path.splitext(os.path.basename(biosys_rxn_json))[0]
        for graphtype in graphtypes:
            dirpath = os.path.join(outdir,graphtype)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)

        if "bipartite-directed-rxnsub" in graphtypes:

            if verbose: print("bipartite-directed-rxnsub")

            outfpath_final = os.path.join(outdir,"bipartite-directed-rxnsub",biosys_id+".gml")           
            nx.write_gml(B,outfpath_final)
        
        if {'bipartite-undirected-rxnsub','unipartite-undirected-rxn','unipartite-undirected-sub'} & set(graphtypes):

            if verbose: print("(bipartite-undirected-rxnsub or unipartite-undirected-rxn or unipartite-undirected-sub)")

            B_un = B.to_undirected()

            if 'bipartite-undirected-rxnsub' in graphtypes:

                if verbose: print("- bipartite-undirected-rxnsub")

                outfpath_final = os.path.join(outdir,"bipartite-undirected-rxnsub",biosys_id+".gml")          
                nx.write_gml(B_un,outfpath_final)

            if 'unipartite-undirected-rxn' in graphtypes:

                if verbose: print("- unipartite-undirected-rxn")

                G_r = bipartite.projected_graph(B_un,[n for n in B_un.nodes() if n.startswith('R')])
                outfpath_final = os.path.join(outdir,"unipartite-undirected-rxn",biosys_id+".gml")
                nx.write_gml(G_r,outfpath_final)

            if 'unipartite-undirected-sub' in graphtypes:

                if verbose: print("- unipartite-undirected-sub")

                G_c = bipartite.projected_graph(B_un, [n for n in B_un.nodes() if n.startswith('C')])
                outfpath_final = os.path.join(outdir,"unipartite-undirected-sub",biosys_id+".gml")
                nx.write_gml(G_c,outfpath_final)

        if {'unipartite-directed-sub','unipartite-undirected-subfromdirected'} & set(graphtypes):

            if verbose: print("(unipartite-directed-sub or unipartite-undirected-subfromdirected)")

            G_cdir = bipartite.projected_graph(B, [n for n in B.nodes() if n.startswith('C')])

            if 'unipartite-directed-sub' in graphtypes:

                if verbose: print("- unipartite-directed-sub")
                
                outfpath_final = os.path.join(outdir,"unipartite-directed-sub",biosys_id+".gml")
                nx.write_gml(G_cdir,outfpath_final)


            if 'unipartite-undirected-subfromdirected' in graphtypes:

                if verbose: print("- unipartite-undirected-subfromdirected")

                G_cun = G_cdir.to_undirected()
                outfpath_final = os.path.join(outdir,"unipartite-undirected-subfromdirected",biosys_id+".gml")
                nx.write_gml(G_cun,outfpath_final)
        
        ## Write rxns in genome missing from KEGG (if not empty)
        if rxns_missing_from_rxn_edges:

            if not os.path.exists(missingdir):
                os.makedirs(missingdir)

            outfpath_final = os.path.join(missingdir,biosys_id+".json")
            self.__write_json(rxns_missing_from_rxn_edges, outfpath_final)

    def _write_biosystem_graphs_from_json_dir(self,
                                              biosys_rxn_json_dir,
                                              master_json,
                                              graphtypes=["unipartite-undirected-subfromdirected"],
                                              outdir="graphs",
                                              missingdir="taxon_with_rxns_missing_from_kegg",
                                              verbose=True):
        """
        Writes all jsons in biosystem's dir to one or more gml files each.

        See `write_graphs_from_one_genome` docstring for details.

        :param biosys_rxn_json: the filepath to the biosystem reaction json file
        :param master_json: the filepath to the json with details information about all KEGG reactions
        :param graphtypes: which types of graphs to write to gml files. see notes
                        below for description of possible inputs.
        :param outdir: the dir to store subdirs for each graph type, and subsequent gml files
        :param missingdir: the dir to store reactions which are missing from biosystems as jsons
        :param verbose: if True, prints the graph types as they're created
        """
        for biosys_rxn_json in glob.glob(os.path.join(biosys_rxn_json_dir,"*.json")):

            if verbose: print("Creating gml from: %s ..."%biosys_rxn_json)

            self._write_biosystem_graphs_from_json_file(biosys_rxn_json,
                                                        master_json,
                                                        graphtypes=graphtypes,
                                                        outdir=outdir,
                                                        missingdir=missingdir,
                                                        verbose=verbose)

    def write_biosystem_graphs(self,
                               biosys_rxn_json,
                               master_json,
                               graphtypes=["unipartite-undirected-subfromdirected"],
                               outdir="graphs",
                               missingdir="taxon_with_rxns_missing_from_kegg",
                               verbose=True):
        """
        Converts a directory or file of biosystem reaction jsons to one or more gml files.

        :param biosys_rxn_json: the filepath to the biosystem reaction json file
        :param master_json: the filepath to the json with details information about all KEGG reactions
        :param graphtypes: which types of graphs to write to gml files. see notes
                           below for description of possible inputs.
        :param outdir: the dir to store subdirs for each graph type, and subsequent gml files
        :param missingdir: the dir to store reactions which are missing from biosystems as jsons
        :param verbose: if True, prints the graph types as they're created

        ---------------------------------------------------------------------------------
        Notes: 
        ---------------------------------------------------------------------------------
        Steps involved:
        1. Creates directed bipartite graph
        2. Projects graph if needed
        3. Undirects graph if needed

        These steps allow for less overhead when wishing to produce multiple graph types.

        ------------------------
        Implemented graphtypes:
        ------------------------
        bipartite-directed-rxnsub
        bipartite-undirected-rxnsub
        unipartite-undirected-rxn
        unipartite-directed-sub
        unipartite-undirected-sub
        unipartite-undirected-subfromdirected --same connection rules used in 
                                                "Universal Scaling" paper
        """
        
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if os.path.isfile(biosys_rxn_json):
            self._write_biosystem_graphs_from_json_file(biosys_rxn_json,
                                                        master_json,
                                                        graphtypes=graphtypes,
                                                        outdir=outdir,
                                                        missingdir=missingdir,
                                                        verbose=verbose)
        
        elif os.path.isdir(biosys_rxn_json):
            self._write_biosystem_graphs_from_json_dir(biosys_rxn_json,
                                                        master_json,
                                                        graphtypes=graphtypes,
                                                        outdir=outdir,
                                                        missingdir=missingdir,
                                                        verbose=verbose)

def __execute_cli(args):
    """
    Call appropriate methods based on command line interface input.
    """
    
    if args.write_rxns == True:
        E = Ecg()
        
        E.write_biosystem_rxns(args.jgi,
                                     args.ecrxn,
                                     outdir=args.outdir)

    if args.write_graphs == True:
        E = Ecg()
        E.write_biosystem_graphs(args.biorxn, 
                                 args.master,
                                 graphtypes=args.grapthtypes,
                                 outdir=args.graphoutdir,
                                 missingdir=args.missingdir,
                                 verbose=args.verbose)

if __name__ == '__main__':
    # Initial setup of argparse with description of program.
    parser = argparse.ArgumentParser(description='WARNING. CLI HAS NOT BEEN IMPLEMENTED OR TESTED YET. Combine KEGG derived reaction data with JGI derived enzyme data to generate reaction lists (meta)genomes.')

    parser.add_argument('--jgi',default=None,required=True,type=str,help='Filepath to the directory or file where JGI data is located. (Required)')
    parser.add_argument('--ecrxn',default=None,required=True,type=str,help='Filepath to "enzyme_reaction.json"; the json containing relationship between ec numbers and reactions. (Required)')
    parser.add_argument('--biorxn',default=None,required=True,type=str,help='Filepath to the biosystem reaction json file. (Required)')
    parser.add_argument('--master',default=None,required=True,type=str,help='Filepath to "master.json"; json with information details about all KEGG reactions. (Required)')
    parser.add_argument('--write_rxns',default=True,type=bool,help='Write reaction lists from either a single biosystem file or biosystem directory; all JGI jsons. (Default = True)')
    parser.add_argument('--write_graphs',default=True,type=bool,help='Write gmls from either a single biosystem reactionfile or biosystem reaction directory; all JGI reaction jsons. (Default = True)')
    
    parser.add_argument('--outdir',default='taxon_reactions',type=str,help='Path where biosystem reactions will be saved. (Default = "taxon_reactions")')
    parser.add_argument('--graphtypes',default='unipartite-undirected-subfromdirected',choices = ['bipartite-directed-rxnsub','bipartite-undirected-rxnsub','unipartite-undirected-rxn','unipartite-directed-sub','unipartite-undirected-sub','unipartite-undirected-subfromdirected'],nargs='+',type=str,help='Which types of graphs to write to gml files. (Default = "unipartite-undirected-subfromdirected")')
    parser.add_argument('--graphoutdir',default='graphs',type=str,help='The directory to store subdirs for each graph type, and subsequent gml files. (Default = "graphs")')
    parser.add_argument('--missingdir',default='taxon_with_rxns_missing_from_kegg',type=str,help='The directory to store reactions which are missing from biosystems as jsons. (Default = "taxon_with_rxns_missing_from_kegg")')
    parser.add_argument('--verbose',default=True,type=bool,help='If True, prints the graph types as they are created. (Default = True)')

    args = parser.parse_args()
 
    __execute_cli(args)