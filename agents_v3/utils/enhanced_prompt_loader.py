"""Enhanced utility for loading external prompt files with metadata and variable support"""

import os
import yaml
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptMetadata:
    """Metadata for a prompt template"""
    name: str
    description: str
    version: str
    agent_role: str
    variables: Dict[str, Dict[str, Any]]  # variable_name -> {type, description, default, required}
    usage_notes: List[str]
    last_updated: str
    tags: List[str]


@dataclass
class LoadedPrompt:
    """A loaded prompt with metadata and content"""
    metadata: PromptMetadata
    template: str
    
    def render(self, variables: Dict[str, Any] = None) -> str:
        """Render the prompt template with provided variables
        
        Args:
            variables: Dictionary of variables to substitute
            
        Returns:
            Rendered prompt content
            
        Raises:
            ValueError: If required variables are missing
        """
        if variables is None:
            variables = {}
        
        # Add default values for missing variables
        final_variables = {}
        for var_name, var_config in self.metadata.variables.items():
            if var_name in variables:
                final_variables[var_name] = variables[var_name]
            elif var_config.get('default') is not None:
                final_variables[var_name] = var_config['default']
            elif var_config.get('required', False):
                raise ValueError(f"Required variable '{var_name}' not provided for prompt '{self.metadata.name}'")
            else:
                # Optional variable with no default - use empty string
                final_variables[var_name] = ""
        
        # Add common system variables
        final_variables.update({
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'current_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_year': datetime.now().year,
            'current_month': datetime.now().month,
            'current_day': datetime.now().day
        })
        
        # Render template
        try:
            return self.template.format(**final_variables)
        except KeyError as e:
            raise ValueError(f"Missing variable {e} in prompt template '{self.metadata.name}'")


class EnhancedPromptLoader:
    """Enhanced loader for prompt files with metadata and variable support"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """Initialize enhanced prompt loader
        
        Args:
            prompts_dir: Directory containing prompt files (defaults to ../prompts)
        """
        if prompts_dir is None:
            # Default to prompts directory relative to this file
            current_dir = Path(__file__).parent
            self.prompts_dir = current_dir.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
        
        self._cache: Dict[str, LoadedPrompt] = {}
    
    def load_prompt(self, prompt_name: str, use_cache: bool = True) -> LoadedPrompt:
        """Load a prompt with metadata from file
        
        Args:
            prompt_name: Name of the prompt file (without extension)
            use_cache: Whether to use cached version if available
            
        Returns:
            LoadedPrompt with metadata and template
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            ValueError: If prompt format is invalid
        """
        # Check cache first
        if use_cache and prompt_name in self._cache:
            return self._cache[prompt_name]
        
        # Try both .yaml and .md extensions
        prompt_file = None
        for ext in ['.yaml', '.yml', '.md']:
            candidate = self.prompts_dir / f"{prompt_name}{ext}"
            if candidate.exists():
                prompt_file = candidate
                break
        
        if prompt_file is None:
            raise FileNotFoundError(f"Prompt file not found: {prompt_name} (tried .yaml, .yml, .md)")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the prompt file
            loaded_prompt = self._parse_prompt_file(content, prompt_name, prompt_file.suffix)
            
            # Cache the content
            if use_cache:
                self._cache[prompt_name] = loaded_prompt
            
            return loaded_prompt
            
        except Exception as e:
            raise IOError(f"Failed to read prompt file {prompt_file}: {e}")
    
    def _parse_prompt_file(self, content: str, prompt_name: str, file_ext: str) -> LoadedPrompt:
        """Parse prompt file content based on format"""
        
        if file_ext in ['.yaml', '.yml']:
            # Parse YAML format with metadata and template sections
            return self._parse_yaml_prompt(content, prompt_name)
        elif file_ext == '.md':
            # Check if it has YAML frontmatter
            if content.strip().startswith('---\n'):
                return self._parse_frontmatter_prompt(content, prompt_name)
            else:
                # Legacy plain markdown - create default metadata
                return self._parse_legacy_prompt(content, prompt_name)
        else:
            raise ValueError(f"Unsupported prompt file format: {file_ext}")
    
    def _parse_yaml_prompt(self, content: str, prompt_name: str) -> LoadedPrompt:
        """Parse YAML format prompt file"""
        try:
            data = yaml.safe_load(content)
            
            # Extract metadata
            metadata = PromptMetadata(
                name=data.get('name', prompt_name),
                description=data.get('description', ''),
                version=data.get('version', '1.0'),
                agent_role=data.get('agent_role', ''),
                variables=data.get('variables', {}),
                usage_notes=data.get('usage_notes', []),
                last_updated=data.get('last_updated', ''),
                tags=data.get('tags', [])
            )
            
            # Extract template
            template = data.get('template', '')
            if not template:
                raise ValueError(f"No template section found in {prompt_name}")
            
            return LoadedPrompt(metadata=metadata, template=template)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in prompt file {prompt_name}: {e}")
    
    def _parse_frontmatter_prompt(self, content: str, prompt_name: str) -> LoadedPrompt:
        """Parse markdown with YAML frontmatter"""
        try:
            # Split frontmatter and content
            parts = content.split('---\n', 2)
            if len(parts) < 3:
                raise ValueError("Invalid frontmatter format")
            
            frontmatter = parts[1]
            template = parts[2].strip()
            
            # Parse frontmatter
            data = yaml.safe_load(frontmatter)
            
            metadata = PromptMetadata(
                name=data.get('name', prompt_name),
                description=data.get('description', ''),
                version=data.get('version', '1.0'),
                agent_role=data.get('agent_role', ''),
                variables=data.get('variables', {}),
                usage_notes=data.get('usage_notes', []),
                last_updated=data.get('last_updated', ''),
                tags=data.get('tags', [])
            )
            
            return LoadedPrompt(metadata=metadata, template=template)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid frontmatter in prompt file {prompt_name}: {e}")
    
    def _parse_legacy_prompt(self, content: str, prompt_name: str) -> LoadedPrompt:
        """Parse legacy plain markdown prompt"""
        # Create default metadata for legacy prompts
        metadata = PromptMetadata(
            name=prompt_name,
            description=f"Legacy prompt: {prompt_name}",
            version="1.0",
            agent_role=prompt_name.replace('_agent', '').replace('_', ' ').title(),
            variables={},
            usage_notes=["This is a legacy prompt file without metadata"],
            last_updated="",
            tags=["legacy"]
        )
        
        return LoadedPrompt(metadata=metadata, template=content.strip())
    
    def render_prompt(self, prompt_name: str, variables: Dict[str, Any] = None) -> str:
        """Load and render a prompt with variables
        
        Args:
            prompt_name: Name of the prompt
            variables: Variables to substitute
            
        Returns:
            Rendered prompt content
        """
        prompt = self.load_prompt(prompt_name)
        return prompt.render(variables)
    
    def get_prompt_info(self, prompt_name: str) -> PromptMetadata:
        """Get metadata for a prompt without loading the full template
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Prompt metadata
        """
        prompt = self.load_prompt(prompt_name)
        return prompt.metadata
    
    def list_available_prompts(self) -> List[str]:
        """List all available prompt files
        
        Returns:
            List of prompt names (without extensions)
        """
        if not self.prompts_dir.exists():
            return []
        
        prompt_files = set()
        for pattern in ["*.yaml", "*.yml", "*.md"]:
            for file_path in self.prompts_dir.glob(pattern):
                prompt_files.add(file_path.stem)
        
        return sorted(list(prompt_files))
    
    def validate_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Validate all available prompts
        
        Returns:
            Dictionary mapping prompt names to validation info
        """
        validation_results = {}
        
        for prompt_name in self.list_available_prompts():
            try:
                prompt = self.load_prompt(prompt_name, use_cache=False)
                validation_results[prompt_name] = {
                    "valid": True,
                    "has_metadata": len(prompt.metadata.description) > 0,
                    "has_variables": len(prompt.metadata.variables) > 0,
                    "template_length": len(prompt.template),
                    "agent_role": prompt.metadata.agent_role,
                    "version": prompt.metadata.version,
                    "error": None
                }
            except Exception as e:
                validation_results[prompt_name] = {
                    "valid": False,
                    "has_metadata": False,
                    "has_variables": False,
                    "template_length": 0,
                    "agent_role": "",
                    "version": "",
                    "error": str(e)
                }
        
        return validation_results
    
    def reload_prompt(self, prompt_name: str) -> LoadedPrompt:
        """Reload a prompt from file, bypassing cache
        
        Args:
            prompt_name: Name of the prompt file
            
        Returns:
            Fresh loaded prompt
        """
        # Clear from cache
        self._cache.pop(prompt_name, None)
        
        # Load fresh
        return self.load_prompt(prompt_name, use_cache=True)
    
    def clear_cache(self):
        """Clear all cached prompts"""
        self._cache.clear()
    
    def create_prompt_template(self, prompt_name: str, metadata: PromptMetadata, template: str) -> str:
        """Create a new prompt file with metadata
        
        Args:
            prompt_name: Name for the new prompt
            metadata: Prompt metadata
            template: Prompt template content
            
        Returns:
            Path to created file
        """
        # Create the YAML content
        yaml_content = {
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'agent_role': metadata.agent_role,
            'variables': metadata.variables,
            'usage_notes': metadata.usage_notes,
            'last_updated': metadata.last_updated or datetime.now().strftime('%Y-%m-%d'),
            'tags': metadata.tags,
            'template': template
        }
        
        # Write to file
        output_file = self.prompts_dir / f"{prompt_name}.yaml"
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, default_flow_style=False, sort_keys=False, indent=2)
        
        return str(output_file)


# Global enhanced prompt loader instance
enhanced_prompt_loader = EnhancedPromptLoader()