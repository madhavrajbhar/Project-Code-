# EV Charging Station Analysis

**Student project:** Madhav Rajbhar · B.Tech · CSE  
**Admission number:** 2026B01010120

A beginner Python data-analysis project exploring electric-vehicle charging sessions: usage patterns, station rankings, charging duration, energy delivered, charger types and locations.

## Dataset

The supplied CSV has **862 rows and 8 columns**. It contains 12 duplicate Session_ID records (duplicate IDs beyond the first), and missing values in Energy_kWh and Charging_Duration_Mins. The analysis documents these issues and saves a cleaned version. Dataset source/provider should be added if known; do not assume the records represent real-world operations.

## Questions

- How many sessions and how much energy remain after cleaning?
- What are average charging duration and energy per session?
- Which stations rank highest by sessions and energy?
- What hours and weekdays are busiest?
- How do duration and energy patterns differ by charger type and location?
- What duration values are flagged by the IQR method?

## Folder structure

```text
ev-charging-station-analysis/
├── data/
│   ├── raw/26_ev_charging_sessions.csv
│   └── processed/ev_charging_sessions_clean.csv  # created on run
├── src/ev_charging_analysis.py
├── outputs/                                    # tables and charts created on run
├── requirements.txt
└── README.md
```

## Run the analysis

1. Install Python 3 and open a terminal in this project folder.
2. (Optional) create and activate a virtual environment.
3. Install packages:

   ```bash
   pip install -r requirements.txt
   ```
4. Run:

   ```bash
   python src/ev_charging_analysis.py
   ```

The script saves a cleaned CSV, metric and comparison tables, IQR flags, a recommendations text file, and PNG charts in `outputs/`.

## Cleaning choices

- Keep the first record for each Session_ID to remove duplicate IDs.
- Convert Charging_Start_Time to datetime.
- Drop records missing energy, duration or a valid timestamp for this descriptive analysis.
- Remove records with negative energy or nonpositive duration.
- IQR flags are reported separately; they are not automatically removed.

## Limitations

This is descriptive analysis of the supplied dataset. The dataset's provenance is not verified, and patterns should not be generalised to actual charging networks without context. Correlation or descriptive differences do not prove causes. Recommendations are prompts for further investigation, not operational instructions.
