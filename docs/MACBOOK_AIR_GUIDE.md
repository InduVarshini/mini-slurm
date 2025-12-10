# MacBook Air (16GB) Quick Start Guide

## Data Sources

**All data is generated synthetically in-memory** - no external files needed!

All tasks use NumPy's `np.random` to generate synthetic data:
- **Neural Network Training**: Generates random matrices for forward/backward passes
- **Monte Carlo**: Generates random points for statistical simulations
- **Matrix Operations**: Generates random matrices for linear algebra
- **Image Processing**: Generates random image arrays
- **Data Processing**: Generates random datasets
- **Scientific Computing**: Generates random initial conditions for simulations

**No downloads, no datasets, no external dependencies** - everything runs in-memory!

## Recommended Setup for MacBook Air (16GB RAM)

### 1. Start Scheduler with Conservative Limits

```bash
# Use 6-8 CPUs max (MacBook Air typically has 8 cores)
# Reserve 12GB for system + other apps, use 4GB for jobs
python3 mini-slurm.py scheduler --total-cpus 6 --total-mem 4GB
```

### 2. Submit MacBook Air-Friendly Jobs

```bash
# Use the special MacBook Air mode (recommended)
python3 examples.py macbook
```

This submits jobs with:
- **2GB memory per job** (safe for 16GB system)
- **2 CPUs per job** (allows multiple concurrent jobs)
- **Reduced parameters** (smaller matrices, fewer iterations)

### 3. Manual Submission (MacBook Air-Friendly)

If you want to submit jobs manually with safe parameters:

```bash
# Neural Network Training (lightweight)
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "EPOCHS=20 MODEL_SIZE=small python3 tasks/train_neural_network.py"

# Monte Carlo (reduced samples)
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "SIM_TYPE=pi NUM_SAMPLES=50000000 python3 tasks/monte_carlo_simulation.py"

# Matrix Operations (smaller matrices)
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "OP=multiply SIZE=1500 ITERATIONS=3 python3 tasks/matrix_operations.py"

# Image Processing (fewer images)
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "TASK=batch NUM_IMAGES=200 IMAGE_SIZE=512 python3 tasks/image_processing.py"

# Data Processing (smaller datasets)
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "TASK=dataset NUM_ROWS=1000000 NUM_FEATURES=20 python3 tasks/data_processing.py"

# Scientific Computing (smaller grids)
python3 mini-slurm.py submit --cpus 2 --mem 2GB \
  "SIM_TYPE=heat GRID_SIZE=300 TIME_STEPS=200 python3 tasks/scientific_computing.py"
```

## Memory Usage Guidelines

### Safe Parameters for 16GB MacBook Air:

| Task Type | Matrix Size | Dataset Size | Memory per Job |
|-----------|-------------|--------------|----------------|
| Matrix Ops | 1000-2000   | -            | 2GB            |
| Data Proc  | -            | 1-5M rows    | 2GB            |
| Images     | 512x512      | 100-500 imgs | 2GB            |
| Training   | Small model  | -            | 2GB            |
| Monte Carlo| 50M samples  | -            | 2GB            |
| Scientific | 300x300 grid | -            | 2GB            |

### Avoid These (Too Heavy for 16GB):

- Matrix sizes > 3000x3000
- Datasets > 10M rows
- Image sizes > 2048x2048
- Multiple jobs requesting > 4GB each simultaneously

## Example Workflow

```bash
# Terminal 1: Start scheduler
python3 mini-slurm.py scheduler --total-cpus 6 --total-mem 4GB

# Terminal 2: Submit jobs
python3 examples.py macbook

# Terminal 3: Monitor
watch -n 2 'python3 mini-slurm.py queue'
```

## Troubleshooting

### "Out of Memory" Errors
- Reduce matrix sizes (use SIZE=1000 instead of 5000)
- Reduce dataset sizes (use NUM_ROWS=1000000 instead of 10000000)
- Submit fewer jobs at once
- Reduce scheduler memory: `--total-mem 2GB`

### Jobs Running Slowly
- This is normal! MacBook Air has limited CPU cores
- Reduce iterations/epochs for faster completion
- Use smaller parameters for quicker tests

### System Becoming Unresponsive
- Stop the scheduler: `Ctrl+C`
- Check running jobs: `python3 mini-slurm.py queue`
- Cancel jobs if needed: `python3 mini-slurm.py cancel <job_id>`
- Reduce scheduler limits: `--total-cpus 4 --total-mem 2GB`

## Quick Test

Test with a single lightweight job first:

```bash
# Start scheduler
python3 mini-slurm.py scheduler --total-cpus 4 --total-mem 2GB

# Submit one small job
python3 mini-slurm.py submit --cpus 2 --mem 1GB \
  "EPOCHS=10 MODEL_SIZE=small python3 tasks/train_neural_network.py"

# Check it runs successfully
python3 mini-slurm.py queue
```

If this works, you can scale up gradually!
