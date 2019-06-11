import os
import re
import json
import glob
import itertools
from Bio.KEGG import REST, Enzyme, Compound, Map
import Bio.TogoWS as TogoWS
from tqdm import tqdm

"""
keggdir
|-entries
|  |-compounds 
|  |-reactions 
|  |-enzymes 
|  |-pathways 
|
|-lists
|  |-compounds 
|  |-reactions 
|  |-enzymes 
|  |-pathways 
|
|-links
|  |-compound_enzyme
|  |-reaction_compound
|  |-enzyme_compound
|  |-pathway_reaction
|  ...
|
version.json # file with all the info that is in the version entry of the master, created upon download and updated upon update
|
master.json


Kegg = ecg.Kegg(keggdir) # keggdir is the top level dir 
                     # which kegg will be stored to or updated in

Kegg.download() #defaults to ["pathway","enzyme",""]. should output all necessary files and dirs
Kegg.update() #same defaults
-> Kegg.update(deep=False) #default, only updates based on list changes
-> Kegg.update(deep=True) #redownloads everything, maintains versioning metadata
Kegg.detail_reactions() #add detailed information to reactions. need detailed field with true/false.
Kegg.linkdbs() #create mappings between databases
Kegg.write_master_json(metadata=True) #this is edges plus metadata. include metadata in metadata field by default. otherwise can include empty metadata field

# properties
Kegg.release_short # returns release of database eg. 90.0
Kegg.release_full # returns 90.0+/06-06, Jun 19
Kegg.info  #returns info from http://rest.kegg.jp/info/kegg

# helper methods
Kegg.__check_if_already_linked
Kegg.__check_if_download_dir_empty
Kegg.__check_if_updating_kegg_changes_release
Kegg.__check_if_updating_kegg_changes_any_dbs #eg the set of reactions, compounds, enzymes, or pathways


# in master_json, store metadata on which cpds/enx/rxn/paths were updated in the update
 kegg_rxns = {"version": 
                {"original":
                    {"release_short":
                     "release_full":
                     "dbkeys_added":
                        {"compounds":
                         "reactions":
                         "enzymes":
                         "pathways":
                         }
                     "dbkeys_count":
                        {"compounds":#ncompounds
                         "reactions":#nreactions
                         "enzymes":#nenzymes
                         "pathways:"#npathways
                         }
                    }
                 "updates":
                    [{"release_short":
                     "release_full":
                     "info":
                        {"compounds":#ncompounds
                         "reactions":#nreactions
                         "enzymes":#nenzymes
                         "pathways:"#npathways
                         }
                    },
                    {"release_short":
                     "release_full":
                     "info":
                        {"compounds":#ncompounds
                         "reactions":#nreactions
                         "enzymes":#nenzymes
                         "pathways:"#npathways
                         }
                    },...]
                "current":
                    {"release_short":
                     "release_full":
                     "info":
                        {"compounds":#ncompounds
                         "reactions":#nreactions
                         "enzymes":#nenzymes
                         "pathways:"#npathways
                         }
                    }
                }
            "reactions":{}
            }

## Each above function should check to make sure necessary prereqs are met
"""
class Kegg(object):

    def __init__(self,path):

        self.path = path
        self.lists = dict()
        ## If path not empty, try to load relevent properties
        try:
            version_path = os.path.join(path, "version.json")
            with open(version_path) as f:    
                version = json.load(f) #[0]
            self.version = version
            self.lists = self.version["current"]["lists"]
            # os.path.isfile(path+"version.json")
        except:
            self.version = None

        # self.dbkeys = None 

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

        for dirpath, dirnames, files in os.walk(self.path):
            if files:
                raise ValueError("Directory must be empty to initiate a fresh KEGG download.\
                              Looking to update KEGG? Try `Kegg.update()` instead.")
        
        self._download_lists(dbs)
        self._download_entries(dbs)


        if run_pipeline:

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

        for db in dbs:
        
            ## Retreive all entry ids and names
            id_name_dict = dict()
            raw_list = REST.kegg_list(db)
            id_name_list = [s.split('\t') for s in raw_list.read().splitlines()]
            for i in id_name_list:
                id_name_dict[i[0]] = i[1]

            ## Add to self.lists
            self.lists[db] = set(id_name_dict.keys())

            ## Write json of all entry ids and names
            list_path = os.path.join(lists_path, db+".json")
            with open(list_path, 'w') as f:   
                json.dump(id_name_dict, f, indent=2)

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
            for i, entry in enumerate(tqdm(list_data)):
                
                entry_id = entry.split(":")[1]
                entry_fname = entry_id+".json"
                entry_path = os.path.join(entries_path, entry_fname)

                # print "Saving (verifying) %s entry %s of %s (%s)..."%(db,i+1,len(list_data),entry_id)

                while entry_fname not in os.listdir(entries_path):
                    try:
                    # print(db,entry_id)
                    # print(entry_fname)
                    # print(entry_path)
                        handle = TogoWS.entry(db, entry_id, format="json")
                        with open(entry_path, 'a') as f:
                            f.write(handle.read())
                    except:
                        pass

    def _detail_reactions(self):
        """
        Add reaction details in convenient fields for rn jsons.
        """

        reaction_path = os.path.join(self.path,'entries','reaction','')
        
        for path in glob.glob(reaction_path+"*.json"):
            
            with open(path) as f:    
                data = json.load(f)
                
                equation = data[0]["equation"]

                if re.search(r'(G\d+)',equation) == None: ## Only find entries without glycans

                    for i, side in enumerate(equation.split(" <=> ")):

                        compounds = []
                        stoichiometries = []

                        ## !!! Need to optimize the code here

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
                        elif i==1:
                            data[0]["right"] = compounds
                            data[0]["right_stoichiometries"] = stoichiometries

                        assert len(compounds) == len(stoichiometries)
                        data[0]["glycans"] = False

                else:

                    data[0]["glycans"] = True

            ## Rewrite file with added detail
            with open(path, 'w') as f:
                
                json.dump(data, f, indent=2)
    
    def _download_links(self,dbs=["pathway","enzyme","reaction","compound"]):
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

        {"version": 
            {"original":
                {"release_short":
                "release_full":
                "dbkeys_count":
                    {"compounds":#ncompounds
                        "reactions":#nreactions
                        "enzymes":#nenzymes
                        "pathways:"#npathways
                        }
                "dbkeys_list":
                    {"compounds":
                        "reactions":
                        "enzymes":
                        "pathways":
                        }
                }
            "updates":
                [{"release_short":
                "release_full":
                "dbkeys_count":
                    {"compounds":#ncompounds
                        "reactions":#nreactions
                        "enzymes":#nenzymes
                        "pathways:"#npathways
                        }
                "dbkeys_added":
                    {"compounds":
                        "reactions":
                        "enzymes":
                        "pathways":
                        }
                "dbkeys_removed":
                    {"compounds":
                        "reactions":
                        "enzymes":
                        "pathways":
                        }
                },...]
            "current":
                {"release_short":
                "release_full":
                "dbkeys_count":
                    {"compounds":#ncompounds
                        "reactions":#nreactions
                        "enzymes":#nenzymes
                        "pathways:"#npathways
                        }
                "dbkeys_list":
                    {"compounds":#ncompounds
                        "reactions":#nreactions
                        "enzymes":#nenzymes
                        "pathways:"#npathways
                        }
                }
            }
        }
        """
        current = {}

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

        ## Lists of compounds, reactions, etc. and their counts (calculated from these lists)
        # current["lists"] = self.lists

        ## Lists of .... from the directories
        current["lists"] = dict()
        for db in dbs:
            lists_path = os.path.join(self.path, "lists", db+".json")
            with open(lists_path) as f:    
                data = json.load(f)#[0]
            current["lists"][db] = list(data.keys())
            # db_entries = glob.glob(lists_path+"*.json")
            # current["lists"][db] = [os.path.splitext(os.path.basename(entry))[0] for entry in db_entries]
        self.lists = current["lists"]

        ## Counts based on the lists
        counts = dict()
        for db in self.lists:
            counts[db] = len(self.lists[db])
        current["count_lists"] = counts

        ## Assign version info to object
        self.version = {"current":current}

        ## Write json
        version_path = os.path.join(self.path, "version.json")
        with open(version_path, 'w') as f:   
            json.dump(current, f, indent=2)

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
                data = json.load(f)[0]
                
                if data["glycans"] == False:

                    ## Main data
                    rID = data.pop("entry_id")
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

    def update(self):
        raise Warning("Updating will NOT reflect changes made to invdividual \
                        entries' fields, and it will NOT remove entries which \
                        have been removed from KEGG. It will only add entries \
                        which have been added.\n\n To guarantee the most \
                        up-to-date KEGG database, a full re-download is \
                        necessary.")

        # self._check_if_release_changed()
        # if True:
        #     release_change = True
        # self._check_if_dbkeys_count_changed()
        # if True:
        #     count_change = True
        # self._check_if_dbkeys_list_changed()
        # if True:
        #     list_change = True

        # if release_change and count_change and list_change:
        #     update as normal
        # if release_change
        pass



