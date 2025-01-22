# HPC Research Project Documentation

## Overview
This project provides a distributed system for running High-Performance Computing (HPC) benchmarks across multiple nodes. It consists of a master node that coordinates benchmark executions and multiple worker nodes that perform the actual computations.

## Architecture

### Master Node
Located in `src/master`, the master node:
- Manages node registration and coordination
- Provides a command-line interface for benchmark control
- Handles SSH key distribution for node communication
- Collects and aggregates benchmark results

Key components:
- `main.py`: Entry point and server initialization
- `menu_handler.py`: CLI interface
- `node_api.py`: Node communication interface

### Worker Nodes 
Located in `src/node`, worker nodes:
- Execute HPL benchmarks
- Collect system metrics using Collectl
- Report results back to master

Key components:
- `server.py`: Node API server
- `scheduler.py`: Benchmark execution manager
- `worker.py`: Task execution handler

## Features

### 1. Benchmark Types

#### Competitive Mode
- Multiple HPL instances run simultaneously on each node
- Each instance competes for system resources
- Used to measure maximum node performance

#### Cooperative Mode
- Single HPL instance distributed across multiple nodes
- Nodes work together on one large problem
- Tests inter-node communication and scaling

### 2. Monitoring
- Real-time system metrics collection via Collectl
- Resource utilization tracking
- Performance data aggregation

### 3. Result Analysis
Located in `src/report`:
- Result parsing and aggregation
- Statistical analysis
- Graph generation
- Performance comparisons

## Prerequisites
- Linux-based operating system
- Python 3.8 or higher
- Root access for installation
- Network connectivity between nodes

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hpc-research.git
cd hpc-research
```
2. Install dependencies:
```bash
sudo bash ./src/ressources/new_hpc.sh
```

3. Start the master node:
```bash
./run.sh --master
```

4. Start worker nodes:
```bash
./run.sh
```

## Configuration

### Master Node
- Default port: 8000
- Configurable via environment variables:
  - `API_HOST`
  - `API_PORT`

### Worker Node
- Default port: 5000
- Configurable via environment variables:
  - `API_HOST`
  - `API_PORT`
  - `MASTER_IP`
  - `MASTER_PORT`

## Security
- SSH key-based authentication between nodes
- Automatic key distribution
- No password authentication

## Testing
Located in `testsuite`:
- Unit tests for core functionality
- Integration tests for node communication
- Collectl testing suite

## Dependencies
Core requirements from `requirements.txt`:
```
flask==3.0.0
types-flask==1.1.6
typing-extensions>=4.8.0
requests==2.31.0
psutil==5.9.8
```

Additional system requirements:
- Python 3.x
- HPL (High-Performance Linpack)
- Collectl
- OpenMPI

## License
This project is licensed under the MIT License.