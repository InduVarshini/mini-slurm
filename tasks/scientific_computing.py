#!/usr/bin/env python3
"""
Scientific computing simulations.
Simulates physics simulations, differential equations, and numerical methods.
"""
import numpy as np
import time
import os

def solve_heat_equation(grid_size=1000, time_steps=1000):
    """Solve 2D heat equation using finite difference method."""
    print(f"[Scientific Computing] Solving heat equation: grid={grid_size}x{grid_size}, steps={time_steps}")
    
    # Initialize grid
    u = np.zeros((grid_size, grid_size), dtype=np.float32)
    
    # Set initial conditions (hot spot in center)
    center = grid_size // 2
    u[center-10:center+10, center-10:center+10] = 100.0
    
    # Boundary conditions (zero temperature at edges)
    u[0, :] = 0.0
    u[-1, :] = 0.0
    u[:, 0] = 0.0
    u[:, -1] = 0.0
    
    # Diffusion coefficient
    alpha = 0.1
    dt = 0.01
    dx = 1.0
    
    # Time stepping
    for step in range(time_steps):
        # Compute Laplacian using finite differences
        laplacian = np.zeros_like(u)
        laplacian[1:-1, 1:-1] = (
            u[2:, 1:-1] + u[:-2, 1:-1] + 
            u[1:-1, 2:] + u[1:-1, :-2] - 
            4 * u[1:-1, 1:-1]
        ) / (dx**2)
        
        # Update using explicit Euler method
        u[1:-1, 1:-1] += alpha * dt * laplacian[1:-1, 1:-1]
        
        # Maintain boundary conditions
        u[0, :] = 0.0
        u[-1, :] = 0.0
        u[:, 0] = 0.0
        u[:, -1] = 0.0
        
        if step % 100 == 0:
            max_temp = np.max(u)
            print(f"[Scientific Computing] Step {step}/{time_steps}, max temperature: {max_temp:.4f}")
    
    print(f"[Scientific Computing] Final max temperature: {np.max(u):.4f}")
    return u


def n_body_simulation(num_bodies=10000, time_steps=1000):
    """N-body gravitational simulation."""
    print(f"[Scientific Computing] N-body simulation: {num_bodies} bodies, {time_steps} steps")
    
    np.random.seed(42)
    
    # Initialize positions and velocities
    positions = np.random.randn(num_bodies, 3).astype(np.float32) * 10.0
    velocities = np.random.randn(num_bodies, 3).astype(np.float32) * 0.1
    masses = np.random.uniform(0.1, 10.0, num_bodies).astype(np.float32)
    
    dt = 0.01
    G = 1.0  # Gravitational constant
    
    for step in range(time_steps):
        # Compute forces between all pairs (O(n^2) operation)
        forces = np.zeros_like(positions)
        
        for i in range(num_bodies):
            for j in range(num_bodies):
                if i != j:
                    # Vector from i to j
                    r_vec = positions[j] - positions[i]
                    r = np.linalg.norm(r_vec)
                    
                    if r > 0.1:  # Avoid division by zero
                        # Gravitational force
                        force_magnitude = G * masses[i] * masses[j] / (r**2)
                        force_vec = force_magnitude * r_vec / r
                        forces[i] += force_vec
        
        # Update velocities and positions
        accelerations = forces / masses[:, np.newaxis]
        velocities += accelerations * dt
        positions += velocities * dt
        
        if step % 100 == 0:
            center_of_mass = np.sum(positions * masses[:, np.newaxis], axis=0) / np.sum(masses)
            print(f"[Scientific Computing] Step {step}/{time_steps}, center of mass: {center_of_mass}")
    
    print(f"[Scientific Computing] Simulation completed")
    return positions, velocities


def solve_linear_system(matrix_size=5000):
    """Solve large system of linear equations."""
    print(f"[Scientific Computing] Solving linear system: {matrix_size}x{matrix_size}")
    
    np.random.seed(42)
    
    # Generate system Ax = b
    A = np.random.randn(matrix_size, matrix_size).astype(np.float32)
    A = A + A.T + np.eye(matrix_size) * matrix_size  # Make it positive definite
    b = np.random.randn(matrix_size).astype(np.float32)
    
    # Solve using various methods
    print("[Scientific Computing] Solving using LU decomposition...")
    start = time.time()
    x_lu = np.linalg.solve(A, b)
    lu_time = time.time() - start
    print(f"[Scientific Computing] LU solve completed in {lu_time:.2f}s")
    
    # Verify solution
    residual = np.linalg.norm(A @ x_lu - b)
    print(f"[Scientific Computing] Residual: {residual:.2e}")
    
    return x_lu


def finite_element_analysis(grid_size=500):
    """Simulate finite element analysis (structural mechanics)."""
    print(f"[Scientific Computing] FEA simulation: grid={grid_size}x{grid_size}")
    
    np.random.seed(42)
    
    # Create stiffness matrix (simplified)
    num_nodes = grid_size * grid_size
    print(f"[Scientific Computing] Number of nodes: {num_nodes:,}")
    
    # Simplified: create sparse-like structure
    # In real FEA, this would be assembled from element matrices
    K = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    
    # Populate stiffness matrix (simplified band structure)
    for i in range(num_nodes):
        K[i, i] = 4.0  # Diagonal
        if i > 0:
            K[i, i-1] = -1.0  # Lower diagonal
        if i < num_nodes - 1:
            K[i, i+1] = -1.0  # Upper diagonal
        if i >= grid_size:
            K[i, i-grid_size] = -1.0  # Lower band
        if i < num_nodes - grid_size:
            K[i, i+grid_size] = -1.0  # Upper band
    
    # Apply boundary conditions (fix some nodes)
    fixed_nodes = list(range(0, grid_size))  # Fix bottom edge
    for node in fixed_nodes:
        K[node, :] = 0.0
        K[:, node] = 0.0
        K[node, node] = 1.0
    
    # Load vector
    F = np.random.randn(num_nodes).astype(np.float32)
    F[fixed_nodes] = 0.0  # No load on fixed nodes
    
    # Solve Ku = F
    print("[Scientific Computing] Solving system...")
    start = time.time()
    u = np.linalg.solve(K, F)
    solve_time = time.time() - start
    print(f"[Scientific Computing] System solved in {solve_time:.2f}s")
    
    max_displacement = np.max(np.abs(u))
    print(f"[Scientific Computing] Maximum displacement: {max_displacement:.4f}")
    
    return u


if __name__ == "__main__":
    simulation_type = os.getenv("SIM_TYPE", "heat")
    grid_size = int(os.getenv("GRID_SIZE", "1000"))
    time_steps = int(os.getenv("TIME_STEPS", "1000"))
    num_bodies = int(os.getenv("NUM_BODIES", "10000"))
    matrix_size = int(os.getenv("MATRIX_SIZE", "5000"))
    
    start_time = time.time()
    
    if simulation_type == "heat":
        result = solve_heat_equation(grid_size=grid_size, time_steps=time_steps)
    elif simulation_type == "nbody":
        result = n_body_simulation(num_bodies=num_bodies, time_steps=time_steps)
    elif simulation_type == "linear":
        result = solve_linear_system(matrix_size=matrix_size)
    elif simulation_type == "fea":
        result = finite_element_analysis(grid_size=grid_size)
    else:
        print(f"Unknown simulation type: {simulation_type}")
        sys.exit(1)
    
    total_time = time.time() - start_time
    print(f"[Scientific Computing] Total runtime: {total_time:.2f} seconds")
