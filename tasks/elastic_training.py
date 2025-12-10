#!/usr/bin/env python3
"""
Elastic Neural Network Training Job

This job demonstrates elastic scaling capabilities:
- Starts with minimum resources
- Scales up when more CPUs become available
- Scales down gracefully when resources are needed elsewhere
- Uses control file to detect resource changes

Usage:
    python3 mini-slurm.py submit --elastic --cpus 2 --min-cpus 2 --max-cpus 8 --mem 4GB \
        "python3 tasks/elastic_training.py"
"""
import numpy as np
import time
import sys
import os
import threading

# Signal handling (Unix only)
try:
    import signal
    HAS_SIGNAL = True
except ImportError:
    HAS_SIGNAL = False

# Global state for handling resource changes
current_cpus = None
control_file = None
should_check_resources = True
resource_lock = threading.Lock()


def signal_handler(signum, frame):
    """Handle SIGUSR1 signal indicating resource change."""
    global should_check_resources
    should_check_resources = True
    print(f"[Elastic Training] Received resource change signal (SIGUSR1)")


def read_control_file(control_file_path):
    """Read current resource allocation from control file."""
    if not os.path.exists(control_file_path):
        return None
    
    try:
        with open(control_file_path, 'r') as f:
            config = {}
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
        return config
    except (IOError, OSError) as e:
        print(f"[Elastic Training] Warning: Could not read control file: {e}", file=sys.stderr)
        return None


def get_current_cpus():
    """Get current CPU allocation from control file or environment."""
    global current_cpus, control_file
    
    # Try control file first (most up-to-date)
    if control_file and os.path.exists(control_file):
        config = read_control_file(control_file)
        if config and 'CPUS' in config:
            try:
                return int(config['CPUS'])
            except ValueError:
                pass
    
    # Fall back to environment variable
    env_cpus = os.getenv("MINI_SLURM_CURRENT_CPUS")
    if env_cpus:
        try:
            return int(env_cpus)
        except ValueError:
            pass
    
    # Default fallback
    return current_cpus or 2


def check_and_update_resources():
    """Check for resource changes and update accordingly."""
    global current_cpus, should_check_resources
    
    if not should_check_resources:
        return current_cpus
    
    with resource_lock:
        if not should_check_resources:
            return current_cpus
        
        new_cpus = get_current_cpus()
        if new_cpus != current_cpus:
            old_cpus = current_cpus
            current_cpus = new_cpus
            should_check_resources = False
            
            if old_cpus is not None:
                print(f"[Elastic Training] Resource change detected: {old_cpus} -> {new_cpus} CPUs")
                if new_cpus > old_cpus:
                    print(f"[Elastic Training] Scaling UP: Increasing parallelism")
                else:
                    print(f"[Elastic Training] Scaling DOWN: Reducing parallelism")
            else:
                print(f"[Elastic Training] Initialized with {new_cpus} CPUs")
        
        return current_cpus


def simulate_training_epoch(epoch, num_cpus, batch_size_base=128):
    """Simulate a training epoch with adaptive batch size based on CPUs."""
    # Scale batch size with available CPUs (rough approximation)
    effective_batch_size = batch_size_base * num_cpus
    
    print(f"[Elastic Training] Epoch {epoch}: Using {num_cpus} CPUs, batch_size={effective_batch_size}")
    
    epoch_start = time.time()
    
    # Simulate training with matrix operations
    # More CPUs = more parallel operations
    num_batches = 100 // num_cpus  # Adjust batches based on CPUs
    
    for batch in range(num_batches):
        # Simulate forward pass
        a = np.random.randn(1000, 1000).astype(np.float32)
        b = np.random.randn(1000, 1000).astype(np.float32)
        c = np.dot(a, b)
        
        # Simulate backward pass
        grad = np.random.randn(1000, 1000).astype(np.float32)
        _ = np.dot(c, grad)
        
        # Check for resource changes periodically
        if batch % 10 == 0:
            check_and_update_resources()
    
    epoch_time = time.time() - epoch_start
    loss = np.random.uniform(0.5, 2.0)
    
    return epoch_time, loss


def elastic_training(epochs=50):
    """Main training loop that adapts to resource changes."""
    global current_cpus, control_file
    
    # Initialize resource tracking
    control_file = os.getenv("MINI_SLURM_CONTROL_FILE")
    if control_file:
        print(f"[Elastic Training] Control file: {control_file}")
    
    # Set up signal handler for resource change notifications (Unix only)
    if HAS_SIGNAL:
        try:
            signal.signal(signal.SIGUSR1, signal_handler)
        except (AttributeError, ValueError):
            # SIGUSR1 not available on this platform
            pass
    
    # Get initial CPU allocation
    current_cpus = check_and_update_resources()
    min_cpus = int(os.getenv("MINI_SLURM_MIN_CPUS", str(current_cpus)))
    max_cpus = int(os.getenv("MINI_SLURM_MAX_CPUS", str(current_cpus)))
    
    print(f"[Elastic Training] Starting elastic training")
    print(f"[Elastic Training] CPU range: {min_cpus} - {max_cpus}")
    print(f"[Elastic Training] Initial CPUs: {current_cpus}")
    print(f"[Elastic Training] Epochs: {epochs}")
    
    # Training loop
    for epoch in range(epochs):
        # Check for resource changes at start of each epoch
        num_cpus = check_and_update_resources()
        
        # Run training epoch with current resource allocation
        epoch_time, loss = simulate_training_epoch(epoch, num_cpus)
        
        if epoch % 5 == 0:
            print(f"[Elastic Training] Epoch {epoch}/{epochs} - Loss: {loss:.4f} - "
                  f"Time: {epoch_time:.2f}s - CPUs: {num_cpus}")
    
    print(f"[Elastic Training] Training completed successfully!")
    return {"final_loss": loss, "total_epochs": epochs, "final_cpus": current_cpus}


if __name__ == "__main__":
    # Parse command line arguments
    epochs = int(os.getenv("EPOCHS", "50"))
    
    start_time = time.time()
    result = elastic_training(epochs=epochs)
    total_time = time.time() - start_time
    
    print(f"[Elastic Training] Total runtime: {total_time:.2f} seconds")
    print(f"[Elastic Training] Final loss: {result['final_loss']:.4f}")
    print(f"[Elastic Training] Final CPU allocation: {result['final_cpus']}")
