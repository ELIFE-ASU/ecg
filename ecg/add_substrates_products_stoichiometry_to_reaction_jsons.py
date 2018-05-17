import json
import re
import os
import glob

def add_substrates_products_stoichiometry_to_reaction_jsons(dirname,outdirname):

    if not os.path.exists(outdirname):
        os.makedirs(outdirname)

    for path in glob.glob(dirname+"*.json"):
        print path
        outpath = outdirname+os.path.basename(path)

        with open(path) as data_file:    
            data = json.load(data_file)
            
            equation = data[0]["equation"]

            # print equation

            if re.search(r'(G\d+)',equation) == None: ## Only find entries without glycans

                glycan = False

                for i, side in enumerate(equation.split(" <=> ")):
                    # print i, side
                    # if i==0:
                    #   reactants = []
                    #   reactants_stoichiometry = []
                    # elif i==1:
                    #   products = []
                    #   products_stoichiometry = []

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
                        # print "Substrates!"
                        data[0]["substrates"] = compounds
                        data[0]["substrate_stoichiometries"] = stoichiometries
                    elif i==1:
                        # print "Products!"
                        data[0]["products"] = compounds
                        data[0]["product_stoichiometries"] = stoichiometries

                    # print compounds
                    # print stoichiometries
                    assert len(compounds) == len(stoichiometries)
                    # print "="*70
                    data[0]["glycans"] = False




            else:

                data[0]["glycans"] = True


        with open(outpath, 'w') as outfile:
            
            json.dump(data, outfile, indent=2)

def test_parsing(dirname):

    with open(dirname+"R00001.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["C00404","C00001"])
        assert set(data["products"]) == set(["C02174"])

        assert set(data["substrate_stoichiometries"]) == set(["1","n"])
        assert set(data["product_stoichiometries"]) == set(["(n+1)"])

    with open(dirname+"R00006.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["C00900","C00011"])
        assert set(data["products"]) == set(["C00022"])

        assert set(data["substrate_stoichiometries"]) == set(["1"])
        assert set(data["product_stoichiometries"]) == set(["2"])

    with open(dirname+"R00008.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["C06033"])
        assert set(data["products"]) == set(["C00022"])

        assert set(data["substrate_stoichiometries"]) == set(["1"])
        assert set(data["product_stoichiometries"]) == set(["2"])

    with open(dirname+"R00011.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["C19610","C00027","C00080"])
        assert set(data["products"]) == set(["C19611","C00001"])

        assert set(data["substrate_stoichiometries"]) == set(["1","2"])
        assert set(data["product_stoichiometries"]) == set(["2"])

    with open(dirname+"R05624.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["C00001","C06215"])
        assert set(data["products"]) == set(["C06215"])

        assert set(data["substrate_stoichiometries"]) == set(["1","(m+n)"])
        assert set(data["product_stoichiometries"]) == set(["(m)","(n)"])

    with open(dirname+"R07640.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["C00002","C00046","C00046"])
        assert set(data["products"]) == set(["C00020","C00013","C00046"])

        assert set(data["substrate_stoichiometries"]) == set(["1","(m)","(n)"])
        assert set(data["product_stoichiometries"]) == set(["1","(n+m)"])





def main():
    dirname = "newdata/20171201/reactions/"
    outdirname = "newdata/20171201/reactions_detailed/"

    # add_substrates_products_stoichiometry_to_reaction_jsons(dirname,outdirname)
    test_parsing(outdirname)


if __name__ == '__main__':
    main()


# (\(\S*\) C\d+)            # match (n+1) C00001, (m-1) C00001 or similar
# (\d*[n,m] C\d+)           # match 23n C00001, m C00001 or similar
# (C\d+\(\S*\))             # match C06215(m+n), C06215(23m) or similar
# (\d+ C\d+)                # match 3 C00002 or similar (but NOT C00002 without a number)
# (^C\d+)                   # match "C00001 "at the start of the line (no coefficients)
# (\+ C\d+ )                # match "+ C00001 " (no coefficients)
# (\+ C\d+$)                # match "+ C00001" at the end of the line (no coefficients)
# (^C\d+$)                  # match "C00001" which is at the start and end of the line
