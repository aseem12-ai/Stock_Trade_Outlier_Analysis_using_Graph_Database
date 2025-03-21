import numpy as np


def compute_guideline_deviation(df):
    """
    Identifies trades deviating from expected guidelines based on volume and return thresholds.

    - Volume is considered normal if within the 25th to 75th percentile.
    - Return is considered normal if within mean ± 2 standard deviations.

    Flags trades that fall outside these ranges.
    """
    volume_bounds = np.percentile(df["Volume"], [5, 95])
    return_mean, return_std = df["Return"].mean(), df["Return"].std()
    return_bounds = (return_mean - 2 * return_std, return_mean + 2 * return_std)

    df["deviates_guideline"] = df.apply(
        lambda row: not (volume_bounds[0] <= row["Volume"] <= volume_bounds[1]) or
                    not (return_bounds[0] <= row["Return"] <= return_bounds[1]),
        axis=1
    )
    return df
