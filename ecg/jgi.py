"""

"""
## Need to add verbosity tag and find all print statements


from selenium import webdriver
import time
from tqdm import tqdm
import os
import re
import json
import warnings
from bs4 import BeautifulSoup   

class Jgi(object):

    ## Add required path argument and update function

    def __init__(self,path,chromedriver_path=None, 
                 homepage_url='https://img.jgi.doe.gov/cgi-bin/m/main.cgi'):

        self.path = path
        self.homepage_url = homepage_url

        if not chromedriver_path:
            self.driver = webdriver.Chrome()

        else:
            self.driver = webdriver.Chrome(chromedriver_path)

    @property
    def path(self):
        return self.__path 

    @path.setter
    def path(self,path):
        if not os.path.exists(path):
            os.makedirs(path)
        self.__path = path

    @property
    def driver(self):
        """
        webdriver.Chrome(os.path.expanduser('~')+'/chromedriver')
        """
        return self.__driver

    @driver.setter
    def driver(self,driver):
        self.__driver = driver

    @property
    def homepage_url(self):
        return self.__homepage_url

    @homepage_url.setter
    def homepage_url(self,homepage_url):
        self.__homepage_url = homepage_url

    def __get_domain_url(self,domain,database):
        if database == 'jgi':
            database_str = "&seq_center=jgi"
        elif database == 'all':
            database_str = ""
        else:
            raise ValueError("`database` must be 'jgi' or 'all'")
        
        alpha2 = ['*Microbiome','cell','sps','Metatranscriptome'] # these datasets use a different URL pattern
        if domain in alpha2:
            alpha_str = "2"
        else:
            alpha_str = ""

        domain_url = "https://img.jgi.doe.gov/cgi-bin/m/main.cgi?section=TaxonList&page=taxonListAlpha{0}&domain={1}{2}".format(alpha_str, domain, database_str)
        return domain_url
    
    def __get_domain_json(self,domain_url,database,domain):
        ## Identify correct time to allow page to load
        if (domain=="Bacteria") and (database=="all"):
            sleep_time = 60
        else:
            sleep_time = 5
        
        self.driver.get(domain_url)
        ## Takes a long time to load all bacteria (because there are 60k of them)
        time.sleep(sleep_time) 
        htmlSource = self.driver.page_source
        # driver.quit()

        regex = r'var myDataSource = new YAHOO\.util\.DataSource\(\"(.*)\"\);'
        match = re.search(regex, htmlSource)
        domain_json_suffix = match.group(1)
        domain_url_prefix = domain_url.split('main.cgi')[0]
        domain_json_url = domain_url_prefix+domain_json_suffix

        self.driver.get(domain_json_url)
        time.sleep(sleep_time)

        domain_json = json.loads(self.driver.find_element_by_tag_name('body').text)
        return domain_json

    def __get_organism_urls(self,domain_json):

        all_GenomeNameSampleNameDisp =  [d['GenomeNameSampleNameDisp'] for d in domain_json['records']]

        organism_urls = list()

        for htmlandjunk in all_GenomeNameSampleNameDisp:
            regex = r"<a href='main\.cgi(.*)'>"
            match = re.search(regex, htmlandjunk)
            html_suffix = match.group(1)
            full_url = self.homepage_url+html_suffix
            organism_urls.append(full_url)
        
        return organism_urls

    def __get_organism_htmlSource(self,organism_url):
        self.driver.get(organism_url)
        time.sleep(5)
        return self.driver.page_source

    def __get_organism_metadata(self,htmlSource):
        # return dict of metagenome table data
        bs = BeautifulSoup(htmlSource,"html.parser")
        metadata_table = bs.findAll('table')[0]

        metadata_table_dict = dict()
        for row in metadata_table.findAll('tr'):

            if (len(row.findAll('th')) == 1) and (len(row.findAll('td')) == 1):

                row_key = row.findAll('th')[0].text.rstrip()
                row_value = row.findAll('td')[0].text.rstrip() if row.findAll('td')[0] else None
                metadata_table_dict[row_key] = row_value

        metadata_table_dict.pop('Project Geographical Map', None)

        ## metadata_table_dict['Taxon Object ID'] should be the way we identify a metagenome
        return metadata_table_dict

    #### NEED TO ADD METAGENOME SPECIFIC GET COMMANDS FOR ASSEMBLED/UNASSEMBLED/BOTH
    # assembly_types

    def __get_enzyme_url_metagenome(self,organism_url,htmlSource,assembly_type):

        regex = r'<a href=\"(main\.cgi\?section=MetaDetail&amp;page=enzymes.*data_type=%s.*)\" onclick'%assembly_type
        match = re.search(regex, htmlSource)

        if match:
            # print "Metagenome url: %s ...\n...has assembly_type: %s"%(url,assembly_type)
            enzyme_url_suffix = match.group(1)
            enzyme_url_prefix = organism_url.split('main.cgi')[0]
            enzyme_url = enzyme_url_prefix+enzyme_url_suffix

        else:
            print("Metagenome url: %s ...\n...does not have assembly_type: %s"%(organism_url,assembly_type))
            enzyme_url = None

        return enzyme_url


    def __get_enzyme_url(self,organism_url,htmlSource):
        regex = r'<a href=\"(main\.cgi\?section=TaxonDetail&amp;page=enzymes&amp;taxon_oid=\d*)\"'
        match = re.search(regex, htmlSource)

        # print("Getting enzyme_url from organism url: %s"%(organism_url))
        if match:
            enzyme_url_suffix = match.group(1)
            enzyme_url_prefix = organism_url.split('main.cgi')[0]
            enzyme_url = enzyme_url_prefix+enzyme_url_suffix    

        else:
            print("Organism url: %s ...\n...does not have enzyme data."%(organism_url))
            enzyme_url = None

        return enzyme_url

    def __get_enzyme_json(self,enzyme_url):
        self.driver.get(enzyme_url)
        time.sleep(5)
        htmlSource = self.driver.page_source
        # driver.quit()

        regex = r'var myDataSource = new YAHOO\.util\.DataSource\(\"(.*)\"\);'
        match = re.search(regex, htmlSource)
        enzyme_json_suffix = match.group(1)
        enzyme_url_prefix = enzyme_url.split('main.cgi')[0]
        enzyme_json_url = enzyme_url_prefix+enzyme_json_suffix

        self.driver.get(enzyme_json_url)
        time.sleep(5)

        ## JSON formatted object ready to be dumped
        enzyme_json = json.loads(self.driver.find_element_by_tag_name('body').text)

        return enzyme_json

    def __prune_enzyme_json(self,enzyme_json):
        """
        Reduce keys in enzyme json by discarding "display" keys.
        """

        enzyme_dict = dict() # Dictionary of ec:[enzymeName,genecount] for all ecs in a single metagenome

        for singleEnzymeDict in enzyme_json['records']:
            ec = singleEnzymeDict['EnzymeID']
            enzymeName = singleEnzymeDict['EnzymeName']
            genecount = singleEnzymeDict['GeneCount']

            enzyme_dict[ec] = [enzymeName,genecount]

        return enzyme_dict

    def scrape_domain(self, domain, database='all', 
                      assembly_types = ['assembled','unassembled','both']):
        ## Do scraping functions
        """
        database: choose to use only the jgi database, or all database [default=jgi]
        domain: one of...
            ## Alpha
            'Eukaryota'
            'Bacteria' (wait 45 seconds)
            'Archaea'
            'Plasmids' UNTESTED
            'Viruses' UNTESTED
            'GFragment' (gene fragments) UNTESTED
            ## Alpha2
            '*Microbiome' (metagenome)
            'cell' (metagenome- cell enrichment) UNTESTED
            'sps' (metagenome- single particle sort) UNTESTED
            'Metatranscriptome' UNTESTED
        """
        ## Only allow scraping into empty directory
        for _dirpath, _dirnames, files in os.walk(self.path):
            if files:
                raise ValueError("Directory must be empty to initiate a fresh KEGG download.\
                              Looking to update KEGG? Try `Kegg.update()` instead.")
        

        ## Assembled or unassembled -- applies to metagenomes only
        assembly_options = ['assembled','unassembled','both']
        metagenome_domains = ['*Microbiome','cell','sps','Metatranscriptome']
        
        ## Validate input
        untested = ['Plasmids','Viruses','GFragment','cell','sps','Metatranscriptome']
        tested = ['Eukaryota','Bacteria','Archaea','*Microbiome']

        ## Validate domain
        if domain in untested:
            warnings.warn("This domain is untested for this function.")
        elif domain not in tested:
            raise ValueError("`domain` must be one of JGI datasets: {0} See: IMG Content table on ".format(tested+untested)+
                              "img/m homepage: https://img.jgi.doe.gov/cgi-bin/m/main.cgi")
        
        ## Validate assembly_types
        if domain in metagenome_domains:
            if not set(assembly_types).issubset(set(assembly_options)):
                raise ValueError("`assembly_types` must be subset of %s"%assembly_options)
        
        ## Make save_dir if not exit
        if not os.path.exists(os.path.join(self.path,domain)):
            os.makedirs(os.path.join(self.path,domain))

        ## Get all organism URLs
        domain_url = self.__get_domain_url(domain,database)
        domain_json = self.__get_domain_json(domain_url,domain,database)
        organism_urls = self.__get_organism_urls(domain_json)

        org_jsons = list()
        for organism_url in tqdm(organism_urls):

            print("Scraping: %s ..."%(organism_url))
            
            ## Get enzyme json for single organism
            htmlSource = self.__get_organism_htmlSource(organism_url)
            metadata_dict = self.__get_organism_metadata(htmlSource)
            taxon_id = metadata_dict['Taxon ID']
            org_dict = {'metadata':metadata_dict}

            ## Different methods for metagenomes/genomes
            if domain in metagenome_domains:
                for assembly_type in assembly_types:
                    enzyme_url = self.__get_enzyme_url_metagenome(organism_url,htmlSource,assembly_type)
                    if enzyme_url:
                        enzyme_json = self.__get_enzyme_json(enzyme_url)
                        enzyme_json = self.__prune_enzyme_json(enzyme_json)

                        org_dict[assembly_type] = enzyme_json
                
                org_jsons.append(org_dict)

                with open(os.path.join(self.path,domain,taxon_id+".json"), 'w') as f:
        
                    json.dump(org_dict, f)

            else:
                enzyme_url = self.__get_enzyme_url(organism_url,htmlSource)
                if enzyme_url:
                    enzyme_json = self.__get_enzyme_json(enzyme_url)
                    enzyme_json = self.__prune_enzyme_json(enzyme_json)
                    
                    org_dict["enzymes"] = enzyme_json
                    org_jsons.append(org_dict)
                
                with open(os.path.join(self.path,domain,taxon_id+".json"), 'w') as f:
        
                    json.dump(org_dict, f)

        print("Writing combined json to file...")
        with open(os.path.join(self.path,domain+".json"), 'w') as f:
            
            json.dump(org_jsons,f)

        print("Done.")

        ## Get enzyme json for single organism
        # htmlSource = self.__get_organism_htmlSource(self,organism_url)
        # metadata_dict = self.__get_organism_metadata(self,htmlSource)
        # enzyme_url = self.__get_enzyme_url(self,htmlSource)
        # enzyme_json = self.__get_enzyme_json(self,enzyme_url)

    def scrape_bunch(self,taxon_ids):
        ## Taxon IDs must be a list
        pass

# ###############################################################
# ## get URLs for pH specific scraping
# ###############################################################
# def load_json(fname):
#     """
#     Wrapper to load json in single line

#     :param fname: the filepath to the json file
#     """
#     with open(fname) as f:
#         return json.load(f)

# ## Tested and works
# def check_overlap_number(range_1,i):
#     if (i>=min(range_1)) and (i<=max(range_1)):
#         return True
#     else:
#         return False

# ## Tested and works
# def check_overlap_ranges(range_1,range_2):
#     # order the ranges so that the range with the smallest min is first
#     # check if the min of range2 is less than the max of range 1
#     ranges = [range_1,range_2]
#     if min(range_2)<min(range_1):
#         ranges = ranges[::-1]
#     if min(ranges[1])<=max(ranges[0]):
#         return True
#     else:
#         return False

# def get_entries_within_ph_range(records, desired_ph_range):
#     entries_with_phs_in_range = list()
#     for entry in records:
#         in_desired_ph_range = False
#         ph_range_str = entry['pH'].split('-')

#         if len(ph_range_str) == 1:
#             try:
#                 ph = float(ph_range_str[0])
#                 in_desired_ph_range = check_overlap_number(desired_ph_range,ph)

#             except:
#                 pass
#         elif len(ph_range_str) == 2:
#             try:
#                 ph_min = float(ph_range_str[0])
#                 ph_max = float(ph_range_str[1])
#                 ph = (ph_min,ph_max)
#                 in_desired_ph_range = check_overlap_ranges(desired_ph_range,ph)
#             except:
#                 pass
        
#         if in_desired_ph_range == True:
#             entries_with_phs_in_range.append(entry)
    
#     return entries_with_phs_in_range

# def format_urls_for_scraping(homepage_url,entries_with_phs_in_range):
#     all_GenomeNameSampleNameDisp =  [d['GenomeNameSampleNameDisp'] for d in entries_with_phs_in_range]

#     organism_urls = list()

#     for htmlandjunk in all_GenomeNameSampleNameDisp:
#         regex = r"<a href='main\.cgi(.*)'>"
#         match = re.search(regex, htmlandjunk)
#         html_suffix = match.group(1)
#         full_url = homepage_url+html_suffix
#         organism_urls.append(full_url)

#     return organism_urls

# def main():

#     driver = activate_driver()
#     homepage_url = 'https://img.jgi.doe.gov/cgi-bin/m/main.cgi'
#     domain = 'bacteria'
#     database = 'all'
#     save_dir = 'jgi/2018-09-29/ph_jsons/%s/'%domain

#     if not os.path.exists(save_dir):
#         os.makedirs(save_dir)

#     jgi_eukarya = list()

#     print "Scraping all %s genomes ..."%domain

#     ## Get all urls from the domain
#     # domain_url = get_domains_url_from_jgi_img_homepage(driver,homepage_url,domain,database=database)
#     # domain_json = get_domain_json_from_domain_url(driver,domain_url)
#     # organism_urls = get_organism_urls_from_domain_json(driver,homepage_url,domain_json)

#     ## Get pH specific urls from the domain
#     if domain=='archaea':
#         metadata = load_json("jgi/metadata/archaea_metadata.json")
#     elif domain=='bacteria':
#         metadata = load_json("jgi/metadata/bacteria_metadata_subset.json")
#     elif domain=='eukarya':
#         raise Warning("Eukarya do not have any organisms in range currently")
#         metadata = load_json("jgi/metadata/eukarya_metadata.json")

#     records = metadata['records']
#     ph_range = (9.0,11.0)
#     entries_with_phs_in_range = get_entries_within_ph_range(records,ph_range)

#     entries_to_scrape = []
#     for entry in entries_with_phs_in_range:
#         fname = entry['IMGGenomeID']+".json"
#         future_path = save_dir+fname
#         if future_path not in glob.glob(save_dir+"*.json"):
#             entries_to_scrape.append(entry)

#     organism_urls = format_urls_for_scraping(homepage_url,entries_to_scrape)

#     ## 
#     for organism_url in organism_urls:

#         print "Scraping %s: %s ..."%(domain,organism_url)
#         organism_htmlSource,metadata_table_dict = get_organism_htmlSource_and_metadata(driver, organism_url)

#         # single_organism_dict = {'metadata':metadata_table_dict}
#         taxon_id = metadata_table_dict['Taxon ID']
#         enzyme_url = get_enzyme_url_from_organism_url(organism_url, organism_htmlSource)
#         enzyme_json = get_enzyme_json_from_enzyme_url(driver,enzyme_url)

#         # enzyme_dict = parse_enzyme_info_from_enzyme_json(enzyme_json)
#         # single_organism_dict['genome'] = enzyme_dict

#         jgi_eukarya.append(enzyme_json)

#         with open(save_dir+taxon_id+'.json', 'w') as outfile:
    
#             json.dump(enzyme_json,outfile)

#         print "Done scraping %s."%domain
#         print "-"*80

#     print "Done scraping %s."%domain
#     print "="*90



#     print "Writing json to file..."

#     combined_json_fname = 'jgi/2018-09-29/ph_jsons/jgi_ph_%s.json'%domain
#     with open(combined_json_fname, 'w') as outfile:
        
#         json.dump(jgi_eukarya,outfile)

#     print "Done."

#     ## Can i write it so that it scrapes many at a time?

# if __name__ == '__main__':
#     main()




