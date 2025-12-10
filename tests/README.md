# Tests

This directory contains test scripts for mini-slurm functionality.

## Directory Structure

- **`topology/`** - Tests for topology-aware scheduling
  - `test_topology_direct.py` - Direct in-process test of topology scheduling
  - `test_topology_elastic.py` - Test topology with elastic workloads
  - `test_topology_simple.sh` - Shell script for manual topology testing
  - `test_workload.py` - Simple CPU workload for testing

- **Root tests/** - General functionality tests
  - `test_elastic_*.py` - Elastic job tests
  - `test_scaling.py` - Resource scaling tests
  - `test_workloads.sh` - Workload tests
  - `test_local.sh` - Local execution tests

## Running Tests

### Topology Tests

```bash
# Direct test (recommended)
python tests/topology/test_topology_direct.py

# Elastic workloads with topology
python tests/topology/test_topology_elastic.py

# Manual shell script test
./tests/topology/test_topology_simple.sh
```

### Elastic Job Tests

```bash
# Simple elastic test
python tests/test_elastic_simple.py

# Manual elastic test
./tests/test_elastic_manual.sh

# Full elastic test suite
./tests/test_elastic.sh
```

### General Tests

```bash
# Local execution test
./tests/test_local.sh

# Workload tests
./tests/test_workloads.sh

# Scaling tests
python tests/test_scaling.py
```

## Writing New Tests

When writing new tests:

1. Place topology-related tests in `tests/topology/`
2. Place general tests in `tests/`
3. Use descriptive names: `test_<feature>_<scenario>.py`
4. Include docstrings explaining what the test verifies
5. Clean up any temporary files created during testing
