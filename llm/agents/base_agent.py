"""
Base Agent class for multi-agent system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from llm.clients.gemini_client import GeminiClient


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        name: str,
        role: str,
        client: GeminiClient,
        temperature: float = 0.7
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            role: Agent role/title
            client: LLM client instance
            temperature: Sampling temperature for generation
        """
        self.name = name
        self.role = role
        self.client = client
        self.temperature = temperature
        self.system_instruction = self._build_system_instruction()
    
    @abstractmethod
    def _build_system_instruction(self) -> str:
        """Build system instruction for this agent. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform analysis based on context.
        
        Args:
            context: Dictionary containing input data for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    def _generate_response(
        self, 
        prompt: str, 
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate response using LLM client.
        
        Args:
            prompt: User prompt
            temperature: Override default temperature
            
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        return self.client.generate(
            prompt=prompt,
            system_instruction=self.system_instruction,
            temperature=temp
        )
    
    def _generate_with_images(
        self,
        prompt: str,
        image_paths: list,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate response with image inputs.
        
        Args:
            prompt: User prompt
            image_paths: List of image file paths
            temperature: Override default temperature
            
        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature
        return self.client.generate_with_images(
            prompt=prompt,
            image_paths=image_paths,
            system_instruction=self.system_instruction,
            temperature=temp
        )
