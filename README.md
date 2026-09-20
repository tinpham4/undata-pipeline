# UNdata Data Engineering Pipeline

## About this project

I am a data science undergraduate teaching myself data engineering by building a real pipeline instead of just reading about one.

The data comes from UNdata, which is the United Nations statistics portal. The files I am using are from the Statistical Yearbook, and they hold country level numbers like population, surface area, and density.

The goal is a pipeline that downloads those files, cleans them, checks them for problems, and eventually loads them into a cloud warehouse where they can be queried with SQL.

Right now only the local Python part is finished. Everything involving PostgreSQL, AWS, and Snowflake is still planned, and I mark it that way all through this README so nobody has to guess what actually runs today.

Status at a glance:

* Python downloader: working
* Python cleaning: working
* Data quality checks: working, two checks so far
* M49 area code validation: not started
* PostgreSQL warehouse tables: not started
* AWS S3 storage: not started
* Snowflake loading and star schema: not started

## Data source

The files come from the UNdata homepage at data.un.org, under the popular statistical tables section. Each table is offered as a PDF or a CSV, and I use the CSV.

The dataset I am working with right now is the population file from the 68th edition of the Statistical Yearbook, which covers population estimates, surface area, and density.

These files are in what is called long format. That means each row is one measurement instead of one country. A single country shows up many times, once for every year and every statistic. Here is the idea:

```
area_code   area_name      year   series                                    value
004         Afghanistan    2020   Population mid year estimates (millions)  38.97
004         Afghanistan    2020   Population density                        59.7
840         United States  2020   Population mid year estimates (millions)  335.94
```

One more thing worth knowing: the files mix countries with totals. Rows for World, Africa, and other regions sit in the same column as real countries. Handling that properly is part of my next step.

## Current pipeline

This is what runs today, all on my laptop:

```
UNdata
  ↓
Python downloader (download.py)
  ↓
Local raw CSV (untouched)
  ↓
Python cleaning (clean.py)
  ↓
Data quality checks (quality_checks.py)
  ↓
Local cleaned CSV
```

Nothing is in the cloud yet. That is on purpose, and I explain why near the bottom.

## Project structure

```
undata pipeline/
    data/
        raw/
            SYB68_2025/
                population.csv
        cleaned/
            SYB68_2025/
                population.csv
    src/
        download.py
        clean.py
        quality_checks.py
    .gitignore
    README.md
```

The folders are split by stage and then by edition. Raw holds the file exactly as UNdata published it. Cleaned holds my processed version. The edition folder name, SYB68_2025, means the 68th edition of the Statistical Yearbook, so when next year's edition comes out it gets its own folder instead of writing over this one.

## Downloading the data

`download.py` uses the requests library to pull the CSV straight from UNdata and save it here:

```
data/raw/SYB68_2025/population.csv
```

I download it with code instead of clicking the link myself so the whole thing can be repeated and so somebody reading my repo can see exactly where the data came from.

The raw file is never edited. If my cleaning code has a bug, I want to be able to go back to the original file and start over without downloading it again. Keeping the source data untouched is a habit I picked up from reading about how real pipelines are built.

## Cleaning the data

`clean.py` reads the raw file with pandas and fixes the messy parts. The UNdata files are published for people to read, not for computers to load, so there is a fair amount to deal with.

**The header is on the wrong line.** The first line of the file is the dataset title, not the column names, so the script skips that first row and uses the second one as the header.

**The encoding is not UTF 8.** These files need cp1252 encoding. Without it, country names with accented letters fail to read.

**The column names are awkward.** The country name column has no header at all, so pandas calls it `Unnamed: 1`. I rename everything to simple names:

```
Region/Country/Area  →  area_code
Unnamed: 1           →  area_name
Year                 →  year
Series               →  series
Value                →  value
Footnotes            →  footnotes
Source               →  source
```

**Area codes lose their leading zeros.** The codes are official United Nations M49 codes, and some of them start with a zero. Pandas reads them as numbers, so 004 turns into 4. I convert the column to text and pad it back to three digits:

```
1  becomes  001
4  becomes  004
```

**Numbers are stored as text with commas.** A value shows up as `7,021.73`, which pandas treats as a string, so I cannot add or average it. The script strips the commas and converts the column to a numeric type:

```
"7,021.73"  becomes  7021.73
```

**The series column holds two pieces of information.** It contains the name of the statistic and its unit, stuck together. I split them into two columns:

```
Population mid year estimates (millions)
    series_name = Population mid year estimates
    unit        = millions

Surface area (thousand km2)
    series_name = Surface area
    unit        = thousand km2
```

Population density has no unit in the source file, so its unit stays empty rather than being made up.

I also keep the original series column. That way I can always compare my cleaned version back to the source, which has already saved me when I was not sure whether a split went right.

Finally the script adds two columns of its own:

```
topic    = population
edition  = SYB68_2025
```

Those exist because more datasets are coming. Once GDP and emissions files are in here too, `topic` tells me which table a row came from, and `edition` tells me which yearly release it came from. That matters later when a new edition revises an old number.

The result is saved to:

```
data/cleaned/SYB68_2025/population.csv
```

## Data quality checks

`quality_checks.py` runs after cleaning. It has two checks right now, and both stop the program with an error if they fail. I would rather the pipeline break loudly than quietly save a bad file.

**Duplicate check.** One observation should be unique for a combination of:

```
area_code
year
series
```

If the same country, year, and statistic appears twice, something went wrong, either in the source file or in my cleaning. The pipeline stops so I can look at it.

**Missing value check.** These columns are required and cannot be empty:

```
area_code
area_name
year
series
value
```

`footnotes` and `unit` are allowed to be empty, because plenty of rows legitimately have neither.

Current results on the population file:

```
Duplicate rows     = 0
Missing area_code  = 0
Missing area_name  = 0
Missing year       = 0
Missing series     = 0
Missing value      = 0
```

## What each Python file does

`download.py`
Downloads the UNdata population CSV with requests and saves it to the raw folder without changing anything.

`clean.py`
Reads the raw CSV, skips the title line, uses cp1252 encoding, renames the columns, pads the area codes, converts the values to numbers, splits the series into a name and a unit, adds topic and edition, and writes the cleaned CSV.

`quality_checks.py`
Checks the cleaned file for duplicate observations and missing required values, and raises an error if it finds either.

## What I learned so far

Most of my time went to the data itself rather than to clever code, which surprised me.

* Real published data is built for humans. Title rows, blank headers, and numbers with commas are normal, not rare.
* Encoding is a real thing. I hit an error on accented country names before I figured out the file needed cp1252.
* Text that looks like a number is not a number. Nothing worked until I stripped the commas and converted the column.
* Leading zeros disappear if you let a code column be read as a number, and area codes are codes, not quantities.
* Checks are worth writing early. Both of mine pass right now, but I want them in place before I add four more datasets, because that is when problems will show up.
* Keeping the raw file untouched means a mistake in my cleaning code costs me a rerun instead of a redownload.

## Next steps

**1. M49 area code validation.** Every area code in the file should be a real United Nations M49 code. My first version will be a CSV I maintain by hand with the valid codes, their names, and their region, plus a flag for whether the row is a country or an aggregate like World or Africa. The pipeline will check the file against that list and flag anything unknown.

**2. More datasets.** GDP, carbon dioxide emissions, internet usage, and education. They share the same layout as the population file, so the point is to build one reusable loader that handles all of them instead of writing five separate scripts.

**3. The warehouse tables**, locally in PostgreSQL first.

**4. AWS S3 and Snowflake** last.

## Planned PostgreSQL warehouse

Status: not started.

Once a few datasets are cleaned, I want them in database tables instead of CSV files. The plan is a star schema, which means one big table of measurements surrounded by smaller tables that describe them.

```
dim_area
    M49 code, area name, region, and whether the area is an aggregate

dim_series
    series name, unit, and topic

fact_observation
    area, series, year, value, footnote, source, and edition
```

`fact_observation` is the big one, with a row for each country, year, and statistic. The two dim tables hold the descriptions, so country names and units are stored once instead of repeated on every row.

I am using PostgreSQL 15 or newer because it supports the MERGE command, which is the same command I will use in Snowflake later. That way I can practice the hard part locally.

## Planned AWS and Snowflake setup

Status: not started.

The plan:

* AWS S3 stores both the raw and the cleaned files, with a folder for each edition, the same layout I use locally.
* Snowflake reads the cleaned files from S3 using an external stage, which is basically a pointer from Snowflake to my S3 folder, and loads them with COPY INTO.
* SQL in Snowflake builds the same star schema described above.
* The final load uses MERGE so that rerunning it is safe.

I also plan to write a few analysis queries and draw an architecture diagram once the pipeline is actually running end to end.

## Idempotency

This is the one bit of jargon I want to be able to explain out loud, because it is the whole reason the warehouse load uses MERGE.

Idempotent means running something twice gives the same result as running it once. For this project that means three things:

* If I load the same file again, nothing is duplicated.
* If a newer edition revises a number, the existing row updates instead of a second copy appearing.
* If a new year, country, or statistic shows up, it gets added.

That matters here because UNdata publishes a new edition roughly once a year, and each edition repeats older years while sometimes revising them. Without this, a second load would double my data.

## Why I am building this project

I want a data engineering project that is honest about where the data came from and what happens to it, instead of a notebook that loads a clean Kaggle file.

I am also building it locally before touching the cloud, on purpose, for two reasons:

First, learning one thing at a time. If I tried to learn pandas cleaning, IAM permissions, S3, and Snowflake all at once, I would not know which part broke when something failed.

Second, the Snowflake trial is 30 days. Once the clock starts, it keeps running whether my code works or not, and when the trial ends the data gets deleted. So I would rather show up with working code and spend those 30 days loading and querying than spend them debugging pandas.

## Technologies

Working now:

* Python
* pandas
* requests
* Git and GitHub
* VS Code

Planned:

* PostgreSQL
* AWS S3
* Snowflake
* SQL for the star schema and MERGE loads
