import pandas as pd
import os

# Set paths
RAW_PATH = "../../data/raw/recipes.csv"
CLEANED_PATH = "data/processed/recipes_cleaned.csv"

# Load the dataset (RecipeId as index if present)
df = pd.read_csv(RAW_PATH, index_col=0)

# Drop rows missing key fields
df = df.dropna(subset=["Name", "RecipeIngredientParts", "RecipeInstructions"])

# Clean and flatten the "list-like" strings
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

# Combine fields for RAG
df["combined"] = df["name"] + " " + df["ingredients"] + " " + df["steps"]

# Select final columns
df_clean = df[["name", "ingredients", "steps", "combined"]].copy()

# Save cleaned dataset
os.makedirs("data/processed", exist_ok=True)
df_clean.to_csv(CLEANED_PATH, index=False)

print("✅ Cleaned dataset saved to:", CLEANED_PATH)