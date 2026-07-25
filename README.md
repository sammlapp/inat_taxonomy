# iNat Taxonomy for python and polars
Utilities for accessing the iNaturalist taxonomy via polars dataframes

### Install:
```bash
pip install git+https://github.com/sammlapp/inat_taxonomy.git
```

### Usage:
```python

import inat_taxonomy as tax

# common names in any supported language
# (takes first match for each entry)
spanish_names = tax.vernacular_names(['Setophaga fusca','Homo sapiens'],'spanish')

# access the full polars df
tax.TAXONOMY

# check available languages
tax.list_lexicons()

# join taxonomy table with vernacular names
# note that this will create duplicate rows
# since some taxa have multiple vernacular name entries
tax_chinese = tax.add_vernacular_names('chinese-simplified')

# add another language to this same dataframe
table_with_2languages =tax.add_vernacular_names('czech',tax_chinese)

# look up higher taxonomic levels
family = tax.sp_to_level(['Setophaga fusca','Homo sapiens'], 'family')

# get scientific and common names of bird species
import polars as pl
bird_names = tax.add_vernacular_names('english').filter(pl.col('class').eq('Aves'),pl.col('taxonRank').eq('species')).select(['scientificName','vernacularName_english'])
```