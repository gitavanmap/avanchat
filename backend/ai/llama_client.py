"""
Client simplu pentru Ollama
"""

import httpx
from typing import Dict, Optional

class LlamaClient:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama3.2:3b"
        
    async def generate_response(self, prompt: str) -> Dict:
        try:
            system_prompt = """Ești un asistent AI pentru primării din România. 
Răspunde în română la întrebări despre taxe și impozite locale.
Fii concis și util."""
            
            full_prompt = f"{system_prompt}\n\nÎntrebare: {prompt}\n\nRăspuns:"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "response": result.get("response", "").strip()
                    }
                else:
                    return {
                        "success": False,
                        "response": "Nu am putut genera răspuns"
                    }
        except Exception as e:
            return {
                "success": False,
                "response": f"Eroare: {str(e)}"
            }
    
    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/version")
                return response.status_code == 200
        except:
            return False

class FiscalChatService:
    def __init__(self):
        self.llama_client = LlamaClient()
    
    async def process_message(self, message: str, session_id: str, municipality_name: str, context_documents=None) -> Dict:
        result = await self.llama_client.generate_response(message)
        return {
            "success": result["success"],
            "response": result["response"],
            "sources": [],
            "model_info": {}
        }

fiscal_chat_service = FiscalChatService()
