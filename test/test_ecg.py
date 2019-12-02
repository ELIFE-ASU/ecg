import unittest
import os
import glob
import json
import networkx as nx
from ecg.ecg import Ecg

def clear_dir(mydir):
    if os.path.exists(mydir):
        files = glob.glob(os.path.join(mydir,"*.json"))+glob.glob(os.path.join(mydir,"*.gml"))
        for f in files:
            ## Keyword to keep certain files during tests
            if "keep" not in f:
                os.remove(f)

class TestEcgRxnJsons(unittest.TestCase):
    @classmethod
    def setup_class(self):
        self.__current_dir = os.path.dirname(os.path.abspath(__file__))
        self.__ec_rxn_link_json = os.path.join(self.__current_dir,"userdata","kegg","links","enzyme_reaction.json")
        self.__taxon_ids_indir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_ids")

        self.__biosystem_json_file_2enz = "1234567890.json"
        self.__biosystem_json_file_1enz2rxn = "1234567891.json"
        self.__biosystem_json_file_2components = "1234567892.json"
        self.__biosystem_json_file_no_enzymes_key = "no_enzymes_key.json"
        self.__biosystem_json_file_no_ec_keys = "no_ec_keys.json"
        
        self.__taxon_reactions_outdir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_reactions")

        ## Clear outdirs to ensure tests are fresh each time
        clear_dir(self.__taxon_reactions_outdir)

    def test_get_biosystem_eclist(self):

        files_ecs = {self.__biosystem_json_file_2enz: ["2.5.1.10","2.5.1.87"],
            self.__biosystem_json_file_1enz2rxn: ["1.1.1.3"],
            self.__biosystem_json_file_2components: ["1.1.1.3","2.5.1.10","2.5.1.87"]}

        myecg = Ecg()
        for f in files_ecs:
            f_full_path = os.path.join(self.__taxon_ids_indir,f)
            self.assertEqual(set(myecg._get_biosystem_eclist(f_full_path)),
                             set(files_ecs[f]))

    def test_get_biosystem_rxnlist(self):

        files_rxns = {self.__biosystem_json_file_2enz: ["R05556","R02003"],
            self.__biosystem_json_file_1enz2rxn: ["R01773","R01775"],
            self.__biosystem_json_file_2components: ["R05556","R02003","R01773","R01775"]}

        myecg = Ecg()
        for f in files_rxns:
            f_full_path = os.path.join(self.__taxon_ids_indir,f)
            ec_list = myecg._get_biosystem_eclist(f_full_path)
            self.assertEqual(set(myecg._get_biosystem_rxnlist(ec_list,self.__ec_rxn_link_json)),
                             set(files_rxns[f]))

    def test_write_biosystem_rxns_file_names(self):

        clear_dir(self.__taxon_reactions_outdir)
        
        files_names = [self.__biosystem_json_file_2enz,
            self.__biosystem_json_file_1enz2rxn,
            self.__biosystem_json_file_2components]

        ## Writes reaction jsons to be used in `test_write_biosystem_rxns_file_rxns`
        myecg = Ecg()
        for f in files_names:
            f_full_path = os.path.join(self.__taxon_ids_indir,f)
            myecg.write_biosystem_rxns(f_full_path,self.__ec_rxn_link_json,self.__taxon_reactions_outdir)
            self.assertTrue(os.path.exists(os.path.join(self.__taxon_reactions_outdir,f)))

    def test_write_biosystem_rxns_file_rxns(self):
        ## Assumes you've already run `test_write_biosystem_rxns_file_names`

        files_rxns = {self.__biosystem_json_file_2enz: ["R05556","R02003"],
            self.__biosystem_json_file_1enz2rxn: ["R01773","R01775"],
            self.__biosystem_json_file_2components: ["R05556","R02003","R01773","R01775"]}

        for f in files_rxns:
            f_full_path = os.path.join(self.__taxon_reactions_outdir,f)
            with open(f_full_path) as fjson:
                self.assertEqual(set(json.load(fjson)),set(files_rxns[f]))

    def test_no_enzymes_key(self):

        myecg = Ecg()
        f_full_path = os.path.join(self.__taxon_ids_indir,self.__biosystem_json_file_no_enzymes_key)
        myecg.write_biosystem_rxns(f_full_path,self.__ec_rxn_link_json,self.__taxon_reactions_outdir)

    def test_no_ec_keys(self):

        myecg = Ecg()
        f_full_path = os.path.join(self.__taxon_ids_indir,self.__biosystem_json_file_no_ec_keys)
        myecg.write_biosystem_rxns(f_full_path,self.__ec_rxn_link_json,self.__taxon_reactions_outdir)


    def test_write_biosystem_rxns_dir_names(self):

        clear_dir(self.__taxon_reactions_outdir)

        files_names = [self.__biosystem_json_file_2enz,
            self.__biosystem_json_file_1enz2rxn,
            self.__biosystem_json_file_2components]

        myecg = Ecg()
        myecg.write_biosystem_rxns(self.__taxon_ids_indir,self.__ec_rxn_link_json,self.__taxon_reactions_outdir)

        for f in files_names:
            self.assertTrue(os.path.exists(os.path.join(self.__taxon_reactions_outdir,f)))

    def test_write_biosystem_rxns_dir_rxns(self):
        ## Assumes you've already run `test_write_biosystem_rxns_dir_names`

        files_rxns = {self.__biosystem_json_file_2enz: ["R05556","R02003"],
            self.__biosystem_json_file_1enz2rxn: ["R01773","R01775"],
            self.__biosystem_json_file_2components: ["R05556","R02003","R01773","R01775"]}

        myecg = Ecg()
        myecg.write_biosystem_rxns(self.__taxon_ids_indir,self.__ec_rxn_link_json,self.__taxon_reactions_outdir)

        for f in files_rxns:
            f_full_path = os.path.join(self.__taxon_reactions_outdir,f)
            with open(f_full_path) as fjson:
                self.assertEqual(set(json.load(fjson)),set(files_rxns[f]))

class TestEcgGraphsFromFiles(unittest.TestCase):
    @classmethod
    def setup_class(self):
        self.__current_dir = os.path.dirname(os.path.abspath(__file__))
        self.__master_json = os.path.join(self.__current_dir,"userdata","kegg","master.json")
        self.__taxon_reactions_indir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_reactions")
        self.__ec_rxn_link_json = os.path.join(self.__current_dir,"userdata","kegg","links","enzyme_reaction.json")
        self.__taxon_ids_indir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_ids")

        ## rxn jsons (will turn to graphs)
        self.__biosystem_json_file_2enz = "1234567890"
        self.__biosystem_json_file_1enz2rxn = "1234567891"
        self.__biosystem_json_file_2components = "1234567892"
        
        self.__files_names = [self.__biosystem_json_file_2enz,
            self.__biosystem_json_file_1enz2rxn,
            self.__biosystem_json_file_2components]
        
        ## outdirs (cleared before tests)
        self.__graphs_outdir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","graphs")
        self.__missingdir_outdir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_with_rxns_missing_from_kegg")

        ## test all graphtypes
        self.__graphtypes = ['bipartite-directed-rxnsub',
        'bipartite-undirected-rxnsub',
        'unipartite-undirected-rxn',
        'unipartite-directed-sub',
        'unipartite-undirected-sub',
        'unipartite-undirected-subfromdirected']

        ## Clear outdirs to ensure tests are fresh each time
        clear_dir(self.__graphs_outdir)
        clear_dir(self.__missingdir_outdir)


        myecg = Ecg()
        ## Make sure json rxn files are created
        for f in self.__files_names:
            f_full_path = os.path.join(self.__taxon_reactions_indir,f+".json")
            if not os.path.exists(f_full_path):
                myecg.write_biosystem_rxns(f_full_path,self.__ec_rxn_link_json,self.__taxon_reactions_indir)

            ## Write graphs
            myecg.write_biosystem_graphs(f_full_path,
                                self.__master_json,
                                graphtypes=self.__graphtypes,
                                outdir=self.__graphs_outdir,
                                missingdir=self.__missingdir_outdir,
                                verbose=True)
        
    # 'bipartite-directed-rxnsub'
    def test_bipartite_directed_rxnsub_is_directed(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),True)

    def test_bipartite_directed_rxnsub_is_bipartite(self):
        ## FYI: Unipartite networks aren't necessarily NOT bipartite as far as the check
        ## by networkx is concerned (e.g. a path network from 0->1,1->2,2->3 is 
        ## bipartite, but if you add a connection from 3->1 it is no longer bipartite.
        ## All it checks is if the graph can be returned as a two-color graph.

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_bipartite(G),True)

    def test_bipartite_directed_rxnsub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["R05556",
                             "R02003",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["R01773",
                             "R01775",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["R05556",
                             "R02003",
                             "R01773",
                             "R01775",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_bipartite_directed_rxnsub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [("C00448","R05556"),
                             ("C00129","R05556"),
                             ("R05556","C05859"),
                             ("R05556","C00013"),
                             ("C00341","R02003"),
                             ("C00129","R02003"),
                             ("R02003","C00013"),
                             ("R02003","C00448")],
                          self.__biosystem_json_file_1enz2rxn:
                            [("C00263","R01773"),
                             ("C00003","R01773"),
                             ("R01773","C00441"),
                             ("R01773","C00004"),
                             ("R01773","C00080"),
                             ("C00263","R01775"),
                             ("C00006","R01775"),
                             ("R01775","C00441"),
                             ("R01775","C00005"),
                             ("R01775","C00080")],
                          self.__biosystem_json_file_2components:
                            [("C00448","R05556"),
                             ("C00129","R05556"),
                             ("R05556","C05859"),
                             ("R05556","C00013"),
                             ("C00341","R02003"),
                             ("C00129","R02003"),
                             ("R02003","C00013"),
                             ("R02003","C00448"),
                             ("C00263","R01773"),
                             ("C00003","R01773"),
                             ("R01773","C00441"),
                             ("R01773","C00004"),
                             ("R01773","C00080"),
                             ("C00263","R01775"),
                             ("C00006","R01775"),
                             ("R01775","C00441"),
                             ("R01775","C00005"),
                             ("R01775","C00080")]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(G.edges()))

    # 'bipartite-undirected-rxnsub'
    def test_bipartite_undirected_rxnsub_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_bipartite_undirected_rxnsub_is_bipartite(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_bipartite(G),True)

    def test_bipartite_undirected_rxnsub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["R05556",
                             "R02003",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["R01773",
                             "R01775",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["R05556",
                             "R02003",
                             "R01773",
                             "R01775",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_bipartite_undirected_rxnsub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"C00448","R05556"}),
                             frozenset({"C00129","R05556"}),
                             frozenset({"R05556","C05859"}),
                             frozenset({"R05556","C00013"}),
                             frozenset({"C00341","R02003"}),
                             frozenset({"C00129","R02003"}),
                             frozenset({"R02003","C00013"}),
                             frozenset({"R02003","C00448"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"C00263","R01773"}),
                             frozenset({"C00003","R01773"}),
                             frozenset({"R01773","C00441"}),
                             frozenset({"R01773","C00004"}),
                             frozenset({"R01773","C00080"}),
                             frozenset({"C00263","R01775"}),
                             frozenset({"C00006","R01775"}),
                             frozenset({"R01775","C00441"}),
                             frozenset({"R01775","C00005"}),
                             frozenset({"R01775","C00080"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"C00448","R05556"}),
                             frozenset({"C00129","R05556"}),
                             frozenset({"R05556","C05859"}),
                             frozenset({"R05556","C00013"}),
                             frozenset({"C00341","R02003"}),
                             frozenset({"C00129","R02003"}),
                             frozenset({"R02003","C00013"}),
                             frozenset({"R02003","C00448"}),
                             frozenset({"C00263","R01773"}),
                             frozenset({"C00003","R01773"}),
                             frozenset({"R01773","C00441"}),
                             frozenset({"R01773","C00004"}),
                             frozenset({"R01773","C00080"}),
                             frozenset({"C00263","R01775"}),
                             frozenset({"C00006","R01775"}),
                             frozenset({"R01775","C00441"}),
                             frozenset({"R01775","C00005"}),
                             frozenset({"R01775","C00080"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

    # 'unipartite-undirected-rxn'
    def test_unipartite_undirected_rxn_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-rxn',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_unipartite_undirected_rxn_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["R05556",
                             "R02003"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["R01773",
                             "R01775"],
                          self.__biosystem_json_file_2components:
                            ["R05556",
                             "R02003",
                             "R01773",
                             "R01775"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-rxn',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_undirected_rxn_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"R05556","R02003"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"R01775","R01773"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"R05556","R02003"}),
                             frozenset({"R01775","R01773"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-rxn',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

    # 'unipartite-directed-sub'
    def test_unipartite_directed_sub_is_directed(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-directed-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),True)

    def test_unipartite_directed_sub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-directed-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_directed_sub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [("C00448","C05859"),
                             ("C00448","C00013"),
                             ("C00129","C05859"),
                             ("C00129","C00013"),
                             ("C00129","C00448"),
                             ("C00341","C00013"),
                             ("C00341","C00448")],
                          self.__biosystem_json_file_1enz2rxn:
                            [("C00263","C00441"),
                             ("C00263","C00004"),
                             ("C00263","C00080"),
                             ("C00263","C00005"),
                             ("C00003","C00441"),
                             ("C00003","C00004"),
                             ("C00003","C00080"),
                             ("C00006","C00441"),
                             ("C00006","C00005"),
                             ("C00006","C00080")],
                          self.__biosystem_json_file_2components:
                            [("C00448","C05859"),
                             ("C00448","C00013"),
                             ("C00129","C05859"),
                             ("C00129","C00013"),
                             ("C00129","C00448"),
                             ("C00341","C00013"),
                             ("C00341","C00448"),
                             ("C00263","C00441"),
                             ("C00263","C00004"),
                             ("C00263","C00080"),
                             ("C00263","C00005"),
                             ("C00003","C00441"),
                             ("C00003","C00004"),
                             ("C00003","C00080"),
                             ("C00006","C00441"),
                             ("C00006","C00005"),
                             ("C00006","C00080")]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-directed-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(G.edges()))

    # 'unipartite-undirected-sub'
    def test_unipartite_undirected_sub_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_unipartite_undirected_sub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_undirected_sub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"}),
                             frozenset({"C05859","C00013"}),
                             frozenset({"C00341","C00129"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"}),
                             frozenset({"C00263","C00003"}),
                             frozenset({"C00441","C00004"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00004","C00080"}),
                             frozenset({"C00263","C00006"}),
                             frozenset({"C00441","C00005"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00005","C00080"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"}),
                             frozenset({"C05859","C00013"}),
                             frozenset({"C00341","C00129"}),
                             frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"}),
                             frozenset({"C00263","C00003"}),
                             frozenset({"C00441","C00004"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00004","C00080"}),
                             frozenset({"C00263","C00006"}),
                             frozenset({"C00441","C00005"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00005","C00080"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

    # 'unipartite-undirected-subfromdirected'
    def test_unipartite_undirected_subfromdirected_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-subfromdirected',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_unipartite_undirected_subfromdirected_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-subfromdirected',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_undirected_subfromdirected_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"}),
                             frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-subfromdirected',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

class TestEcgGraphsFromDir(unittest.TestCase):
    @classmethod
    def setup_class(self):
        self.__current_dir = os.path.dirname(os.path.abspath(__file__))
        self.__master_json = os.path.join(self.__current_dir,"userdata","kegg","master.json")
        self.__taxon_reactions_indir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_reactions")
        self.__ec_rxn_link_json = os.path.join(self.__current_dir,"userdata","kegg","links","enzyme_reaction.json")
        self.__taxon_ids_indir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_ids")

        ## rxn jsons (will turn to graphs)
        self.__biosystem_json_file_2enz = "1234567890"
        self.__biosystem_json_file_1enz2rxn = "1234567891"
        self.__biosystem_json_file_2components = "1234567892"
        
        self.__files_names = [self.__biosystem_json_file_2enz,
            self.__biosystem_json_file_1enz2rxn,
            self.__biosystem_json_file_2components]
        
        ## outdirs (cleared before tests)
        self.__graphs_outdir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","graphs")
        self.__missingdir_outdir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_with_rxns_missing_from_kegg")

        ## test all graphtypes
        self.__graphtypes = ['bipartite-directed-rxnsub',
        'bipartite-undirected-rxnsub',
        'unipartite-undirected-rxn',
        'unipartite-directed-sub',
        'unipartite-undirected-sub',
        'unipartite-undirected-subfromdirected']

        ## Clear outdirs to ensure tests are fresh each time
        clear_dir(self.__graphs_outdir)
        clear_dir(self.__missingdir_outdir)


        myecg = Ecg()
        ## Make sure json rxn files are created
        for f in self.__files_names:
            f_full_path = os.path.join(self.__taxon_reactions_indir,f+".json")
            if not os.path.exists(f_full_path):
                myecg.write_biosystem_rxns(f_full_path,self.__ec_rxn_link_json,self.__taxon_reactions_indir)

        ## Write graphs
        myecg.write_biosystem_graphs(self.__taxon_reactions_indir,
                            self.__master_json,
                            graphtypes=self.__graphtypes,
                            outdir=self.__graphs_outdir,
                            missingdir=self.__missingdir_outdir,
                            verbose=True)
        
    # 'bipartite-directed-rxnsub'
    def test_bipartite_directed_rxnsub_is_directed(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),True)

    def test_bipartite_directed_rxnsub_is_bipartite(self):
        ## FYI: Unipartite networks aren't necessarily NOT bipartite as far as the check
        ## by networkx is concerned (e.g. a path network from 0->1,1->2,2->3 is 
        ## bipartite, but if you add a connection from 3->1 it is no longer bipartite.
        ## All it checks is if the graph can be returned as a two-color graph.

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_bipartite(G),True)

    def test_bipartite_directed_rxnsub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["R05556",
                             "R02003",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["R01773",
                             "R01775",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["R05556",
                             "R02003",
                             "R01773",
                             "R01775",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_bipartite_directed_rxnsub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [("C00448","R05556"),
                             ("C00129","R05556"),
                             ("R05556","C05859"),
                             ("R05556","C00013"),
                             ("C00341","R02003"),
                             ("C00129","R02003"),
                             ("R02003","C00013"),
                             ("R02003","C00448")],
                          self.__biosystem_json_file_1enz2rxn:
                            [("C00263","R01773"),
                             ("C00003","R01773"),
                             ("R01773","C00441"),
                             ("R01773","C00004"),
                             ("R01773","C00080"),
                             ("C00263","R01775"),
                             ("C00006","R01775"),
                             ("R01775","C00441"),
                             ("R01775","C00005"),
                             ("R01775","C00080")],
                          self.__biosystem_json_file_2components:
                            [("C00448","R05556"),
                             ("C00129","R05556"),
                             ("R05556","C05859"),
                             ("R05556","C00013"),
                             ("C00341","R02003"),
                             ("C00129","R02003"),
                             ("R02003","C00013"),
                             ("R02003","C00448"),
                             ("C00263","R01773"),
                             ("C00003","R01773"),
                             ("R01773","C00441"),
                             ("R01773","C00004"),
                             ("R01773","C00080"),
                             ("C00263","R01775"),
                             ("C00006","R01775"),
                             ("R01775","C00441"),
                             ("R01775","C00005"),
                             ("R01775","C00080")]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(G.edges()))

    # 'bipartite-undirected-rxnsub'
    def test_bipartite_undirected_rxnsub_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_bipartite_undirected_rxnsub_is_bipartite(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_bipartite(G),True)

    def test_bipartite_undirected_rxnsub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["R05556",
                             "R02003",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["R01773",
                             "R01775",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["R05556",
                             "R02003",
                             "R01773",
                             "R01775",
                             "C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_bipartite_undirected_rxnsub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"C00448","R05556"}),
                             frozenset({"C00129","R05556"}),
                             frozenset({"R05556","C05859"}),
                             frozenset({"R05556","C00013"}),
                             frozenset({"C00341","R02003"}),
                             frozenset({"C00129","R02003"}),
                             frozenset({"R02003","C00013"}),
                             frozenset({"R02003","C00448"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"C00263","R01773"}),
                             frozenset({"C00003","R01773"}),
                             frozenset({"R01773","C00441"}),
                             frozenset({"R01773","C00004"}),
                             frozenset({"R01773","C00080"}),
                             frozenset({"C00263","R01775"}),
                             frozenset({"C00006","R01775"}),
                             frozenset({"R01775","C00441"}),
                             frozenset({"R01775","C00005"}),
                             frozenset({"R01775","C00080"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"C00448","R05556"}),
                             frozenset({"C00129","R05556"}),
                             frozenset({"R05556","C05859"}),
                             frozenset({"R05556","C00013"}),
                             frozenset({"C00341","R02003"}),
                             frozenset({"C00129","R02003"}),
                             frozenset({"R02003","C00013"}),
                             frozenset({"R02003","C00448"}),
                             frozenset({"C00263","R01773"}),
                             frozenset({"C00003","R01773"}),
                             frozenset({"R01773","C00441"}),
                             frozenset({"R01773","C00004"}),
                             frozenset({"R01773","C00080"}),
                             frozenset({"C00263","R01775"}),
                             frozenset({"C00006","R01775"}),
                             frozenset({"R01775","C00441"}),
                             frozenset({"R01775","C00005"}),
                             frozenset({"R01775","C00080"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-undirected-rxnsub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

    # 'unipartite-undirected-rxn'
    def test_unipartite_undirected_rxn_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-rxn',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_unipartite_undirected_rxn_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["R05556",
                             "R02003"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["R01773",
                             "R01775"],
                          self.__biosystem_json_file_2components:
                            ["R05556",
                             "R02003",
                             "R01773",
                             "R01775"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-rxn',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_undirected_rxn_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"R05556","R02003"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"R01775","R01773"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"R05556","R02003"}),
                             frozenset({"R01775","R01773"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-rxn',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

    # 'unipartite-directed-sub'
    def test_unipartite_directed_sub_is_directed(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-directed-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),True)

    def test_unipartite_directed_sub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-directed-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_directed_sub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [("C00448","C05859"),
                             ("C00448","C00013"),
                             ("C00129","C05859"),
                             ("C00129","C00013"),
                             ("C00129","C00448"),
                             ("C00341","C00013"),
                             ("C00341","C00448")],
                          self.__biosystem_json_file_1enz2rxn:
                            [("C00263","C00441"),
                             ("C00263","C00004"),
                             ("C00263","C00080"),
                             ("C00263","C00005"),
                             ("C00003","C00441"),
                             ("C00003","C00004"),
                             ("C00003","C00080"),
                             ("C00006","C00441"),
                             ("C00006","C00005"),
                             ("C00006","C00080")],
                          self.__biosystem_json_file_2components:
                            [("C00448","C05859"),
                             ("C00448","C00013"),
                             ("C00129","C05859"),
                             ("C00129","C00013"),
                             ("C00129","C00448"),
                             ("C00341","C00013"),
                             ("C00341","C00448"),
                             ("C00263","C00441"),
                             ("C00263","C00004"),
                             ("C00263","C00080"),
                             ("C00263","C00005"),
                             ("C00003","C00441"),
                             ("C00003","C00004"),
                             ("C00003","C00080"),
                             ("C00006","C00441"),
                             ("C00006","C00005"),
                             ("C00006","C00080")]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-directed-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(G.edges()))

    # 'unipartite-undirected-sub'
    def test_unipartite_undirected_sub_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_unipartite_undirected_sub_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_undirected_sub_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"}),
                             frozenset({"C05859","C00013"}),
                             frozenset({"C00341","C00129"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"}),
                             frozenset({"C00263","C00003"}),
                             frozenset({"C00441","C00004"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00004","C00080"}),
                             frozenset({"C00263","C00006"}),
                             frozenset({"C00441","C00005"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00005","C00080"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"}),
                             frozenset({"C05859","C00013"}),
                             frozenset({"C00341","C00129"}),
                             frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"}),
                             frozenset({"C00263","C00003"}),
                             frozenset({"C00441","C00004"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00004","C00080"}),
                             frozenset({"C00263","C00006"}),
                             frozenset({"C00441","C00005"}),
                             frozenset({"C00441","C00080"}),
                             frozenset({"C00005","C00080"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-sub',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

    # 'unipartite-undirected-subfromdirected'
    def test_unipartite_undirected_subfromdirected_is_undirected(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-subfromdirected',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),False)

    def test_unipartite_undirected_subfromdirected_nodes(self):
        expected_nodes = {self.__biosystem_json_file_2enz: 
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341"],
                          self.__biosystem_json_file_1enz2rxn:
                            ["C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"],
                          self.__biosystem_json_file_2components:
                            ["C00448",
                             "C05859",
                             "C00129",
                             "C00013",
                             "C00341",
                             "C00263",
                             "C00441",
                             "C00003",
                             "C00004",
                             "C00006",
                             "C00005",
                             "C00080"]}
        for f in expected_nodes:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-subfromdirected',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_nodes[f]),set(G.nodes()))

    def test_unipartite_undirected_subfromdirected_edges(self):

        expected_edges = {self.__biosystem_json_file_2enz: 
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"})],
                          self.__biosystem_json_file_1enz2rxn:
                            [frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"})],
                          self.__biosystem_json_file_2components:
                            [frozenset({"C00448","C05859"}),
                             frozenset({"C00448","C00013"}),
                             frozenset({"C00129","C05859"}),
                             frozenset({"C00129","C00013"}),
                             frozenset({"C00129","C00448"}),
                             frozenset({"C00341","C00013"}),
                             frozenset({"C00341","C00448"}),
                             frozenset({"C00263","C00441"}),
                             frozenset({"C00263","C00004"}),
                             frozenset({"C00263","C00080"}),
                             frozenset({"C00263","C00005"}),
                             frozenset({"C00003","C00441"}),
                             frozenset({"C00003","C00004"}),
                             frozenset({"C00003","C00080"}),
                             frozenset({"C00006","C00441"}),
                             frozenset({"C00006","C00005"}),
                             frozenset({"C00006","C00080"})]}

        for f in expected_edges:
            f_full_path = os.path.join(self.__graphs_outdir,'unipartite-undirected-subfromdirected',f+".gml")
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(frozenset(edge) for edge in G.edges()))

class TestEcgGraphsMissingrxn(unittest.TestCase):
    @classmethod
    def setup_class(self):
        self.__current_dir = os.path.dirname(os.path.abspath(__file__))
        self.__master_json = os.path.join(self.__current_dir,"userdata","kegg","master.json")
        self.__taxon_reactions_indir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_reactions")
        self.__ec_rxn_link_json = os.path.join(self.__current_dir,"userdata","kegg","links","enzyme_reaction.json")
        self.__taxon_ids_indir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_ids")

        ## rxn jsons (will turn to graphs)
        self.__biosystem_json_file_missingrxn = "1234567890missingkeep"
        
        self.__files_names = [self.__biosystem_json_file_missingrxn]
        
        ## outdirs (cleared before tests)
        self.__graphs_outdir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","graphs")
        self.__missingdir_outdir = os.path.join(self.__current_dir,"userdata","jgi","Eukaryota","taxon_with_rxns_missing_from_kegg")

        ## test all graphtypes
        self.__graphtypes = ['bipartite-directed-rxnsub',
        'bipartite-undirected-rxnsub',
        'unipartite-undirected-rxn',
        'unipartite-directed-sub',
        'unipartite-undirected-sub',
        'unipartite-undirected-subfromdirected']

        ## Clear outdirs to ensure tests are fresh each time
        clear_dir(self.__graphs_outdir)
        clear_dir(self.__missingdir_outdir)


        myecg = Ecg()
        ## Make sure json rxn files are created
        for f in self.__files_names:
            f_full_path = os.path.join(self.__taxon_reactions_indir,f+".json")
            if not os.path.exists(f_full_path):
                myecg.write_biosystem_rxns(f_full_path,self.__ec_rxn_link_json,self.__taxon_reactions_indir)

            ## Write graphs
            myecg.write_biosystem_graphs(f_full_path,
                                self.__master_json,
                                graphtypes=self.__graphtypes,
                                outdir=self.__graphs_outdir,
                                missingdir=self.__missingdir_outdir,
                                verbose=True)

    def test_missing_rxn_json_formatting(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__missingdir_outdir,f+".json")
            with open(f_full_path) as fjson:
                missing_rxns = json.load(fjson)
            self.assertEqual(set(["R99999999","R00000000"]),set(missing_rxns))        