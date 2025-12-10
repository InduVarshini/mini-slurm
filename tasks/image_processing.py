#!/usr/bin/env python3
"""
Heavy image processing pipeline.
Simulates batch image processing, feature extraction, and transformations.
"""
import numpy as np
import time
import os

def process_image_batch(num_images=1000, image_size=2048):
    """Process a batch of images with various transformations."""
    print(f"[Image Processing] Processing {num_images} images of size {image_size}x{image_size}")
    
    np.random.seed(42)
    processed_count = 0
    
    for i in range(num_images):
        # Simulate loading image (large array)
        image = np.random.randint(0, 255, (image_size, image_size, 3), dtype=np.uint8)
        
        # Convert to float for processing
        image_float = image.astype(np.float32) / 255.0
        
        # Apply transformations (CPU intensive)
        # 1. Gaussian blur simulation (convolution)
        kernel_size = 15
        kernel = np.random.randn(kernel_size, kernel_size)
        kernel = kernel / np.sum(kernel)
        
        # Simulate convolution (simplified)
        blurred = np.convolve(image_float.flatten(), kernel.flatten(), mode='same')
        blurred = blurred.reshape(image_float.shape)
        
        # 2. Edge detection (gradient computation)
        grad_x = np.gradient(blurred[:, :, 0], axis=1)
        grad_y = np.gradient(blurred[:, :, 0], axis=0)
        edges = np.sqrt(grad_x**2 + grad_y**2)
        
        # 3. Feature extraction (compute statistics)
        features = {
            'mean': np.mean(image_float),
            'std': np.std(image_float),
            'max': np.max(image_float),
            'min': np.min(image_float),
            'edge_strength': np.mean(edges),
        }
        
        # 4. Resize simulation (downsample)
        scale_factor = 0.5
        new_size = int(image_size * scale_factor)
        resized = np.random.randn(new_size, new_size, 3)  # Simulated resize
        
        processed_count += 1
        
        if (i + 1) % 100 == 0:
            print(f"[Image Processing] Processed {i+1}/{num_images} images")
    
    print(f"[Image Processing] Successfully processed {processed_count} images")
    return processed_count


def feature_extraction_pipeline(num_images=500, feature_dim=2048):
    """Extract features from images (simulating CNN feature extraction)."""
    print(f"[Image Processing] Feature extraction: {num_images} images, {feature_dim}D features")
    
    np.random.seed(42)
    features_list = []
    
    for i in range(num_images):
        # Simulate image
        image = np.random.randn(224, 224, 3).astype(np.float32)
        
        # Simulate feature extraction (multiple convolutional layers)
        # This simulates the computational cost of CNN forward pass
        x = image
        for layer in range(5):  # 5 layers
            # Simulate convolution + activation
            x = np.random.randn(*x.shape).astype(np.float32)
            x = np.maximum(0, x)  # ReLU activation
            
            # Simulate pooling
            if layer % 2 == 0:
                x = x[::2, ::2, :]  # Max pooling simulation
        
        # Global average pooling
        feature_vector = np.mean(x, axis=(0, 1))
        
        # Expand to desired dimension
        if len(feature_vector) < feature_dim:
            feature_vector = np.tile(feature_vector, feature_dim // len(feature_vector) + 1)[:feature_dim]
        
        features_list.append(feature_vector)
        
        if (i + 1) % 50 == 0:
            print(f"[Image Processing] Extracted features from {i+1}/{num_images} images")
    
    features_array = np.array(features_list)
    print(f"[Image Processing] Feature matrix shape: {features_array.shape}")
    
    return features_array


if __name__ == "__main__":
    task_type = os.getenv("TASK", "batch")
    num_images = int(os.getenv("NUM_IMAGES", "1000"))
    image_size = int(os.getenv("IMAGE_SIZE", "2048"))
    feature_dim = int(os.getenv("FEATURE_DIM", "2048"))
    
    start_time = time.time()
    
    if task_type == "batch":
        result = process_image_batch(num_images=num_images, image_size=image_size)
    elif task_type == "features":
        result = feature_extraction_pipeline(num_images=num_images, feature_dim=feature_dim)
    else:
        print(f"Unknown task type: {task_type}")
        sys.exit(1)
    
    total_time = time.time() - start_time
    print(f"[Image Processing] Total runtime: {total_time:.2f} seconds")
