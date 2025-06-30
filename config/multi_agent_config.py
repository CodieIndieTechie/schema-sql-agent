"""
Multi-Agent System Configuration Management

This module handles configuration loading and validation for the multi-agent system.
It reads environment variables and provides structured configuration objects.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class OpenAIConfig:
    """Configuration for OpenAI API"""
    api_key: str
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 3000
    
    @classmethod
    def from_env(cls) -> 'OpenAIConfig':
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("AGENT_MODEL", "gpt-4o"),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "3000"))
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature must be between 0 and 2")
        if self.max_tokens < 100 or self.max_tokens > 4000:
            raise ValueError("Max tokens must be between 100 and 4000")
        return True

@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator"""
    max_iterations: int = 10
    timeout_seconds: int = 300
    enable_caching: bool = True
    
    @classmethod
    def from_env(cls) -> 'OrchestratorConfig':
        return cls(
            max_iterations=int(os.getenv("MAX_AGENT_ITERATIONS", "10")),
            timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", "300")),
            enable_caching=os.getenv("ENABLE_AGENT_CACHING", "true").lower() == "true"
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if self.max_iterations < 1 or self.max_iterations > 50:
            raise ValueError("Max iterations must be between 1 and 50")
        if self.timeout_seconds < 30 or self.timeout_seconds > 1800:
            raise ValueError("Timeout must be between 30 and 1800 seconds")
        return True

@dataclass
class WebAgentConfig:
    """Configuration for web research agent"""
    enabled: bool = False
    search_enabled: bool = False
    scraping_timeout: int = 30
    max_sources: int = 5
    
    @classmethod
    def from_env(cls) -> 'WebAgentConfig':
        return cls(
            enabled=os.getenv("ENABLE_WEB_RESEARCH", "true").lower() == "true",
            search_enabled=os.getenv("WEB_SEARCH_ENABLED", "false").lower() == "true",
            scraping_timeout=int(os.getenv("WEB_SCRAPING_TIMEOUT", "30")),
            max_sources=int(os.getenv("MAX_WEB_SOURCES", "5"))
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if self.scraping_timeout < 5 or self.scraping_timeout > 120:
            raise ValueError("Scraping timeout must be between 5 and 120 seconds")
        if self.max_sources < 1 or self.max_sources > 20:
            raise ValueError("Max sources must be between 1 and 20")
        return True

@dataclass
class FormatterConfig:
    """Configuration for data formatter agent"""
    enable_charts: bool = True
    max_chart_points: int = 100
    
    @classmethod
    def from_env(cls) -> 'FormatterConfig':
        return cls(
            enable_charts=os.getenv("ENABLE_CHART_GENERATION", "true").lower() == "true",
            max_chart_points=int(os.getenv("MAX_CHART_DATA_POINTS", "100"))
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        if self.max_chart_points < 10 or self.max_chart_points > 1000:
            raise ValueError("Max chart points must be between 10 and 1000")
        return True

@dataclass
class ExpertConfig:
    """Configuration for mutual fund expert agent"""
    enabled: bool = True
    analysis_depth: str = "comprehensive"
    
    @classmethod
    def from_env(cls) -> 'ExpertConfig':
        return cls(
            enabled=os.getenv("MUTUAL_FUND_EXPERT_ENABLED", "true").lower() == "true",
            analysis_depth=os.getenv("FINANCIAL_ANALYSIS_DEPTH", "comprehensive")
        )
    
    def validate(self) -> bool:
        """Validate configuration"""
        valid_depths = ["basic", "standard", "comprehensive", "detailed"]
        if self.analysis_depth not in valid_depths:
            raise ValueError(f"Analysis depth must be one of: {valid_depths}")
        return True

@dataclass
class MultiAgentSystemConfig:
    """Complete multi-agent system configuration"""
    openai: OpenAIConfig
    orchestrator: OrchestratorConfig
    web_agent: WebAgentConfig
    formatter: FormatterConfig
    expert: ExpertConfig
    
    @classmethod
    def from_env(cls) -> 'MultiAgentSystemConfig':
        """Load configuration from environment variables"""
        return cls(
            openai=OpenAIConfig.from_env(),
            orchestrator=OrchestratorConfig.from_env(),
            web_agent=WebAgentConfig.from_env(),
            formatter=FormatterConfig.from_env(),
            expert=ExpertConfig.from_env()
        )
    
    def validate(self) -> bool:
        """Validate all configuration sections"""
        try:
            self.openai.validate()
            self.orchestrator.validate()
            self.web_agent.validate()
            self.formatter.validate()
            self.expert.validate()
            return True
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "openai": {
                "model": self.openai.model,
                "temperature": self.openai.temperature,
                "max_tokens": self.openai.max_tokens,
                "api_key_configured": bool(self.openai.api_key)
            },
            "orchestrator": {
                "max_iterations": self.orchestrator.max_iterations,
                "timeout_seconds": self.orchestrator.timeout_seconds,
                "caching_enabled": self.orchestrator.enable_caching
            },
            "web_agent": {
                "enabled": self.web_agent.enabled,
                "search_enabled": self.web_agent.search_enabled,
                "scraping_timeout": self.web_agent.scraping_timeout,
                "max_sources": self.web_agent.max_sources
            },
            "formatter": {
                "charts_enabled": self.formatter.enable_charts,
                "max_chart_points": self.formatter.max_chart_points
            },
            "expert": {
                "enabled": self.expert.enabled,
                "analysis_depth": self.expert.analysis_depth
            }
        }

# Global configuration instance
_config: Optional[MultiAgentSystemConfig] = None

def get_config() -> MultiAgentSystemConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = MultiAgentSystemConfig.from_env()
        _config.validate()
    return _config

def reload_config() -> MultiAgentSystemConfig:
    """Reload configuration from environment"""
    global _config
    _config = None
    return get_config()

def is_feature_enabled(feature: str) -> bool:
    """Check if a specific feature is enabled"""
    config = get_config()
    
    feature_map = {
        "web_research": config.web_agent.enabled,
        "web_search": config.web_agent.search_enabled,
        "chart_generation": config.formatter.enable_charts,
        "expert_analysis": config.expert.enabled,
        "agent_caching": config.orchestrator.enable_caching
    }
    
    return feature_map.get(feature, False)

def get_openai_config() -> OpenAIConfig:
    """Get OpenAI configuration"""
    return get_config().openai

def get_orchestrator_config() -> OrchestratorConfig:
    """Get orchestrator configuration"""
    return get_config().orchestrator
