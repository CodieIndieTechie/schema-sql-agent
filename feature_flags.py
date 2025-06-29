#!/usr/bin/env python3
"""
Feature Flag System for Schema-per-Tenant Migration

Provides feature flagging capabilities to enable gradual rollout of the new
schema-per-tenant architecture while maintaining backward compatibility.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class FeatureFlag(Enum):
    """Available feature flags."""
    SCHEMA_PER_TENANT = "schema_per_tenant"
    POSTGRESQL_CHAT_HISTORY = "postgresql_chat_history"
    NEW_FILE_UPLOAD = "new_file_upload"
    ENHANCED_QUERY_PROCESSING = "enhanced_query_processing"

@dataclass
class FeatureFlagConfig:
    """Configuration for a feature flag."""
    enabled: bool = False
    rollout_percentage: float = 0.0  # 0-100
    enabled_users: List[str] = None  # List of user emails
    disabled_users: List[str] = None  # List of user emails to exclude
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: str = ""
    
    def __post_init__(self):
        if self.enabled_users is None:
            self.enabled_users = []
        if self.disabled_users is None:
            self.disabled_users = []

class FeatureFlagManager:
    """Manages feature flags for the application."""
    
    def __init__(self):
        self.flags: Dict[FeatureFlag, FeatureFlagConfig] = {}
        self._load_feature_flags()
    
    def _load_feature_flags(self):
        """Load feature flags from environment variables and configuration."""
        # Default configurations
        self.flags = {
            FeatureFlag.SCHEMA_PER_TENANT: FeatureFlagConfig(
                enabled=self._get_env_bool("FEATURE_SCHEMA_PER_TENANT", False),
                rollout_percentage=self._get_env_float("FEATURE_SCHEMA_PER_TENANT_PERCENTAGE", 0.0),
                enabled_users=self._get_env_list("FEATURE_SCHEMA_PER_TENANT_USERS"),
                description="Enable schema-per-tenant architecture instead of database-per-tenant"
            ),
            FeatureFlag.POSTGRESQL_CHAT_HISTORY: FeatureFlagConfig(
                enabled=self._get_env_bool("FEATURE_POSTGRESQL_CHAT_HISTORY", False),
                rollout_percentage=self._get_env_float("FEATURE_POSTGRESQL_CHAT_HISTORY_PERCENTAGE", 0.0),
                enabled_users=self._get_env_list("FEATURE_POSTGRESQL_CHAT_HISTORY_USERS"),
                description="Use PostgreSQL-backed chat history instead of in-memory storage"
            ),
            FeatureFlag.NEW_FILE_UPLOAD: FeatureFlagConfig(
                enabled=self._get_env_bool("FEATURE_NEW_FILE_UPLOAD", False),
                rollout_percentage=self._get_env_float("FEATURE_NEW_FILE_UPLOAD_PERCENTAGE", 0.0),
                enabled_users=self._get_env_list("FEATURE_NEW_FILE_UPLOAD_USERS"),
                description="Use new schema-aware file upload process"
            ),
            FeatureFlag.ENHANCED_QUERY_PROCESSING: FeatureFlagConfig(
                enabled=self._get_env_bool("FEATURE_ENHANCED_QUERY_PROCESSING", False),
                rollout_percentage=self._get_env_float("FEATURE_ENHANCED_QUERY_PROCESSING_PERCENTAGE", 0.0),
                enabled_users=self._get_env_list("FEATURE_ENHANCED_QUERY_PROCESSING_USERS"),
                description="Use enhanced query processing with schema-per-tenant"
            )
        }
        
        logger.info("Loaded feature flags configuration")
        for flag, config in self.flags.items():
            if config.enabled or config.rollout_percentage > 0:
                logger.info(f"  {flag.value}: enabled={config.enabled}, rollout={config.rollout_percentage}%")
    
    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_env_float(self, key: str, default: float = 0.0) -> float:
        """Get float value from environment variable."""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_env_list(self, key: str) -> List[str]:
        """Get list of strings from environment variable (comma-separated)."""
        value = os.getenv(key, "")
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def is_enabled(self, flag: FeatureFlag, user_email: Optional[str] = None) -> bool:
        """
        Check if a feature flag is enabled for a user.
        
        Args:
            flag: The feature flag to check
            user_email: User email to check against (optional)
            
        Returns:
            True if the feature is enabled for the user
        """
        if flag not in self.flags:
            return False
        
        config = self.flags[flag]
        
        # Check if feature is globally disabled
        if not config.enabled and config.rollout_percentage == 0:
            return False
        
        # Check date constraints
        now = datetime.now()
        if config.start_date and now < config.start_date:
            return False
        if config.end_date and now > config.end_date:
            return False
        
        # If no user email provided, return global enabled status
        if not user_email:
            return config.enabled
        
        # Check if user is explicitly disabled
        if user_email in config.disabled_users:
            return False
        
        # Check if user is explicitly enabled
        if user_email in config.enabled_users:
            return True
        
        # If globally enabled, return true
        if config.enabled:
            return True
        
        # Check rollout percentage
        if config.rollout_percentage > 0:
            # Use deterministic hash of user email for consistent rollout
            import hashlib
            user_hash = int(hashlib.md5(user_email.encode()).hexdigest(), 16)
            user_percentage = (user_hash % 100) + 1  # 1-100
            return user_percentage <= config.rollout_percentage
        
        return False
    
    def enable_flag(self, flag: FeatureFlag, user_email: Optional[str] = None):
        """Enable a feature flag globally or for a specific user."""
        if flag not in self.flags:
            self.flags[flag] = FeatureFlagConfig()
        
        if user_email:
            if user_email not in self.flags[flag].enabled_users:
                self.flags[flag].enabled_users.append(user_email)
            # Remove from disabled list if present
            if user_email in self.flags[flag].disabled_users:
                self.flags[flag].disabled_users.remove(user_email)
        else:
            self.flags[flag].enabled = True
        
        logger.info(f"Enabled feature flag {flag.value}" + (f" for {user_email}" if user_email else " globally"))
    
    def disable_flag(self, flag: FeatureFlag, user_email: Optional[str] = None):
        """Disable a feature flag globally or for a specific user."""
        if flag not in self.flags:
            return
        
        if user_email:
            if user_email not in self.flags[flag].disabled_users:
                self.flags[flag].disabled_users.append(user_email)
            # Remove from enabled list if present
            if user_email in self.flags[flag].enabled_users:
                self.flags[flag].enabled_users.remove(user_email)
        else:
            self.flags[flag].enabled = False
        
        logger.info(f"Disabled feature flag {flag.value}" + (f" for {user_email}" if user_email else " globally"))
    
    def set_rollout_percentage(self, flag: FeatureFlag, percentage: float):
        """Set rollout percentage for a feature flag."""
        if flag not in self.flags:
            self.flags[flag] = FeatureFlagConfig()
        
        self.flags[flag].rollout_percentage = max(0.0, min(100.0, percentage))
        logger.info(f"Set rollout percentage for {flag.value} to {percentage}%")
    
    def get_flag_status(self, flag: FeatureFlag) -> Dict[str, Any]:
        """Get detailed status of a feature flag."""
        if flag not in self.flags:
            return {"exists": False}
        
        config = self.flags[flag]
        return {
            "exists": True,
            "enabled": config.enabled,
            "rollout_percentage": config.rollout_percentage,
            "enabled_users_count": len(config.enabled_users),
            "disabled_users_count": len(config.disabled_users),
            "description": config.description,
            "start_date": config.start_date.isoformat() if config.start_date else None,
            "end_date": config.end_date.isoformat() if config.end_date else None
        }
    
    def get_all_flags_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all feature flags."""
        return {flag.value: self.get_flag_status(flag) for flag in FeatureFlag}
    
    def get_user_flags(self, user_email: str) -> Dict[str, bool]:
        """Get all feature flags status for a specific user."""
        return {flag.value: self.is_enabled(flag, user_email) for flag in FeatureFlag}

# Global feature flag manager instance
feature_flags = FeatureFlagManager()

# Convenience functions
def is_schema_per_tenant_enabled(user_email: Optional[str] = None) -> bool:
    """Check if schema-per-tenant is enabled for a user."""
    return feature_flags.is_enabled(FeatureFlag.SCHEMA_PER_TENANT, user_email)

def is_postgresql_chat_history_enabled(user_email: Optional[str] = None) -> bool:
    """Check if PostgreSQL chat history is enabled for a user."""
    return feature_flags.is_enabled(FeatureFlag.POSTGRESQL_CHAT_HISTORY, user_email)

def is_new_file_upload_enabled(user_email: Optional[str] = None) -> bool:
    """Check if new file upload process is enabled for a user."""
    return feature_flags.is_enabled(FeatureFlag.NEW_FILE_UPLOAD, user_email)

def is_enhanced_query_processing_enabled(user_email: Optional[str] = None) -> bool:
    """Check if enhanced query processing is enabled for a user."""
    return feature_flags.is_enabled(FeatureFlag.ENHANCED_QUERY_PROCESSING, user_email)

# Migration helper functions
def enable_schema_per_tenant_for_user(user_email: str):
    """Enable schema-per-tenant for a specific user."""
    feature_flags.enable_flag(FeatureFlag.SCHEMA_PER_TENANT, user_email)
    feature_flags.enable_flag(FeatureFlag.POSTGRESQL_CHAT_HISTORY, user_email)
    feature_flags.enable_flag(FeatureFlag.NEW_FILE_UPLOAD, user_email)
    feature_flags.enable_flag(FeatureFlag.ENHANCED_QUERY_PROCESSING, user_email)

def enable_schema_per_tenant_rollout(percentage: float):
    """Enable schema-per-tenant for a percentage of users."""
    feature_flags.set_rollout_percentage(FeatureFlag.SCHEMA_PER_TENANT, percentage)
    feature_flags.set_rollout_percentage(FeatureFlag.POSTGRESQL_CHAT_HISTORY, percentage)
    feature_flags.set_rollout_percentage(FeatureFlag.NEW_FILE_UPLOAD, percentage)
    feature_flags.set_rollout_percentage(FeatureFlag.ENHANCED_QUERY_PROCESSING, percentage)

def enable_schema_per_tenant_globally():
    """Enable schema-per-tenant for all users."""
    feature_flags.enable_flag(FeatureFlag.SCHEMA_PER_TENANT)
    feature_flags.enable_flag(FeatureFlag.POSTGRESQL_CHAT_HISTORY)
    feature_flags.enable_flag(FeatureFlag.NEW_FILE_UPLOAD)
    feature_flags.enable_flag(FeatureFlag.ENHANCED_QUERY_PROCESSING)

if __name__ == "__main__":
    # Test feature flags
    print("Feature Flags Status:")
    print(json.dumps(feature_flags.get_all_flags_status(), indent=2))
    
    # Test user-specific flags
    test_email = "test@example.com"
    print(f"\nFeature flags for {test_email}:")
    print(json.dumps(feature_flags.get_user_flags(test_email), indent=2))
    
    # Test enabling for specific user
    enable_schema_per_tenant_for_user(test_email)
    print(f"\nAfter enabling schema-per-tenant for {test_email}:")
    print(json.dumps(feature_flags.get_user_flags(test_email), indent=2))
