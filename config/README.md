# Configuration Files

This directory contains example configuration files for mini-slurm.

## Files

- **`topology.conf.example`** - Example topology configuration file for topology-aware scheduling

## Usage

### Topology Configuration

To enable topology-aware scheduling, copy the example configuration file to your home directory:

```bash
cp config/topology.conf.example ~/.mini_slurm_topology.conf
```

Or specify a custom path when starting the scheduler:

```bash
mini-slurm scheduler --topology-config /path/to/topology.conf
```

For detailed topology configuration information, visit the [GitHub repository](https://github.com/InduVarshini/mini-slurm).
