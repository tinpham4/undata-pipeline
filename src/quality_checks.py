def check_duplicates(df):
    duplicate_rows = df.duplicated(
        subset=["area_code", "year", "series"],
        keep=False
    )

    duplicate_count = duplicate_rows.sum()

    print("Duplicate rows:")
    print(duplicate_count)

    if duplicate_count > 0:
        raise ValueError("Duplicate observations found")


def check_missing_values(df):
    required_columns = [
        "area_code",
        "area_name",
        "year",
        "series",
        "value"
    ]

    missing_counts = df[required_columns].isna().sum()

    print("Missing required values:")
    print(missing_counts)

    total_missing = missing_counts.sum()

    if total_missing > 0:
        raise ValueError("Missing required values found")