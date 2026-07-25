import polars as pl
import os
import subprocess

# check existence of data files, or download
if not os.path.exists("../data/inaturalist-taxonomy.dwca/taxa.csv"):
    subprocess.run(["bash", "scripts/download_taxonomy.sh"])

# read full taxonomy
df = pl.read_csv("../data/inaturalist-taxonomy.dwca/taxa.csv")

# discard heavy columns with urls and other metadata
df = df[
    [
        "id",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "specificEpithet",
        "infraspecificEpithet",
        "scientificName",
        "taxonRank",
    ]
]
# save efficiently
df.write_parquet("../data/cleaned_taxa.parquet", compression="zstd")
