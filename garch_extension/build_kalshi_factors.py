from pathlib import Path
import numpy as np
import pandas as pd
import hashlib, json

def normalized_entropy(probabilities):
    p = np.asarray(probabilities, dtype=float)
    p = p[np.isfinite(p) & (p > 0)]
    if p.size <= 1:
        return 0.0
    p = p / p.sum()
    return float(-(p * np.log(p)).sum() / np.log(p.size))

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def build_factors(
    moments_csv,
    distributions_csv,
    calendar_csv,
    output_csv,
    manifest_json,
    start_rel_day=-30,
    end_rel_day=-3,
):
    moments = pd.read_csv(moments_csv)
    dist = pd.read_csv(distributions_csv)
    cal = pd.read_csv(calendar_csv)

    moments["date"] = pd.to_datetime(moments["date"])
    dist["date"] = pd.to_datetime(dist["date"])
    cal["meeting_date"] = pd.to_datetime(cal["meeting_date"])

    entropy = (
        dist.groupby(["contract_preamble", "date"])["probability"]
        .apply(normalized_entropy)
        .rename("normalized_entropy")
        .reset_index()
    )

    daily = moments.merge(entropy, on=["contract_preamble", "date"], how="left")
    daily = daily.merge(cal, on="contract_preamble", how="inner")
    daily["rel_day"] = (daily["date"] - daily["meeting_date"]).dt.days

    window = daily[
        daily["rel_day"].between(start_rel_day, end_rel_day, inclusive="both")
    ].copy()

    factors = (
        window.groupby(["contract_preamble", "meeting_date"])
        .agg(
            kalshi_var_28d_mean=("variance", "mean"),
            kalshi_entropy_28d_mean=("normalized_entropy", "mean"),
            kalshi_volume_28d_mean=("daily_volume", "mean"),
            kalshi_window_obs=("date", "nunique"),
            kalshi_first_rel_day=("rel_day", "min"),
            kalshi_last_rel_day=("rel_day", "max"),
        )
        .reset_index()
    )

    snap = (
        daily.assign(abs_to_m28=(daily["rel_day"] + 28).abs())
        .sort_values(["contract_preamble", "abs_to_m28", "date"])
        .groupby("contract_preamble", as_index=False)
        .first()[
            ["contract_preamble", "variance", "normalized_entropy", "rel_day"]
        ]
        .rename(
            columns={
                "variance": "kalshi_var_m28_snapshot",
                "normalized_entropy": "kalshi_entropy_m28_snapshot",
                "rel_day": "kalshi_snapshot_rel_day",
            }
        )
    )
    factors = factors.merge(snap, on="contract_preamble", how="left")

    for col in ["kalshi_var_28d_mean", "kalshi_entropy_28d_mean"]:
        sd = factors[col].std(ddof=1)
        factors[col + "_z"] = (factors[col] - factors[col].mean()) / sd

    factors["meeting_date"] = factors["meeting_date"].dt.strftime("%Y-%m-%d")
    factors.to_csv(output_csv, index=False)

    manifest = {
        "source_moments": str(moments_csv),
        "source_distributions": str(distributions_csv),
        "calendar": str(calendar_csv),
        "moments_sha256": sha256_file(moments_csv),
        "distributions_sha256": sha256_file(distributions_csv),
        "calendar_sha256": sha256_file(calendar_csv),
        "output_sha256": sha256_file(output_csv),
        "window": {"start_rel_day": start_rel_day, "end_rel_day": end_rel_day},
        "meetings": int(len(factors)),
        "minimum_window_observations": int(factors["kalshi_window_obs"].min()),
        "maximum_window_observations": int(factors["kalshi_window_obs"].max()),
    }
    Path(manifest_json).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return factors

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--moments", required=True)
    p.add_argument("--distributions", required=True)
    p.add_argument("--calendar", default="garch_extension/data/fomc_contract_calendar.csv")
    p.add_argument("--output", default="garch_extension/data/kalshi_fomc_factors.csv")
    p.add_argument("--manifest", default="garch_extension/data/source_manifest.json")
    args = p.parse_args()
    f = build_factors(
        args.moments, args.distributions, args.calendar, args.output, args.manifest
    )
    print(f.to_string(index=False))
