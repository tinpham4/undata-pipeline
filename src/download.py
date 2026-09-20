import requests

url = "https://data.un.org/_Docs/SYB/CSV/SYB68_1_202511_Population%2C%20Surface%20Area%20and%20Density.csv"

response = requests.get(url)

response.raise_for_status()

file_path = "data/raw/SYB68_2025/population.csv"

with open(file_path, "wb") as file:
    file.write(response.content)