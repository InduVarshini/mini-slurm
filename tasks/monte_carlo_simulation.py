#!/usr/bin/env python3
"""
Monte Carlo simulation for option pricing or scientific computing.
CPU-intensive statistical simulation.
"""
import numpy as np
import time
import os
import sys

def monte_carlo_pi(num_samples=100_000_000):
    """Estimate pi using Monte Carlo method."""
    print(f"[Monte Carlo] Starting simulation with {num_samples:,} samples")
    
    # Generate random points
    np.random.seed(42)
    x = np.random.uniform(-1, 1, num_samples)
    y = np.random.uniform(-1, 1, num_samples)
    
    # Count points inside unit circle
    inside_circle = (x**2 + y**2) <= 1
    count_inside = np.sum(inside_circle)
    
    # Estimate pi
    pi_estimate = 4 * count_inside / num_samples
    error = abs(pi_estimate - np.pi)
    
    print(f"[Monte Carlo] Pi estimate: {pi_estimate:.10f}")
    print(f"[Monte Carlo] Actual pi:   {np.pi:.10f}")
    print(f"[Monte Carlo] Error:       {error:.10f}")
    
    return pi_estimate


def monte_carlo_option_pricing(num_simulations=10_000_000):
    """Simulate option pricing using Monte Carlo method."""
    print(f"[Monte Carlo] Option pricing simulation with {num_simulations:,} paths")
    
    # Parameters
    S0 = 100.0  # Initial stock price
    K = 105.0   # Strike price
    T = 1.0     # Time to expiration
    r = 0.05    # Risk-free rate
    sigma = 0.2 # Volatility
    
    np.random.seed(42)
    
    # Generate random paths
    dt = T / 252  # Daily steps
    num_steps = int(T / dt)
    
    # Simulate stock price paths
    payoffs = []
    for _ in range(num_simulations // 1000):  # Batch processing
        # Generate random increments
        random_shocks = np.random.normal(0, 1, (1000, num_steps))
        
        # Simulate price paths
        for i in range(1000):
            S = S0
            for step in range(num_steps):
                S *= np.exp((r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * random_shocks[i, step])
            
            # Calculate payoff (European call option)
            payoff = max(S - K, 0)
            payoffs.append(payoff)
    
    # Discount and average
    option_price = np.exp(-r * T) * np.mean(payoffs)
    
    print(f"[Monte Carlo] Estimated option price: ${option_price:.4f}")
    return option_price


if __name__ == "__main__":
    simulation_type = os.getenv("SIM_TYPE", "pi")
    num_samples = int(os.getenv("NUM_SAMPLES", "100000000"))
    
    start_time = time.time()
    
    if simulation_type == "pi":
        result = monte_carlo_pi(num_samples=num_samples)
    elif simulation_type == "option":
        result = monte_carlo_option_pricing(num_simulations=num_samples)
    else:
        print(f"Unknown simulation type: {simulation_type}")
        sys.exit(1)
    
    total_time = time.time() - start_time
    print(f"[Monte Carlo] Total runtime: {total_time:.2f} seconds")
