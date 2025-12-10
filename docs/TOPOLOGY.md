# Topology-Aware Scheduling

Mini-SLURM supports topology-aware scheduling, similar to SLURM's topology plugin feature. This allows the scheduler to understand which nodes are "close" (connected to the same leaf switch) versus "far" (requiring communication across core switches), enabling better job placement for network-intensive workloads.

## Overview

When topology-aware scheduling is enabled, the scheduler:

1. **Prefers nodes on the same leaf switch** - Jobs requiring multiple nodes will be allocated nodes that share a leaf switch when possible
2. **Minimizes network distance** - For jobs that can't fit on a single switch, the scheduler minimizes the maximum distance between allocated nodes
3. **Tracks node assignments** - Each job's node allocation is tracked and displayed

## Configuration

### Topology Configuration File

Create a topology configuration file (default: `~/.mini_slurm_topology.conf`) or specify a custom path with `--topology-config`.

The configuration file uses a format similar to SLURM's `slurm.conf`:

```conf
# Enable topology plugin
TopologyPlugin=topology/tree

# Define leaf switches and their nodes
SwitchName=switch1 Nodes=node[1-4]
SwitchName=switch2 Nodes=node[5-8]
SwitchName=switch3 Nodes=node[9-12]
SwitchName=switch4 Nodes=node[13-16]

# Define core switch hierarchy
SwitchName=core1 Switches=switch[1-4]
```

### Configuration Format

- **TopologyPlugin**: Enable topology-aware scheduling (`topology/tree`, `topology`, `yes`, `1`, or `true`)
- **SwitchName**: Define a switch and its connections
  - `SwitchName=<name> Nodes=<node_list>` - Connect nodes to a leaf switch
  - `SwitchName=<name> Switches=<switch_list>` - Connect child switches to a parent (core) switch
- **Node ranges**: Use `node[1-4]` syntax for ranges, or comma-separated lists like `node1,node2,node3`

### Example: Multi-Level Hierarchy

```conf
TopologyPlugin=topology/tree

# Leaf switches
SwitchName=switch1 Nodes=node[1-2]
SwitchName=switch2 Nodes=node[3-4]
SwitchName=switch3 Nodes=node[5-6]
SwitchName=switch4 Nodes=node[7-8]

# Rack-level switches
SwitchName=rack1 Switches=switch[1-2]
SwitchName=rack2 Switches=switch[3-4]

# Core switch
SwitchName=core1 Switches=rack[1-2]
```

## Usage

### Starting the Scheduler with Topology

```bash
# Use default config file (~/.mini_slurm_topology.conf)
mini-slurm scheduler

# Use custom config file
mini-slurm scheduler --topology-config /path/to/topology.conf
```

### Viewing Node Assignments

When topology-aware scheduling is enabled, job details include node assignments:

```bash
mini-slurm show <job_id>
```

Output includes:
```
Job 1
  ...
  Nodes:       node1,node2,node3
  ...
```

### Default Behavior

If no topology configuration file exists, mini-slurm automatically creates a default topology:
- Each CPU core becomes a virtual node
- Nodes are grouped into leaf switches (4 nodes per switch by default)
- Multiple switches are connected via a core switch

This allows topology-aware scheduling to work out of the box, even without explicit configuration.

## How It Works

### Node Distance Calculation

The scheduler calculates the "distance" between nodes based on switch hierarchy:

- **Distance 0**: Same node (trivial case)
- **Distance 0**: Same leaf switch (preferred)
- **Distance 2+**: Different leaf switches, same core
- **Distance 4+**: Different cores

### Scheduling Algorithm

When scheduling a job:

1. Calculate required number of nodes based on CPU and memory requirements
2. Find available nodes that meet resource requirements
3. **Prefer nodes on the same leaf switch** - If a single switch has enough nodes, use them
4. **Minimize maximum distance** - If multiple switches are needed, use a greedy algorithm to minimize the maximum distance between any two allocated nodes
5. Track node assignments in the database

### CPU Affinity

When nodes are assigned, CPU affinity is set based on the node-to-CPU mapping:
- On Linux: Uses `taskset` to pin processes to specific CPU cores
- On macOS: Sets environment variables for thread limits

## Example Scenarios

### Scenario 1: Single Switch Allocation

Job requires 4 CPUs, and 4 nodes are available on `switch1`:
- **Result**: All 4 nodes allocated from `switch1` (distance = 0)

### Scenario 2: Multi-Switch Allocation

Job requires 8 CPUs, but only 4 nodes available per switch:
- **Result**: 4 nodes from `switch1` + 4 nodes from `switch2` (both under same core, distance = 2)

### Scenario 3: Cross-Core Allocation

Job requires 12 CPUs, but switches are on different cores:
- **Result**: Nodes allocated to minimize maximum distance, but may span multiple cores

## Benefits

1. **Reduced Network Latency**: Jobs communicating between processes benefit from being on the same switch
2. **Better Bandwidth**: Same-switch communication avoids core switch bottlenecks
3. **Improved Performance**: Network-intensive workloads see better performance with topology-aware placement
4. **Realistic Simulation**: Allows experimentation with scheduling policies relevant to real HPC systems

## Limitations

- Currently, each node is assumed to have equal CPU and memory resources
- Node-to-CPU mapping is simplified (node N maps to CPU N-1)
- Topology changes require scheduler restart
- No dynamic topology updates during runtime

## Future Enhancements

Potential improvements:
- Per-node resource specifications (CPUs, memory per node)
- More sophisticated distance metrics (bandwidth, latency)
- Topology-aware job migration
- Support for GPU topology
- Dynamic topology updates
