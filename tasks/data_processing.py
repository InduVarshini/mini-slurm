#!/usr/bin/env python3
"""
Heavy data processing and transformation pipeline.
Simulates ETL operations, data cleaning, and feature engineering.
"""
import numpy as np
import time
import os

def process_large_dataset(num_rows=10_000_000, num_features=100):
    """Process a large dataset with various transformations."""
    print(f"[Data Processing] Processing dataset: {num_rows:,} rows x {num_features} features")
    
    np.random.seed(42)
    
    # Generate synthetic dataset
    print("[Data Processing] Generating dataset...")
    data = np.random.randn(num_rows, num_features).astype(np.float32)
    
    # Data cleaning operations
    print("[Data Processing] Cleaning data...")
    
    # Remove outliers (beyond 3 standard deviations)
    for col in range(num_features):
        col_data = data[:, col]
        mean = np.mean(col_data)
        std = np.std(col_data)
        mask = np.abs(col_data - mean) <= 3 * std
        data[:, col] = np.where(mask, col_data, mean)
    
    # Feature engineering
    print("[Data Processing] Engineering features...")
    
    # Create polynomial features
    new_features = []
    for i in range(min(10, num_features)):
        for j in range(i, min(10, num_features)):
            if i != j:
                poly_feature = data[:, i] * data[:, j]
                new_features.append(poly_feature)
    
    if new_features:
        poly_data = np.column_stack(new_features)
        data = np.hstack([data, poly_data])
        print(f"[Data Processing] Added {len(new_features)} polynomial features")
    
    # Normalization
    print("[Data Processing] Normalizing features...")
    data = (data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-8)
    
    # Aggregations
    print("[Data Processing] Computing aggregations...")
    aggregations = {
        'mean': np.mean(data, axis=0),
        'std': np.std(data, axis=0),
        'min': np.min(data, axis=0),
        'max': np.max(data, axis=0),
        'median': np.median(data, axis=0),
    }
    
    print(f"[Data Processing] Dataset shape after processing: {data.shape}")
    print(f"[Data Processing] Computed {len(aggregations)} aggregation types")
    
    return data, aggregations


def time_series_processing(num_series=1000, series_length=10000):
    """Process multiple time series with various operations."""
    print(f"[Data Processing] Processing {num_series} time series of length {series_length}")
    
    np.random.seed(42)
    processed_series = []
    
    for i in range(num_series):
        # Generate time series
        series = np.cumsum(np.random.randn(series_length)) + np.sin(np.linspace(0, 4*np.pi, series_length))
        
        # Apply transformations
        # 1. Moving average
        window = 100
        moving_avg = np.convolve(series, np.ones(window)/window, mode='valid')
        
        # 2. Differencing
        diff = np.diff(series)
        
        # 3. FFT for frequency analysis
        fft = np.fft.fft(series)
        power_spectrum = np.abs(fft)**2
        
        # 4. Autocorrelation
        autocorr = np.correlate(series, series, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        autocorr = autocorr / autocorr[0]  # Normalize
        
        processed_series.append({
            'series': series,
            'moving_avg': moving_avg,
            'diff': diff,
            'power_spectrum': power_spectrum,
            'autocorr': autocorr,
        })
        
        if (i + 1) % 100 == 0:
            print(f"[Data Processing] Processed {i+1}/{num_series} time series")
    
    print(f"[Data Processing] Successfully processed {len(processed_series)} time series")
    return processed_series


def parallel_sorting(num_elements=50_000_000):
    """Perform large-scale sorting operations."""
    print(f"[Data Processing] Sorting {num_elements:,} elements")
    
    np.random.seed(42)
    
    # Generate large array
    data = np.random.randn(num_elements).astype(np.float32)
    
    # Multiple sorting operations
    print("[Data Processing] Performing quicksort...")
    start = time.time()
    sorted_data = np.sort(data)
    sort_time = time.time() - start
    print(f"[Data Processing] Quicksort completed in {sort_time:.2f}s")
    
    # Partial sort (top-k)
    k = 1000
    print(f"[Data Processing] Finding top {k} elements...")
    start = time.time()
    top_k = np.partition(data, -k)[-k:]
    top_k_sorted = np.sort(top_k)
    topk_time = time.time() - start
    print(f"[Data Processing] Top-k selection completed in {topk_time:.2f}s")
    
    return sorted_data, top_k_sorted


if __name__ == "__main__":
    task_type = os.getenv("TASK", "dataset")
    num_rows = int(os.getenv("NUM_ROWS", "10000000"))
    num_features = int(os.getenv("NUM_FEATURES", "100"))
    num_series = int(os.getenv("NUM_SERIES", "1000"))
    series_length = int(os.getenv("SERIES_LENGTH", "10000"))
    num_elements = int(os.getenv("NUM_ELEMENTS", "50000000"))
    
    start_time = time.time()
    
    if task_type == "dataset":
        result = process_large_dataset(num_rows=num_rows, num_features=num_features)
    elif task_type == "timeseries":
        result = time_series_processing(num_series=num_series, series_length=series_length)
    elif task_type == "sort":
        result = parallel_sorting(num_elements=num_elements)
    else:
        print(f"Unknown task type: {task_type}")
        sys.exit(1)
    
    total_time = time.time() - start_time
    print(f"[Data Processing] Total runtime: {total_time:.2f} seconds")
