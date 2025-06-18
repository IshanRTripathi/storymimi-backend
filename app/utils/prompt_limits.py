"""Configuration for prompt length limits and component allocations."""

# Total prompt length limits
MAX_TOTAL_PROMPT_LENGTH = 2500  # Maximum total length for all components
MIN_TOTAL_PROMPT_LENGTH = 1000  # Minimum recommended length

# Component allocations (percentages of total)
PROMPT_COMPONENT_ALLOCATIONS = {
    'base_style': 0.25,      # Base style and composition (25%)
    'scene': 0.35,           # Scene description (35%) 
    'characters': 0.20,      # Character/subject details (20%)
    'atmosphere': 0.10,      # Lighting and atmosphere (10%)
    'technical': 0.10,       # Technical parameters (10%)
}

# Per-model length limits
MODEL_SPECIFIC_LIMITS = {
    'midjourney': {
        'max_length': 2000,
        'optimal_length': 1500,
    },
    'leonardo': {
        'max_length': 3000,
        'optimal_length': 2500,
    },
    'stable_diffusion': {
        'max_length': 2500,
        'optimal_length': 2000,
    },
    'google_imagen': {
        'max_length': 2500,
        'optimal_length': 2000,
    }
}

def get_component_limit(component: str, total_length: int = MAX_TOTAL_PROMPT_LENGTH) -> int:
    """Calculate character limit for a specific prompt component."""
    if component not in PROMPT_COMPONENT_ALLOCATIONS:
        raise ValueError(f"Unknown component: {component}")
    return int(total_length * PROMPT_COMPONENT_ALLOCATIONS[component])

def get_model_limits(model: str) -> dict:
    """Get length limits for a specific model."""
    if model not in MODEL_SPECIFIC_LIMITS:
        return {
            'max_length': MAX_TOTAL_PROMPT_LENGTH,
            'optimal_length': MAX_TOTAL_PROMPT_LENGTH
        }
    return MODEL_SPECIFIC_LIMITS[model] 

