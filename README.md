# iNat Taxonomy for python and polars
Utilities for accessing the iNaturalist taxonomy via polars dataframes

### Usage:
```python

import inat_taxonomy as tax

# access the full polars df
tax.TAXONOMY

# check available languages
tax.list_lexicons()

# join taxonomy table with vernacular names
# note that this will create duplicate rows
# since some taxa have multiple vernacular name entries
tax.add_vernacular_names('spanish')

# look up higher taxonomic levels
family = tax.sp_to_level(['Setophaga fusca','Homo sapiens'], 'family')

```