import pandas as pd
import numpy as np


def load_and_clean_data(csv_file):
    """
    Load CSV data, convert date column, remove duplicates, and filter out zero-volume entries.
    """
    data = pd.read_csv(csv_file)

    # Convert 'Gmt time' column to datetime format
    data['Gmt time'] = pd.to_datetime(data['Gmt time'], format='%d.%m.%Y %H:%M:%S.%f', dayfirst=True)

    # Remove duplicate rows
    data.drop_duplicates(inplace=True)

    # Convert numeric columns to float
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    data[numeric_cols] = data[numeric_cols].apply(pd.to_numeric, errors='coerce')

    # Remove rows with zero or NaN volume
    data = data[data['Volume'] > 0].dropna()

    return data


def detect_outliers(data, threshold=3):
    """
    Compute daily returns, calculate Z-scores, and flag outliers.
    """
    # Calculate daily percentage return
    data['Return'] = data['Close'].pct_change()

    # Drop NaN values after computing return
    data.dropna(subset=['Return'], inplace=True)

    # Compute mean and standard deviation
    mean_return, std_return = np.mean(data['Return']), np.std(data['Return'])

    # Calculate Z-score
    data['z_score'] = (data['Return'] - mean_return) / (std_return + 1e-6)  # Avoid division by zero

    # Flag outliers based on threshold
    data['is_outlier'] = data['z_score'].abs() > threshold

    return data
