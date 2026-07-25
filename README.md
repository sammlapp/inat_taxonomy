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

### Releasing a new version to PyPI:

1. Bump `version` in `pyproject.toml` (PyPI rejects re-uploading an existing version number).
2. Build the distribution:
   ```bash
   python -m pip install --upgrade build twine
   rm -rf dist build *.egg-info
   python -m build
   ```
3. Check the build:
   ```bash
   twine check dist/*
   ```
4. (Optional) upload to TestPyPI first to verify install works:
   ```bash
   twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ inat_taxonomy
   ```
5. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

Both `twine upload` commands prompt for credentials — use `__token__` as the username and a PyPI API token (from Account Settings → API tokens) as the password. To avoid retyping, save tokens in `~/.pypirc`:
```ini
[pypi]
  username = __token__
  password = pypi-...your-token...

[testpypi]
  username = __token__
  password = pypi-...your-testpypi-token...
```