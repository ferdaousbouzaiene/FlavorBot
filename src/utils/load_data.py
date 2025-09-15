import pandas as pd
import os

def load_and_clean_foodcom(
    raw_path="data/raw/recipes.csv",
    save_path="data/processed/recipes_cleaned.csv",
    save=True
):
    """Load and clean Food.com dataset. Returns cleaned DataFrame."""
    df = pd.read_csv(raw_path, index_col=0)

    # Drop rows missing critical fields
    df = df.dropna(subset=["Name", "RecipeIngredientParts", "RecipeInstructions"])

    # Flatten stringified list columns
    def clean_list_column(col):
        return (
            col.astype(str)
            .str.replace("c\\(", "", regex=True)
            .str.replace("\\)", "", regex=True)
            .str.replace('"', "", regex=False)
            .str.replace(",", " ", regex=False)
            .str.replace("'", "", regex=False)
            .str.lower()
        )

    df["ingredients"] = clean_list_column(df["RecipeIngredientParts"])
    df["steps"] = clean_list_column(df["RecipeInstructions"])
    df["name"] = df["Name"].fillna("").str.lower()

    # Combine into a single field for embedding
    df["combined"] = df["name"] + " " + df["ingredients"] + " " + df["steps"]

    # Final cleaned DataFrame
    df_clean = df[["name", "ingredients", "steps", "combined"]].copy()

    if save:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df_clean.to_csv(save_path, index=False)

    return df_clean
