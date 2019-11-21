import unittest
import os
import glob
import json
import networkx as nx
from ecg.ecg import Ecg

def clear_dir(mydir):
    if os.path.exists(mydir):
        files = glob.glob(os.path.join(mydir,"*.json"))
        for f in files:
            os.remove(f)

class TestEcgRxnJsons(unittest.TestCase):
    @classmethod
    def setup_class(self):
        self.__ec_rxn_link_json = "userdata/kegg/links/enzyme_reaction.json"
        self.__taxon_ids_indir = "userdata/jgi/Eukaryota/taxon_ids"

        self.__biosystem_json_file_2enz = "1234567890.json"
        self.__biosystem_json_file_1enz2rxn = "1234567891.json"
        self.__biosystem_json_file_2components = "1234567892.json"
        
        self.__taxon_reactions_outdir = "userdata/jgi/Eukaryota/taxon_reactions"

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

        for f in files_rxns:
            f_full_path = os.path.join(self.__taxon_reactions_outdir,f)
            with open(f_full_path) as fjson:
                self.assertEqual(set(json.load(fjson)),set(files_rxns[f]))

class TestEcgGraphsFromFiles(unittest.TestCase):
    @classmethod
    def setup_class(self):
        self.__master_json = "userdata/kegg/master.json"
        self.__taxon_reactions_indir = "userdata/jgi/Eukaryota/taxon_reactions"
        self.__ec_rxn_link_json = "userdata/kegg/links/enzyme_reaction.json"
        self.__taxon_ids_indir = "userdata/jgi/Eukaryota/taxon_ids"

        ## rxn jsons (will turn to graphs)
        self.__biosystem_json_file_2enz = "1234567890.json"
        self.__biosystem_json_file_1enz2rxn = "1234567891.json"
        self.__biosystem_json_file_2components = "1234567892.json"
        
        ## outdirs (cleared before tests)
        self.__graphs_outdir = "userdata/jgi/Eukaryota/graphs"
        self.__missingdir_outdir = "userdata/jgi/Eukaryota/rxns_missing_from_kegg"

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

        self.__files_names = [self.__biosystem_json_file_2enz,
            self.__biosystem_json_file_1enz2rxn,
            self.__biosystem_json_file_2components]
        
        myecg = Ecg()
        ## Make sure json rxn files are created
        for f in self.__files_names:
            f_full_path = os.path.join(self.__taxon_reactions_indir,f)
            if not os.path.exists(f_full_path):
                myecg.write_biosystem_rxns(f_full_path,self.__ec_rxn_link_json,self.__taxon_reactions_outdir)

        for f in self.__files_names:
            myecg.write_biosystem_graphs(f,
                                self.__master_json,
                                graphtypes=self.__graphtypes,
                                outdir=self.__graphs_outdir,
                                missingdir=self.__missingdir_outdir,
                                verbose=True)
        
    ## 'bipartite-directed-rxnsub'
    def test_bipartite_directed_rxnsub_is_directed(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f)
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_directed(G),True)

    def test_bipartite_directed_rxnsub_is_bipartite(self):

        for f in self.__files_names:
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f)
            G = nx.read_gml(f_full_path)
            self.assertEqual(nx.is_bipartite(G),True)

    def test_bipartite_directed_rxnsub_nodes(self):
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
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f)
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
            f_full_path = os.path.join(self.__graphs_outdir,'bipartite-directed-rxnsub',f)
            G = nx.read_gml(f_full_path)
            self.assertEqual(set(expected_edges[f]),set(G.edges()))

####### need to modify below still
class TestTopologyBipartiteUndirectedRxnsub(unittest.TestCase):

    ## fpath for testing graphs
    gmldir = 'test/userdata/gmls/'
    gmltypedir = 'bipartite-undirected-rxnsub/'
    gmlfname = '1.1.1.3;test_ec_1.1.1.3.dat.gml'
    fpath=gmldir+gmltypedir+gmlfname

    G = nx.read_gml(fpath)

    ## 'bipartite-undirected-rxnsub'
    def test_bipartite_undirected_rxnsub_is_undirected(self):

        self.assertEqual(nx.is_directed(self.G),False)

    def test_bipartite_undirected_rxnsub_is_bipartite(self):

        self.assertEqual(nx.is_bipartite(self.G),True)

    def test_bipartite_undirected_rxnsub_nodes(self):

        expected_nodes = {'C00003',
                          'C00004',
                          'C00005',
                          'C00006',
                          'C00080',
                          'C00263',
                          'C00441',
                          'R01773',
                          'R01775'}

        self.assertEqual(expected_nodes,set(self.G.nodes()))

    def test_bipartite_undirected_rxnsub_edges(self):

        expected_edges = {frozenset({'C00441', 'R01775'}),
                         frozenset({'C00080', 'R01775'}),
                         frozenset({'C00005', 'R01775'}),
                         frozenset({'C00080', 'R01773'}),
                         frozenset({'C00003', 'R01773'}),
                         frozenset({'C00263', 'R01775'}),
                         frozenset({'C00006', 'R01775'}),
                         frozenset({'C00441', 'R01773'}),
                         frozenset({'C00004', 'R01773'}),
                         frozenset({'C00263', 'R01773'})}

        self.assertEqual(expected_edges,set(frozenset(edge) for edge in self.G.edges()))

class TestTopologyUnipartiteUndirectedRxn(unittest.TestCase):

    ## fpath for testing graphs
    gmldir = 'test/userdata/gmls/'
    gmltypedir = 'unipartite-undirected-rxn/'
    gmlfname = '1.1.1.3;test_ec_1.1.1.3.dat.gml'
    fpath=gmldir+gmltypedir+gmlfname

    G = nx.read_gml(fpath)

    ## 'unipartite-undirected-rxn'
    def test_unipartite_undirected_rxn_is_undirected(self):

        self.assertEqual(nx.is_directed(self.G),False)

    ## Unipartite networks aren't necessarily NOT bipartite as far as the check
    ## by networkx is concerned (e.g. a path network from 0->1,1->2,2->3 is 
    ## bipartite, but if you add a connection from 3->1 it is no longer bipartite.
    # def test_unipartite_undirected_rxn_is_unipartite(self):

    #     self.assertEqual(nx.is_bipartite(self.G),False)

    def test_unipartite_undirected_rxn_nodes(self):

        expected_nodes = {'R01773','R01775'}

        self.assertEqual(expected_nodes,set(self.G.nodes()))

    def test_unipartite_undirected_rxn_edges(self):

        expected_edges = [{'R01773','R01775'}]

        self.assertEqual(expected_edges,[set(edge) for edge in self.G.edges()])

class TestTopologyUnipartiteDirectedSub(unittest.TestCase):

    ## fpath for testing graphs
    gmldir = 'test/userdata/gmls/'
    gmltypedir = 'unipartite-directed-sub/'
    gmlfname = '1.1.1.3;test_ec_1.1.1.3.dat.gml'
    fpath=gmldir+gmltypedir+gmlfname

    G = nx.read_gml(fpath)

    ## 'unipartite-directed-sub'
    def test_unipartite_directed_sub_is_directed(self):

        self.assertEqual(nx.is_directed(self.G),True)

    # def test_unipartite_directed_sub_is_unipartite(self):

    #     self.assertEqual(nx.is_bipartite(self.G),False)

    def test_unipartite_directed_sub_nodes(self):

        expected_nodes = {'C00003',
                          'C00004',
                          'C00005',
                          'C00006',
                          'C00080',
                          'C00263',
                          'C00441'}

        self.assertEqual(expected_nodes,set(self.G.nodes()))

    def test_unipartite_directed_sub_edges(self):

        expected_edges = {('C00003', 'C00004'),
                          ('C00003', 'C00080'),
                          ('C00003', 'C00441'),
                          ('C00263', 'C00004'),
                          ('C00263', 'C00441'),
                          ('C00263', 'C00080'),
                          ('C00263', 'C00005'),
                          ('C00006', 'C00005'),
                          ('C00006', 'C00080'),
                          ('C00006', 'C00441')}

        self.assertEqual(expected_edges,set(self.G.edges()))

class TestTopologyUnipartiteUndirectedSub(unittest.TestCase):

    ## fpath for testing graphs
    gmldir = 'test/userdata/gmls/'
    gmltypedir = 'unipartite-undirected-sub/'
    gmlfname = '1.1.1.3;test_ec_1.1.1.3.dat.gml'
    fpath=gmldir+gmltypedir+gmlfname

    G = nx.read_gml(fpath)

    # ## 'unipartite-undirected-sub'
    def test_unipartite_undirected_sub_is_undirected(self):

        self.assertEqual(nx.is_directed(self.G),False)

    # def test_unipartite_undirected_sub_is_unipartite(self):

    def test_unipartite_undirected_sub_nodes(self):

        expected_nodes = {'C00003',
                          'C00004',
                          'C00005',
                          'C00006',
                          'C00080',
                          'C00263',
                          'C00441'}

        self.assertEqual(expected_nodes,set(self.G.nodes()))

    def test_unipartite_undirected_sub_edges(self):

        expected_edges = {frozenset({'C00003', 'C00004'}),
                          frozenset({'C00003', 'C00080'}),
                          frozenset({'C00003', 'C00441'}),
                          frozenset({'C00003', 'C00263'}),
                          frozenset({'C00004', 'C00080'}),
                          frozenset({'C00004', 'C00441'}),
                          frozenset({'C00005', 'C00080'}),
                          frozenset({'C00005', 'C00441'}),
                          frozenset({'C00080', 'C00441'}),
                          frozenset({'C00263', 'C00004'}),
                          frozenset({'C00263', 'C00441'}),
                          frozenset({'C00263', 'C00080'}),
                          frozenset({'C00263', 'C00005'}),
                          frozenset({'C00263', 'C00006'}),
                          frozenset({'C00006', 'C00005'}),
                          frozenset({'C00006', 'C00080'}),
                          frozenset({'C00006', 'C00441'})}

        self.assertEqual(expected_edges,set(frozenset(edge) for edge in self.G.edges()))

class TestTopologyUnipartiteUndirectedSub(unittest.TestCase):

    ## fpath for testing graphs
    gmldir = 'test/userdata/gmls/'
    gmltypedir = 'unipartite-undirected-subfromdirected/'
    gmlfname = '1.1.1.3;test_ec_1.1.1.3.dat.gml'
    fpath=gmldir+gmltypedir+gmlfname

    G = nx.read_gml(fpath)
    ## 'unipartite-undirected-subfromdirected'

    def test_unipartite_undirected_subfromdirected_is_undirected(self):

        self.assertEqual(nx.is_directed(self.G),False)

    # def test_unipartite_undirected_subfromdirected_is_unipartite(self):

    def test_unipartite_undirected_subfromdirected_nodes(self):

        expected_nodes = {'C00003',
                          'C00004',
                          'C00005',
                          'C00006',
                          'C00080',
                          'C00263',
                          'C00441'}

        self.assertEqual(expected_nodes,set(self.G.nodes()))

    def test_unipartite_undirected_subfromdirected_edges(self):

        expected_edges = {frozenset({'C00003', 'C00004'}),
                          frozenset({'C00003', 'C00080'}),
                          frozenset({'C00003', 'C00441'}),
                          frozenset({'C00263', 'C00004'}),
                          frozenset({'C00263', 'C00441'}),
                          frozenset({'C00263', 'C00080'}),
                          frozenset({'C00263', 'C00005'}),
                          frozenset({'C00006', 'C00005'}),
                          frozenset({'C00006', 'C00080'}),
                          frozenset({'C00006', 'C00441'})}

        self.assertEqual(expected_edges,set(frozenset(edge) for edge in self.G.edges()))

