# Quantum Computing Tools
from quantum_library import QuantumOptimizer

def optimize_system_performance(system_config):
    print("[INFO] Optimizing system performance using quantum computing...")
    optimizer = QuantumOptimizer()
    optimized_config = optimizer.optimize(system_config)
    print("[DEBUG] Optimization complete.")
    return optimized_config
