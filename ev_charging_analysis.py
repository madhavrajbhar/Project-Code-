"""Beginner-friendly EV Charging Station Analysis.
Run from the project root: python src/ev_charging_analysis.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "26_ev_charging_sessions.csv"
CLEAN_FILE = ROOT / "data" / "processed" / "ev_charging_sessions_clean.csv"
OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)
OUTPUTS.mkdir(parents=True, exist_ok=True)

# Fixed charger categories; set collects distinct location labels.
CHARGER_TYPES = ("Level 1", "Level 2", "DC Fast")


def average_energy_per_station(data):
    """Return average energy delivered per session for each station."""
    return data.groupby("Station_ID")["Energy_kWh"].mean().sort_values(ascending=False)


class ChargingSession:
    """Small demonstration class representing a single charging session."""
    def __init__(self, session_id, station_id, energy_kwh, duration_mins):
        self.session_id = session_id
        self.station_id = station_id
        self.energy_kwh = energy_kwh
        self.duration_mins = duration_mins

    def summary(self):
        return (f"Session {self.session_id} at {self.station_id}: "
                f"{self.energy_kwh:.2f} kWh in {self.duration_mins:.0f} minutes")


def save_bar_chart(series, title, xlabel, ylabel, filename, rotate=0):
    plt.figure(figsize=(10, 5))
    series.plot(kind="bar")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=rotate, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES / filename, dpi=150)
    plt.close()


def main():
    print("EV Charging Station Analysis\n" + "=" * 32)
    df = pd.read_csv(RAW_FILE)
    print(f"Raw dataset: {df.shape[0]} rows x {df.shape[1]} columns")
    print("Columns:", list(df.columns))
    print("\nMissing values before cleaning:\n", df.isna().sum())

    # Data quality: duplicate Session_ID values are exact duplicate records here.
    duplicate_ids = df["Session_ID"].duplicated().sum()
    print(f"\nDuplicate Session_ID rows (beyond first): {duplicate_ids}")
    df = df.drop_duplicates(subset="Session_ID", keep="first").copy()

    df["Charging_Start_Time"] = pd.to_datetime(df["Charging_Start_Time"], errors="coerce")
    # Drop rows without the key metrics/time needed for this descriptive analysis.
    before = len(df)
    df = df.dropna(subset=["Energy_kWh", "Charging_Duration_Mins", "Charging_Start_Time"]).copy()
    print(f"Rows removed for missing energy, duration or invalid timestamp: {before-len(df)}")

    # Guard against physically/analytically invalid negative metrics.
    invalid = (df["Energy_kWh"] < 0) | (df["Charging_Duration_Mins"] <= 0)
    print(f"Rows removed for invalid negative energy/nonpositive duration: {invalid.sum()}")
    df = df.loc[~invalid].copy()

    df["Hour"] = df["Charging_Start_Time"].dt.hour
    df["Weekday"] = df["Charging_Start_Time"].dt.day_name()
    df["Month"] = df["Charging_Start_Time"].dt.month
    df["Duration_Group"] = pd.cut(
        df["Charging_Duration_Mins"],
        bins=[0, 60, 120, 240, np.inf],
        labels=["Up to 1 hour", "1–2 hours", "2–4 hours", "Over 4 hours"],
        right=True,
    )
    df.to_csv(CLEAN_FILE, index=False)
    print(f"Cleaned dataset saved: {CLEAN_FILE.relative_to(ROOT)}")

    # Overall metrics
    metrics = {
        "Sessions after cleaning": len(df),
        "Total energy delivered (kWh)": df["Energy_kWh"].sum(),
        "Average charging duration (mins)": df["Charging_Duration_Mins"].mean(),
        "Average energy per session (kWh)": df["Energy_kWh"].mean(),
    }
    metrics_df = pd.DataFrame(list(metrics.items()), columns=["Metric", "Value"])
    metrics_df.to_csv(OUTPUTS / "overall_metrics.csv", index=False)
    print("\nOverall metrics:")
    print(metrics_df.to_string(index=False))

    # Station rankings
    station_sessions = df.groupby("Station_ID").size().sort_values(ascending=False)
    station_energy = df.groupby("Station_ID")["Energy_kWh"].sum().sort_values(ascending=False)
    station_sessions.rename("Session_Count").to_csv(OUTPUTS / "station_session_counts.csv")
    station_energy.rename("Total_Energy_kWh").to_csv(OUTPUTS / "station_energy_rankings.csv")
    station_avg_energy = average_energy_per_station(df)
    station_avg_energy.rename("Average_Energy_kWh").to_csv(OUTPUTS / "station_average_energy.csv")

    # Comparisons and temporal patterns
    charger_duration = df.groupby("Charger_Type")["Charging_Duration_Mins"].mean().reindex(CHARGER_TYPES)
    charger_duration.dropna().to_csv(OUTPUTS / "average_duration_by_charger.csv")
    location_energy = df.groupby("Station_Location")["Energy_kWh"].sum().sort_values(ascending=False)
    location_energy.to_csv(OUTPUTS / "location_energy_totals.csv")
    hour_sessions = df.groupby("Hour").size().sort_index()
    hour_sessions.to_csv(OUTPUTS / "sessions_by_hour.csv")
    weekday_sessions = df.groupby("Weekday").size().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    weekday_sessions.to_csv(OUTPUTS / "sessions_by_weekday.csv")
    df.groupby("Month").size().sort_index().to_csv(OUTPUTS / "sessions_by_month.csv")

    # NumPy summary statistics and IQR flags (flagging, not automatic removal).
    durations = df["Charging_Duration_Mins"].to_numpy()
    stats = pd.DataFrame({"Statistic": ["Mean", "Median", "90th percentile"],
                          "Minutes": [np.mean(durations), np.median(durations), np.percentile(durations, 90)]})
    stats.to_csv(OUTPUTS / "duration_statistics.csv", index=False)
    q1, q3 = np.percentile(durations, [25, 75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    df["Duration_IQR_Outlier"] = (df["Charging_Duration_Mins"] < lower) | (df["Charging_Duration_Mins"] > upper)
    df[["Session_ID", "Charging_Duration_Mins", "Duration_IQR_Outlier"]].to_csv(OUTPUTS / "duration_iqr_flags.csv", index=False)
    stats.to_csv(OUTPUTS / "duration_statistics.csv", index=False)
    print(f"\nDuration IQR bounds: {lower:.2f} to {upper:.2f} minutes")
    print(f"IQR-flagged durations (not automatically deleted): {df['Duration_IQR_Outlier'].sum()}")

    # Demonstrate required set, dictionary, function and class.
    unique_locations = set(df["Station_Location"].dropna())
    station_count_dict = station_sessions.to_dict()
    print("\nUnique locations (set):", unique_locations)
    print("Station-wise session counts (dictionary sample):", dict(list(station_count_dict.items())[:5]))
    print("Average energy per station (function sample):", station_avg_energy.head().to_dict())
    sample = df.iloc[0]
    session = ChargingSession(sample["Session_ID"], sample["Station_ID"], sample["Energy_kWh"], sample["Charging_Duration_Mins"])
    print("Class demonstration:", session.summary())

    # Figures
    save_bar_chart(station_sessions.head(10), "Top 10 Stations by Session Count", "Station ID", "Sessions", "top_stations_sessions.png", 45)
    save_bar_chart(location_energy, "Energy Delivered by Location", "Location", "Energy (kWh)", "energy_by_location.png", 30)
    save_bar_chart(hour_sessions, "Charging Sessions by Hour", "Hour of day", "Sessions", "sessions_by_hour.png")
    save_bar_chart(charger_duration.dropna(), "Average Duration by Charger Type", "Charger type", "Minutes", "duration_by_charger.png", 20)
    save_bar_chart(weekday_sessions.dropna(), "Sessions by Weekday", "Weekday", "Sessions", "sessions_by_weekday.png", 20)

    # Evidence-based descriptive recommendation prompts (not prescriptive claims).
    peak_hour = int(hour_sessions.idxmax()) if len(hour_sessions) else None
    busiest_day = weekday_sessions.idxmax() if weekday_sessions.notna().any() else None
    top_station = station_sessions.index[0] if len(station_sessions) else "N/A"
    top_location = location_energy.index[0] if len(location_energy) else "N/A"
    recommendations = [
        f"Review staffing/availability planning around the busiest hour identified ({peak_hour}:00), after confirming this pattern over time.",
        f"Review weekday operational planning for the busiest weekday ({busiest_day}), while avoiding assumptions about causation.",
        f"Investigate the station with the most sessions ({top_station}) to understand whether its capacity or service pattern should be reviewed.",
        f"Compare location-level energy use and review the leading location ({top_location}) alongside station capacity and local context.",
        "Use charger-type duration comparisons to inform user guidance and capacity planning; average duration alone does not measure charger performance.",
    ]
    (OUTPUTS / "recommendations.txt").write_text("\n".join("- " + r for r in recommendations), encoding="utf-8")
    print("\nAnalysis complete. See outputs/ and outputs/figures/ for results.")


if __name__ == "__main__":
    main()
