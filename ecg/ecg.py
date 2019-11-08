import json
import glob

class Ecg(object):

    # def __init__(self,chromedriver_path="", 
    #              homepage_url='https://img.jgi.doe.gov/cgi-bin/m/main.cgi'):
    # def __init__(self,ec_rxn_link_json):
    #     # self.__master = master_json 
    #     self.__ec_rxn_link_json = ec_rxn_link_json
    
    def __load_json(fname):
        """
        Wrapper to load json in single line

        :param fname: the filepath to the json file
        """
        with open(fname) as f:
            return json.load(f)

    def __write_json(data,fname):
        """
        Wrapper to write json in single line

        :param data: the data to write out
        :param fname: the filepath to write out
        """
        with open(fname, 'w') as outfile:
            json.dump(data, outfile)
    
    def _get_org_eclist(organism_json):

        organism_json = load_json(organism_json)
        
        ec_list = list()
        for d in organism_json['records']:
            ec_list.append(d['EnzymeID'].split("EC:")[1])
        
        return ec_list

    def _get_org_rxnlist(ec_list,ec_rxn_link_json):
    
        ec_rxn_link_json =load_json(ec_rxn_link_json)

        rxn_list = list()
        for ec in ec_list:
            ec_key = 'ec:'+ec
            if ec_key in ec_rxn_link_json:
                rxn_list+=ec_rxn_link_json[ec_key].split("rn:")[1]
            
        return rxn_list

    def _write_org_rxns_from_json_file(fname,ec_rxn_link_json,outdir):
        """

        """
        organism_json = self.__load_json(fname)
        ec_list = self._get_org_eclist(organism_json)
        rxn_list = self._get_org_rxnlist(ec_list,ec_rxn_link_json)
        
        outpath = outdir+'/'
        if not os.path.exists(outpath):
            os.makedirs(outpath)
        outpath = outpath+os.path.basename(fname)
        self.__write_json(rxn_list,outpath)

    def _write_org_rxns_from_json_dir(dirname,ec_rxn_link_json,outdir):
        """
        2019-11-1
        need to check that this will not overwrite the org_json files
        when i write out the org_rxn list
        - also need to check for the above function
        - just write the damn thing. then figure out how to test.
        """
        for fname in glob.glob(dirname/*.json):
            self._write_org_rxns_from_json_file(fname,ec_rxn_link_json,outdir)


    def write_org_rxns(org_json,ec_rxn_link_json,outdir):

        if os.path.isfile(org_json):
            write_org_rxns_from_json_file(org_json,ec_rxn_link_json,outdir)
        
        elif os.path.isdir(org_json):
            write_org_rxns_from_json_dir(org_json,ec_rxn_link_json,outdir)





    # NEW PLAN
    # require master.json and enzyme_reaction_link.json 
    # if master.json isn't generated, tell user to generate it from the data they have using kegg.py
    # def get_omic_edges(master_json,ec_rxn_link_json,org_json):
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
