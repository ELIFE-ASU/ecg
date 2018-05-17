import json
import os
import glob

def generate_reaction_substrate_product_edges_json(dirname,outpath):

    big_dict = dict()
    big_dict["substrates"] = dict()
    big_dict["products"] = dict()

    for path in glob.glob(dirname+"*.json"):

        with open(path) as data_file:    
            data = json.load(data_file)[0]
            
            if data["glycans"] == False:
                # print False
                # print data["entry_id"]
                # print data["substrates"]
                big_dict["substrates"][data["entry_id"]] = data["substrates"]
                big_dict["products"][data["entry_id"]] = data["products"]

    # print "n_glycans ", n_glycans
    # print "n_compounds ", n_compounds
    # print "total ", n_compounds+n_glycans


    with open(outpath, 'w') as outfile:
            
        json.dump(big_dict, outfile, indent=2)

def main():
    dirname = "newdata/20171201/reactions_detailed/"
    outpath = "newdata/20171201/reaction_edges.json"

    generate_reaction_substrate_product_edges_json(dirname, outpath)

if __name__ == '__main__':
	main()