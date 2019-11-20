def test_parsing(keggdir):

    dirname = keggdir+'reaction_detail/'
    with open(dirname+"rn:R00001.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["cpd:C00404","cpd:C00001"])
        assert set(data["products"]) == set(["cpd:C02174"])

        assert set(data["substrate_stoichiometries"]) == set(["1","n"])
        assert set(data["product_stoichiometries"]) == set(["(n+1)"])

    with open(dirname+"rn:R00006.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["cpd:C00900","cpd:C00011"])
        assert set(data["products"]) == set(["cpd:C00022"])

        assert set(data["substrate_stoichiometries"]) == set(["1"])
        assert set(data["product_stoichiometries"]) == set(["2"])

    with open(dirname+"rn:R00008.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["cpd:C06033"])
        assert set(data["products"]) == set(["cpd:C00022"])

        assert set(data["substrate_stoichiometries"]) == set(["1"])
        assert set(data["product_stoichiometries"]) == set(["2"])

    with open(dirname+"rn:R00011.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["cpd:C19610","cpd:C00027","cpd:C00080"])
        assert set(data["products"]) == set(["cpd:C19611","cpd:C00001"])

        assert set(data["substrate_stoichiometries"]) == set(["1","2"])
        assert set(data["product_stoichiometries"]) == set(["2"])

    with open(dirname+"rn:R05624.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["cpd:C00001","cpd:C06215"])
        assert set(data["products"]) == set(["cpd:C06215"])

        assert set(data["substrate_stoichiometries"]) == set(["1","(m+n)"])
        assert set(data["product_stoichiometries"]) == set(["(m)","(n)"])

    with open(dirname+"rn:R07640.json") as data_file:    
        data = json.load(data_file)[0]
        assert set(data["substrates"]) == set(["cpd:C00002","cpd:C00046","cpd:C00046"])
        assert set(data["products"]) == set(["cpd:C00020","cpd:C00013","cpd:C00046"])

        assert set(data["substrate_stoichiometries"]) == set(["1","(m)","(n)"])
        assert set(data["product_stoichiometries"]) == set(["1","(n+m)"])