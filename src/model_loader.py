"""
Model Loader Module

Handles loading trained models and scalers.
"""
import os
import joblib
from typing import Tuple, Optional


def find_model_and_scaler(models_dir: str = 'models') -> Tuple[Optional[str], Optional[str]]:
    """
    Find the best available model and scaler in the models directory.

    Priority:
    1. Random Forest baseline model (rf_day_model_*.joblib)
    2. LightGBM fold3 model (lgb_fold3_*.joblib)

    Args:
        models_dir: Directory containing model files (default: 'models')

    Returns:
        Tuple of (model_path, scaler_path), or (None, None) if not found
    """
    if not os.path.exists(models_dir):
        return None, None
        
    files = os.listdir(models_dir)
    
    # Prefer rf baseline if present
    rf = [f for f in files if f.startswith('rf_day_model') and f.endswith('.joblib')]
    if rf:
        model_path = os.path.join(models_dir, rf[0])
    else:
        # Fallback to lgb fold3
        lg = [f for f in files if f.startswith('lgb_fold3_') and f.endswith('.joblib')]
        model_path = os.path.join(models_dir, lg[0]) if lg else None
    
    # Find scaler
    scaler = [f for f in files if f.startswith('scaler_day') and f.endswith('.joblib')]
    scaler_path = os.path.join(models_dir, scaler[0]) if scaler else None
    
    return model_path, scaler_path


def load_model_and_scaler(model_path: str, scaler_path: str) -> Tuple:
    """
    Load model and scaler from disk.

    Args:
        model_path: Path to the model file
        scaler_path: Path to the scaler file

    Returns:
        Tuple of (model, scaler)
    """
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    return model, scaler
