import os

keggdir
|-get
|  |-compounds 
|  |-reactions 
|  |-enzymes 
|  |-pathways 
|
|-list
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
                     "info":
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

class Kegg(object):

    def __init__(self,keggdir):

