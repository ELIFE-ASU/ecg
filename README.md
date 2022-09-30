# ecg
Pulling information from biological databases, and converting it into easy to use jsons/gmls for network science.

- [ecg](#ecg)
  - [Dependencies](#dependencies)
  - [Local Installation](#local-installation)
  - [Downloading KEGG data (`kegg.py`)](#downloading-kegg-data-keggpy)
    - [Using import](#using-import)
      - [Downloading and running pipeline](#downloading-and-running-pipeline)
      - [Updating KEGG directory with latest entries](#updating-kegg-directory-with-latest-entries)
    - [Using CLI](#using-cli)
    - [Output format](#output-format)
  - [Downloading JGI data (`jgi.py`)](#downloading-jgi-data-jgipy)
    - [Using import](#using-import-1)
      - [Downloading and running pipeline](#downloading-and-running-pipeline-1)
    - [Using CLI](#using-cli-1)
    - [Output format](#output-format-1)
  - [Getting biosystem reaction lists and network graphs using KEGG and JGI (`ecg.py`)](#getting-biosystem-reaction-lists-and-network-graphs-using-kegg-and-jgi-ecgpy)
    - [Using import](#using-import-2)
      - [Writing reaction jsons](#writing-reaction-jsons)
      - [Writing graphs](#writing-graphs)
    - [Using CLI](#using-cli-2)
    - [Output format](#output-format-2)

## Dependencies
- `docopt`<sup>k,j,e</sup>  (for CLI)
- `tqdm`<sup>k,j</sup>  (for visual progress bars)
- `biopython`<sup>k</sup>  (for KEGG REST API and TogoWS)

- `selenium`<sup>j</sup>  (for webdriver)
- `beautifulsoup4`<sup>j</sup>  (for web page parsing)
- `networkx`<sup>e</sup> (for graphs/networks

<sup>k</sup>Used by `kegg.py`

<sup>j</sup>Used by `jgi.py`

<sup>e</sup>Used by `ecg.py` 

## Quickstart

Open your terminal or other Unix/Linux command-line interface. Use it to navigate to your desktop, documents, or other folder in which you tend to store projects (e.g. `cd Desktop/`). Then, copy+paste into the terminal each of the following lines:

```
mkdir ecgHub
pip install docopt; pip install tqdm; pip install biopython; pip install selenium; pip install beautifulsoup4; pip install networkx
cd ecgHub
git clone https://github.com/ELIFE-ASU/ecg
cd ecg
pip install -e .
mkdir mydata
```

## Installing and Using a Webdriver
To use the `jgi` functionality in `ecg` you need to have a webdriver that can be used to drive a browser on your computer. Right now we're devloping this for Chrome. In order to use it you need to have [chromedriver](https://chromedriver.chromium.org/downloads) downloaded, unzipped and added to your `PATH`. You also need a compatible version of Chrome installed. To test this you should just be able to run `chromedriver` from you command prompt and see success message. If not check your `PATH` and try again. 


## Completed Installation

The command `import ecg` should now work for any Python scripts or Jupyter Notebooks created and stored in the top-level `ecg` directory (i.e. `ecgHub/ecg`). Files not used by ecg or generated with ecg, but which are relevant or occasionally needed in scripts which `import ecg`, can then be stored in the `ecgHub` folder. (manuscripts, notes, templates, auxiliary csvs, etc.)

## Local Installation

To install locally, if you haven't navigated to the package directory:

`pip install -e /path/to/package` 

To install locally, if you're in the package directory:

`pip install -e .` 

The `-e` flag indicates a symlink, and forces the package to upgrade whenever the source directory changes (e.g. if you pull from github)

## Downloading KEGG data (`kegg.py`)

Downloading and formatting KEGG data can be done through by importing the `ecg` package in a script, or through a command line interface (CLI).

### Using import

#### Downloading and running pipeline

```python
import ecg

path = "mydata/kegg"
kegg = ecg.Kegg(path)
kegg.download(run_pipeline=True,dbs=["pathway","enzyme","reaction","compound"]) ## These are the default arguments
```

#### Updating KEGG directory with latest entries

*Note: Updating will NOT reflect changes made to invdividual entries' fields, and it will NOT remove entries which have been removed from KEGG. It will only add entries which have been added. To guarantee the most up-to-date KEGG database, a full re-download is necessary.*

```python
import ecg

path = "mydata/kegg"
K = ecg.Kegg(path)
K.update(metadata=True) ## These are the default arguments

## Built-in public methods
K.download;
K.update;
K.path;
K.version;
K.lists;
```



### Using CLI

*Note: If more than one user supplied database is provided it must be done so with its own flag. Each flag can only accept one argument.*

Example: `python kegg.py --path mydir --db compound reaction` 

```python
"""
usage: kegg.py [-h] [--rp RP]
               [--db {pathway,brite,module,ko,genome,<org>,vg,ag,compound,glycan,reaction,rclass,enzyme,network,hsa_var,disease,drug,dgroup,environ} [{pathway,brite,module,ko,genome,<org>,vg,ag,compound,glycan,reaction,rclass,enzyme,network,hsa_var,disease,drug,dgroup,environ} ...]]
               [--md MD] --path PATH [--download DOWNLOAD] [--update UPDATE]

Retrieve KEGG databases and format them for use in network expansions.

optional arguments:
  -h, --help            show this help message and exit
  --rp RP               Whether or not to run the full pipline. (Default =
                        True)
  --db {pathway,brite,module,ko,genome,<org>,vg,ag,compound,glycan,reaction,rclass,enzyme,network,hsa_var,disease,drug,dgroup,environ} [{pathway,brite,module,ko,genome,<org>,vg,ag,compound,glycan,reaction,rclass,enzyme,network,hsa_var,disease,drug,dgroup,environ} ...]
                        Databases to download. For more information on dbs see
                        KEGG DB Links. (Default = ["pathway", "enzyme",
                        "reaction", "compound"])
  --md MD               Whether to add metadata fields from "RXXXXX.json" into
                        master.json. (Default = True)
  --path PATH           Directory where KEGG will be downloaded to or updated.
                        (Required)
  --download DOWNLOAD   Whether to download KEGG and run pipeline to format
                        data. (Default = True)
  --update UPDATE       Whether or not to update existing KEGG directory.
                        Note: Updating will NOT reflect changes made to
                        invdividual entry fields, and it will NOT remove
                        entries which have been removed from KEGG. It will
                        only add entries which have been added. To guarantee
                        the most up-to-date KEGG database, a full re-download
                        is necessary. (Default = False)
"""
```

### Output format

The default file structure output from `Kegg.download()` looks like:

```
mydata/kegg
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
```

The defualt structure of the `version.json` file looks approximately like:

```
Kegg.version  #returns info from http://rest.kegg.jp/info/kegg
|- Kegg.version["original"] = dict() # KEGG stats at time of initial retrieval
|    |-...["release_short"] = float # returns release of database eg. 90.0
|    |-...["release_long"] = str # returns 90.0+/06-06, Jun 19
|    |-...["count_info"] = dict() # returns number of entries in each of the subcategories as found on KEGG's info page at time of retrieval
|        |-...["pathway"] = int
|        |-...["compound"] = int
|        |-...["reaction"] = int
|        |-...["enzyme"] = int
|    |-...["count_lists"] = dict() # returns number of entries in each of the subcategories as found by counting the items in Kegg.version["original"]["lists"]
|        |-...["pathway"] = int
|        |-...["compound"] = int
|        |-...["reaction"] = int
|        |-...["enzyme"] = int
|    |-...["lists"] = dict() # returns name of each entry in each of the subcategories
|        |-...["pathway"] = list()
|        |-...["compound"] = list()
|        |-...["reaction"] = list()
|        |-...["enzyme"] = list()
|- Kegg.version["updates"] = list(dict(),dict(),...) # KEGG stats after each update
|- Kegg.version["current"] = dict() # KEGG stats of latest update
```

## Downloading JGI data (`jgi.py`)

Downloading JGI data can be done through by importing the `ecg` package in a script, or through a command line interface (CLI).

### Using import

#### Downloading and running pipeline

```python
from ecg import jgi
import os

chromedriver_path = os.path.expanduser("~")+"/chromedriver" # "~/chromedriver" should also work
path = "mydata/jgi"
domain = "Eukaryota"

J = jgi.Jgi()
J.scrape_domain(path, 
                domain,
                database='all', 
                assembly_types = ['assembled','unassembled','both'])

## Built-in public methods
J.scrape_domain;
J.scrape_urls; # argument organism_urls should be a list of full urls
J.homepage_url;
J.driver;
```

### Using CLI

Example: `python jgi.py --cd_path=/usr/bin/chromedriver --path myjgidir --domain Bacteria --db=jgi`

```python
"""
usage: jgi.py [-h] --path PATH
              [--scrape_domain SCRAPE_DOMAIN | --scrape_urls SCRAPE_URLS]
              [--organism_urls ORGANISM_URLS [ORGANISM_URLS ...]] --domain
              {Eukaryota,Bacteria,Archaea,*Microbiome,Plasmids,Viruses,GFragment,cell,sps,Metatranscriptome}
              [--cd_path CD_PATH] [--hp_url HP_URL] [--db {jgi,all}]
              [--at {assembled,unassembled,both} [{assembled,unassembled,both} ...]]

Retrieve enzyme data from JGI genomes and metagenomes.

optional arguments:
  -h, --help            show this help message and exit
  --path PATH           Directory where JGI data will be downloaded to.
                        (Required)
  --scrape_domain SCRAPE_DOMAIN
                        Download an entire JGI domain and run pipeline to
                        format data (Default = True).
  --scrape_urls SCRAPE_URLS
                        Download data from one or more (meta)genomes by URL.
                        (Default = False).
  --organism_urls ORGANISM_URLS [ORGANISM_URLS ...]
                        List of (meta)genomes by URL for scrape_urls.
                        (Required only if scrape_urls == True)
  --domain {Eukaryota,Bacteria,Archaea,*Microbiome,Plasmids,Viruses,GFragment,cell,sps,Metatranscriptome}
                        JGI valid domain to scrape data from. (Required)
  --cd_path CD_PATH     Path pointing to chromedriver executable. (Required)
  --hp_url HP_URL       URL of JGI's homepage. (Optional. Default =
                        https://img.jgi.doe.gov/cgi-bin/m/main.cgi)
  --db {jgi,all}        To use only JGI annotated organisms or all organisms.
                        (Optional. Default = all)
  --at {assembled,unassembled,both} [{assembled,unassembled,both} ...]
                        Assembly types. Only used for metagenomic domains.
                        Ignored for others. (Optional. Default = [assembled,
                        unassembled, both])
"""
```

### Output format

The default file structure output from `jgi.Jgi().scrape_domain("myjgidir","Eukarayota")` looks like:

```
mydata/jgi
|-Eukarayota
|  |-combined_taxon_ids 
|  |-missing_enzymes.json 
|  |-taxon_ids
|    |-2789789765.json
|    |-2789789766.json
|    ...
|-Bacteria
|  ...
```

## Getting biosystem reaction lists and network graphs using KEGG and JGI (`ecg.py`)

### Using import

#### Writing reaction jsons

*In preparation for doing network expansions using **BioXP***

```python
from ecg import ecg

E = ecg.Ecg()
ec_rxn_link_json = "mydata/kegg/links/enzyme_reaction.json"

## Write reactions from one jgi biosystem file
biosystem_json = "mydata/jgi/Eukaryota/taxon_ids/2789789765.json"
E.write_biosystem_rxns(biosystem_json,
                       ec_rxn_link_json,
                       outdir="mydata/jgi/Eukaryota/taxon_reactions")

## Write reactions from all jgi biosystem files in the directory
biosystem_json_dir = "mydata/jgi/Eukaryota/taxon_ids"
E.write_biosystem_rxns(biosystem_json_dir,
                       ec_rxn_link_json,
                       outdir="mydata/jgi/Eukaryota/taxon_reactions")
```

#### Writing graphs 

*Note: You must generate biosystem reaction jsons first*

*Not required for network expansions using BioXP*

```python
from ecg import ecg

E = ecg.Ecg()
master_json = "mydata/kegg/master.json"

## Write graphs from one biosystem rxn file
biosystem_rxn_json = "mydata/jgi/Eukaryota/taxon_reactions/2789789765.json"
E.write_biosystem_graphs(biosys_rxn_json,
                        master_json,
                        graphtypes=["unipartite-undirected-subfromdirected"],
                        outdir="mydata/jgi/Eukaryota/graphs",
                        missingdir="mydata/jgi/Eukaryota/taxon_with_rxns_missing_from_kegg",
                        verbose=True)

## Write graphs from all biosystem rxn files in the directory
biosystem_rxn_json_dir = "mydata/jgi/Eukaryota/taxon_reactions"
E.write_biosystem_graphs(biosys_rxn_json,
                        master_json,
                        graphtypes=["unipartite-undirected-subfromdirected"],
                        outdir="mydata/jgi/Eukaryota/graphs",
                        missingdir="mydata/jgi/Eukaryota/taxon_with_rxns_missing_from_kegg",
                        verbose=True)

## Built-in public methods
E.write_biosystem_rxns;
E.write_biosystem_graphs
```

*Note: Implemented `graphtypes` include:*

```
bipartite-directed-rxnsub
bipartite-undirected-rxnsub
unipartite-undirected-rxn
unipartite-directed-sub
unipartite-undirected-sub
unipartite-undirected-subfromdirected #same connection rules used in "Universal Scaling" paper
```

### Using CLI
Example: `python ecg.py --jgi=mydata/jgi/Eukaryota/taxon_reactions/2789789765.json --master= mydata/kegg/master.json --graphtypes unipartite-undirected-subfromdirected --outdir mydata/jgi/Eukaryota/taxon_reactions --graphoutdir mydata/jgi/Eukaryota/graphs --missingdir mydata/jgi/Eukaryota/taxon_with_rxns_missing_from_kegg`

```python
"""
usage: ecg.py [-h] --jgi JGI --ecrxn ECRXN --biorxn BIORXN --master MASTER
              [--write_rxns WRITE_RXNS] [--write_graphs WRITE_GRAPHS]
              [--outdir OUTDIR]
              [--graphtypes {bipartite-directed-rxnsub,bipartite-undirected-rxnsub,unipartite-undirected-rxn,unipartite-directed-sub,unipartite-undirected-sub,unipartite-undirected-subfromdirected} [{bipartite-directed-rxnsub,bipartite-undirected-rxnsub,unipartite-undirected-rxn,unipartite-directed-sub,unipartite-undirected-sub,unipartite-undirected-subfromdirected} ...]]
              [--graphoutdir GRAPHOUTDIR] [--missingdir MISSINGDIR]
              [--verbose VERBOSE]

WARNING. CLI HAS NOT BEEN IMPLEMENTED OR TESTED YET. Combine KEGG derived
reaction data with JGI derived enzyme data to generate reaction lists
(meta)genomes.

optional arguments:
  -h, --help            show this help message and exit
  --jgi JGI             Filepath to the directory or file where JGI data is
                        located. (Required)
  --ecrxn ECRXN         Filepath to "enzyme_reaction.json"; the json
                        containing relationship between ec numbers and
                        reactions. (Required)
  --biorxn BIORXN       Filepath to the biosystem reaction json file.
                        (Required)
  --master MASTER       Filepath to "master.json"; json with information
                        details about all KEGG reactions. (Required)
  --write_rxns WRITE_RXNS
                        Write reaction lists from either a single biosystem
                        file or biosystem directory; all JGI jsons. (Default =
                        True)
  --write_graphs WRITE_GRAPHS
                        Write gmls from either a single biosystem reactionfile
                        or biosystem reaction directory; all JGI reaction
                        jsons. (Default = True)
  --outdir OUTDIR       Path where biosystem reactions will be saved. (Default
                        = "taxon_reactions")
  --graphtypes {bipartite-directed-rxnsub,bipartite-undirected-rxnsub,unipartite-undirected-rxn,unipartite-directed-sub,unipartite-undirected-sub,unipartite-undirected-subfromdirected} [{bipartite-directed-rxnsub,bipartite-undirected-rxnsub,unipartite-undirected-rxn,unipartite-directed-sub,unipartite-undirected-sub,unipartite-undirected-subfromdirected} ...]
                        Which types of graphs to write to gml files. (Default
                        = "unipartite-undirected-subfromdirected")
  --graphoutdir GRAPHOUTDIR
                        The directory to store subdirs for each graph type,
                        and subsequent gml files. (Default = "graphs")
  --missingdir MISSINGDIR
                        The directory to store reactions which are missing
                        from biosystems as jsons. (Default =
                        "taxon_with_rxns_missing_from_kegg")
  --verbose VERBOSE     If True, prints the graph types as they are created.
                        (Default = True)
"""
```

### Output format

Running `ecg.Ecg()` as intended (and with default arguments) will generate the following new folders: 

- `graphs`
- `taxon_reactions`
- `taxon_with_rxns_missing_from_kegg` (directory is only created if your `taxon_ids` contain enzymes with reactions which are missing from the KEGG database)

So your file structure will now look like this:

```
myjgidir
|-Eukarayota
|  |-combined_taxon_ids 
|  |-graphs
|     |-bipartite-directed-rxnsub
|        |-2789789765.gml
|        |-2789789766.gml
|        ...
|     |-bipartite-directed-rxnsub
|        |-2789789765.gml
|        |-2789789766.gml
|        ...
|     ...
|  |-missing_enzymes.json 
|  |-taxon_ids
|     |-2789789765.json
|     |-2789789766.json
|     ...
|  |-taxon_reactions
|     |-2789789765.json
|     |-2789789766.json
|     ...
|  |-taxon_with_rxns_missing_from_kegg
|     |-9999999999.json
|     ...
|-Bacteria
|  ...
```

