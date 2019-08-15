# ecg
Pulling information from biological databases, and converting it into easy to use jsons/gmls for network science.

## Dependencies
### kegg.py and jgi.py
- `docopt` (for CLI)
- `tqdm` (for visual progress bars)
### kegg.py only
- `biopython` (for KEGG REST API and TogoWS)
### jgi.py only
- `selenium` (for webdriver)
- `beautifulsoup4` (for web page parsing)

## Local Installation

To install locally, if you haven't navigated to the package directory:

`pip install -e /path/to/package` 

To install locally, if you're in the package directory:

`pip install -e .` 

To install locally (for user only):

`pip install -e /path/to/package --user` 

The `-e` flag indicates a symlink, and forces the package to upgrade whenever the source directory changes (e.g. if you pull from github)

## Downloading KEGG data

Downloading and formatting KEGG data can be done through by importing the `ecg` package in a script, or through a command line interface (CLI).

### Using import

#### Downloading and running pipeline

```python
import ecg

path = "./kegg"
kegg = ecg.Kegg(path)
kegg.download(run_pipeline=True,dbs=["pathway","enzyme","reaction","compound"]) ## These are the default arguments
```

#### Updating KEGG directory with latest entries

*Note: Updating will NOT reflect changes made to invdividual entries' fields, and it will NOT remove entries which have been removed from KEGG. It will only add entries which have been added. To guarantee the most up-to-date KEGG database, a full re-download is necessary.*

```python
import ecg

path = "./kegg"
kegg = ecg.Kegg(path)
kegg.update(metadata=True) ## These are the default arguments

## Built-in public methods
kegg.path;
kegg.version;
kegg.lists;
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
keggdir
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
|- Kegg.version["original"] = dict()
    |-Kegg.version["original"]["release_short"] = float # returns release of database eg. 90.0
    |-Kegg.version["original"]["release_long"] = str # returns 90.0+/06-06, Jun 19
    |-Kegg.version["original"]["count_info"] = dict()
        |-Kegg.version["original"]["count_info"]["pathway"] = int
        |-Kegg.version["original"]["count_info"]["compound"] = int
        |-Kegg.version["original"]["count_info"]["reaction"] = int
        |-Kegg.version["original"]["count_info"]["enzyme"] = int
    |-Kegg.version["original"]["count_lists"] = dict()
        |-Kegg.version["original"]["count_lists"]["pathway"] = int
        |-Kegg.version["original"]["count_lists"]["compound"] = int
        |-Kegg.version["original"]["count_lists"]["reaction"] = int
        |-Kegg.version["original"]["count_lists"]["enzyme"] = int
    |-Kegg.version["original"]["lists"] = dict()
        |-Kegg.version["original"]["lists"]["pathway"] = list()
        |-Kegg.version["original"]["lists"]["compound"] = list()
        |-Kegg.version["original"]["lists"]["reaction"] = list()
        |-Kegg.version["original"]["lists"]["enzyme"] = list()
|- Kegg.version["updates"] = list()
|- Kegg.version["current"]
```