import unittest
import os
import glob
import json
from ecg.ecg import Ecg
# from nose.tools import assert_equals

def clear_dir(mydir):
    if os.path.exists(mydir):
        files = glob.glob(os.path.join(mydir,"*.json"))
        for f in files:
            os.remove(f)

class TestEcg(unittest.TestCase):
    @classmethod
    def setup_class(self):
        self.__ec_rxn_link_json = "userdata/kegg/links/enzyme_reaction.json"
        self.__taxon_ids_indir = "userdata/jgi/Eukaryota/taxon_ids"

        self.__biosystem_json_file_2enz = "1234567890.json"
        self.__biosystem_json_file_1enz2rxn = "1234567891.json"
        self.__biosystem_json_file_2components = "1234567892.json"
        # self.__biosystem_json_file_fulldir = ""
        
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