import os
import pandas as pd

from quality_checks import check_duplicates, check_missing_values

file_path = "data/raw/SYB68_2025/population.csv"

df = pd.read_csv(
    file_path,
    skiprows=1,
    encoding="cp1252"
)

df = df.rename(
    columns={
        "Region/Country/Area": "area_code",
        "Unnamed: 1": "area_name",
        "Year": "year",
        "Series": "series",
        "Value": "value",
        "Footnotes": "footnotes",
        "Source": "source"
    }
)

df["area_code"] = df["area_code"].astype("string").str.zfill(3)

df["value"] = df["value"].str.replace(",", "")
df["value"] = pd.to_numeric(df["value"])

series_parts = df["series"].str.rsplit(" (", n=1, expand=True)

df["series_name"] = series_parts[0]
df["unit"] = series_parts[1].str.rstrip(")")

df["topic"] = "population"
df["edition"] = "SYB68_2025"

check_duplicates(df)
check_missing_values(df)

output_folder = "data/cleaned/SYB68_2025"

os.makedirs(
    output_folder,
    exist_ok=True
)

output_path = output_folder + "/population.csv"

df.to_csv(
    output_path,
    index=False
)

print("Cleaned file saved to:")
print(output_path)