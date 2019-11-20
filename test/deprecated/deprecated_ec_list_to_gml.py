import unittest
import os
# import sys
# import os
# sys.path.insert(1, os.path.join(sys.path[0], '..')) ## Allows importing module from parent directory
import ecg
import networkx as nx
from ecg.convert_eclists_to_graphs import get_organism_ec_list


class TestGetOrganismECList(unittest.TestCase):

    print os.getcwd()
    
    fpath_header = "test/userdata/ec_lists/domaindir/test_header-1.dat"
    fpath_no_header = "test/userdata/ec_lists/domaindir/test_no_header-1.dat"
    fpath_multiple_hashtag = "test/userdata/ec_lists/test_multiple_hashtag-1.dat"
    fpath_no_dir = "test/userdata/ec_lists/test_no_dir-1.dat"
    
    def test_write_header_valid(self):
        expected_fname = '3300010399.0;test_header-1.dat'
        outfname, genome_ec_list = get_organism_ec_list(self.fpath_header,write_dir_to_outfname=False)
        self.assertEqual(outfname,expected_fname)
    
    def test_write_header_invalid(self):
        with self.assertRaises(ValueError):
            outfname, genome_ec_list = get_organism_ec_list(self.fpath_no_header,write_dir_to_outfname=False)

    def test_multiple_hastag_header(self):
        expected_fname = '3300010399.0;test_multiple_hashtag-1.dat'
        outfname, genome_ec_list = get_organism_ec_list(self.fpath_multiple_hashtag,write_dir_to_outfname=False)
        self.assertEqual(outfname,expected_fname)

    def test_all_arg_false(self):
        with self.assertRaises(ValueError) and self.assertRaises(Warning):
            outfname, genome_ec_list = get_organism_ec_list(self.fpath_header,write_dir_to_outfname=False,write_header_to_outfname=False,write_fname_to_outfname=False)

    def test_write_subdirectory_valid(self):
        expected_fname = 'domaindir;3300010399.0.dat'
        with self.assertRaises(Warning):
            outfname, genome_ec_list = get_organism_ec_list(self.fpath_header, write_fname_to_outfname=False)
            self.assertEqual(outfname,expected_fname)

    def test_write_subdirectory_invalid(self):
        with self.assertRaises(ValueError) and self.assertRaises(Warning):
            outfname, genome_ec_list = get_organism_ec_list(self.fpath_no_dir,write_fname_to_outfname=False)

    def test_write_all(self):
        expected_fname = 'domaindir/domaindir;3300010399.0;test_header-1.dat'
        outfname, genome_ec_list = get_organism_ec_list(self.fpath_header)
        self.assertEqual(outfname,expected_fname)

    def test_ec_list_with_header(self):
        expected_ec_list = ['1.1.-.-',
                            '1.1.1.-',
                            '1.1.1.1',
                            '1.1.1.10',
                            '1.1.1.101',
                            '1.1.1.102',
                            '1.1.1.103',
                            '1.1.1.105',
                            '1.1.1.107']
        
        outfname, genome_ec_list = get_organism_ec_list(self.fpath_header)
        self.assertEqual(genome_ec_list,expected_ec_list)


    def test_ec_list_no_header(self):
        expected_ec_list = ['1.1.-.-',
                            '1.1.1.-',
                            '1.1.1.1',
                            '1.1.1.10',
                            '1.1.1.101',
                            '1.1.1.102',
                            '1.1.1.103',
                            '1.1.1.105',
                            '1.1.1.107']

        outfname, genome_ec_list = get_organism_ec_list(self.fpath_no_header,write_header_to_outfname=False,)
        self.assertEqual(genome_ec_list,expected_ec_list)

class TestGraphTypes(unittest.TestCase):

    ## Paths to user directories
    ## Input
    fpath = 'test/userdata/ec_lists/test_ec_1.1.1.3.dat'
    ## Output
    gmldir = 'test/userdata/gmls/'
    missingdir = 'test/userdata/missingdata/'

    write_dir_to_outfpath=False
    write_dir_to_outfname=False
    write_header_to_outfname=True
    write_fname_to_outfname=True

    def test_write_all_graphs(self):

        ## Arguments
        graphtypes = ['bipartite-directed-rxnsub',
        'bipartite-undirected-rxnsub',
        'unipartite-undirected-rxn',
        'unipartite-directed-sub',
        'unipartite-undirected-sub',
        'unipartite-undirected-subfromdirected']

        ecg.write_graphs_from_one_genome(
            self.fpath,
            self.gmldir,
            self.missingdir,
            graphtypes=graphtypes, 
            write_dir_to_outfpath=self.write_dir_to_outfpath,
            write_dir_to_outfname=self.write_dir_to_outfname,
            write_header_to_outfname=self.write_header_to_outfname,
            write_fname_to_outfname=self.write_fname_to_outfname)

class TestTopologyBipartiteDirectedRxnsub(unittest.TestCase):

    ## fpath for testing graphs
    gmldir = 'test/userdata/gmls/'
    gmltypedir = 'bipartite-directed-rxnsub/'
    gmlfname = '1.1.1.3;test_ec_1.1.1.3.dat.gml'
    fpath=gmldir+gmltypedir+gmlfname

    G = nx.read_gml(fpath)

    ## 'bipartite-directed-rxnsub'
    def test_bipartite_directed_rxnsub_is_directed(self):

        self.assertEqual(nx.is_directed(self.G),True)

    def test_bipartite_directed_rxnsub_is_bipartite(self):

        self.assertEqual(nx.is_bipartite(self.G),True)

    def test_bipartite_directed_rxnsub_nodes(self):

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

    def test_bipartite_directed_rxnsub_edges(self):

        expected_edges = {('C00003', 'R01773'),
                         ('C00006', 'R01775'),
                         ('C00263', 'R01773'),
                         ('C00263', 'R01775'),
                         ('R01773', 'C00004'),
                         ('R01773', 'C00080'),
                         ('R01773', 'C00441'),
                         ('R01775', 'C00005'),
                         ('R01775', 'C00080'),
                         ('R01775', 'C00441')}

        self.assertEqual(expected_edges,set(self.G.edges()))

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






