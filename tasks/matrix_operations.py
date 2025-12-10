#!/usr/bin/env python3
"""
Heavy matrix operations benchmark.
Simulates large-scale linear algebra computations common in ML/AI.
"""
import numpy as np
import time
import os

def matrix_multiplication_benchmark(matrix_size=5000, num_iterations=10):
    """Perform large matrix multiplications."""
    print(f"[Matrix Ops] Starting benchmark: size={matrix_size}x{matrix_size}, iterations={num_iterations}")
    
    np.random.seed(42)
    results = []
    
    for i in range(num_iterations):
        iter_start = time.time()
        
        # Generate large matrices
        A = np.random.randn(matrix_size, matrix_size).astype(np.float32)
        B = np.random.randn(matrix_size, matrix_size).astype(np.float32)
        
        # Matrix multiplication (very CPU intensive)
        C = np.dot(A, B)
        
        # Additional operations
        D = np.linalg.inv(C + np.eye(matrix_size) * 0.01)  # Matrix inversion
        eigenvalues = np.linalg.eigvals(D[:min(100, matrix_size), :min(100, matrix_size)])
        
        iter_time = time.time() - iter_start
        results.append(iter_time)
        
        print(f"[Matrix Ops] Iteration {i+1}/{num_iterations} completed in {iter_time:.2f}s")
    
    avg_time = np.mean(results)
    print(f"[Matrix Ops] Average iteration time: {avg_time:.2f}s")
    print(f"[Matrix Ops] Total operations completed: {num_iterations}")
    
    return results


def svd_decomposition(matrix_size=3000):
    """Perform Singular Value Decomposition on large matrices."""
    print(f"[Matrix Ops] SVD decomposition: size={matrix_size}x{matrix_size}")
    
    np.random.seed(42)
    
    # Generate large matrix
    A = np.random.randn(matrix_size, matrix_size).astype(np.float32)
    
    start_time = time.time()
    
    # SVD decomposition (computationally expensive)
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    
    elapsed = time.time() - start_time
    
    print(f"[Matrix Ops] SVD completed in {elapsed:.2f}s")
    print(f"[Matrix Ops] Singular values range: [{s.min():.4f}, {s.max():.4f}]")
    
    return {"U": U.shape, "s": len(s), "Vt": Vt.shape}


def cholesky_factorization(matrix_size=4000):
    """Perform Cholesky decomposition (common in optimization)."""
    print(f"[Matrix Ops] Cholesky factorization: size={matrix_size}x{matrix_size}")
    
    np.random.seed(42)
    
    # Generate positive definite matrix
    A = np.random.randn(matrix_size, matrix_size).astype(np.float32)
    A = np.dot(A, A.T) + np.eye(matrix_size) * 0.1  # Make it positive definite
    
    start_time = time.time()
    
    # Cholesky decomposition
    L = np.linalg.cholesky(A)
    
    elapsed = time.time() - start_time
    
    print(f"[Matrix Ops] Cholesky factorization completed in {elapsed:.2f}s")
    print(f"[Matrix Ops] Lower triangular matrix shape: {L.shape}")
    
    return L.shape


if __name__ == "__main__":
    operation = os.getenv("OP", "multiply")
    matrix_size = int(os.getenv("SIZE", "5000"))
    num_iterations = int(os.getenv("ITERATIONS", "10"))
    
    start_time = time.time()
    
    if operation == "multiply":
        result = matrix_multiplication_benchmark(matrix_size=matrix_size, num_iterations=num_iterations)
    elif operation == "svd":
        result = svd_decomposition(matrix_size=matrix_size)
    elif operation == "cholesky":
        result = cholesky_factorization(matrix_size=matrix_size)
    else:
        print(f"Unknown operation: {operation}")
        sys.exit(1)
    
    total_time = time.time() - start_time
    print(f"[Matrix Ops] Total runtime: {total_time:.2f} seconds")
