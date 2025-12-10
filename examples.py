#!/usr/bin/env python3
"""
Example AI/HPC workloads for Mini-SLURM.

These examples demonstrate how to use Mini-SLURM for heavy AI/HPC tasks.
All tasks are located in the tasks/ directory.
"""

import subprocess
import time
import sys
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(SCRIPT_DIR, "tasks")


def submit_neural_network_training():
    """Submit multiple neural network training jobs with different configurations."""
    print("Submitting neural network training jobs...")
    
    configs = [
        {"epochs": 50, "batch_size": 128, "model_size": "small", "cpus": 2, "mem": "4GB"},
        {"epochs": 100, "batch_size": 256, "model_size": "medium", "cpus": 4, "mem": "8GB"},
        {"epochs": 200, "batch_size": 512, "model_size": "large", "cpus": 8, "mem": "16GB"},
    ]
    
    for i, config in enumerate(configs):
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(config["cpus"]),
            "--mem", config["mem"],
            "--priority", str(10 - i),  # Higher priority for smaller jobs
            f"EPOCHS={config['epochs']} BATCH_SIZE={config['batch_size']} MODEL_SIZE={config['model_size']} "
            f"python3 {os.path.join(TASKS_DIR, 'train_neural_network.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted training job {i+1}: {config['model_size']} model, {config['epochs']} epochs")
    
    print("\nView queue: mini-slurm queue")


def submit_monte_carlo_simulations():
    """Submit Monte Carlo simulation jobs."""
    print("Submitting Monte Carlo simulation jobs...")
    
    simulations = [
        {"type": "pi", "samples": 100_000_000, "cpus": 4, "mem": "4GB", "priority": 5},
        {"type": "pi", "samples": 500_000_000, "cpus": 8, "mem": "8GB", "priority": 3},
        {"type": "option", "samples": 10_000_000, "cpus": 4, "mem": "4GB", "priority": 5},
    ]
    
    for i, sim in enumerate(simulations):
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(sim["cpus"]),
            "--mem", sim["mem"],
            "--priority", str(sim["priority"]),
            f"SIM_TYPE={sim['type']} NUM_SAMPLES={sim['samples']} "
            f"python3 {os.path.join(TASKS_DIR, 'monte_carlo_simulation.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted Monte Carlo job {i+1}: {sim['type']} with {sim['samples']:,} samples")
    
    print("\nView queue: mini-slurm queue")


def submit_matrix_operations():
    """Submit heavy matrix operation jobs."""
    print("Submitting matrix operation jobs...")
    
    operations = [
        {"op": "multiply", "size": 3000, "iterations": 5, "cpus": 4, "mem": "8GB", "priority": 5},
        {"op": "multiply", "size": 5000, "iterations": 10, "cpus": 8, "mem": "16GB", "priority": 3},
        {"op": "svd", "size": 3000, "iterations": 1, "cpus": 4, "mem": "8GB", "priority": 5},
        {"op": "cholesky", "size": 4000, "iterations": 1, "cpus": 4, "mem": "8GB", "priority": 5},
    ]
    
    for i, op_config in enumerate(operations):
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(op_config["cpus"]),
            "--mem", op_config["mem"],
            "--priority", str(op_config["priority"]),
            f"OP={op_config['op']} SIZE={op_config['size']} ITERATIONS={op_config['iterations']} "
            f"python3 {os.path.join(TASKS_DIR, 'matrix_operations.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted matrix operation {i+1}: {op_config['op']} on {op_config['size']}x{op_config['size']} matrix")
    
    print("\nView queue: mini-slurm queue")


def submit_image_processing():
    """Submit image processing pipeline jobs."""
    print("Submitting image processing jobs...")
    
    jobs = [
        {"task": "batch", "num_images": 500, "image_size": 1024, "cpus": 4, "mem": "8GB", "priority": 5},
        {"task": "batch", "num_images": 1000, "image_size": 2048, "cpus": 8, "mem": "16GB", "priority": 3},
        {"task": "features", "num_images": 500, "feature_dim": 2048, "cpus": 4, "mem": "8GB", "priority": 5},
    ]
    
    for i, job in enumerate(jobs):
        env_vars = f"TASK={job['task']} NUM_IMAGES={job['num_images']}"
        if job['task'] == "batch":
            env_vars += f" IMAGE_SIZE={job['image_size']}"
        else:
            env_vars += f" FEATURE_DIM={job['feature_dim']}"
        
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(job["cpus"]),
            "--mem", job["mem"],
            "--priority", str(job["priority"]),
            f"{env_vars} python3 {os.path.join(TASKS_DIR, 'image_processing.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted image processing job {i+1}: {job['task']} with {job['num_images']} images")
    
    print("\nView queue: mini-slurm queue")


def submit_data_processing():
    """Submit data processing and ETL jobs."""
    print("Submitting data processing jobs...")
    
    jobs = [
        {"task": "dataset", "num_rows": 5_000_000, "num_features": 50, "cpus": 4, "mem": "8GB", "priority": 5},
        {"task": "dataset", "num_rows": 10_000_000, "num_features": 100, "cpus": 8, "mem": "16GB", "priority": 3},
        {"task": "timeseries", "num_series": 500, "series_length": 5000, "cpus": 4, "mem": "8GB", "priority": 5},
        {"task": "sort", "num_elements": 25_000_000, "cpus": 4, "mem": "8GB", "priority": 5},
    ]
    
    for i, job in enumerate(jobs):
        env_vars = f"TASK={job['task']}"
        if job['task'] == "dataset":
            env_vars += f" NUM_ROWS={job['num_rows']} NUM_FEATURES={job['num_features']}"
        elif job['task'] == "timeseries":
            env_vars += f" NUM_SERIES={job['num_series']} SERIES_LENGTH={job['series_length']}"
        else:
            env_vars += f" NUM_ELEMENTS={job['num_elements']}"
        
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(job["cpus"]),
            "--mem", job["mem"],
            "--priority", str(job["priority"]),
            f"{env_vars} python3 {os.path.join(TASKS_DIR, 'data_processing.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted data processing job {i+1}: {job['task']}")
    
    print("\nView queue: mini-slurm queue")


def submit_scientific_computing():
    """Submit scientific computing simulation jobs."""
    print("Submitting scientific computing jobs...")
    
    simulations = [
        {"type": "heat", "grid_size": 500, "time_steps": 500, "cpus": 4, "mem": "8GB", "priority": 5},
        {"type": "heat", "grid_size": 1000, "time_steps": 1000, "cpus": 8, "mem": "16GB", "priority": 3},
        {"type": "nbody", "num_bodies": 5000, "time_steps": 500, "cpus": 4, "mem": "8GB", "priority": 5},
        {"type": "linear", "matrix_size": 3000, "cpus": 4, "mem": "8GB", "priority": 5},
        {"type": "fea", "grid_size": 300, "cpus": 4, "mem": "8GB", "priority": 5},
    ]
    
    for i, sim in enumerate(simulations):
        env_vars = f"SIM_TYPE={sim['type']}"
        if sim['type'] == "heat":
            env_vars += f" GRID_SIZE={sim['grid_size']} TIME_STEPS={sim['time_steps']}"
        elif sim['type'] == "nbody":
            env_vars += f" NUM_BODIES={sim['num_bodies']} TIME_STEPS={sim['time_steps']}"
        elif sim['type'] == "linear":
            env_vars += f" MATRIX_SIZE={sim['matrix_size']}"
        else:
            env_vars += f" GRID_SIZE={sim['grid_size']}"
        
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(sim["cpus"]),
            "--mem", sim["mem"],
            "--priority", str(sim["priority"]),
            f"{env_vars} python3 {os.path.join(TASKS_DIR, 'scientific_computing.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted scientific computing job {i+1}: {sim['type']}")
    
    print("\nView queue: mini-slurm queue")


def submit_elastic_training_jobs():
    """Submit elastic training jobs that can scale up/down dynamically."""
    print("=" * 60)
    print("Submitting Elastic Training Jobs...")
    print("=" * 60)
    print()
    print("Elastic jobs can:")
    print("  - Start with minimum resources")
    print("  - Scale UP when cluster utilization < 50%")
    print("  - Scale DOWN when high-priority jobs arrive")
    print()
    
    # Submit elastic training job
    cmd = [
        "mini-slurm", "submit",
        "--elastic",
        "--cpus", "2",  # Start with 2 CPUs
        "--min-cpus", "2",  # Minimum 2 CPUs
        "--max-cpus", "8",  # Can scale up to 8 CPUs
        "--mem", "4GB",
        "--priority", "5",
        f"EPOCHS=30 python3 {os.path.join(TASKS_DIR, 'elastic_training.py')}"
    ]
    subprocess.run(cmd)
    print("  Submitted elastic training job (2-8 CPUs)")
    
    # Submit a high-priority job that will trigger scale-down
    time.sleep(1)
    cmd = [
        "mini-slurm", "submit",
        "--cpus", "4",
        "--mem", "4GB",
        "--priority", "10",  # Higher priority - will trigger scale-down
        f"EPOCHS=20 python3 {os.path.join(TASKS_DIR, 'train_neural_network.py')}"
    ]
    subprocess.run(cmd)
    print("  Submitted high-priority job (will trigger elastic scale-down)")
    
    print("\n" + "=" * 60)
    print("Elastic jobs submitted!")
    print("Watch the scheduler logs to see scaling in action:")
    print("  - Elastic job will scale UP when cluster is underutilized")
    print("  - Elastic job will scale DOWN when high-priority job arrives")
    print("=" * 60)


def submit_macbook_friendly_workloads():
    """Submit workloads optimized for MacBook Air (16GB RAM)."""
    print("=" * 60)
    print("Submitting MacBook Air-friendly workloads (16GB RAM)...")
    print("=" * 60)
    print()
    
    print("1. Neural Network Training Jobs (lightweight)")
    configs = [
        {"epochs": 20, "batch_size": 64, "model_size": "small", "cpus": 2, "mem": "2GB"},
        {"epochs": 30, "batch_size": 128, "model_size": "small", "cpus": 2, "mem": "2GB"},
    ]
    for i, config in enumerate(configs):
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(config["cpus"]),
            "--mem", config["mem"],
            "--priority", str(10 - i),
            f"EPOCHS={config['epochs']} BATCH_SIZE={config['batch_size']} MODEL_SIZE={config['model_size']} "
            f"python3 {os.path.join(TASKS_DIR, 'train_neural_network.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted training job {i+1}")
    time.sleep(1)
    
    print("\n2. Monte Carlo Simulations (reduced samples)")
    simulations = [
        {"type": "pi", "samples": 50_000_000, "cpus": 2, "mem": "2GB", "priority": 5},
        {"type": "option", "samples": 5_000_000, "cpus": 2, "mem": "2GB", "priority": 5},
    ]
    for i, sim in enumerate(simulations):
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(sim["cpus"]),
            "--mem", sim["mem"],
            "--priority", str(sim["priority"]),
            f"SIM_TYPE={sim['type']} NUM_SAMPLES={sim['samples']} "
            f"python3 {os.path.join(TASKS_DIR, 'monte_carlo_simulation.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted Monte Carlo job {i+1}")
    time.sleep(1)
    
    print("\n3. Matrix Operations (smaller matrices)")
    operations = [
        {"op": "multiply", "size": 1500, "iterations": 3, "cpus": 2, "mem": "2GB", "priority": 5},
        {"op": "svd", "size": 1500, "iterations": 1, "cpus": 2, "mem": "2GB", "priority": 5},
    ]
    for i, op_config in enumerate(operations):
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(op_config["cpus"]),
            "--mem", op_config["mem"],
            "--priority", str(op_config["priority"]),
            f"OP={op_config['op']} SIZE={op_config['size']} ITERATIONS={op_config['iterations']} "
            f"python3 {os.path.join(TASKS_DIR, 'matrix_operations.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted matrix operation {i+1}")
    time.sleep(1)
    
    print("\n4. Image Processing (fewer images)")
    jobs = [
        {"task": "batch", "num_images": 200, "image_size": 512, "cpus": 2, "mem": "2GB", "priority": 5},
        {"task": "features", "num_images": 200, "feature_dim": 1024, "cpus": 2, "mem": "2GB", "priority": 5},
    ]
    for i, job in enumerate(jobs):
        env_vars = f"TASK={job['task']} NUM_IMAGES={job['num_images']}"
        if job['task'] == "batch":
            env_vars += f" IMAGE_SIZE={job['image_size']}"
        else:
            env_vars += f" FEATURE_DIM={job['feature_dim']}"
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(job["cpus"]),
            "--mem", job["mem"],
            "--priority", str(job["priority"]),
            f"{env_vars} python3 {os.path.join(TASKS_DIR, 'image_processing.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted image processing job {i+1}")
    time.sleep(1)
    
    print("\n5. Data Processing (smaller datasets)")
    jobs = [
        {"task": "dataset", "num_rows": 1_000_000, "num_features": 20, "cpus": 2, "mem": "2GB", "priority": 5},
        {"task": "timeseries", "num_series": 200, "series_length": 2000, "cpus": 2, "mem": "2GB", "priority": 5},
    ]
    for i, job in enumerate(jobs):
        env_vars = f"TASK={job['task']}"
        if job['task'] == "dataset":
            env_vars += f" NUM_ROWS={job['num_rows']} NUM_FEATURES={job['num_features']}"
        else:
            env_vars += f" NUM_SERIES={job['num_series']} SERIES_LENGTH={job['series_length']}"
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(job["cpus"]),
            "--mem", job["mem"],
            "--priority", str(job["priority"]),
            f"{env_vars} python3 {os.path.join(TASKS_DIR, 'data_processing.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted data processing job {i+1}")
    time.sleep(1)
    
    print("\n6. Scientific Computing (smaller grids)")
    simulations = [
        {"type": "heat", "grid_size": 300, "time_steps": 200, "cpus": 2, "mem": "2GB", "priority": 5},
        {"type": "linear", "matrix_size": 1500, "cpus": 2, "mem": "2GB", "priority": 5},
    ]
    for i, sim in enumerate(simulations):
        env_vars = f"SIM_TYPE={sim['type']}"
        if sim['type'] == "heat":
            env_vars += f" GRID_SIZE={sim['grid_size']} TIME_STEPS={sim['time_steps']}"
        else:
            env_vars += f" MATRIX_SIZE={sim['matrix_size']}"
        cmd = [
            "mini-slurm", "submit",
            "--cpus", str(sim["cpus"]),
            "--mem", sim["mem"],
            "--priority", str(sim["priority"]),
            f"{env_vars} python3 {os.path.join(TASKS_DIR, 'scientific_computing.py')}"
        ]
        subprocess.run(cmd)
        print(f"  Submitted scientific computing job {i+1}")
    
    print("\n" + "=" * 60)
    print("All MacBook Air-friendly jobs submitted!")
    print("Total memory per job: 2GB (safe for 16GB system)")
    print("Use 'mini-slurm queue' to view status.")
    print("=" * 60)


def submit_all_heavy_workloads():
    """Submit a comprehensive mix of all heavy workloads."""
    print("=" * 60)
    print("Submitting comprehensive heavy workload suite...")
    print("=" * 60)
    print()
    
    print("1. Neural Network Training Jobs")
    submit_neural_network_training()
    time.sleep(1)
    
    print("\n2. Monte Carlo Simulations")
    submit_monte_carlo_simulations()
    time.sleep(1)
    
    print("\n3. Matrix Operations")
    submit_matrix_operations()
    time.sleep(1)
    
    print("\n4. Image Processing")
    submit_image_processing()
    time.sleep(1)
    
    print("\n5. Data Processing")
    submit_data_processing()
    time.sleep(1)
    
    print("\n6. Scientific Computing")
    submit_scientific_computing()
    
    print("\n" + "=" * 60)
    print("All jobs submitted! Use 'mini-slurm queue' to view status.")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 examples.py <command>")
        print("\nCommands:")
        print("  training          - Submit neural network training jobs")
        print("  monte_carlo      - Submit Monte Carlo simulation jobs")
        print("  matrix           - Submit matrix operation jobs")
        print("  image            - Submit image processing jobs")
        print("  data             - Submit data processing jobs")
        print("  scientific       - Submit scientific computing jobs")
        print("  all              - Submit all heavy workload types")
        print("  macbook          - Submit MacBook Air-friendly workloads (16GB RAM)")
        print("  elastic          - Submit elastic training jobs (auto-scaling)")
        print("\nExample:")
        print("  python3 examples.py macbook  # For MacBook Air")
        print("  python3 examples.py all     # For powerful systems")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "training":
        submit_neural_network_training()
    elif command == "monte_carlo":
        submit_monte_carlo_simulations()
    elif command == "matrix":
        submit_matrix_operations()
    elif command == "image":
        submit_image_processing()
    elif command == "data":
        submit_data_processing()
    elif command == "scientific":
        submit_scientific_computing()
    elif command == "all":
        submit_all_heavy_workloads()
    elif command == "macbook":
        submit_macbook_friendly_workloads()
    elif command == "elastic":
        submit_elastic_training_jobs()
    else:
        print(f"Unknown command: {command}")
        print("Run 'python3 examples.py' for usage information")
        sys.exit(1)

