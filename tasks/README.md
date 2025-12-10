# Heavy AI/HPC Task Scripts

This directory contains computationally intensive task scripts designed to test Mini-SLURM's job scheduling capabilities. These tasks simulate real-world AI and HPC workloads.

## Available Tasks

### 1. Neural Network Training (`train_neural_network.py`)
Simulates training deep learning models with configurable parameters.

**Environment Variables:**
- `EPOCHS`: Number of training epochs (default: 50)
- `BATCH_SIZE`: Batch size (default: 128)
- `MODEL_SIZE`: Model size - "small", "medium", or "large" (default: "large")

**Example:**
```bash
python3 mini-slurm.py submit --cpus 8 --mem 16GB \
  "EPOCHS=100 BATCH_SIZE=256 MODEL_SIZE=large python3 tasks/train_neural_network.py"
```

### 2. Monte Carlo Simulation (`monte_carlo_simulation.py`)
Performs Monte Carlo simulations for statistical computing.

**Environment Variables:**
- `SIM_TYPE`: Type of simulation - "pi" or "option" (default: "pi")
- `NUM_SAMPLES`: Number of samples/iterations (default: 100000000)

**Example:**
```bash
python3 mini-slurm.py submit --cpus 4 --mem 8GB \
  "SIM_TYPE=pi NUM_SAMPLES=500000000 python3 tasks/monte_carlo_simulation.py"
```

### 3. Matrix Operations (`matrix_operations.py`)
Heavy linear algebra operations common in ML/AI.

**Environment Variables:**
- `OP`: Operation type - "multiply", "svd", or "cholesky" (default: "multiply")
- `SIZE`: Matrix size (default: 5000)
- `ITERATIONS`: Number of iterations for multiply operation (default: 10)

**Example:**
```bash
python3 mini-slurm.py submit --cpus 8 --mem 16GB \
  "OP=multiply SIZE=5000 ITERATIONS=10 python3 tasks/matrix_operations.py"
```

### 4. Image Processing (`image_processing.py`)
Batch image processing and feature extraction pipelines.

**Environment Variables:**
- `TASK`: Task type - "batch" or "features" (default: "batch")
- `NUM_IMAGES`: Number of images to process (default: 1000)
- `IMAGE_SIZE`: Image dimensions for batch processing (default: 2048)
- `FEATURE_DIM`: Feature dimension for feature extraction (default: 2048)

**Example:**
```bash
python3 mini-slurm.py submit --cpus 4 --mem 8GB \
  "TASK=batch NUM_IMAGES=1000 IMAGE_SIZE=2048 python3 tasks/image_processing.py"
```

### 5. Data Processing (`data_processing.py`)
ETL operations, data cleaning, and feature engineering.

**Environment Variables:**
- `TASK`: Task type - "dataset", "timeseries", or "sort" (default: "dataset")
- `NUM_ROWS`: Number of rows for dataset processing (default: 10000000)
- `NUM_FEATURES`: Number of features (default: 100)
- `NUM_SERIES`: Number of time series (default: 1000)
- `SERIES_LENGTH`: Length of each time series (default: 10000)
- `NUM_ELEMENTS`: Number of elements for sorting (default: 50000000)

**Example:**
```bash
python3 mini-slurm.py submit --cpus 8 --mem 16GB \
  "TASK=dataset NUM_ROWS=10000000 NUM_FEATURES=100 python3 tasks/data_processing.py"
```

### 6. Scientific Computing (`scientific_computing.py`)
Physics simulations and numerical methods.

**Environment Variables:**
- `SIM_TYPE`: Simulation type - "heat", "nbody", "linear", or "fea" (default: "heat")
- `GRID_SIZE`: Grid size for heat/FEA simulations (default: 1000)
- `TIME_STEPS`: Number of time steps (default: 1000)
- `NUM_BODIES`: Number of bodies for N-body simulation (default: 10000)
- `MATRIX_SIZE`: Matrix size for linear system solver (default: 5000)

**Example:**
```bash
python3 mini-slurm.py submit --cpus 8 --mem 16GB \
  "SIM_TYPE=heat GRID_SIZE=1000 TIME_STEPS=1000 python3 tasks/scientific_computing.py"
```

## Quick Start

### Using the Examples Script

The easiest way to submit multiple jobs is using the `examples.py` script:

```bash
# Submit all heavy workloads
python3 examples.py all

# Submit specific workload type
python3 examples.py training
python3 examples.py monte_carlo
python3 examples.py matrix
python3 examples.py image
python3 examples.py data
python3 examples.py scientific
```

### Manual Submission

You can also submit jobs manually:

```bash
# Single job
python3 mini-slurm.py submit --cpus 4 --mem 8GB --priority 5 \
  "EPOCHS=50 python3 tasks/train_neural_network.py"

# Multiple jobs with different configurations
for size in small medium large; do
  python3 mini-slurm.py submit --cpus 4 --mem 8GB \
    "MODEL_SIZE=$size python3 tasks/train_neural_network.py"
done
```

## Resource Requirements

These tasks are designed to be computationally intensive. Recommended resource allocations:

- **Small tasks**: 2-4 CPUs, 4-8 GB memory
- **Medium tasks**: 4-8 CPUs, 8-16 GB memory  
- **Large tasks**: 8+ CPUs, 16+ GB memory

Adjust the parameters (matrix sizes, number of iterations, etc.) based on your system's capabilities.

## Monitoring Jobs

```bash
# View job queue
python3 mini-slurm.py queue

# View specific job
python3 mini-slurm.py show <job_id>

# View statistics
python3 mini-slurm.py stats
```

## Dependencies

All tasks require:
- Python 3.7+
- NumPy (`pip install numpy`)

The tasks are designed to work without additional ML frameworks to keep dependencies minimal.
