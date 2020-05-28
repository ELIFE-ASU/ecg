import time
import os
import re
import json
import warnings
import sys, io
import argparse
from selenium import webdriver
from tqdm import tqdm
from bs4 import BeautifulSoup

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
        if (domain=='Bacteria'):
        #if (domain=="Bacteria") and (database=="all"):
            sleep_time = 75
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

    def __get_organism_urls(self,domain_json,organism_url_path):

        all_GenomeNameSampleNameDisp =  [d['GenomeNameSampleNameDisp'] for d in domain_json['records']]
        organism_urls = list()

        for htmlandjunk in all_GenomeNameSampleNameDisp:
            regex = r"<a href='main\.cgi(.*)'>"
            match = re.search(regex, htmlandjunk)
            html_suffix = match.group(1)
            
            full_url = self.homepage_url+"{}".format(html_suffix)
            organism_urls.append(full_url)
        
        ## Creates a dictionary of organism urls from parsed html list and sets values to 1.
        # If url is to be downloaded, then value is 1.
        # If url is already downloaded, then value is 0.
        organism_dict = dict.fromkeys(organism_urls,1) 

        self.__write_organism_urls_json(organism_url_path,organism_dict)

        return organism_dict

    # Added pruning function to remove organisms already downloaded.
    def __prune_organism_urls(self, organism_urls, domain_path):

        stub = re.sub(r'\d+$', "", next(iter(organism_urls)))
        
        # Checks all .json files already downloaded and removes from organism_urls
        for _dirpath, _dirnames, files in os.walk(domain_path):
            if files:
                for f in files:
                    f = f.split('.json')[0]
                    organism_url = stub + f
                    if organism_url in organism_urls:
                        del organism_urls[organism_url]

        # Checks all organism_urls keys for values not 1 and removes them from organism_urls
        for key, val in organism_urls.items():
            if val != 1:
                del organism_urls[key]
                
        return organism_urls

    def __get_organism_htmlSource(self,organism_url):
        self.driver.get(organism_url)
        time.sleep(5)
        return self.driver.page_source

    def __get_organism_data(self,htmlSource):
        # Create Beautiful Soup object for parsing
        bs = BeautifulSoup(htmlSource,"html.parser")

        # Parses webpage for the division that contains the tables.
        test_table = bs.find('div',attrs={'id':'container'})
        
        # Initialize dictionaries for metadata and genetic statistics.
        metadata = {}
        stats = {}

        # Splits up the webpage into separate tables.
        for row in test_table.findAll('div',attrs = {'id':'content_other'}):
            for table in row.findAll('table'):
                
                # Creates entry for first line in table to check if Overview (metadata) table.
                entry_name = table.findAll('tr',attrs={'class':'img'})
                try:
                    test_title = entry_name[0].findAll('th',attrs={'class':'subhead'})
                    
                    
                    # Checks to see if table is the Overview table for metadata.
                    if len(test_title) == 1:
                        if test_title[0].text.rstrip() == 'Study Name (Proposal Name)':
                            for entry in entry_name:
                                # Parses first line in entry to get category (key) and removes spaces, tabs, etc. from entry.
                                title = entry.findAll('th',attrs={'class':'subhead'})

                                try:
                                    row_key = title[0].text.rstrip().strip()
                                    row_key = row_key.replace('\xa0','')

                                    values = entry.findAll('td',attrs={'class':'img'})
                                    for value in values:
                                        value = value.text.rstrip().strip()
                                        value = value.replace('\xa0','')

                                        if metadata.get(row_key):
                                            if isinstance(metadata[row_key],list):
                                                metadata.setdefault(row_key,[]).append(value)
                                            else:
                                                initial_value = metadata.get(row_key)
                                                metadata[row_key] = [initial_value,value]
                                        else:
                                            metadata[row_key] = value
                                except IndexError:
                                    pass
                        
                    else:
                        entry_name = table.findAll('tr')
                        try:
                            test_title = table.findAll('th',attrs={'class':'subhead'})[0].text.rstrip()
                            if test_title == 'DNA, total number of bases':
                                for entry in entry_name:
                                    if entry.findAll('th',attrs={'class':'subhead'}):
                                        row_key = entry.findAll('th',attrs={'class':'subhead'})[0].text.rstrip().strip()
                                        values = entry.findAll('td',attrs={'class':'img'})
                                        for i in range(len(values)):
                                            values[i] = values[i].text.rstrip().strip()
                                            values[i] = values[i].replace('\xa0','')

                                        stats[row_key] = values

                                    else:
                                        
                                        row = entry.findAll('td',attrs={'class':'img'})
                                        
                                        for i in range(len(row)):
                                            if i == 0:
                                                row_key = row[i].text.rstrip().strip()
                                                row_key = row_key.replace('\xa0','')
                                            else:
                                                row[i] = row[i].text.rstrip().strip()
                                                row[i] = row[i].replace('\xa0','')

                                        stats[row_key] = row[1:]
                        except IndexError:
                            pass
                except IndexError:
                    pass


        stats = {k:v for k, v in stats.items() if k != ''}
        stats = {k:v for k, v in stats.items() if v}

        return metadata, stats

    def __get_metagenome_data(self,htmlSource):
        # Create Beautiful Soup object for parsing
        bs = BeautifulSoup(htmlSource,"html.parser")

        # Parses webpage for the division that contains the tables.
        test_table = bs.find('div',attrs={'id':'container'})
        
        # Initialize dictionaries for metadata and genetic statistics.
        metadata = {}
        stats = {}
        assembled = dict()
        unassembled = dict()
        total = dict()

        # Splits up the webpage into separate tables.
        for row in test_table.findAll('div',attrs = {'id':'content_other'}):
            for table in row.findAll('table'):
                # Creates entry for first line in table to check if Overview (metadata) table.
                entry_name = table.findAll('tr',attrs={'class':'img'})
            
                try:
                    test_title = entry_name[0].findAll('th',attrs={'class':'subhead'})
                    # Checks to see if table is the Overview table for metadata.
                    if len(test_title) == 1:
                        if test_title[0].text.rstrip() == 'Study Name (Proposal Name)':
                            for entry in entry_name:
                                # Parses first line in entry to get category (key) and removes spaces, tabs, etc. from entry.
                                title = entry.findAll('th',attrs={'class':'subhead'})

                                try:
                                    row_key = title[0].text.rstrip().strip()
                                    row_key = row_key.replace('\xa0','')

                                    values = entry.findAll('td',attrs={'class':'img'})
                                    for value in values:
                                        value = value.text.rstrip().strip()
                                        value = value.replace('\xa0','')

                                        if metadata.get(row_key):
                                            if isinstance(metadata[row_key],list):
                                                metadata.setdefault(row_key,[]).append(value)
                                            else:
                                                initial_value = metadata.get(row_key)
                                                metadata[row_key] = [initial_value,value]
                                        else:
                                            metadata[row_key] = value
                                except IndexError:
                                    pass
                except IndexError:
                    pass
                
                # Checks to see if statistics table is present.
                entry_name = table.findAll('tr')
                test_title = entry_name[0].findAll('th',attrs={'class':'img'})
                if len(test_title) != 0:
                    for entry in entry_name:

                        # Finds all subhead categories and their entries.
                        # Appends keys, values to dictionary based on assembly type
                        title = entry.findAll('th',attrs={'class':'subhead'})
                        if title:
                            try:
                                row_key = title[0].text.rstrip().strip()
                                row_key = row_key.replace('\xa0','')
                                
                                values = entry.findAll('td',attrs={'class':'img'})
                                for i in range(len(values)):
                                    value = values[i].text.rstrip().strip()
                                    
                                    if i < 2:
                                        assembled.setdefault(row_key,[]).append(value)
                                    elif i < 4:
                                        unassembled.setdefault(row_key,[]).append(value)
                                    else:
                                        total.setdefault(row_key,[]).append(value)

                            except:
                                pass

                        # Finds all subcategories of the above categories and their entries.
                        # Appends keys, values to dictionary based on assembly type
                        else:
                            title = entry.findAll('td',attrs={'class':'img'})
                            try:
                                for i in range(len(title)):
                                    value = title[i].text.rstrip().strip()

                                    if i == 0:
                                        row_key = value.replace('\xa0','')
                                    elif i < 3:
                                        assembled.setdefault(row_key,[]).append(value)
                                    elif i < 5:
                                        unassembled.setdefault(row_key,[]).append(value)
                                    else:
                                        total.setdefault(row_key,[]).append(value)

                            except:
                                pass
        
        stats['assembled'] = assembled
               
        # If unassembled table exists, add it and the total table to statistics table dictionary.
        if unassembled != dict():
            stats['unassembled'] = unassembled
            stats['total'] = total

        return metadata,stats

    def __get_enzyme_url_metagenome(self,organism_url,htmlSource,assembly_type):
        
        # Create Beautiful Soup object for parsing
        bs = BeautifulSoup(htmlSource,"html.parser")

        # Set prefix and initialize suffix for enzyme url
        prefix = 'https://img.jgi.doe.gov/cgi-bin/m/'
        suffix = ''

        # Get list of all <td class='img'></td>
        td_list = bs.findAll('td',attrs={'class':'img'})

        # Parse above list to find 'with Enzyme' section
        for i in range(len(td_list)):
            if td_list[i].text.rstrip().strip() == 'with Enzyme':
                # Checks assembly type and then looks to see if there is a webpage associated with it. 
                if assembly_type == 'assembled':
                    try:
                        suffix = td_list[i+1].find('a').get('href')
                    except AttributeError:
                        pass
                elif assembly_type == 'unassembled':
                    try:
                        suffix = td_list[i+3].find('a').get('href')
                    except AttributeError:
                        pass
                elif assembly_type == 'both':
                    try:
                        suffix = td_list[i+5].find('a').get('href')
                    except AttributeError:
                        pass

        # If an enzyme url was found, return it. Otherwise, set it to None
        if suffix:
            enzyme_url = prefix+suffix
        else:
            enzyme_url = None
       
        return enzyme_url

    def __get_enzyme_url(self,organism_url,htmlSource):
        # Create Beautiful Soup object for parsing
        bs = BeautifulSoup(htmlSource,"html.parser")

        # Set prefix and initialize suffix for enzyme url
        prefix = 'https://img.jgi.doe.gov/cgi-bin/m/'
        suffix = ''

        # Get list of all <td class='img'></td>
        td_list = bs.findAll('td',attrs={'class':'img'})

        # Parse above list to find 'Protein coding genes with enzymes' section and webpage associated with it, if it exists.
        for i in range(len(td_list)):
            if td_list[i].text.rstrip().strip() == 'Protein coding genes with enzymes':
                try:
                    suffix = td_list[i+1].find('a').get('href')
                except AttributeError:
                    pass

        # If an enzyme url was found, return it. Otherwise, set it to None
        if suffix:
            enzyme_url = prefix+suffix
        else:
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

    def __write_organism_urls_json(self,organism_url_path,organism_urls):

        with open(organism_url_path, 'w') as f:
            json.dump(organism_urls, f)
    
    def __write_missing_enzyme_json(self,missing_enzyme_path,missing_enzyme_data):
    
        with open(missing_enzyme_path,'w') as f:
            json.dump(missing_enzyme_data, f)

    def __read_missing_enzyme_json(self,missing_enzyme_path):

        with open(missing_enzyme_path,'r') as f:
            missing_enzyme_data = json.load(f)

        return missing_enzyme_data

    def __scrape_organism_url_from_metagenome_domain(self,path,organism_url,assembly_types):
        ## Get enzyme json for single organism
        htmlSource = self.__get_organism_htmlSource(organism_url)
        metadata_dict, statistics_dict = self.__get_metagenome_data(htmlSource)
        
        missing_enzyme_path = os.path.join(path,"missing_enzyme_data.json")
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
                if os.path.isfile(missing_enzyme_path):
                    missing_enzyme_data = self.__read_missing_enzyme_json(missing_enzyme_path)
                    if taxon_id not in missing_enzyme_data:
                        missing_enzyme_data[taxon_id] = assembly_type

                else:
                    missing_enzyme_data = {}
                    missing_enzyme_data[taxon_id] = assembly_type
        
        return taxon_id, org_dict

    def __scrape_organism_url_from_regular_domain(self,path,organism_url):

        htmlSource = self.__get_organism_htmlSource(organism_url)
        metadata_dict, statistics_dict = self.__get_organism_data(htmlSource)

        missing_enzyme_path = os.path.join(path,"missing_enzyme_data.json")

        taxon_id = metadata_dict['Taxon ID']
        org_dict = {'metadata':metadata_dict, 'statistics':statistics_dict}

        enzyme_url = self.__get_enzyme_url(organism_url,htmlSource)
        if enzyme_url:
            enzyme_json = self.__get_enzyme_json(enzyme_url)
            enzyme_json = self.__prune_enzyme_json(enzyme_json)
            
            org_dict["enzymes"] = enzyme_json

        ## Write missing data to list
        else:
            if os.path.isfile(missing_enzyme_path):
                missing_enzyme_data = self.__read_missing_enzyme_json(missing_enzyme_path)
                if taxon_id not in missing_enzyme_data:
                    missing_enzyme_data.append(taxon_id)

            else:
                missing_enzyme_data = []
                missing_enzyme_data.append(taxon_id)

            self.__write_missing_enzyme_json(missing_enzyme_path,missing_enzyme_data)

        return taxon_id, org_dict


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
        
        # Checks to see if there is an organism url list already and imports it.
        organism_url_path = os.path.join(path,domain,'organism_url.json')
 
        if os.path.isfile(organism_url_path):
            with open(organism_url_path,'r') as f:
                organism_urls = json.load(f)

        # If no organism url list present, then creates one.
        else:
            domain_url = self.__get_domain_url(domain,database)
            domain_json = self.__get_domain_json(domain_url,domain,database)
            organism_urls = self.__get_organism_urls(domain_json,organism_url_path)

        # Prunes list of organism_urls.
        organism_urls = self.__prune_organism_urls(organism_urls, domain_path)

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

        # Prunes list of organism_urls
        organism_urls = self.__prune_organism_urls(dict.fromkeys(organism_urls,1), domain_path)
        self._scrape_urls_unsafe(path,domain,organism_urls,assembly_types=assembly_types)

    def _scrape_urls_unsafe(self, path, domain, organism_urls,
                    assembly_types = ['assembled','unassembled','both']):
        """
        Only meant to be called internally as it does not validate input.
        """
        
        metagenome_domains = ['*Microbiome','cell','sps','Metatranscriptome']
        
        pbar = tqdm(organism_urls)

        domain_path = os.path.join(path,domain)
        organism_url_path = os.path.join(path,domain,'organism_url.json')
        
        if domain in metagenome_domains:

            for organism_url in pbar:
                pbar.set_description("Scraping %s ..."%(re.search(r'\d+$', organism_url).group(0)))
                taxon_id, org_dict = self.__scrape_organism_url_from_metagenome_domain(domain_path,organism_url,assembly_types)

                organism_urls[organism_url] = 0
                self.__write_organism_urls_json(organism_url_path,organism_urls)

                self.__write_taxon_id_json(path,domain,taxon_id,org_dict)

        else:

            for organism_url in pbar:
                pbar.set_description("Scraping %s ..."%(re.search(r'\d+$', organism_url).group(0)))
                taxon_id, org_dict = self.__scrape_organism_url_from_regular_domain(domain_path,organism_url)

                organism_urls[organism_url] = 0
                self.__write_organism_urls_json(organism_url_path,organism_urls)

                self.__write_taxon_id_json(path,domain,taxon_id,org_dict)

        ## Parses the .json files in directory and creates a combined taxon id list.
        print("Writing combined json to file...")
        for _dirpath, _dirnames, files in os.walk(domain_path):
            if files:
                combined_taxon_ids = [f.split('.json')[0] for f in files]
                
        with open(os.path.join(domain_path,"combined_taxon_ids.json"), 'w') as f:  
            json.dump(combined_taxon_ids,f)

        print("Done.")

    def scrape_ids(self,ids):
        ## Taxon IDs must be a list

        ## Format IDs into organism urls

        ## Call scrape_urls
        pass

def __execute_cli(args):
    """
    Call appropriate methods based on command line interface input.
    """
    chromedriver_path = args.cd_path

    if args.scrape_domain == True:
        J = Jgi(chromedriver_path,args.hp_url)
        J.scrape_domain(args.path, args.domain, database=args.db, assembly_types=args.at)

    if args.scrape_urls == True:
        J = Jgi(chromedriver_path,args.hp_url)
        J.scrape_urls(args.path, args.domain, args.organism_urls, assembly_types=args.at)

if __name__ == '__main__':

    # Initial setup of argparse with description of program.
    parser = argparse.ArgumentParser(description='Retrieve enzyme data from JGI genomes and metagenomes.')
    
    # Adds --path as an argument. Default value is None, it is a required argument, and it looks for a string.
    # Can access the path variable:
    # PATH = args.path
    parser.add_argument('--path',default=None,required=True,type=str,help='Directory where JGI data will be downloaded to. (Required)')
    
    # group1 is a mutually exclusive group
    # Example: If you have --scrape_domain as an argument, then you CANNOT have --scrape_urls as an argument.
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('--scrape_domain',default=True,help='Download an entire JGI domain and run pipeline to format data (Default = True).')
    group1.add_argument('--scrape_urls',default=False,help='Download data from one or more (meta)genomes by URL. (Default = False).')

    parser.add_argument('--organism_urls',nargs='+',type=str,help='List of (meta)genomes by URL for scrape_urls. (Required only if scrape_urls == True)')
    # domain has limited choices and will return error if variable is not set to one of them.
    parser.add_argument('--domain',choices=['Eukaryota','Bacteria','Archaea','*Microbiome','Plasmids','Viruses','GFragment','cell','sps','Metatranscriptome'],required=True,type=str,help='JGI valid domain to scrape data from. (Required)')
    parser.add_argument('--cd_path',default=None,type=str,help='Path pointing to chromedriver executable. (Required)')
    parser.add_argument('--hp_url',default='https://img.jgi.doe.gov/cgi-bin/m/main.cgi',type=str,help="URL of JGI's homepage. (Optional. Default = https://img.jgi.doe.gov/cgi-bin/m/main.cgi)")
    parser.add_argument('--db',choices = ['jgi','all'],default='all',type=str,help='To use only JGI annotated organisms or all organisms. (Optional. Default = all)')
    parser.add_argument('--at',default=['assembled','unassembled','both'],choices = ['assembled','unassembled','both'],nargs='+',type=str,help='Assembly types. Only used for metagenomic domains. Ignored for others. (Optional. Default = [assembled, unassembled, both])')

    # Parses the command line arguments.
    args = parser.parse_args()

    # Runs program using command line arguments
    __execute_cli(args)