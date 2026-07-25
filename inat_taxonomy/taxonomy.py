import polars as pl
from pathlib import Path
from platformdirs import user_cache_dir

_PACKAGE_DATA_DIR = Path(__file__).parent / "data"
_BUNDLED_PARQUET = _PACKAGE_DATA_DIR / "cleaned_taxa.parquet"

_CACHE_DIR = Path(user_cache_dir("inat_taxonomy"))
_DWCA_DIR = _CACHE_DIR / "inaturalist-taxonomy.dwca"
_DWCA_ZIP_URL = "https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip"

TAXONOMY = pl.read_parquet(_BUNDLED_PARQUET)


def _download_taxonomy(force: bool = False) -> None:
    """
    Download the full iNaturalist taxonomy DWCA archive (used for vernacular
    names and re-generating the cleaned taxonomy) into the user cache
    directory, if it does not already exist.
    """
    import shutil
    import urllib.request
    import zipfile

    if not force and (_DWCA_DIR / "taxa.csv").exists():
        return

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if _DWCA_DIR.exists():
        shutil.rmtree(_DWCA_DIR)

    zip_path = _CACHE_DIR / "inaturalist-taxonomy.dwca.zip"
    urllib.request.urlretrieve(_DWCA_ZIP_URL, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(_DWCA_DIR)
    zip_path.unlink()


def update_taxonomy() -> None:
    """
    Update the taxonomy data by re-downloading and re-processing the iNaturalist taxonomy data.

    This overwrites the bundled taxonomy data used for the module-level
    TAXONOMY dataframe in the currently installed package.
    """
    global TAXONOMY

    _download_taxonomy(force=True)
    # read full taxonomy
    df = pl.read_csv(_DWCA_DIR / "taxa.csv")

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
    df.write_parquet(_BUNDLED_PARQUET, compression="zstd")
    TAXONOMY = df


def list_lexicons(normalize: bool = False) -> list[str]:
    """
    List all available lexicons in the vernacular names data.
    """
    _download_taxonomy()
    lexicon_files = _DWCA_DIR.glob("VernacularNames-*.csv")
    lexicons = [Path(f).stem.replace("VernacularNames-", "") for f in lexicon_files]
    if normalize:
        lexicons = [
            "".join(filter(str.isalnum, lexicon.lower())) for lexicon in lexicons
        ]
    return lexicons


def add_vernacular_names(lexicon: str, taxonomy: pl.DataFrame = None) -> pl.DataFrame:
    """
    Add vernacular names to the taxonomy dataframe for a given lexicon.

    Can result in multiple entries per species!

    uses the taxonomy dataframe if provided, otherwise uses the global TAXONOMY dataframe.

    Args:
        lexicon (str): The lexicon (language) to add vernacular names from.
        Check available lexicons with list_lexicons().

        taxonomy (pl.DataFrame, optional): The taxonomy dataframe to add
        vernacular names to, containing an 'id' column for species id. If None,
        uses the global TAXONOMY dataframe.

    Returns:
        pl.DataFrame: The taxonomy dataframe with an additional column for
        vernacular names from the specified lexicon.

    """
    _download_taxonomy()

    # normalize lexicon to lowercase alphanumeric
    lexicon = "".join(filter(str.isalnum, lexicon.lower()))
    assert lexicon in list_lexicons(
        normalize=True
    ), f"Lexicon '{lexicon}' not found. Use list_lexicons() for available lexicons."

    # read vernacular names
    df_vernacular = pl.read_csv(_DWCA_DIR / f"VernacularNames-{lexicon}.csv")
    # select relevant columns
    df_vernacular = df_vernacular.select(["id", "vernacularName"])

    # rename column to include lexicon name
    df_vernacular = df_vernacular.rename(
        {"vernacularName": f"vernacularName_{lexicon}"}
    )

    # join with taxonomy
    if taxonomy is None:
        taxonomy = TAXONOMY
    df_with_names = taxonomy.join(
        df_vernacular, left_on="id", right_on="id", how="left"
    )

    return df_with_names


# efficient helper functions to convert between id, scientificName, genus, family, order, class, phylum, kingdom
def id_to_sp(taxon_id: list[int], level: str = "species") -> str:
    """
    Get scientific names from a list of taxon ids, only at the selected level
    """
    return (
        pl.DataFrame({"id": taxon_id})
        .join(
            TAXONOMY.filter(pl.col("taxonRank") == level),
            left_on="id",
            right_on="id",
            how="left",
        )
        .get_column("scientificName")
        .to_list()
    )


def sp_to_id(scientific_names: list[str], level: str = "species") -> str:
    """
    Get taxon ids from a list of scientific names.
    """
    return (
        pl.DataFrame({"scientificName": scientific_names})
        .join(
            TAXONOMY.filter(pl.col("taxonRank") == level),
            left_on="scientificName",
            right_on="scientificName",
            how="left",
        )
        .get_column("id")
        .to_list()
    )


def id_to_level(taxon_id: list[int], level: str) -> str:
    """
    Get taxon names at a specified level from a list of taxon ids.

    Args:
        taxon_id (list[int]): List of taxon ids.
        level (str): Taxonomic level to retrieve. Must be one of
            'genus', 'family', 'order', 'class', 'phylum', or 'kingdom'.

    Returns:
        list[str]: List of taxon names at the specified level.
    """
    assert level in [
        "genus",
        "family",
        "order",
        "class",
        "phylum",
        "kingdom",
    ], f"Level '{level}' not recognized. Must be one of 'genus', 'family', 'order', 'class', 'phylum', or 'kingdom'."

    return (
        pl.DataFrame({"id": taxon_id})
        .join(TAXONOMY.select(["id", level]), left_on="id", right_on="id", how="left")
        .get_column(level)
        .to_list()
    )


def sp_to_level(scientific_names: list[str], level: str) -> str:
    """
    Get taxon names at a specified level from a list of scientific names.

    Args:
        scientific_names (list[str]): List of scientific names.
        level (str): Taxonomic level to retrieve. Must be one of
            'genus', 'family', 'order', 'class', 'phylum', or 'kingdom'.

    Returns:
        list[str]: List of taxon names at the specified level.
    """
    assert level in [
        "genus",
        "family",
        "order",
        "class",
        "phylum",
        "kingdom",
    ], f"Level '{level}' not recognized. Must be one of 'genus', 'family', 'order', 'class', 'phylum', or 'kingdom'."

    return (
        pl.DataFrame({"scientificName": scientific_names})
        .join(
            TAXONOMY.select(["scientificName", level]),
            left_on="scientificName",
            right_on="scientificName",
            how="left",
        )
        .get_column(level)
        .to_list()
    )
