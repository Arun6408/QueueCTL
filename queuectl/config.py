"""Configuration management for QueueCTL."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager with file-based persistence."""
    
    DEFAULT_CONFIG = {
        "max_retries": 3,
        "backoff_base": 2,
        "default_timeout": 300,  # 5 minutes
        "worker_poll_interval": 1,  # seconds
        "db_path": "queuectl.db",
        "log_dir": "logs",
        "web_dashboard_port": 8080,
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration."""
        if config_file is None:
            config_dir = Path.home() / ".queuectl"
            config_dir.mkdir(exist_ok=True)
            config_file = str(config_dir / "config.json")
        
        self.config_file = Path(config_file)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged = self.DEFAULT_CONFIG.copy()
                    merged.update(config)
                    return merged
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self):
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._config[key] = value
        self._save_config()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration."""
        return self._config.copy()
    
    def reset(self):
        """Reset to default configuration."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_config()

