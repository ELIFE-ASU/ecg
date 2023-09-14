#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web scraping script to retrieve metadata and genetic statistics from JGI database.
"""

import re
import os
import json
import warnings
import logging
import argparse
from typing import Union, Optional
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

from datetime import date
from tqdm import tqdm
from bs4 import BeautifulSoup

TODAY = date.today().strftime("%b-%d-%Y-%H")

def dump_json(json_dict:dict, path:Union[str,Path], filename:str):
    """
    Dumps data to a json file given a filename.

    Parameters
    ----------
    json_dict: dict
        Dictionary to be written as JSON file.

    path: str, Path
        Path for folder of file to be written.

    filename: str
        Filename of file to be written.
    """
    # Checks if folder exists.
    check_folder(path)

    # Writes json file to path using given filename.
    path = Path(path, filename+'.json')
    with open(path, mode= 'w+', encoding='utf-8') as file:
        json.dump(json_dict, file)

def check_folder(path:Union[str,Path]):
    """
    Checks if path exists and creates it if it does not.

    Parameters
    ----------
    path: str, Path
        Path for folder.
    """
    # Checks if folder exists.
    if not Path(path).is_dir():
        # If folder does not exist it creates it.
        Path(path).mkdir(parents=True, exist_ok=True)

def load_json(path:Union[str,Path]) -> dict:
    """
    Loads jsons given a path.

    Parameters
    ----------
    path: str, Path
        Path for file to be read.

    Returns
    -------
    Dictionary of data loaded from JSON file.
    """
    with open(path,mode='r',encoding='utf-8') as f:
        file = json.load(f)
    return file

class Jgi(object):
    """
    Class to retrieve data from DOE JGI IMG/M website (https://img.jgi.doe.gov/cgi-bin/m/main.cgi).
    Parameters
    ----------
    chromedriver_path: str, Path (Optional, default None)
        Path to the chrome driver.
    homepage_url: str (Optional, default 'https://img.jgi.doe.gov/cgi-bin/m/main.cgi')
        Home page url for JGI
    """
    def __init__(self,driver_type = "Chrome", driver_path="", 
                 homepage_url='https://img.jgi.doe.gov/cgi-bin/m/main.cgi'):

        logging.basicConfig(handlers=[logging.FileHandler(f'JGI-{TODAY}.log'),
                                      logging.StreamHandler()],
                            format='%(name)s - %(levelname)s - %(message)s')
        self.homepage_url = homepage_url

        if driver_type == "Firefox":
            if driver_path=="":
                self.driver = webdriver.Firefox(firefox_binary="C:\\Program Files\\Mozilla Firefox\\firefox.exe")
            
            elif driver_path.startswith("~"):
                self.driver = webdriver.Firefox(os.path.expanduser('~')+driver_path[1:])

            else:
                self.driver = webdriver.Firefox(driver_path)

        elif driver_type == "Chrome":
            options = webdriver.ChromeOptions()
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            #raise ValueError("ChromeDriver not currently supported ")
            if driver_path=="":

                self.driver = webdriver.Chrome(options=options)
            
            elif driver_path.startswith("~"):
                self.driver = webdriver.Chrome(os.path.expanduser('~')+driver_path[1:],
                                                options=options)
            else:
                self.driver = webdriver.Chrome(driver_path, options=options)
        else:
            raise ValueError("That driver is not supported")

    @property
    def driver(self):
        """
        Returns the webdriver
        """
        return self.__driver

    @driver.setter
    def driver(self,driver):
        self.__driver = driver

    @property
    def homepage_url(self):
        """
        Returns the homepage url
        """
        return self.__homepage_url

    @homepage_url.setter
    def homepage_url(self,homepage_url):
        self.__homepage_url = homepage_url

    def safe_web_get(self, url, wait_times=[1,5,60, 60*60, 4*60*60]):

        success = False
        errors = ["Status: 404", "SCRIPT ERROR"]
        for time in wait_times:
            try:
                self.driver.get(url)
                WebDriverWait(self.driver, time).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                htmlSource = self.driver.page_source
                error_found = [e in htmlSource for e in errors]
                if sum(error_found) == 0:
                    success = True
                    return success
                else:
                    logging.warning(f"HTML get failed with time: {time} \n on URL: {url}")
            except TimeoutError:
                print(f"Wait time {time} didn't work, trying next timeout")
                pass
        
        return success

    def __get_domain_url(self, domain:str, database:str) -> str:
        """
        Retrieves the domain url for the given domain and database.

        Parameters
        ----------
        domain: str
            Domain of data (e.g. Bacteria).
        database:str
            Type of database (e.g. jgi, all).

        Returns
        -------
        domain_url: str
            Url of domain.
        """
        if database == 'jgi':
            database_str = "&seq_center=jgi"
        elif database == 'all':
            database_str = ""
        else:
            raise ValueError("`database` must be 'jgi' or 'all'")

        # These datasets use a different URL pattern
        if domain in ['*Microbiome','cell','sps','Metatranscriptome']:
            alpha_str = "2"
        else:
            alpha_str = ""

        jgi_url = "https://img.jgi.doe.gov/cgi-bin/m/main.cgi"
        section_url = f"?section=TaxonList&page=taxonListAlpha{alpha_str}"
        domain_url = f"{jgi_url}{section_url}&domain={domain}{database_str}"

        return domain_url

    def __get_domain_json(self, domain_url:str, domain:str) -> dict:
        """
        Retrieves the domain json dict for the given domain and database.

        Parameters
        ----------
        domain: str
            Domain of data (e.g. Bacteria).
        database:str
            Type of database (e.g. jgi, all).

        Returns
        -------
        domain_json: dict
            Dictionary of data from JGI for the domain.
        """
        ## Identify correct time to allow page to load
        if domain=='Bacteria':
        #if (domain=="Bacteria") and (database=="all"):
            sleep_time = 75
        else:
            sleep_time = 5

        self.safe_web_get(domain_url)
        ## Takes a long time to load all bacteria (because there are 60k of them)
        #time.sleep(sleep_time) 
        # WebDriverWait(self.driver, sleep_time*2).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        htmlSource = self.driver.page_source
        # driver.quit()

        regex = r'var myDataSource = new YAHOO\.util\.DataSource\(\"(.*)\"\);'
        match = re.search(regex, htmlSource)
        domain_json_suffix = match.group(1)
        domain_url_prefix = domain_url.split('main.cgi')[0]
        domain_json_url = domain_url_prefix+domain_json_suffix

        success = self.safe_web_get(domain_json_url)
        # WebDriverWait(self.driver, sleep_time*2).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # time.sleep(sleep_time)

        # domain_json = json.loads(self.driver.find_element_by_tag_name('body').text)
        domain_json = json.loads(self.driver.find_element(By.TAG_NAME,'body').text)


        return domain_json

    def __get_organism_urls(self, domain_json:dict,
                            organism_url_path:Union[str,Path]) -> dict:
        """
        Creates dictionary of organism urls and sets the values to 1.
        If url is to be downloaded, then value is 1.
        If url is already downloaded, then value is 0.

        Writes the resulting dictionary to a file and returns the dictionary.

        Parameters
        ----------
        domain_json: dict
            Dictionary of data from JGI for the domain.
        organisum_url_path: str, Path
            Path for the organims url data to be written to.

        Returns
        -------
        organism_dict: dict
            Dictionary of organism urls with key being the url and the value being if they are to
            be downloaded or not.
        """
        genome_name =  [d['GenomeNameSampleNameDisp'] for d in domain_json['records']]
        organism_urls = []

        for htmlandjunk in genome_name:
            regex = r"<a href='main\.cgi(.*)'>"
            match = re.search(regex, htmlandjunk)
            html_suffix = match.group(1)

            full_url = f"{self.homepage_url}{html_suffix}"
            organism_urls.append(full_url)

        organism_dict = dict.fromkeys(organism_urls,1)
        # Writes the dictionary of organisms urls.
        dump_json(organism_dict, organism_url_path,'organism_url')
        return organism_dict

    def __prune_organism_urls(self, organism_urls:dict, domain_path:Union[str,Path]):
        """
        Checks to see if files are already downloaded and removes them from the organism_urls.json
        temporary file.

        Parameters
        ----------
        organism_urls: dict
            Dictionary of organism urls fora domain.
        domain_path: str, Path
            Path to the domain data downloaded.
        """
        stub = re.sub(r'\d+$', "", next(iter(organism_urls)))

        # Checks all .json files already downloaded and removes from organism_urls
        for file in Path(domain_path).rglob('*.json'):
            f = file.name.split('.json')[0]
            organism_url = stub + f
            if organism_url in organism_urls:
                del organism_urls[organism_url]

        # Checks all organism_urls keys for values not 1 and removes them from organism_urls
        for key, val in organism_urls.items():
            if val != 1:
                del organism_urls[key]

        return organism_urls

    def __get_organism_htmlsource(self, organism_url:str):
        """
        Retrieves html source from organism url page.
        """
        self.safe_web_get(organism_url)
        # time.sleep(5)
        # WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        return self.driver.page_source

    def __get_organism_data(self, htmlsource):
        # Create Beautiful Soup object for parsing
        bsoup = BeautifulSoup(htmlsource,"html.parser")

        # Parses webpage for the division that contains the tables.
        test_table = bsoup.find('div',attrs={'id':'container'})

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
                                # Parses first line in entry to get category (key) and removes
                                # spaces, tabs, etc. from entry.
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
                            test_title = table.findAll('th',
                                                       attrs={'class':'subhead'}
                                                       )[0].text.rstrip()
                            if test_title == 'DNA, total number of bases':
                                for entry in entry_name:
                                    if entry.findAll('th',attrs={'class':'subhead'}):
                                        row_key = entry.findAll('th',
                                                                attrs={'class':'subhead'}
                                                                )[0].text.rstrip().strip()
                                        values = entry.findAll('td',attrs={'class':'img'})
                                        for i, _ in enumerate(values):
                                            values[i] = values[i].text.rstrip().strip()
                                            values[i] = values[i].replace('\xa0','')

                                        stats[row_key] = values

                                    else:

                                        row = entry.findAll('td',attrs={'class':'img'})

                                        for i, _ in enumerate(row):
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

    def __get_metagenome_data(self,htmlsource):
        # Create Beautiful Soup object for parsing
        bsoup = BeautifulSoup(htmlsource,"html.parser")

        # Parses webpage for the division that contains the tables.
        test_table = bsoup.find('div',attrs={'id':'container'})

        # Initialize dictionaries for metadata and genetic statistics.
        metadata = {}
        stats = {}
        assembled = {}
        unassembled = {}
        total = {}

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
                                # Parses first line in entry to get category (key) and removes
                                # spaces, tabs, etc. from entry.
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
                                for i, _ in enumerate(values):
                                    value = values[i].text.rstrip().strip()

                                    if i < 2:
                                        assembled.setdefault(row_key,[]).append(value)
                                    elif i < 4:
                                        unassembled.setdefault(row_key,[]).append(value)
                                    else:
                                        total.setdefault(row_key,[]).append(value)

                            except (IndexError, KeyError):
                                pass

                        # Finds all subcategories of the above categories and their entries.
                        # Appends keys, values to dictionary based on assembly type
                        else:
                            title = entry.findAll('td',attrs={'class':'img'})
                            try:
                                for i, _ in enumerate(title):
                                    value = title[i].text.rstrip().strip()

                                    if i == 0:
                                        row_key = value.replace('\xa0','')
                                    elif i < 3:
                                        assembled.setdefault(row_key,[]).append(value)
                                    elif i < 5:
                                        unassembled.setdefault(row_key,[]).append(value)
                                    else:
                                        total.setdefault(row_key,[]).append(value)

                            except (IndexError, KeyError):
                                pass

        stats['assembled'] = assembled

        # If unassembled table exists, add it and the total table to statistics table dictionary.
        if unassembled != dict():
            stats['unassembled'] = unassembled
            stats['total'] = total

        return metadata,stats

    def __get_enzyme_url_metagenome(self, htmlsource, assembly_type):

        # Create Beautiful Soup object for parsing
        bsoup = BeautifulSoup(htmlsource,"html.parser")

        # Set prefix and initialize suffix for enzyme url
        prefix = 'https://img.jgi.doe.gov/cgi-bin/m/'
        suffix = ''

        # Get list of all <td class='img'></td>
        td_list = bsoup.findAll('td',attrs={'class':'img'})

        # Parse above list to find 'with Enzyme' section
        for i, _ in enumerate(td_list):
            if td_list[i].text.rstrip().strip() == 'with Enzyme':
                # Checks assembly type and then looks to see if there is an associated webpage.
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

    def __get_enzyme_url(self, htmlsource):
        # Create Beautiful Soup object for parsing
        bsoup = BeautifulSoup(htmlsource,"html.parser")

        # Set prefix and initialize suffix for enzyme url
        prefix = 'https://img.jgi.doe.gov/cgi-bin/m/'
        suffix = ''

        # Get list of all <td class='img'></td>
        td_list = bsoup.findAll('td',attrs={'class':'img'})

        # Parse above list to find 'Protein coding genes with enzymes' section and webpage
        # associated with it, if it exists.
        for i, _ in enumerate(td_list):
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
        enzyme_json = None
        success = self.safe_web_get(enzyme_url)
        if success:
            # time.sleep(5)
            # WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            htmlSource = self.driver.page_source
            # driver.quit()

            regex = r'var myDataSource = new YAHOO\.util\.DataSource\(\"(.*)\"\);'
            match = re.search(regex, htmlSource)
            enzyme_json_suffix = match.group(1)
            enzyme_url_prefix = enzyme_url.split('main.cgi')[0]
            enzyme_json_url = enzyme_url_prefix+enzyme_json_suffix

            success = self.safe_web_get(enzyme_json_url)
            if success:
                ## JSON formatted object ready to be dumped
                # enzyme_json = json.loads(self.driver.find_element_by_tag_name('body').text)
                enzyme_json = json.loads(self.driver.find_element(By.TAG_NAME, 'body').text)
            else:
                logging.warning(f"Enzyme JSON failed for URL: {enzyme_url}")
                enzyme_json = None

        else:
            enzyme_json = None

        return enzyme_json

    def __prune_enzyme_json(self,enzyme_json):
        """
        Reduce keys in enzyme json by discarding "display" keys.
        """
        # Dictionary of ec:[enzymeName,genecount] for all ecs in a single metagenome.
        enzyme_dict = dict()

        enzyme_dict = dict() # Dictionary of ec:[enzymeName,genecount] for all ecs in a single metagenome

        for singleEnzymeDict in enzyme_json['records']:
            ec = singleEnzymeDict.get("EnzymeID", None)
            if ec:
                # ec = singleEnzymeDict['EnzymeID']
                enzymeName = singleEnzymeDict['EnzymeName']
                genecount = singleEnzymeDict['GeneCount']

                enzyme_dict[ec] = [enzymeName,genecount]

        return enzyme_dict

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
        domain_path = os.path.join(path,domain).replace("*","")
        taxon_ids_path = os.path.join(domain_path,"taxon_ids",taxon_id+".json")
        with open(taxon_ids_path, 'w') as f:
            json.dump(org_dict, f)

        # taxon_ids_path = Path(path, domain,"taxon_ids")
        # fname = f"{taxon_id}"
        # dump_json(org_dict, taxon_ids_path, fname)

    def __write_missing_enzyme_json(self,missing_enzyme_path,missing_enzyme_data):

        with open(missing_enzyme_path,'w', encoding='utf-8') as f:
            json.dump(missing_enzyme_data, f)

    def __read_missing_enzyme_json(self,missing_enzyme_path):
        return load_json(missing_enzyme_path)

    def __scrape_organism_url_from_metagenome(self,path,organism_url,assembly_types):

        # Record whether scrape was successful 
        successful = False
        # Get enzyme json for single organism
        htmlsource = self.__get_organism_htmlsource(organism_url)
        metadata_dict, statistics_dict = self.__get_metagenome_data(htmlsource)

        missing_enzyme_path = Path(path,"missing_enzyme_data.json")
        taxon_id = metadata_dict['Taxon Object ID']
        org_dict = {'metadata':metadata_dict, 'statistics':statistics_dict}

        ## Different methods for metagenomes/genomes
        for assembly_type in assembly_types:
            enzyme_url = self.__get_enzyme_url_metagenome(htmlsource, assembly_type)
            if enzyme_url:
                enzyme_json = self.__get_enzyme_json(enzyme_url)

                if enzyme_json:
                    enzyme_json = self.__prune_enzyme_json(enzyme_json)
                    org_dict[assembly_type] = enzyme_json
                    successful = True
                else:
                    logging.warning(f"Enzyme JSON failed for URL: {enzyme_url}")
            ## Write missing data to dict
            else:
                if missing_enzyme_path.is_file():
                    missing_enzyme_data = self.__read_missing_enzyme_json(missing_enzyme_path)
                    if taxon_id not in missing_enzyme_data:
                        missing_enzyme_data[taxon_id] = assembly_type

                else:
                    missing_enzyme_data = {}
                    missing_enzyme_data[taxon_id] = assembly_type

        return taxon_id, org_dict, successful

    def __scrape_organism_url_from_regular_domain(self,path,organism_url):

        successful = False
        htmlsource = self.__get_organism_htmlsource(organism_url)
        metadata_dict, statistics_dict = self.__get_organism_data(htmlsource)

        missing_enzyme_path = Path(path,"missing_enzyme_data.json")

        taxon_id = metadata_dict['Taxon ID']
        org_dict = {'metadata':metadata_dict, 'statistics':statistics_dict}

        enzyme_url = self.__get_enzyme_url(htmlsource)
        if enzyme_url:
            enzyme_json = self.__get_enzyme_json(enzyme_url)
            if enzyme_json:
                enzyme_json = self.__prune_enzyme_json(enzyme_json)
                org_dict["enzymes"] = enzyme_json
                successful = True
            else:
                logging.warning(f"Enzyme JSON failed for URL: {enzyme_url}")
        ## Write missing data to list
        else:
            if missing_enzyme_path.is_file():
                missing_enzyme_data = self.__read_missing_enzyme_json(missing_enzyme_path)
                if taxon_id not in missing_enzyme_data:
                    missing_enzyme_data.append(taxon_id)

            else:
                missing_enzyme_data = []
                missing_enzyme_data.append(taxon_id)

            self.__write_missing_enzyme_json(missing_enzyme_path,missing_enzyme_data)

        return taxon_id, org_dict, successful


    def scrape_domain(self,
                      path:Optional[Union[str,Path]],
                      domain:str,
                      database:Optional[str]='all',
                      assembly_types:Optional[list] = None):
        """
        Scrapes the web for the given domain and retrieves the information from the JGI website.

        Parameters
        ----------
        path: str, Path (Optional)
            Path to store domain directories in and to write combined jsons to.
        domain: str
            Which domain to retrieve the information from. *Microbiome domain is the Metagenome
            domain.

            Valid Choices are: [Eukaryota, Bacteria, Archaea, Plasmids, Viruses, GFragment,
                                *Microbiome, cell, sps, Metatranscriptome]
            Tested Choices are: [Eukaryota, Bacteria, Archaea, *Microbiome]

        database: str (Optional, default all)
            Choose to use only the `jgi` database, or `all` database.
        assembly_types: list[str] (Optional, default None)
            Only used for metagenomic domains (*Microbiome, cell, sps, Metatranscriptome).
            Ignored for others. If metagenomic domain, defaults to: [unassembled, assembled, both].
        """
        if not assembly_types:
            assembly_types = ['assembled','unassembled','both']
        ## Make save_dir
        domain_path = os.path.join(path,domain,"taxon_ids").replace("*","")
        check_folder(domain_path)


        ## Validate assembly_types
        metagenome_domains = ['*Microbiome','cell','sps','Metatranscriptome']
        if domain in metagenome_domains:
            self.__validate_assembly_types(assembly_types)

        ## Validate domain
        self.__validate_domain(domain)


        ## Get all organism URLs
        # Checks to see if there is an organism url list already and imports it.
        domain_path = os.path.join(path,domain).replace("*","")
        organism_url_path = os.path.join(domain_path,'organism_url.json')

        if os.path.isfile(organism_url_path):
            with open(organism_url_path,'r') as f:
                organism_urls = json.load(f)


        # If no organism url list present, then creates one.
        else:
            domain_url = self.__get_domain_url(domain, database)
            domain_json = self.__get_domain_json(domain_url, domain)
            organism_urls = self.__get_organism_urls(domain_json, organism_url_path)

        # Prunes list of organism_urls.
        organism_urls = self.__prune_organism_urls(organism_urls, domain_path)

        self._scrape_urls_unsafe(path,domain,organism_urls, assembly_types=assembly_types)

    def scrape_urls(self,
                    path:Optional[Union[str,Path]],
                    domain:str,
                    organism_urls:list,
                    assembly_types:Optional[list] = None):
        """
        Scrapes the web for the given domain and retrieves the information from the JGI website.
        Uses a list of organism_urls as input to download a specific set of organisms.

        Parameters
        ----------
        path: str, Path (Optional)
            Path to store domain directories in and to write combined jsons to.
        domain: str
            Which domain to retrieve the information from. *Microbiome domain is the Metagenome
            domain.

            Valid Choices are: [Eukaryota, Bacteria, Archaea, Plasmids, Viruses, GFragment,
                                *Microbiome, cell, sps, Metatranscriptome]
            Tested Choices are: [Eukaryota, Bacteria, Archaea, *Microbiome]

        organism_urls: list[str]
            Takes a list of urls for organisms and scrapes the database for their info.
        assembly_types: list[str] (Optional, default None)
            Only used for metagenomic domains (*Microbiome, cell, sps, Metatranscriptome).
            Ignored for others. If metagenomic domain, defaults to: [unassembled, assembled, both].
        """
        if not assembly_types:
            assembly_types = ['assembled','unassembled','both']

        ## Make save_dir
        domain_path = os.path.join(path,domain,"taxon_ids").replace("*","")
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)


        ## Only allow scraping into empty directory
        files = [file.name for file in Path(domain_path).rglob('*.json')]
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
                    assembly_types = None):
        """
        Only meant to be called internally as it does not validate input.
        """
        if not assembly_types:
            assembly_types = ['assembled','unassembled','both']
        metagenome_domains = ['*Microbiome','cell','sps','Metatranscriptome']

        pbar = tqdm(organism_urls)

        domain_path = os.path.join(path,domain).replace("*","")
        organism_url_path = os.path.join(domain_path,'organism_url.json')
        # Log errors
        error_urls = []

        if domain in metagenome_domains:

            for organism_url in pbar:
                taxon_description = re.search(r'\d+$', organism_url).group(0)
                pbar.set_description(f"Scraping {taxon_description} ...")
                taxon_id, org_dict, successful = self.__scrape_organism_url_from_metagenome(domain_path,
                                                                                            organism_url,
                                                                                            assembly_types)
                if successful:
                    organism_urls[organism_url] = 0
                    dump_json(organism_urls, organism_url_path,'organism_url')

                    self.__write_taxon_id_json(path,domain,taxon_id,org_dict)
                
                else:
                    # More error logging here
                    error_urls.append(organism_url)

        else:

            for organism_url in pbar:
                taxon_description = re.search(r'\d+$', organism_url).group(0)
                pbar.set_description(f"Scraping {taxon_description} ...")
                taxon_id, org_dict, successful = self.__scrape_organism_url_from_regular_domain(domain_path,
                                                                                                organism_url)

                if successful:
                    organism_urls[organism_url] = 0
                    dump_json(organism_urls, organism_url_path,'organism_url')

                    self.__write_taxon_id_json(path,domain,taxon_id,org_dict)
                else:
                    # More error logging here
                    error_urls.append(organism_url)

        ## Parses the .json files in directory and creates a combined taxon id list.
        print("Writing combined json to file...")
        combined_taxon_ids = [file.name for file in Path(domain_path).rglob('*json')]
        combined_taxon_ids = [file.split('.json')[0] for file in combined_taxon_ids]

        dump_json(combined_taxon_ids,domain_path,'combined_taxon_ids')
        print("Done.")

def __execute_cli(args):
    """
    Call appropriate methods based on command line interface input.
    """
    chromedriver_path = args.cd_path

    if args.scrape_domain:
        J = Jgi(chromedriver_path, args.hp_url)
        J.scrape_domain(args.path, args.domain,
                        database=args.db, assembly_types=args.at)

    if args.scrape_urls:
        J = Jgi(chromedriver_path, args.hp_url)
        J.scrape_urls(args.path, args.domain,
                      args.organism_urls, assembly_types=args.at)

def main():
    """
    Calls the JGI class to scrape the website for data using the options provided by the CLI
    options.
    """
    # Initial setup of argparse with description of program.
    description = 'Retrieve enzyme data from JGI genomes and metagenomes.'
    parser = argparse.ArgumentParser(description=description)

    # Adds --path as an argument. Default value is None, it is a required argument, and it looks
    # for a string.
    parser.add_argument('--path', default=None, required=True, type=str,
                        help='Directory where JGI data will be downloaded to. (Required)')

    # group1 is a mutually exclusive group
    # Example: If you have --scrape_domain as an argument, then you CANNOT have --scrape_urls as
    # an argument.
    group1 = parser.add_mutually_exclusive_group()
    scrape_domain_help ='Download an entire JGI domain and run pipeline to format data \
                        (Default = True).'
    group1.add_argument('--scrape_domain', default=True,
                        help=scrape_domain_help)

    scrape_url_help = 'Download data from one or more (meta)genomes by URL. (Default = False).'
    group1.add_argument('--scrape_urls', default=False,
                        help=scrape_url_help)

    organism_url_help = "List of (meta)genomes by URL for scrape_urls. \
                        (Required only if scrape_urls is True)"
    parser.add_argument('--organism_urls', nargs='+', type=str,
                        help=organism_url_help)

    # domain has limited choices and will return error if variable is not set to one of them.
    domains = ['Eukaryota','Bacteria','Archaea','*Microbiome','Plasmids','Viruses','GFragment',
               'cell','sps','Metatranscriptome']
    parser.add_argument('--domain', choices= domains, required=True, type=str,
                        help='JGI valid domain to scrape data from. (Required)')

    parser.add_argument('--cd_path', default=None, type=str,
                        help='Path pointing to chromedriver executable. (Optional)')

    hp_url_help = "URL of JGI's homepage. \
                  (Optional. Default = https://img.jgi.doe.gov/cgi-bin/m/main.cgi)"
    parser.add_argument('--hp_url', default='https://img.jgi.doe.gov/cgi-bin/m/main.cgi', type=str,
                        help=hp_url_help)

    db_help = 'To use only JGI annotated organisms or all organisms. (Optional. Default = all)'
    parser.add_argument('--db', choices = ['jgi','all'], default='all', type=str,
                        help=db_help)

    assembly_type_help = 'Assembly types. Only used for metagenomic domains. Ignored for others. \
                         (Optional. Default = [assembled, unassembled, both])'
    parser.add_argument('--at', default=['assembled','unassembled','both'],
                        choices = ['assembled','unassembled','both'],
                        nargs='+', type=str, help=assembly_type_help)

    # Parses the command line arguments.
    args = parser.parse_args()

    # Runs program using command line arguments
    __execute_cli(args)

if __name__ == '__main__':
    main()
