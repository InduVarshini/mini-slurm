# Repository Structure

This document describes the organization of the Mini-SLURM repository.

## Directory Layout

```
mini-slurm/
├── src/
│   └── mini_slurm/       # Main package
│       ├── __init__.py
│       ├── core.py        # Core scheduler and topology classes
│       ├── cli.py         # Command-line interface
│       ├── database.py    # Database functions
│       └── utils.py       # Utility functions
├── pyproject.toml         # Package configuration
├── MANIFEST.in            # Package manifest
├── LICENSE                # MIT License
├── examples.py            # Example workload submission script
├── requirements.txt       # Python dependencies
├── README.md              # Main project documentation
├── .gitignore             # Git ignore rules
│
├── docs/                  # Documentation directory
│   ├── QUICK_START.md     # Quick start guide
│   ├── GUIDE.md           # Comprehensive usage guide
│   ├── ARCHITECTURE.md    # Technical architecture details
│   ├── ELASTIC_JOBS.md    # Elastic job feature documentation
│   ├── TOPOLOGY.md        # Topology-aware scheduling documentation
│   ├── TESTING_GUIDE.md   # Testing instructions
│   ├── VIEW_LOGS.md       # Log viewing guide
│   ├── VIEW_DATABASE.md   # Database inspection guide
│   └── STRUCTURE.md       # This file
│
├── config/                # Configuration files
│   ├── README.md          # Configuration documentation
│   └── topology.conf.example  # Example topology configuration
│
├── tasks/                 # Example workload tasks
│   ├── README.md          # Tasks documentation
│   ├── train_neural_network.py
│   ├── elastic_training.py
│   ├── monte_carlo_simulation.py
│   ├── matrix_operations.py
│   ├── image_processing.py
│   ├── data_processing.py
│   └── scientific_computing.py
│
├── tests/                 # Test scripts
│   ├── README.md          # Test documentation
│   ├── test_local.sh      # Local testing script
│   ├── test_workloads.sh  # Workload testing script
│   ├── test_elastic.sh    # Elastic job comprehensive test
│   ├── test_elastic_manual.sh  # Manual elastic test
│   ├── test_elastic_simple.py  # Simple elastic test
│   ├── test_scaling.py    # Scaling behavior test
│   └── topology/          # Topology-aware scheduling tests
│       ├── test_topology_direct.py  # Direct topology test
│       ├── test_topology_elastic.py # Topology with elastic jobs
│       ├── test_topology_simple.sh  # Shell script topology test
│       └── test_workload.py         # Test workload helper
│
└── scripts/               # Utility scripts
    └── view_logs.py       # Log viewing utility
```

## File Descriptions

### Root Directory

- **src/mini_slurm/**: Main package. Contains the scheduler, CLI, and core functionality.
  - `core.py`: Core MiniSlurm scheduler class and TopologyConfig
  - `cli.py`: Command-line interface and argument parsing
  - `database.py`: SQLite database functions
  - `utils.py`: Utility functions (memory parsing, timestamps, etc.)
- **examples.py**: Script for submitting example workloads (training, simulations, etc.)
- **requirements.txt**: Python package dependencies
- **README.md**: Main project documentation and quick start

### docs/

All documentation files are organized here:

- **QUICK_START.md**: Get started quickly with Mini-SLURM
- **GUIDE.md**: Comprehensive guide covering all features
- **ARCHITECTURE.md**: Deep technical dive into system design
- **ELASTIC_JOBS.md**: Documentation for elastic/auto-resizing jobs feature
- **TOPOLOGY.md**: Topology-aware scheduling documentation
- **TESTING_GUIDE.md**: How to test the system
- **VIEW_LOGS.md**: Guide for viewing job logs
- **VIEW_DATABASE.md**: Guide for inspecting the database
- **STRUCTURE.md**: Repository structure documentation (this file)

### tasks/

Example workload tasks that demonstrate Mini-SLURM usage:

- **train_neural_network.py**: Neural network training simulation
- **elastic_training.py**: Elastic training job example
- **monte_carlo_simulation.py**: Monte Carlo simulations
- **matrix_operations.py**: Matrix computation tasks
- **image_processing.py**: Image processing workloads
- **data_processing.py**: Data processing and ETL tasks
- **scientific_computing.py**: Scientific computing simulations

### config/

Configuration files and examples:

- **topology.conf.example**: Example topology configuration for topology-aware scheduling
- **README.md**: Configuration documentation and usage instructions

### tests/

Test scripts for verifying functionality:

**General Tests:**
- **test_local.sh**: Basic local functionality test
- **test_workloads.sh**: Test with various workload types
- **test_elastic.sh**: Comprehensive elastic job test
- **test_elastic_manual.sh**: Manual elastic job testing
- **test_elastic_simple.py**: Simple elastic job verification
- **test_scaling.py**: Test scaling behavior

**Topology Tests** (`tests/topology/`):
- **test_topology_direct.py**: Direct in-process test of topology scheduling
- **test_topology_elastic.py**: Test topology with elastic workloads
- **test_topology_simple.sh**: Shell script for manual topology testing
- **test_workload.py**: Simple CPU workload helper for testing

### scripts/

Utility scripts:

- **view_logs.py**: Command-line tool for viewing job logs

## Data Files (Not in Repository)

These files are created at runtime and ignored by git:

- **~/.mini_slurm.db**: SQLite database storing job metadata
- **~/.mini_slurm_logs/**: Directory containing job logs and control files
  - `job_<id>.out`: Job stdout
  - `job_<id>.err`: Job stderr
  - `job_<id>.control`: Elastic job control file (if elastic)
- **~/.mini_slurm_topology*.conf**: Topology configuration files (test files)

## Usage Patterns

### Running Tests

```bash
# Run basic tests
./tests/test_local.sh

# Test elastic jobs
./tests/test_elastic.sh

# Run Python test
python3 tests/test_scaling.py

# Test topology-aware scheduling
python3 tests/topology/test_topology_direct.py
./tests/topology/test_topology_simple.sh
```

### Viewing Logs

```bash
# Use the utility script
python3 scripts/view_logs.py <job_id>

# Or directly
cat ~/.mini_slurm_logs/job_<id>.out
```

### Submitting Example Workloads

```bash
# Submit example workloads
python3 examples.py all
python3 examples.py elastic
python3 examples.py macbook
```

## Organization Principles

1. **Separation of Concerns**: Core code, documentation, tests, and utilities are separated
2. **Documentation Centralization**: All docs in `docs/` directory
3. **Test Organization**: All tests in `tests/` directory, with feature-specific subdirectories
4. **Configuration Files**: Example configs in `config/` directory
5. **Utility Scripts**: Helper scripts in `scripts/` directory
6. **Example Workloads**: Example tasks in `tasks/` directory
7. **Feature Grouping**: Related tests grouped in subdirectories (e.g., `tests/topology/`)

## Adding New Files

When adding new files:

- **Documentation**: Add to `docs/`
- **Tests**: Add to `tests/` (create subdirectories for feature-specific tests)
- **Configuration Examples**: Add to `config/`
- **Utility Scripts**: Add to `scripts/`
- **Example Tasks**: Add to `tasks/`
- **Core Code**: Add to root or appropriate subdirectory

## Git Ignore

The `.gitignore` file excludes:
- Python cache files (`__pycache__/`, `*.pyc`)
- Database files (`*.db`)
- Log files (`*.log`, `*.out`, `*.err`)
- IDE files (`.vscode/`, `.idea/`)
- Virtual environments (`venv/`, `env/`)
- System files (`.DS_Store`)
