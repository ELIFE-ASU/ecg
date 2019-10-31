"""
WARNING. CLI HAS NOT BEEN TESTED YET.

Retrieve enzyme data from JGI genomes and metagenomes.

Usage:
  jgi.py [--chromedriver_path=<cd_path>|--homepage_url=<hp_url>] scrape_domain PATH DOMAIN [--database=<db>|--assembly_types=<at>...]
  jgi.py [--chromedriver_path=<cd_path>|--homepage_url=<hp_url>] scrape_urls PATH DOMAIN ORGANISM_URLS [--assembly_types=<at>...]

Arguments:
  PATH  Directory where JGI data will be downloaded to
  DOMAIN    JGI valid domain to scrape data from (one of: 'Eukaryota','Bacteria','Archaea','*Microbiome','Plasmids','Viruses','GFragment','cell','sps','Metatranscriptome')
  ORGANISM_URLS     (meta)genome URLs to download data from
  scrape_domain     Download an entire JGI domain and run pipeline to format data
  scrape_urls   Download data from one or more (meta)genomes by URL

Options:
  --chromedriver_path=<cd_path>   Path pointing to the chromedriver executable (leaving blank defaults to current dir) [default: None]
  --homepage_url=<hp_url>     URL of JGI's homepage [default: "https://img.jgi.doe.gov/cgi-bin/m/main.cgi"] 
  --database=<db>   To use only JGI annotated organisms or all organisms [default: "all"]
  --assembly_types=<at>...  Only used for metagenomic domains. Ignored for others [default: unassembled assembled both]
"""

import time
import os
import re
import json
import warnings
import sys, io
from selenium import webdriver
from ast import literal_eval
from tqdm import tqdm
from docopt import docopt
from bs4 import BeautifulSoup

# Loads the correct pickle program and options.
if sys.version_info[0] > 2:
    # python 3 automatically defaults to cPickle
    import pickle as cPickle
else:
    import cPickle

def save(obj,filename):
    fout = io.open(filename,'wb')
    cPickle.dump(obj,fout,2)
    fout.close()

def load(filename):
    fin = io.open(filename,'rb')
    obj = cPickle.load(fin)
    fin.close()
    return obj

class Jgi(object):

    def __init__(self,chromedriver_path="", 
                 homepage_url='https://img.jgi.doe.gov/cgi-bin/m/main.cgi'):

        self.homepage_url = homepage_url

        if chromedriver_path=="":
            self.driver = webdriver.Chrome()
        
        elif chromedriver_path.startswith("~"):
            self.driver = webdriver.Chrome(os.path.expanduser('~')+chromedriver_path[1:])

        else:
            self.driver = webdriver.Chrome(chromedriver_path)

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
            
            #full_url = self.homepage_url+html_suffix
            full_url = "https://img.jgi.doe.gov/cgi-bin/m/main.cgi{}".format(html_suffix)
            organism_urls.append(full_url)
        
        return organism_urls
    
    # Added pruning function to remove organisms already downloaded.
    def __prune_organism_urls(self, organism_urls, domain_path):
        organism_id_list = []
        for htmlandjunk in organism_urls:
            m = re.search(r'\d+$', htmlandjunk)
            organism_id = m.group(0)
            organism_id_list.append(organism_id)

        remove_list = []
        for _dirpath, _dirnames, files in os.walk(domain_path):
            if files:
                for f in files:
                    f = f.split('.json')[0]
                    if f in organism_id_list:
                        remove_list.append(organism_id_list.pop(organism_id_list.index(f)))
                
        new_organism_url_list = [htmlandjunk for htmlandjunk in organism_urls if (re.search(r'\d+$', htmlandjunk).group(0) not in remove_list)]

        return new_organism_url_list

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

    def __get_organism_statistics(self,htmlSource):
        # return dict of metagenome table data
        bs = BeautifulSoup(htmlSource,"html.parser")

        statistics_table = bs.findAll('table')[-1]
  
        statistics_table_dict = dict()

        for row in statistics_table.findAll('tr'):
            if (len(row.findAll('th')) == 1):
                row_key = row.findAll('th')[0].text.rstrip()
                row_value = []
                row_value.append(row.findAll('td')[0].text.rstrip() if row.findAll('td')[0] else None)
                row_value.append(row.findAll('td')[1].text.rstrip() if row.findAll('td')[1] else None)
                statistics_table_dict[row_key] = row_value

            elif (len(row.findAll('th')) == 0):
                row_value = []
                row_key = row.findAll('td')[0].text.rstrip().strip()
                row_key = row_key.replace('\xa0','')
                #regexp = re.compile(r'\s+',re.UNICODE)
                #row_key = [regexp.sub('',p) for p in row_key]

                row_value.append(row.findAll('td')[1].text.rstrip() if row.findAll('td')[1] else None)
                row_value.append(row.findAll('td')[2].text.rstrip() if row.findAll('td')[2] else None)
                statistics_table_dict[row_key] = row_value
                
        return statistics_table_dict

    def __get_organism_statistics_metagenome(self,htmlSource):
        # return dict of metagenome table data
        bs = BeautifulSoup(htmlSource,"html.parser")

        statistics_table = bs.findAll('table')[-2]
  
        statistics_table_dict = dict()
        assembled_dict = dict()
        unassembled_dict = dict()
        total_dict = dict()

        for row in statistics_table.findAll('tr'):
            if (len(row.findAll('th')) == 1):
                row_key = row.findAll('th')[0].text.rstrip()

                row_value = []
                row_value.append(row.findAll('td')[0].text.rstrip() if row.findAll('td')[0] else None)
                row_value.append(row.findAll('td')[1].text.rstrip() if row.findAll('td')[1] else None)
                assembled_dict[row_key] = row_value

                try:
                    row_value = []
                    row_value.append(row.findAll('td')[2].text.rstrip() if row.findAll('td')[2] else None)
                    row_value.append(row.findAll('td')[3].text.rstrip() if row.findAll('td')[3] else None)
                    unassembled_dict[row_key] = row_value

                    row_value = []
                    row_value.append(row.findAll('td')[4].text.rstrip() if row.findAll('td')[4] else None)
                    row_value.append(row.findAll('td')[5].text.rstrip() if row.findAll('td')[5] else None)
                    total_dict[row_key] = row_value
                except:
                    pass

                

            elif (len(row.findAll('th')) == 0):
                if len(row.findAll('td')) > 0:
                    row_key = row.findAll('td')[0].text.rstrip().strip()
                    row_key = row_key.replace('\xa0','')
                    #regexp = re.compile(r'\s+',re.UNICODE)
                    #row_key = [regexp.sub('',p) for p in row_key]

                    row_value = []
                    row_value.append(row.findAll('td')[1].text.rstrip() if row.findAll('td')[1] else None)
                    row_value.append(row.findAll('td')[2].text.rstrip() if row.findAll('td')[2] else None)
                    assembled_dict[row_key] = row_value

                    try:
                        row_value = []
                        row_value.append(row.findAll('td')[3].text.rstrip() if row.findAll('td')[3] else None)
                        row_value.append(row.findAll('td')[4].text.rstrip() if row.findAll('td')[4] else None)
                        unassembled_dict[row_key] = row_value

                        row_value = []
                        row_value.append(row.findAll('td')[5].text.rstrip() if row.findAll('td')[5] else None)
                        row_value.append(row.findAll('td')[6].text.rstrip() if row.findAll('td')[6] else None)
                        total_dict[row_key] = row_value
                    except:
                        pass
        
        statistics_table_dict['assembled'] = assembled_dict

        if unassembled_dict != dict():
            statistics_table_dict['unassembled'] = unassembled_dict
            statistics_table_dict['total'] = total_dict

        return statistics_table_dict

    def __get_enzyme_url_metagenome(self,organism_url,htmlSource,assembly_type):

        regex = r'<a href=\"(main\.cgi\?section=MetaDetail&amp;page=enzymes.*data_type=%s.*)\" onclick'%assembly_type
        match = re.search(regex, htmlSource)

        if match:
            # print "Metagenome url: %s ...\n...has assembly_type: %s"%(url,assembly_type)
            enzyme_url_suffix = match.group(1)
            enzyme_url_prefix = organism_url.split('main.cgi')[0]
            enzyme_url = enzyme_url_prefix+enzyme_url_suffix

        else:
            # print("Metagenome url: %s ...\n...does not have assembly_type: %s"%(organism_url,assembly_type))
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
            # print("Organism url: %s ...\n...does not have enzyme data."%(organism_url))
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

    # def __identify_domain(self,htmlSource):

    #     regex = r'main.cgi?section=FindGenesBlast&page=geneSearchBlast&taxon_oid=%s&domain=(.*)\"\);'%taxon_id
    #     match = re.search(regex, htmlSource)
    #     domain_json_suffix = match.group(1)

    def __validate_assembly_types(self,assembly_types):
        ## Assembled or unassembled -- applies to metagenomes only
        assembly_options = ['assembled','unassembled','both']
        if not set(assembly_types).issubset(set(assembly_options)):
            raise ValueError("`assembly_types` must be subset of %s"%assembly_options)

    def __validate_domain(self,domain):

        untested = ['Plasmids','Viruses','GFragment','cell','sps','Metatranscriptome']
        tested = ['Eukaryota','Bacteria','Archaea','*Microbiome']

        ## Validate domain
        if domain in untested:
            warnings.warn("This domain is untested for this function.")
        elif domain not in tested:
            raise ValueError("`domain` must be one of JGI datasets: {0} See: IMG Content table on ".format(tested+untested)+
                              "img/m homepage: https://img.jgi.doe.gov/cgi-bin/m/main.cgi")

      
    def __write_taxon_id_json(self,path,domain,taxon_id,org_dict):

        taxon_ids_path = os.path.join(path,domain,"taxon_ids",taxon_id+".json")
        with open(taxon_ids_path, 'w') as f:
            json.dump(org_dict, f)

    def __scrape_organism_url_from_metagenome_domain(self,organism_url,assembly_types,missing_enzyme_data):
        ## Get enzyme json for single organism
        htmlSource = self.__get_organism_htmlSource(organism_url)
        metadata_dict = self.__get_organism_metadata(htmlSource)
        statistics_dict = self.__get_organism_statistics_metagenome(htmlSource)
        taxon_id = metadata_dict['Taxon Object ID']
        org_dict = {'metadata':metadata_dict, 'statistics':statistics_dict}

        ## Different methods for metagenomes/genomes
        for assembly_type in assembly_types:
            enzyme_url = self.__get_enzyme_url_metagenome(organism_url,htmlSource,assembly_type)
            if enzyme_url:
                enzyme_json = self.__get_enzyme_json(enzyme_url)
                enzyme_json = self.__prune_enzyme_json(enzyme_json)

                org_dict[assembly_type] = enzyme_json
            ## Write missing data to dict
            else:
                if not taxon_id in missing_enzyme_data:
                    missing_enzyme_data[taxon_id] = [assembly_type]
                else:
                    missing_enzyme_data[taxon_id].append(assembly_type)
        
        return taxon_id, org_dict, missing_enzyme_data

    def __scrape_organism_url_from_regular_domain(self,organism_url,missing_enzyme_data):

        htmlSource = self.__get_organism_htmlSource(organism_url)
        metadata_dict = self.__get_organism_metadata(htmlSource)
        statistics_dict = self.__get_organism_statistics(htmlSource)
        taxon_id = metadata_dict['Taxon ID']
        org_dict = {'metadata':metadata_dict, 'statistics':statistics_dict}

        enzyme_url = self.__get_enzyme_url(organism_url,htmlSource)
        if enzyme_url:
            enzyme_json = self.__get_enzyme_json(enzyme_url)
            enzyme_json = self.__prune_enzyme_json(enzyme_json)
            
            org_dict["enzymes"] = enzyme_json

        ## Write missing data to list
        else:
            missing_enzyme_data.append(taxon_id)

        return taxon_id, org_dict, missing_enzyme_data


    def scrape_domain(self, path, domain, database='all', 
                      assembly_types = ['assembled','unassembled','both']):
        ## Do scraping functions
        """
        path: path to store domain directories in and to write combined jsons to        
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
        database: choose to use only the `jgi` database, or `all` database [default=all]
        assembly_types: Only used for metagenomic domains. Ignored for others.
                        [default=[`unassembled`, `assembled`, `both`]]. 
        """
        ## Make save_dir
        domain_path = os.path.join(path,domain,"taxon_ids")
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)

        ## Only allow scraping into empty directory
        #for _dirpath, _dirnames, files in os.walk(domain_path):
        #    if files:
        #        raise ValueError("Directory must be empty to initiate a fresh JGI download."+
        #                     "Looking to update a JGI domain? Try `Jgi.update()` instead.")        

        ## Validate assembly_types
        metagenome_domains = ['*Microbiome','cell','sps','Metatranscriptome']
        if domain in metagenome_domains:
            self.__validate_assembly_types(assembly_types)

        ## Validate domain
        self.__validate_domain(domain)


        ## Get all organism URLs
        domain_url = self.__get_domain_url(domain,database)
        domain_json = self.__get_domain_json(domain_url,domain,database)
        organism_urls = self.__get_organism_urls(domain_json)
        
        organism_urls = self.__prune_organism_urls(organism_urls, domain_path)
        print("*** Warning! ***")
        print("If directory is not empty, will attempt to finish missing files in domain.")
        print("Looking to update a JGI domain? Try 'Jgi.update()' instead. ***Function upcoming.")

        self._scrape_urls_unsafe(path,domain,organism_urls, assembly_types=assembly_types)
        
    def scrape_urls(self, path, domain, organism_urls,
                    assembly_types = ['assembled','unassembled','both']):

        ## Make save_dir
        domain_path = os.path.join(path,domain,"taxon_ids")
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)

        ## Only allow scraping into empty directory
        for _dirpath, _dirnames, files in os.walk(domain_path):
            if files:
                raise ValueError("Directory must be empty to initiate a fresh JGI download."+
                             "Looking to update a JGI domain? Try `Jgi.update()` instead.")        

        ## Validate assembly_types
        metagenome_domains = ['*Microbiome','cell','sps','Metatranscriptome']
        if domain in metagenome_domains:
            self.__validate_assembly_types(assembly_types)

        ## Validate domain
        self.__validate_domain(domain)

        organism_urls = self.__prune_organism_urls(organism_urls, domain_path)
        self._scrape_urls_unsafe(path,domain,organism_urls,assembly_types=assembly_types)

    def _scrape_urls_unsafe(self, path, domain, organism_urls,
                    assembly_types = ['assembled','unassembled','both']):
        """
        Only meant to be called internally as it does not validate input.
        """
        
        metagenome_domains = ['*Microbiome','cell','sps','Metatranscriptome']
        
        pbar = tqdm(organism_urls)

        domain_path = os.path.join(path,domain)

        temp_missing_path = os.path.join(domain_path,"missing_enzyme_data.dat")
        temp_org_jsons_path = os.path.join(domain_path,"org_jsons.dat")

        if os.path.exists(temp_org_jsons_path):
            org_jsons = load(temp_org_jsons_path)
        else:
            org_jsons = list()

        if domain in metagenome_domains:
            if os.path.exists(temp_missing_path):
                missing_enzyme_data = load(temp_missing_path)
            else:
                missing_enzyme_data = dict()
         

            for organism_url in pbar:
                pbar.set_description("Scraping %s ..."%(re.search(r'\d+$', organism_url).group(0)))
                taxon_id, org_dict, missing_enzyme_data = self.__scrape_organism_url_from_metagenome_domain(organism_url,assembly_types,missing_enzyme_data)

                org_jsons.append(org_dict)
                self.__write_taxon_id_json(path,domain,taxon_id,org_dict)

                save(missing_enzyme_data,temp_missing_path)
                save(org_jsons,temp_org_jsons_path)

        else:
            if os.path.exists(temp_missing_path):
                missing_enzyme_data = load(temp_missing_path)
            else:
                missing_enzyme_data = list()

            for organism_url in pbar:
                pbar.set_description("Scraping %s ..."%(re.search(r'\d+$', organism_url).group(0)))
                taxon_id, org_dict, missing_enzyme_data = self.__scrape_organism_url_from_regular_domain(organism_url,missing_enzyme_data)

                org_jsons.append(org_dict)
                self.__write_taxon_id_json(path,domain,taxon_id,org_dict)

                save(missing_enzyme_data,temp_missing_path)
                save(org_jsons,temp_org_jsons_path)

        
        #domain_path = os.path.join(path,domain)
        print("Writing missing enzyme data to file...")
        with open(os.path.join(domain_path,"missing_enzymes.json"), 'w') as f:
            json.dump(missing_enzyme_data,f)

        print("Writing combined json to file...")
        with open(os.path.join(domain_path,"combined_taxon_ids.json"), 'w') as f:  
            json.dump(org_jsons,f)

        print("Done.")

    def scrape_ids(self,ids):
        ## Taxon IDs must be a list

        ## Format IDs into organism urls

        ## Call scrape_urls
        pass
# def __check_cli_input_types(arguments):
#     """
#     Check docopt input types.
    
#     Each docopt flag can only take one arg
#     to download more than one database, you need one flag per db
#     ex. `python kegg.py mydir download --db reaction --db compound`
#     """

#     dbs = arguments['--db']
#     if not isinstance(dbs,list):
#         raise TypeError("`db` must be a list")
#     for db in dbs:
#         if not isinstance(db,str):
#             raise TypeError("Each entry in `db` must be a string")
    
#     run_pipeline = literal_eval((arguments['--run_pipeline']))
#     if not isinstance(run_pipeline,bool):
#         raise TypeError("`run_pipeline` must be a boolean (True or False)")
    
#     metadata = literal_eval((arguments['--metadata']))
#     if not isinstance(metadata,bool):
#         raise TypeError("`metadata` must be a boolean (True or False)")

def __execute_cli(arguments):
    """
    Call appropriate methods based on command line interface input.
    """
    # chromedriver_path = literal_eval((arguments['--chromedriver_path']))
    chromedriver_path = arguments['--chromedriver_path']

    if arguments['scrape_domain'] == True:
        J = Jgi(chromedriver_path,arguments['--homepage_url'])
        J.scrape_domain(arguments['PATH'], arguments['DOMAIN'], database=arguments['--database'], assembly_types=arguments['--assembly_types'])

    if arguments['scrape_urls'] == True:
        J = Jgi(arguments['--chromedriver_path'],arguments['--homepage_url'])
        J.scrape_urls(arguments['PATH'], arguments['DOMAIN'], arguments['ORGANISM_URLS'], assembly_types=arguments['--assembly_types'])

if __name__ == '__main__':
    arguments = docopt(__doc__, version='jgi 1.0')
    # __check_cli_input_types(arguments)
    __execute_cli(arguments)


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




