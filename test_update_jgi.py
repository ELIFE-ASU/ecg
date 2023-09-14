from ecg import jgi 

J = jgi.Jgi()
domain = "*Microbiome"
path = "test_download"

J.scrape_urls(path, domain, 
                ["https://img.jgi.doe.gov/cgi-bin/m/main.cgi?section=TaxonDetail&page=taxonDetail&taxon_oid=3300037805"])