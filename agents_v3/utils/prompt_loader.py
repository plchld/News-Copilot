"""Utility for loading external prompt files - wrapper for enhanced loader"""

from typing import Dict, Optional
from .enhanced_prompt_loader import enhanced_prompt_loader


class PromptLoader:
    """Legacy wrapper for enhanced prompt loader - maintains backward compatibility"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """Initialize prompt loader
        
        Args:
            prompts_dir: Directory containing prompt files (defaults to ../prompts)
        """
        # Delegate to enhanced loader
        if prompts_dir is not None:
            self._enhanced_loader = type(enhanced_prompt_loader)(prompts_dir)
        else:
            self._enhanced_loader = enhanced_prompt_loader
    
    def load_prompt(self, prompt_name: str, use_cache: bool = True) -> str:
        """Load a prompt from file - returns rendered template
        
        Args:
            prompt_name: Name of the prompt file
            use_cache: Whether to use cached version if available
            
        Returns:
            Prompt content as string (rendered template)
        """
        try:
            # Load prompt with enhanced loader and render with default variables
            loaded_prompt = self._enhanced_loader.load_prompt(prompt_name, use_cache)
            return loaded_prompt.render()
        except Exception:
            # Fallback: if enhanced loading fails, the enhanced loader 
            # will automatically handle legacy .md files
            raise
    
    def reload_prompt(self, prompt_name: str) -> str:
        """Reload a prompt from file, bypassing cache
        
        Args:
            prompt_name: Name of the prompt file
            
        Returns:
            Fresh prompt content
        """
        loaded_prompt = self._enhanced_loader.reload_prompt(prompt_name)
        return loaded_prompt.render()
    
    def clear_cache(self):
        """Clear all cached prompts"""
        self._enhanced_loader.clear_cache()
    
    def list_available_prompts(self) -> list[str]:
        """List all available prompt files
        
        Returns:
            List of prompt names (without extensions)
        """
        return self._enhanced_loader.list_available_prompts()
    
    def validate_prompts(self) -> Dict[str, bool]:
        """Validate that all expected prompt files exist and are readable
        
        Returns:
            Dictionary mapping prompt names to validation status
        """
        validation_results = self._enhanced_loader.validate_prompts()
        
        # Convert to legacy format (bool only)
        legacy_results = {}
        for prompt_name, result in validation_results.items():
            legacy_results[prompt_name] = result.get("valid", False)
        
        return legacy_results


# Global prompt loader instance - maintains backward compatibility
prompt_loader = PromptLoader()