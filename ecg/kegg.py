import os
import re
import json
import copy
import glob
import itertools
import warnings
import argparse
from Bio.KEGG import REST #, Enzyme, Compound, Map
import Bio.TogoWS as TogoWS
from tqdm import tqdm
import pandas as pd

class Kegg(object):

    def __init__(self,path):

        self.path = path
        ## If path not empty, try to load relevent properties
        try:
            ## Set version
            version_path = os.path.join(path, "version.json")
            with open(version_path) as f:
                version = json.load(f) #[0]
            self.version = version

        except:
            self.version = None
        
        try:
            ## Set lists
            self.lists = self.version["current"]["lists"]
        except:
            self.lists = None

    @property
    def path(self):
        return self.__path 

    @path.setter
    def path(self,path):
        if not os.path.exists(path):
            os.makedirs(path)
        self.__path = path

    @property
    def version(self):
        return self.__version 

    @version.setter
    def version(self,version):
        self.__version = version

    @property
    def lists(self):
        return self.__lists 
    
    @lists.setter 
    def lists(self,lists):
        self.__lists = lists

    def download(self,run_pipeline=True,dbs=["pathway","enzyme","reaction","compound"]):

        for _dirpath, _dirnames, files in os.walk(self.path):
            if files:
                raise ValueError("Directory must be empty to initiate a fresh KEGG download.\
                              Looking to update KEGG? Try `Kegg.update()` instead.")
        
        self._download_lists(dbs)
        self._download_entries(dbs)


        if run_pipeline:

            self._detail_compounds()
            self._detail_reactions()
            self._download_links()
            self._get_current_version()
            self._write_master()

    def _download_lists(self,dbs=["pathway","enzyme","reaction","compound"]):
        """
        Returns db.json of ids and names in dbs (default: map (pathway), ec, rn, cpd).
        """

        lists_path = os.path.join(self.path, "lists")
        if not os.path.exists(lists_path):
            os.makedirs(lists_path)

        self.lists = self.__retrieve_lists(dbs)

        ## Write json of all entry ids and names
        for db in dbs:
            list_path = os.path.join(lists_path, db+".json")
            with open(list_path, 'w') as f:   
                json.dump(self.lists[db], f, indent=2)

    def _download_entries(self,dbs=["pathway","enzyme","reaction","compound"]):
        """
        Returns jsons of entries of dbs (default: map (pathway), ec, rn, cpd).
        """

        ## Get entries on all kegg types
        for db in dbs:

            ## Read list of all kegg ids
            list_path = os.path.join(self.path,"lists",db+".json")
            with open(list_path) as f:    
                list_data = json.load(f) #[0]

            ## Create dir to store entries in
            entries_path = os.path.join(self.path,"entries",db)
            if not os.path.exists(entries_path):
                os.makedirs(entries_path)

            ## Grab each entry in list
            for entry in tqdm(list_data):
                # print(entry)
                # print(entry == None)
                # entry_id = entry.split(":")[1]
                entry_id = entry
                entry_fname = entry_id+".json"
                entry_path = os.path.join(entries_path, entry_fname)

                while entry_fname not in os.listdir(entries_path):
                    try:
                        handle = TogoWS.entry(db, entry_id, format="json")
                        with open(entry_path, 'a') as f:
                            f.write(handle.read())
                    except:
                        pass
    
    def _detail_compounds(self):
        """
        Add information about elements in compounds
        """

        compound_path = os.path.join(self.path,'entries','compound','')

        for path in glob.glob(compound_path+"*.json"):
            with open(path) as f:
                data = json.load(f)[0]
                elements = re.findall(r"([A-Z][a-z]?)",data['formula'])
                data["elements"] = list(set(elements))

            ## Rewrite file with added detail
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def _detail_reactions(self):
        """
        Add reaction details in convenient fields for rn jsons.
        """

        reaction_path = os.path.join(self.path,'entries','reaction','')
        compound_path = os.path.join(self.path,'entries','compound','')

        compound_dict = dict()
        for path in glob.glob(compound_path+"*.json"):
            with open(path) as f:
                compound_json = json.load(f) #[0]
                compound_dict[compound_json["entry_id"]] = compound_json
        
        for path in glob.glob(reaction_path+"*.json"):
            
            with open(path) as f:
                data = json.load(f)
                if data[0].get("entry_id", None):
                    equation = data[0]["equation"]

                    if re.search(r'(G\d+)',equation) == None: ## Only find entries without glycans

                        for i, side in enumerate(equation.split(" <=> ")):

                            compounds = []
                            stoichiometries = []

                            ## match (n+1) C00001, (m-1) C00001 or similar
                            matches = re.findall(r'(\(\S*\) C\d+)',side)
                            # print matches
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = re.search(r'(\(\S*\))',match).group(1)
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            ## match 23n C00001, m C00001 or similar
                            matches = re.findall(r'(\d*[n,m] C\d+)',side)
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = re.search(r'(\d*[n,m])',match).group(1)
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            ## match C06215(m+n), C06215(23m) or similar
                            matches = re.findall(r'(C\d+\(\S*\))',side)
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = re.search(r'(\(\S*\))',match).group(1)
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            ## match "3 C00002" or similar (but NOT C00002 without a number)
                            matches = re.findall(r'(\d+ C\d+)',side)
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = match.split(' '+compound)[0]# re.search(r'(\(\S*\))',match).group(1)
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            ## match "C00001 "at the start of the line (no coefficients)
                            matches = re.findall(r'(^C\d+) ',side)
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = '1'
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            ## match "+ C00001 " (no coefficients)
                            matches = re.findall(r'(\+ C\d+ )',side)
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = "1"
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            ## match "+ C00001" at the end of the line (no coefficients)
                            matches = re.findall(r'(\+ C\d+$)',side)
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = "1"
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            ## match "C00001" which is at the start and end of the line
                            matches = re.findall(r'(^C\d+$)',side)
                            if len(matches) != 0:
                                for match in matches:
                                    compound = re.search(r'(C\d+)',match).group(1)
                                    stoichiometry = "1"
                                    
                                    compounds.append(compound)
                                    stoichiometries.append(stoichiometry)

                            if i==0:
                                data[0]["left"] = compounds
                                data[0]["left_stoichiometries"] = stoichiometries
                                data[0]["left_elements"] = set()
                                ## Add element data
                                for c in compounds:
                                    if c in compound_dict:
                                        data[0]["left_elements"] = data[0]["left_elements"].union(compound_dict[c]['elements'])
                                    else:
                                        data[0]["left_elements"] = data[0]["left_elements"].union('missing_cid')
                                        data[0]["contains_missingcid"] = True
                            elif i==1:
                                data[0]["right"] = compounds
                                data[0]["right_stoichiometries"] = stoichiometries
                                data[0]["right_elements"] = set()
                                ## Add element data
                                for c in compounds:
                                    if c in compound_dict:
                                        data[0]["right_elements"] = data[0]["right_elements"].union(compound_dict[c]['elements'])
                                    else:
                                        data[0]["right_elements"] = data[0]["right_elements"].union('missing_cid')
                                        data[0]["contains_missingcid"] = True
                            
                        if "contains_missingcid" not in data[0]:
                            data[0]["contains_missingcid"] = False
                        print(path)
                        if data[0]["left_elements"] != data[0]["right_elements"]:
                            data[0]["element_conservation"] = False
                            data[0]["elements_mismatched"] = list(data[0]["left_elements"]^data[0]["right_elements"])
                        else:
                            data[0]["element_conservation"] = True
                            data[0]["elements_mismatched"] = list()
                        
                        assert len(compounds) == len(stoichiometries)
                        data[0]["glycans"] = False

                    else:

                        data[0]["glycans"] = True

                ## Rewrite file with added detail
                with open(path, 'w') as f:

                    json.dump(data, f, indent=2, default=serialize_sets)
    
    def _download_links(self,dbs=["pathway","enzyme","reaction","compound", "orthology"]):
        """
        Returns jsons of mappings between each db (default: map (pathway), ec, rn, cpd).
        """

        for sourcedb, targetdb in itertools.permutations(dbs,2):

            links_raw = REST.kegg_link(targetdb, sourcedb)
            links = [s.split('\t') for s in links_raw.read().splitlines()]

            d = dict()
            for i in links:
                if i[0] in d:
                    d[i[0]].append(i[1])
                else:
                    d[i[0]] = [i[1]]

            ## Write json of all entry ids and names
            link_fname = sourcedb+"_"+targetdb
            links_path = os.path.join(self.path,'links')
            if not os.path.exists(links_path):
                os.makedirs(links_path)
            link_path = os.path.join(links_path, link_fname+".json")
            with open(link_path, 'w') as f:   
                json.dump(d, f, indent=2)

    def _get_current_version(self,dbs=["pathway","enzyme","reaction","compound"]):
        """
        Retrieves version info from KEGG
        Stores db lists onto Kegg object
        Writes version.json
        """
        current = self.__retrieve_info(dbs)

        ## Lists of .... from the directories
        current["lists"] = dict()
        for db in dbs:
            lists_path = os.path.join(self.path, "lists", db+".json")
            with open(lists_path) as f:    
                data = json.load(f)#[0]
            current["lists"][db] = data
            # db_entries = glob.glob(lists_path+"*.json")
            # current["lists"][db] = [os.path.splitext(os.path.basename(entry))[0] for entry in db_entries]
        self.lists = current["lists"]

        ## Counts based on the lists
        counts = dict()
        for db in self.lists:
            counts[db] = len(self.lists[db])
        current["count_lists"] = counts

        ## Assign version info to object
        self.version = {"original":current,"updates":[],"current":current}

        ## Write json
        version_path = os.path.join(self.path, "version.json")
        with open(version_path, 'w') as f:   
            json.dump(self.version, f, indent=2)

    def _write_master(self,metadata=True):
        """
        Write reaction edges + version info into master.json

        :param metadata: metadata fields from "RXXXXX.json"

        "reactions":
            {"R1":
                {"left":..., 
                "right":..., 
                "metadata":...},
            "R2":
                {"left":..., 
                "right":..., 
                "metadata":...},
            ...}
        """

        reactions = dict()
        indir = os.path.join(self.path, "entries", "reaction",'') ## Should be the detailed reactions
        for path in glob.glob(indir+"*.json"):
            
            with open(path) as f:
                print(path)
                data = json.load(f)[0]
                if data.get("glycans", False) == False:
                    
                    ## Main data
                    rID = data.pop("entry_id")
                    print(rID)
                    reactions[rID] = dict()
                    reactions[rID]["left"] = data.pop("left")
                    reactions[rID]["right"] = data.pop("right")

                    ## Metadata
                    if metadata:
                        reactions[rID]["metadata"] = data
                    else:
                        reactions[rID]["metadata"] = {}

        master = dict()
        master["version"] = self.version 
        master["reactions"] = reactions

        master_path = os.path.join(self.path,'master.json')
        with open(master_path, 'w') as f:
            json.dump(master, f, indent=2)

    def update(self,metadata=True):
        warnings.warn("""
                        Updating will NOT reflect changes made to invdividual
                        entries' fields, and it will NOT remove entries which
                        have been removed from KEGG. It will only add entries
                        which have been added. To guarantee the most
                        up-to-date KEGG database, a full re-download is
                        necessary.
                        """)

        release_change = False
        list_change = False
        dbs = list(self.lists.keys())

        ## Check short_release differences
        old_release_short = self.version["current"]["release_short"]
        new_release = self.__retrieve_info(dbs)
        new_release_short = new_release["release_short"]

        if old_release_short != new_release_short:

            print("Release change identified")
            release_change = True

        ## Check list differences
        new_release["added"] = dict()
        new_release["removed"] = dict()

        old_lists = self.lists
        new_lists = self.__retrieve_lists(dbs)

        for db in dbs:
            old_keys = set(old_lists[db])
            new_keys = set(new_lists[db])
            if old_keys != new_keys:
                list_change = True
                print("Database list content change identified")
                new_release["added"][db] = list(new_keys - old_keys)
                new_release["removed"][db] = list(old_keys - new_keys)
        
        ## Update counts based on the lists
        counts = dict()
        for db in new_lists:
            counts[db] = len(new_lists[db])
        new_release["count_lists"] = counts 
        
        ## Execute updating
        if release_change or list_change:
            print("Updating local kegg database...")

            ## Update version["updates"]
            self.version["updates"].append(copy.copy(new_release)) #prevents lists from being written
            # Includes the following keys:
            # added
            # removed
            # count_lists
            # count_info
            # release_short
            # release_long
            
            ## Update version["current"]
            # Adds the key for `lists`
            self.lists = new_lists
            new_release["lists"] = self.lists # this won't include entries which
                                              # have been removed but are still 
                                              # in the entries dir
            self.version["current"] = new_release

            # print(type(new_release))
            # print(new_release)

            ## Rewrite version.json
            version_path = os.path.join(self.path, "version.json")
            with open(version_path, 'w') as f:   
                json.dump(self.version, f, indent=2)

            ## Rewrite list jsons (fast)
            lists_path = os.path.join(self.path, "lists")
            for db in dbs:
                list_path = os.path.join(lists_path, db+".json")
                with open(list_path, 'w') as f:   
                    json.dump(self.lists[db], f, indent=2)

            ## Rewrite link jsons (fast)
            self._download_links(dbs)

            ## Add to entries jsons (does not remove `removed` entries)
            for db in new_release["added"]:
                entries_path = os.path.join(self.path,"entries",db)
                for entry in tqdm(new_release["added"][db]):

                    entry_id = entry.split(":")[1]
                    entry_fname = entry_id+".json"
                    entry_path = os.path.join(entries_path, entry_fname)

                    while entry_fname not in os.listdir(entries_path):
                        try:
                            handle = TogoWS.entry(db, entry_id, format="json")
                            with open(entry_path, 'a') as f:
                                f.write(handle.read())
                        except:
                            pass

            ## Rewrite master json 
            self._write_master(metadata)

            print("Done.")

        else:
            print("No release or database list changes identified. \nNo updates available.")

    def __retrieve_info(self,dbs):

        current = dict()
        ## Get info from http://rest.kegg.jp/info/kegg
        ## Note that this does not necessarily match what is returned from lists
        raw_list = REST.kegg_info("kegg")
        split = raw_list.read().splitlines()
        current["count_info"] = dict()
        for line in split:
            split_line = line.split()
            overlap = set(dbs) & set(split_line)
            if "Release" in split_line:
                current["release_short"] = float(split_line[2].split("/")[0][:-1])
                release_long = [split_line[2][:-1]]+split_line[3:]
                current["release_long"] = ("_").join(release_long)
            elif overlap:
                current["count_info"][split_line[0]] = int(split_line[1].replace(',' , ''))

        return current

    def __retrieve_lists(self,dbs):
        
        lists = dict()
        for db in dbs:
        
            ## Retreive all entry ids and names
            id_name_dict = dict()
            raw_list = REST.kegg_list(db)
            id_name_list = [s.split('\t') for s in raw_list.read().splitlines()]
            for i in id_name_list:
                id_name_dict[i[0]] = i[1]

            lists[db] = list(id_name_dict.keys())
            
        return lists

def __execute_cli(args):

    """
    Call appropriate methods based on command line interface input.
    """
    
    run_pipeline = args.rp
    metadata = args.md
    path = args.path
    
    if args.download == True:
        K = Kegg(path)
        K.download(run_pipeline=run_pipeline,dbs=args.db)

    if args.update == True:
        K = Kegg(path)
        K.update(metadata=metadata)

def serialize_sets(obj):
    if isinstance(obj, set):
        return list(obj)

    return obj

if __name__ == '__main__':

    # Initial setup of argparse with description of program.
    parser = argparse.ArgumentParser(description='Retrieve KEGG databases and format them for use in network expansions.')

    parser.add_argument('--rp',default=True,type=bool,help='Whether or not to run the full pipline. (Default = True)')
    parser.add_argument('--db',default=['pathway','enzyme','reaction','compound'],choices = ['pathway', 'brite', 'module', 'ko', 'genome', '<org>', 'vg', 'ag', 'compound', 'glycan', 'reaction', 'rclass', 'enzyme', 'network', 'hsa_var', 'disease', 'drug', 'dgroup', 'environ'],nargs='+',type=str,help='Databases to download. For more information on dbs see KEGG DB Links. (Default = ["pathway", "enzyme", "reaction", "compound"])')
    parser.add_argument('--md',default=True,type=bool,help='Whether to add metadata fields from "RXXXXX.json" into master.json. (Default = True)')
    parser.add_argument('--path',default=None,required=True,type=str,help='Directory where KEGG will be downloaded to or updated. (Required)')
    parser.add_argument('--download',default=True,type=bool,help='Whether to download KEGG and run pipeline to format data. (Default = True)')
    parser.add_argument('--update',default=False,type=bool,help='Whether or not to update existing KEGG directory. Note: Updating will NOT reflect changes made to invdividual entry fields, and it will NOT remove entries which have been removed from KEGG. It will only add entries which have been added. To guarantee the most up-to-date KEGG database, a full re-download is necessary. (Default = False)')

    args = parser.parse_args()
 
    __execute_cli(args)

def retrieve_ec_transfers(directory='KEGG_Transfers', kegg_filter=False):
        
        """
        Identifies EC#s that have been "transferred" i.e. deprecated and re-labeled.
        Writes these to text files in directory, if provided
        
        Parameters
        ----------
        directory : str (optional) 
            folder to write the files to
        kegg_filter : bool
            whether or not to limit outputs to those linked to a reaction in KEGG
        
        Returns
        ----------
        transfer_info : dict
            guide to keys...
                ecs : pandas.Series
                    Series of all valid EC numbers and names
                trs_1 : pandas.Series
                    Series of all 1:1 EC number transfers, i.e. transferred from index to value
                trs_N : pandas.Series
                    Series of lists for 1:N EC number transfers, i.e. transferred from index to {value1, value2 ... valueN}
                trs_1_kegg : pandas.Series
                    same as trs_1, filtered to include only transfers from index to value WHERE value is linked to a rxn in KEGG,
                    PLUS entries originally from trs_N WHERE only ONE value (of N values) is linked to a rxn in KEGG
                trs_N_kegg : pandas.Series
                    trs_N, filtered to include only transfers with multiple values linked to a rxn in KEGG
                kegg_ecs : set
                    set of EC#s tied to at least one reaction in KEGG
        """
        if len(directory)>1:
            directory = directory + '/'
            if not os.path.exists(directory):
                os.mkdir(directory)
        
        # download catalogue of all EC#s in kegg
        ecs = pd.Series(dict([i.split('\t') for i in REST.kegg_list('enzyme').read().split('\n')][:-1]))
        ecs.index = ecs.index.str.lstrip('ec:') 
        
        # note which ones have been transferred to *one or more* other EC#s
        s = 'Transferred to '
        trs = ecs[ecs.str.contains(s)].str.lstrip(s).str.replace(' and ',', ').str.split(', ') #turns all into lists
        trs.drop('3.6.3.17', inplace=True)    # new EC# not provided - IntEnz suggests 7.5.2.8, others 7.5.2.-
        
        # tag those with only one transfer destination 
        one = trs.apply(len)==1 
        
        # use that info to access their new EC#; retain list of EC#s for others
        trs_1, trs_N = trs[one].apply(lambda x: x[0]), trs[~one]
        
        # write files
        ecs.to_csv(directory+'EC_db_active.csv')
        trs_1.to_csv(directory+'EC_transfers_1to1.csv')
        trs_N.apply(lambda x: ' '.join(x)).to_csv(directory+'EC_transfers_1toN.csv')
        
        transfer_info = {'ecs':ecs, 'trs_1':trs_1, 'trs_N':trs_N}
        
        if kegg_filter:
            trs_1_kegg, trs_N_kegg, kegg_ecs = xref_transfers_with_kegg(trs_1=trs_1,trs_N=trs_N, directory=directory)
            transfer_info.update({'trs_1_kegg':trs_1_kegg, 'trs_N_kegg':trs_N_kegg, 'kegg_ecs': kegg_ecs})
        
        return(transfer_info)

def xref_transfers_with_kegg(trs_1, trs_N, directory='KEGG_Transfers/'):
    """
    Identifies which enzymes are linked to KEGG reactions; filters and updates transfer lists accordingly.
    
    Parameters
    ----------
    trs_1 : pandas.Series
        Series of all 1:1 EC number transfers, i.e. from index to value
    trs_N : pandas.Series
        Series of lists for 1:N EC number transfers, i.e. transferred from index to {value1, value2, ... valueN}
    directory : str (optional)
        folder to write the files to
    
    Returns
    ----------        
    trs_1N_kegg_1 : pandas.Series
        trs_1, filtered to include only transfers from index to value WHERE value is linked to a rxn in KEGG,
        PLUS entries originally from trs_N WHERE only ONE value (of N values) is linked to a rxn in KEGG
    trs_N_kegg_N : pandas.Series
         trs_N, filtered to include only transfers with multiple values linked to a rxn in KEGG
    """
    d = directory
    open(d+'reaction_enzyme_links.csv','w').write(REST.kegg_link('enzyme','reaction').read().replace('\t',',').
                                           replace('rn:','').replace('ec:',''))
    RnEz = pd.read_csv(d+'reaction_enzyme_links.csv',names=['rn','ec'], header=None)
    kegg_ecs = set(RnEz.ec.values)
    
    # Some target ECs are linked to KEGG rxns
    trs_N_kegg = trs_N.apply(lambda x: list(set(x) & kegg_ecs))
    # Some source ECs have multiple such target ECs
    trs_N_lengths = trs_N_kegg.apply(len)
    trs_N_kegg_N = trs_N_kegg[trs_N_lengths>1]
    # Other source ECs only point to one target EC
    trs_1N_kegg_1 = pd.concat([trs_1[trs_1.apply(lambda x: x in kegg_ecs)], # 1:1 xfers w/KEGG ties
                              trs_N_kegg[trs_N_lengths==1].apply(lambda x: x[0])]) # orig 1:N, now 1:1
    # Prints these filtered catalogues
    trs_1N_kegg_1.to_csv(d+'EC_transfers_1to1_inkegg.csv')
    trs_N_kegg_N.apply(lambda x: ' '.join(list(x))).to_csv(d+'EC_transfers_1toN_inkegg.csv')
    open(d+'ECs_w_kegg_linkage.csv','w').write(' '.join(kegg_ecs))

    return(trs_1N_kegg_1, trs_N_kegg_N, kegg_ecs)

# ecs,trs_1,trs_N = retrieve_ec_transfers(kegg_filter=True, directory='KEGG_Transfers')

