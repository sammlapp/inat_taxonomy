import polars as pl
from pathlib import Path

TAXONOMY = pl.read_parquet("../data/cleaned_taxa.parquet")


def _download_taxonomy(force: bool = False) -> None:
    """
    Download the iNaturalist taxonomy data if it does not exist.
    """
    import os
    import subprocess

    if force or not os.path.exists("../data/inaturalist-taxonomy.dwca/taxa.csv"):
        subprocess.run(["bash", "scripts/download_taxonomy.sh"])


def update_taxonomy() -> None:
    """
    Update the taxonomy data by re-downloading and re-processing the iNaturalist taxonomy data.
    """
    _download_taxonomy(force=True)
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


def list_lexicons(normalize: bool = False) -> list[str]:
    """
    List all available lexicons in the vernacular names data.
    """
    _download_taxonomy()
    lexicon_files = Path("../data/inaturalist-taxonomy.dwca").glob(
        "VernacularNames-*.csv"
    )
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
    # normalize lexicon to lowercase alphanumeric
    lexicon = "".join(filter(str.isalnum, lexicon.lower()))
    assert lexicon in list_lexicons(
        normalize=True
    ), f"Lexicon '{lexicon}' not found. Use list_lexicons() for available lexicons."

    # read vernacular names
    df_vernacular = pl.read_csv(
        f"../data/inaturalist-taxonomy.dwca/VernacularNames-{lexicon}.csv"
    )
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
