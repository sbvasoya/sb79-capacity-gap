# How Much Will Actually Get Built? SB 79's Housing Capacity Gap Near Transit

**CYPLAN 101, Group 27, MTC Project 3**<br>
Rohan Kosalge, Abhishek Dandekar, Bhairavi Senthilkumar, Suhani Vasoya

## Research question
Within SB 79 Transit-Oriented Development (TOD) zones in Alameda and Santa Clara Counties, how much legal housing capacity does SB 79 create? How is that capacity distributed across transit tiers and MTC Equity Priority Communities (EPCs)? And what share of it sits on parcels with characteristics associated with near-term redevelopment (soft-site capacity), indicating where realistic yield is likely to concentrate?

We distinguish **capacity** (units SB 79 legally allows) from **yield** (units likely to be built). Soft-site capacity is a first yield indicator, not a forecast.

## Status (midterm, Nov 2026)
- [x] Project proposal
- [x] County-wide pipeline for Alameda County in EPSG:3310 (`notebooks/01_data_cleaning.ipynb`)
- [x] Gross SB 79 capacity by tier and distance band
- [x] Equity Priority Community overlay
- [x] Soft-site and recent-activity indicators
- [x] Exploratory charts (`notebooks/02_eda.ipynb`)
- [ ] Santa Clara County parcels, same pipeline (`src/capacity.py`)
- [ ] Net capacity (subtract existing units)
- [ ] Soft-site threshold sensitivity (0.3 / 0.5 / 1.0)
- [ ] Station-area summary and four typologies (Tier 1/2 × EPC/non-EPC)
- [ ] *Stretch:* HCD APR Table A2 permits (2018–2025) as a historical baseline

Set aside for now: the 511 GTFS service-frequency index (the SB 79 tier stands in for transit quality).

## Method
1. **Load.** Read MTC SB 79 TOD zones and EPC tracts. Read Alameda County parcels using the union of TOD zones as a spatial mask (the parcel file is >1 GB), keeping `APN`, `UseCode`, `Land`, `Imps`, `LatestDocu`, `SitusCity`. Reproject everything to **EPSG:3310** (California Albers).
2. **Filter parcels.**
   - Drop duplicate geometries and parcels with zero land *and* improvement value (exempt / public land): 71,742 → 50,157
   - Drop ineligible use codes (industrial, institutional, condos/co-ops, deed-restricted affordable and a few specific codes): 50,157 → 47,512
   - Keep only Alameda (FIPS 001) and Santa Clara (FIPS 085) EPC tracts: 353 → 170
3. **Join to TOD zones.** Each parcel's representative point is joined to the TOD zones (`within`). Where zones overlap, the most permissive density is kept.
4. **Gross capacity** = floor(acres × SB 79 density standard). Parcels with fewer than 5 allowed units are dropped (SB 79 minimum project size).

   | Tier | 200 ft | ¼ mile | ½ mile |
   |---|---|---|---|
   | Tier 1 | 160 du/ac | 120 du/ac | 100 du/ac |
   | Tier 2 | 140 du/ac | 100 du/ac | 80 du/ac |

5. **EPC overlay.** Each TOD parcel's representative point is joined to EPC tracts, giving `epc_class` (Not EPC / High / Higher / Highest) and `is_epc`.
6. **Yield indicators.**
   - `soft_site`: improvement value < 50% of land value
   - `recent_activity`: latest recorded document in 2016 or later

Output: `data/processed/parcels_tod_clean.parquet`.

## Early results (Alameda County)
- **43,130** eligible parcels in TOD zones, with **688,068** allowed units in total (Tier 1: 473,262; Tier 2: 214,806). About half the parcels (50.3%) fall in an EPC.
- Most capacity sits in the ½-mile bands rather than next to stations.
- EPC capacity leans much more on Tier 2 than non-EPC capacity does. Tier 2's share of allowed units is 11% outside EPCs, 47% in High, 76% in Higher and 64% in Highest EPCs.
- Only **12.9%** of allowed units sit on soft sites. The share is lower in EPCs: 15.0% outside EPCs, 13.6% in High, 7.1% in Higher and 8.5% in Highest.

## Data sources

| Dataset | Source | File |
|---|---|---|
| SB 79 TOD zones | [MTC Open Data – Senate Bill 79 TOD Zones](https://opendata.mtc.ca.gov/datasets/ff3aca5ea60145c0ad677edbbf3f896f_1/explore) | `data/raw/tod_zones.geojson` |
| Alameda County parcels | [Alameda County Open Data – Parcels](https://data.acgov.org/datasets/2b026350b5dd40b18ed7a321fdcdba81_0/explore) | `data/raw/parcels.geojson` |
| Equity Priority Communities | [MTC Open Data – EPCs, Plan Bay Area 2050 Plus (ACS 2018–2022)](https://opendata.mtc.ca.gov/datasets/1ae2ccc15b4a4fe9a6d0cd84ae47f2a5_0/explore) | `data/raw/epc_data.geojson` |
| HCD APR Table A2 | *stretch goal for the final* | – |

Raw files are stored with **Git LFS**. Run `git lfs install` before cloning, or `git lfs pull` afterwards, to get the real files instead of pointer stubs.

## Repo structure
```
data/raw/              # raw data (Git LFS)
data/processed/        # parcels_tod.parquet (masked parcels), parcels_tod_clean.parquet (final)
notebooks/             # 01_data_cleaning.ipynb → 02_eda.ipynb
visualizations/charts/ # EDA charts
visualizations/maps/   # county-wide map
Group_27_midterm.pdf   # midterm report
```

## How to run
1. Clone with Git LFS (see above) and install dependencies: `pip install -r requirements.txt`
2. Run `notebooks/01_data_cleaning.ipynb`, then `notebooks/02_eda.ipynb`, from inside `notebooks/`.

Loading the full parcel file takes a few minutes. To skip it, start from `data/processed/parcels_tod.parquet`.
