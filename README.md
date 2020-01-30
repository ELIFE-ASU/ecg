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

## Local Installation

To install locally, if you haven't navigated to the package directory:

`pip install -e /path/to/package` 

To install locally, if you're in the package directory:

`pip install -e .` 

To install locally (for user only):

`pip install -e /path/to/package --user` 

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

Example: `python kegg.py mydir download --db compound --db reaction`

```python
"""
Retrieve KEGG databases and format them for use in network expansions.

Usage:
  kegg.py PATH download [--run_pipeline=<rp>|--db=<db>...]
  kegg.py PATH update [--metadata=<md>]

Arguments:
  PATH  Directory will kegg will be downloaded to (or where it already exists)  
  download  Download KEGG and run pipeline to format data
  update    Update existing KEGG directory     

Options:
  --run_pipeline=<rp>   Whether or not to run the full pipeline [default: True]
  --db=<db>...     Databases to download [default: pathway enzyme reaction compound] 
  --metadata=<md>   Add metadata fields from "RXXXXX.json" into master.json [default: True]
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

Example: `python jgi.py --chromedriver_path=/Users/Me/Applications/chromedriver scrape_domain myjgidir Bacteria --database=jgi`

```python
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

```python
"""
WARNING. CLI HAS NOT IMPLEMENTED OR TESTED YET.

Combine KEGG derived reaction data with JGI derived enzyme data to generate reaction lists (meta)genomes

Usage:
  ecg.py write_biosystem_rxns BIOSYSTEM_JSON EC_RXN_LINK_JSON [--outdir=<outdir>]
  ecg.py write_biosystem_graphs BIOSYS_RXN_JSON MASTER_JSON [--graphtypes=<graphtypes>|--outdir=<graphoutdir>|--missingdir=<missingdir>|--verbose=<verbose>]

Arguments:
  BIOSYSTEM_JSON    the filepath to the directory or file where JGI data is located
  EC_RXN_LINK_JSON  the filepath to `enzyme_reaction.json` (the json containing relationship between ec numbers and reactions)
  BIOSYS_RXN_JSON   the filepath to the biosystem reaction json file
  MASTER_JSON       the filepath to `master.json` (json with details information about all KEGG reactions)
  write_biosystem_rxns   Write reaction lists from either a single biosystem file or biosystem directory (all JGI jsons)
  write_biosystem_graphs   Write gmls from either a single biosystem reaction file or biosystem reaction directory (all JGI reaction jsons)

Options:
  --outdir=<outdir>   Path where biosystem reactions will be saved [default: "taxon_reactions"]
  --graphtypes=<graphtypes> Which types of graphs to write to gml files [default: ["unipartite-undirected-subfromdirected"]]
  --outdir=<graphoutdir> The dir to store subdirs for each graph type, and subsequent gml files [default: "graphs"]
  --missingdir=<missingdir> The dir to store reactions which are missing from biosystems as jsons [default: "taxon_with_rxns_missing_from_kegg"]
  --verbose=<verbose> If True, prints the graph types as they're created [default: True]

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

