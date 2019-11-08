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

        biosystem_json = self.__load_json(biosystem_json)
        
        ec_list = list()
        for d in biosystem_json['records']:
            ec_list.append(d['EnzymeID'].split("EC:")[1])
        
        return ec_list

    def _get_biosystem_rxnlist(self,ec_list,ec_rxn_link_json):
    
        ec_rxn_link_json =self.__load_json(ec_rxn_link_json)

        rxn_list = list()
        for ec in ec_list:
            ec_key = 'ec:'+ec
            if ec_key in ec_rxn_link_json:
                rxn_list+=ec_rxn_link_json[ec_key].split("rn:")[1]
            
        return rxn_list

    def _write_biosystem_rxns_from_jgi_json_file(self,infile,ec_rxn_link_json,outdir="taxon_reactions"):
        """

        """
        biosystem_json = self.__load_json(infile)
        ec_list = self._get_biosystem_eclist(biosystem_json)
        rxn_list = self._get_biosystem_rxnlist(ec_list,ec_rxn_link_json)

        # if outdir==None:
        #     splitext = os.path.splitext(infile)[0]
        #     outpath = splitext+"_rxns.json"
        
        
        # if not os.path.exists(outpath):
        #     os.makedirs(outpath)
        # outpath = outpath+os.path.basename(fname)
        outpath = os.path.join(outdir,os.path.basename(infile))
        self.__write_json(rxn_list,outpath)

    def _write_biosystem_rxns_from_jgi_json_dir(self,indir,ec_rxn_link_json,outdir="taxon_reactions"):
        """
        2019-11-1
        need to check that this will not overwrite the biosystem_json files
        when i write out the org_rxn list
        - also need to check for the above function
        - just write the damn thing. then figure out how to test.
        """
        for fname in glob.glob(os.path.join(indir, '*.json')):
            self._write_biosystem_rxns_from_jgi_json_file(fname,ec_rxn_link_json,outdir)


    def write_biosystem_rxns(self,ec_rxn_link_json,outdir="taxon_reactions"):

        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if os.path.isfile(self.__biosystem_json):
            self._write_biosystem_rxns_from_jgi_json_file(self.__biosystem_json,ec_rxn_link_json,outdir)
        
        elif os.path.isdir(self.__biosystem_json):
            self._write_biosystem_rxns_from_jgi_json_dir(self.__biosystem_json,ec_rxn_link_json,outdir)





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
