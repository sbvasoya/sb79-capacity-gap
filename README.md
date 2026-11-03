# How Much Will Actually Get Built? SB 79's Housing Capacity Gap Near Transit

**CYPLAN 101, Group 27, MTC Project 3**<br>
Rohan Kosalge, Abhishek Dandekar, Bhairavi Senthilkumar, Suhani Vasoya

## Research question
Within SB 79 Transit-Oriented Development zones in Alameda and Santa Clara Counties, how much housing capacity does SB 79 permit, how is that capacity distributed relative to transit service quality and Equity Priority Community status, and how does historical development near these stops inform the gap between legally allowed and likely-built housing?

## Status (midterm check-in, Oct 2026)
- [x] Project proposal
- [x] Data Preparation and Analysis (`notebooks/data_cleaning.ipynb`, `notebooks/eda.ipynb`)
- [ ] Net capacity (subtract existing units, ineligible zoning)
- [ ] Equity Priority Community overlay
- [ ] Santa Clara County case-study city
- [ ] GTFS transit-quality index
- [ ] HCD APR historical build-out baseline

## Method (so far)
1. MTC SB 79 TOD zones → tier (1/2) and distance band (200 ft / ¼ mi / ½ mi)
2. Alameda County parcels → reprojected to EPSG:26910, parcel acreage computed
3. Parcel centroid spatial join to TOD zones (highest standard kept on overlap)
4. Gross capacity = acres × SB 79 density floor

| Tier | 200 ft | ¼ mile | ½ mile |
|---|---|---|---|
| Tier 1 | 160 du/ac | 120 du/ac | 100 du/ac |
| Tier 2 | 140 du/ac | 100 du/ac | 80 du/ac |

## Data sources

| Dataset | Source |
|---|---|
| SB 79 TOD stops & zones | [MTC SB 79 Regional Map](https://mtc.ca.gov/planning/land-use/senate-bill-79-regional-map) [`raw_data/tod_zones.geojson`]|
| Alameda County parcels | [data.acgov.org](https://data.acgov.org) – Alameda County Parcel Boundaries [`raw_data/parcels.geojson`]|
| Equity Priority Communities | [MTC EPCs](https://www.mtc.ca.gov/planning/transportation/access-equity-mobility/equity-priority-communities) [`raw_data/epc_data.geojson`]|
| 511 Regional GTFS | *plan to use between Midterm and Final Deadlines* |
| Housing Element APR, Table A2 | *plan to use between Midterm and Final Deadlines* |

## Repo structure
```
data/raw/         # raw data from the sources linked above
data/processed/  # data post-processing (filtering, spatial joins, etc.)
notebooks/       # analysis notebooks, numbered in order
visualizations/  # maps and tables

```

## How to run
Open a notebook in Google Colab (File → Upload notebook), upload the data files via the folder panel, and run all cells.
