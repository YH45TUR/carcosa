"""
Sistema Legal CO - Cliente LLM
Abstracción unificada via LiteLLM para múltiples proveedores.
"""
from typing import Optional, List, Dict, Any
import os


class LLMClient:
    """
    Cliente unificado para múltiples proveedores LLM.
    Soporta: Ollama, Gemini, Claude, OpenAI, OpenRouter.
    """
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "ollama")
        self._client = None
    
    def _get_client(self):
        """Obtener cliente según proveedor."""
        if self._client:
            return self._client
        
        if self.provider == "ollama":
            from litellm import acompletion
            self._client = acompletion
        elif self.provider == "gemini":
            from litellm import acompletion
            self._client = acompletion
        elif self.provider == "claude":
            from litellm import acompletion
            self._client = acompletion
        elif self.provider == "openai":
            from litellm import acompletion
            self._client = acompletion
        else:
            from litellm import acompletion
            self._client = acompletion
        
        return self._client
    
    async def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict]] = None,
        **kwargs
    ) -> str:
        """
        Enviar mensaje al LLM.
        """
        client = self._get_client()
        
        # Construir mensajes
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        # Determinar modelo
        model = self._get_model()
        
        try:
            response = await client(
                model=model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error al procesar solicitud: {str(e)}"
    
    def _get_model(self) -> str:
        """Obtener nombre del modelo según proveedor."""
        models = {
            "ollama": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            "gemini": "gemini/gemini-2.0-flash",
            "claude": "claude/claude-sonnet-4-20250514",
            "openai": "gpt-4o",
            "openrouter": "openrouter/any"
        }
        return models.get(self.provider, "ollama/llama3.1:8b")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """Generar texto con el LLM."""
        return await self.chat(
            message=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )