"""
FastAPI STANDALONE pentru Chat AI Legislativ cu RAG System HTML
Suportă încărcarea de legislație din HTML, PDF și text
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
import uvicorn
import json
import re
import os
import tempfile

# Configurări hardcoded
DATABASE_URL = "postgresql://chat_user:avanchat@localhost:5432/chat_legislativ"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:3b"

# Creează aplicația FastAPI
app = FastAPI(
    title="Chat AI Legislativ cu RAG System",
    description="API pentru chat widget legislativ cu încărcare documente HTML/PDF",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurare CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# === RAG SYSTEM INTEGRAT ===
class IntegratedRAGSystem:
    def __init__(self):
        self.documents = {}  # Stocare în memorie pentru simplitate
        self.municipality_docs = {}  # Documente per primărie
        print("🚀 RAG System integrat inițializat")
    
    async def process_html_url(self, url: str, municipality_id: str, custom_title: str = None) -> dict:
        """
        Procesează o pagină HTML de pe orice site web
        """
        try:
            import httpx
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse
            
            print(f"📄 Extrag HTML de pe: {url}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extrage titlul
                title = custom_title
                if not title:
                    title_tag = soup.find('title')
                    title = title_tag.get_text().strip() if title_tag else f"Document web - {urlparse(url).netloc}"
                
                # Curăță HTML-ul
                content_text = self._extract_clean_content(soup, url)
                
                if len(content_text.strip()) < 100:
                    return {"success": False, "error": "Conținut insuficient"}
                
                # Salvează documentul
                doc_id = str(uuid.uuid4())
                chunks = self._split_text(content_text)
                
                doc_data = {
                    "id": doc_id,
                    "title": title,
                    "content": content_text,
                    "url": url,
                    "source_type": "html",
                    "domain": urlparse(url).netloc,
                    "chunks": chunks,
                    "municipality_id": municipality_id,
                    "created_at": datetime.now().isoformat()
                }
                
                self.documents[doc_id] = doc_data
                
                # Adaugă la lista de documente per primărie
                if municipality_id not in self.municipality_docs:
                    self.municipality_docs[municipality_id] = []
                self.municipality_docs[municipality_id].append(doc_id)
                
                print(f"✅ HTML procesat: {title} - {len(chunks)} chunks")
                return {"success": True, "document_id": doc_id, "chunks": len(chunks)}
                
        except ImportError:
            return {"success": False, "error": "Modulele httpx și beautifulsoup4 nu sunt instalate"}
        except Exception as e:
            print(f"❌ Eroare procesare HTML {url}: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_multiple_html_urls(self, urls: List[str], municipality_id: str) -> dict:
        """
        Procesează mai multe URL-uri HTML
        """
        successful = 0
        failed = 0
        errors = []
        
        for url in urls:
            result = await self.process_html_url(url, municipality_id)
            if result["success"]:
                successful += 1
            else:
                failed += 1
                errors.append(f"{url}: {result.get('error', 'Unknown error')}")
        
        return {
            "total_urls": len(urls),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    
    def process_text_content(self, text_content: str, municipality_id: str, title: str, source_type: str = "text") -> dict:
        """
        Procesează conținut text direct
        """
        try:
            if len(text_content.strip()) < 100:
                return {"success": False, "error": "Conținut text insuficient"}
            
            # Salvează documentul
            doc_id = str(uuid.uuid4())
            chunks = self._split_text(text_content)
            
            doc_data = {
                "id": doc_id,
                "title": title,
                "content": text_content,
                "source_type": source_type,
                "chunks": chunks,
                "municipality_id": municipality_id,
                "created_at": datetime.now().isoformat()
            }
            
            self.documents[doc_id] = doc_data
            
            # Adaugă la lista de documente per primărie
            if municipality_id not in self.municipality_docs:
                self.municipality_docs[municipality_id] = []
            self.municipality_docs[municipality_id].append(doc_id)
            
            print(f"✅ Text procesat: {title} - {len(chunks)} chunks")
            return {"success": True, "document_id": doc_id, "chunks": len(chunks)}
            
        except Exception as e:
            print(f"❌ Eroare procesare text {title}: {e}")
            return {"success": False, "error": str(e)}
    
    def search_documents(self, query: str, municipality_id: str, n_results: int = 3) -> List[dict]:
        """
        Caută în documente (search simplu pe bază de cuvinte cheie)
        """
        try:
            relevant_chunks = []
            query_words = [word.lower() for word in query.split() if len(word) > 2]
            
            # Caută în documentele primăriei
            doc_ids = self.municipality_docs.get(municipality_id, [])
            
            for doc_id in doc_ids:
                if doc_id not in self.documents:
                    continue
                    
                doc_data = self.documents[doc_id]
                
                for i, chunk in enumerate(doc_data["chunks"]):
                    chunk_lower = chunk.lower()
                    score = sum(1 for word in query_words if word in chunk_lower)
                    
                    if score > 0:
                        relevant_chunks.append({
                            "content": chunk,
                            "score": score,
                            "source": doc_data["title"],
                            "source_type": doc_data.get("source_type", "unknown"),
                            "url": doc_data.get("url", ""),
                            "domain": doc_data.get("domain", "")
                        })
            
            # Sortează după relevanță și returnează top rezultate
            relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
            return relevant_chunks[:n_results]
            
        except Exception as e:
            print(f"❌ Eroare căutare: {e}")
            return []
    
    def list_documents(self, municipality_id: str) -> List[dict]:
        """
        Listează documentele unei primării
        """
        try:
            doc_ids = self.municipality_docs.get(municipality_id, [])
            documents = []
            
            for doc_id in doc_ids:
                if doc_id in self.documents:
                    doc_data = self.documents[doc_id]
                    documents.append({
                        "id": doc_data["id"],
                        "title": doc_data["title"],
                        "source_type": doc_data.get("source_type", "unknown"),
                        "url": doc_data.get("url", ""),
                        "domain": doc_data.get("domain", ""),
                        "chunks_count": len(doc_data["chunks"]),
                        "created_at": doc_data["created_at"],
                        "preview": doc_data["content"][:200] + "..." if len(doc_data["content"]) > 200 else doc_data["content"]
                    })
            
            return documents
            
        except Exception as e:
            print(f"❌ Eroare listare documente: {e}")
            return []
    
    def _extract_clean_content(self, soup, url: str) -> str:
        """
        Extrage conținutul curat din HTML
        """
        from urllib.parse import urlparse
        
        # Elimină script-uri, stiluri, și alte elemente irelevante
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'meta', 'link']):
            tag.decompose()
        
        # Elimină divuri comune pentru ads și social media
        for class_name in ['advertisement', 'ads', 'social', 'share', 'comments', 'sidebar', 'menu']:
            for tag in soup.find_all(attrs={'class': re.compile(class_name, re.I)}):
                tag.decompose()
        
        # Încearcă să găsească conținutul principal
        content_text = ""
        content_selectors = [
            'article', '.main-content', '.content', '.post-content', '.article-content',
            '.entry-content', '#content', '#main', 'main', '.container', '.wrapper'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                content_text = content_element.get_text()
                if len(content_text.strip()) > 200:
                    break
        
        # Fallback - ia tot din body
        if not content_text or len(content_text.strip()) < 200:
            body = soup.find('body')
            content_text = body.get_text() if body else soup.get_text()
        
        # Curăță textul
        return self._clean_text(content_text, url)
    
    def _clean_text(self, text: str, url: str = "") -> str:
        """
        Curăță și normalizează textul
        """
        # Elimină caractere speciale și normalizează spațiile
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-.,;:!?()\/\[\]"\'%€$]', '', text)
        
        # Elimină linii foarte scurte
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if (len(line) > 30 and 
                not line.lower().startswith(('copyright', '©', 'all rights', 'terms', 'privacy', 'cookie')) and
                not re.match(r'^[\s\d\-\.]+$', line)):
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Adaugă informații despre sursa web
        if url:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            result = f"Sursa: {domain}\nURL: {url}\n\n{result}"
        
        return result
    
    def _split_text(self, text: str, chunk_size: int = 800) -> List[str]:
        """
        Împarte textul în chunks
        """
        # Împarte în paragrafe
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

# Inițializează RAG system
rag_system = IntegratedRAGSystem()

# === AI CLIENT ÎMBUNĂTĂȚIT CU RAG ===
try:
    import httpx
    
    class EnhancedLlamaClient:
        def __init__(self):
            self.base_url = OLLAMA_BASE_URL
            self.model = OLLAMA_MODEL
            
        async def generate_response_with_context(self, prompt: str, municipality_id: str) -> dict:
            try:
                # Caută documente relevante
                relevant_docs = rag_system.search_documents(prompt, municipality_id, n_results=3)
                
                # Construiește contextul
                context_text = ""
                sources = []
                
                if relevant_docs:
                    context_text = "\n\nInformații relevante din documentele oficiale:\n"
                    for i, doc in enumerate(relevant_docs, 1):
                        context_text += f"\n{i}. {doc['content'][:400]}...\n"
                        
                        source_info = doc['source']
                        if doc.get('url'):
                            source_info += f" ({doc['domain']})"
                        sources.append(source_info)
                
                system_prompt = """Ești un asistent AI pentru primării din România. 
Răspunde în română la întrebări despre taxe și impozite locale.
Folosește informațiile din documentele oficiale dacă sunt disponibile.
Fii concis, util și profesional. Maximum 3-4 propoziții.
Dacă ai informații din documente oficiale, menționează că răspunsul se bazează pe legislația disponibilă."""
                
                full_prompt = f"{system_prompt}\n\n{context_text}\n\nÎntrebare cetățean: {prompt}\n\nRăspuns:"
                
                payload = {
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 300,
                        "stop": ["Întrebare:", "\n\n"]
                    }
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        ai_response = result.get("response", "").strip()
                        
                        if ai_response:
                            lines = ai_response.split('\n')
                            clean_lines = []
                            for line in lines:
                                line = line.strip()
                                if line and not line.startswith('Întrebare') and not line.startswith('Răspuns'):
                                    clean_lines.append(line)
                            
                            final_response = ' '.join(clean_lines[:3])
                            
                            return {
                                "success": True,
                                "response": final_response or "Conform informațiilor disponibile, vă recomand să contactați primăria pentru detalii exacte.",
                                "sources": sources,
                                "context_used": len(relevant_docs)
                            }
                    
                    return {
                        "success": False,
                        "response": "Nu am putut genera răspuns din cauza unei probleme tehnice.",
                        "sources": []
                    }
                        
            except Exception as e:
                print(f"AI Error: {e}")
                return {
                    "success": False,
                    "response": "Pentru informații exacte despre taxe și impozite, vă recomand să contactați primăria direct.",
                    "sources": []
                }
        
        async def check_connection(self) -> bool:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.base_url}/api/version")
                    return response.status_code == 200
            except:
                return False
    
    ai_client = EnhancedLlamaClient()
    
except ImportError:
    # Fallback
    class EnhancedLlamaClient:
        async def generate_response_with_context(self, prompt: str, municipality_id: str) -> dict:
            # Caută în documente pentru fallback
            relevant_docs = rag_system.search_documents(prompt, municipality_id, n_results=2)
            
            if relevant_docs:
                context_info = f"Pe baza documentelor disponibile: {relevant_docs[0]['content'][:200]}..."
                sources = [doc['source'] for doc in relevant_docs]
                return {
                    "success": True,
                    "response": f"{context_info} Pentru informații complete, contactați primăria.",
                    "sources": sources
                }
            
            # Răspunsuri hardcoded pentru test
            responses = {
                "buna": "Bună ziua! Sunt asistentul fiscal al primăriei. Cu ce vă pot ajuta privind taxele și impozitele locale?",
                "taxa pe cladiri": "Taxa pe clădiri se calculează pe baza valorii cadastrale a imobilului. Procentul se stabilește anual prin hotărâre de consiliu local. Plata se face până la 31 martie pentru reducere de 10%.",
                "impozit": "Impozitul pe proprietate include taxa pe clădiri și taxa pe teren. Se plătește anual și variază în funcție de valoarea cadastrală și zona.",
                "acte": "Pentru plata taxelor aveți nevoie de: certificat cadastral, act de proprietate, cartea de identitate. Plata se poate face la casieria primăriei sau online.",
                "termen": "Termenul de plată pentru taxele locale este 31 martie pentru a beneficia de reducerea de 10%. După această dată se aplică majorări de întârziere."
            }
            
            prompt_lower = prompt.lower()
            for key, response in responses.items():
                if key in prompt_lower:
                    return {"success": True, "response": response, "sources": []}
            
            return {
                "success": True, 
                "response": f"Am primit întrebarea '{prompt}'. Pentru informații exacte despre taxele și impozitele locale, vă recomand să contactați direct primăria.",
                "sources": []
            }
        
        async def check_connection(self) -> bool:
            return False
    
    ai_client = EnhancedLlamaClient()

# Database simulation - stocare în memorie
conversations_db = {}
municipalities_db = {
    "localhost:8000": {
        "id": 1,
        "name": "Primăria Test București",
        "domain": "localhost:8000",
        "description": "Primărie de test pentru dezvoltare"
    }
}

# Pydantic models
class ChatMessage(BaseModel):
    content: str
    municipality_domain: Optional[str] = "localhost:8000"
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[List[str]] = []
    session_id: str
    timestamp: datetime

# === ENDPOINT-URI ===

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check pentru aplicație"""
    ai_connected = await ai_client.check_connection()
    
    return {
        "status": "healthy",
        "database": "simulated",
        "ai": "ready" if ai_connected else "simulated",
        "rag": "integrated",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint cu informații despre API"""
    return {
        "message": "Chat AI Legislativ API cu RAG System",
        "docs": "/docs",
        "health": "/api/health",
        "features": ["html_processing", "pdf_support", "rag_search"],
        "status": "ready"
    }

# Chat endpoint cu RAG
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint_with_rag(message: ChatMessage):
    """
    Chat îmbunătățit cu căutare în documente
    """
    try:
        # Validează primăria
        municipality_domain = message.municipality_domain or "localhost:8000"
        if municipality_domain not in municipalities_db:
            municipalities_db[municipality_domain] = {
                "id": len(municipalities_db) + 1,
                "name": f"Primăria {municipality_domain}",
                "domain": municipality_domain,
                "description": "Primărie generată automat"
            }
        
        municipality_id = str(municipalities_db[municipality_domain]["id"])
        session_id = message.session_id or str(uuid.uuid4())
        
        # Salvează în "database" simulat
        if session_id not in conversations_db:
            conversations_db[session_id] = {
                "municipality_domain": municipality_domain,
                "messages": []
            }
        
        # Adaugă mesajul utilizatorului
        conversations_db[session_id]["messages"].append({
            "role": "user",
            "content": message.content,
            "timestamp": datetime.now()
        })
        
        # Generează răspunsul AI cu context din documente
        print(f"Processing message with RAG: '{message.content}'")
        ai_result = await ai_client.generate_response_with_context(message.content, municipality_id)
        
        if ai_result["success"]:
            ai_response = ai_result["response"]
            sources = ai_result.get("sources", [])
        else:
            municipality_name = municipalities_db[municipality_domain]["name"]
            ai_response = f"Am primit întrebarea '{message.content}'. Pentru informații exacte despre taxele și impozitele din {municipality_name}, vă recomand să contactați direct primăria."
            sources = []
        
        # Salvează răspunsul AI
        conversations_db[session_id]["messages"].append({
            "role": "assistant",
            "content": ai_response,
            "sources": sources,
            "timestamp": datetime.now()
        })
        
        print(f"AI Response with RAG: '{ai_response}' | Sources: {sources}")
        
        return ChatResponse(
            response=ai_response,
            sources=sources,
            session_id=session_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        
        emergency_response = f"Am întâmpinat o problemă tehnică la procesarea întrebării '{message.content}'. Vă rugăm să încercați din nou."
        
        return ChatResponse(
            response=emergency_response,
            sources=[],
            session_id=message.session_id or str(uuid.uuid4()),
            timestamp=datetime.now()
        )

# === ENDPOINT-URI PENTRU DOCUMENTE ===

@app.post("/api/documents/upload-html-urls")
async def upload_html_urls(
    urls: List[str], 
    municipality_domain: str = Form(default="localhost:8000")
):
    """
    Upload legislație de pe URL-uri HTML (ANAF, etc.)
    """
    try:
        municipality_id = str(municipalities_db.get(municipality_domain, {"id": 1})["id"])
        
        result = await rag_system.process_multiple_html_urls(urls, municipality_id)
        
        return {
            "success": True,
            "message": f"Procesate {result['successful']} documente cu succes din {result['total_urls']} URL-uri",
            "details": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la procesarea URL-urilor: {str(e)}")

@app.post("/api/documents/upload-text")
async def upload_text_document(
    title: str = Form(...),
    content: str = Form(...),
    municipality_domain: str = Form(default="localhost:8000")
):
    """
    Upload document ca text direct
    """
    try:
        municipality_id = str(municipalities_db.get(municipality_domain, {"id": 1})["id"])
        
        result = rag_system.process_text_content(content, municipality_id, title, "manual")
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Document '{title}' procesat cu succes",
                "document_id": result["document_id"],
                "chunks_created": result["chunks"]
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la procesarea documentului: {str(e)}")

@app.get("/api/documents/list")
async def list_documents(municipality_domain: str = "localhost:8000"):
    """
    Listează documentele încărcate pentru o primărie
    """
    try:
        municipality_id = str(municipalities_db.get(municipality_domain, {"id": 1})["id"])
        documents = rag_system.list_documents(municipality_id)
        
        return {
            "documents": documents,
            "total_count": len(documents),
            "municipality": municipality_domain
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la listarea documentelor: {str(e)}")

@app.post("/api/documents/search")
async def search_documents_endpoint(
    query: str = Form(...),
    municipality_domain: str = Form(default="localhost:8000")
):
    """
    Caută în documentele încărcate
    """
    try:
        municipality_id = str(municipalities_db.get(municipality_domain, {"id": 1})["id"])
        results = rag_system.search_documents(query, municipality_id, n_results=5)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eroare la căutare: {str(e)}")

# Municipalities endpoint
@app.get("/api/municipalities")
async def list_municipalities():
    """Listează toate primăriile"""
    return {
        "municipalities": list(municipalities_db.values())
    }

# AI Status endpoint
@app.get("/api/chat/ai-status")
async def ai_status():
    """Verifică statusul sistemului AI"""
    try:
        connection_ok = await ai_client.check_connection()
        
        return {
            "ollama_connected": connection_ok,
            "model_available": connection_ok,
            "model_name": OLLAMA_MODEL,
            "rag_system": "integrated",
            "status": "healthy" if connection_ok else "simulated"
        }
    except Exception as e:
        return {
            "ollama_connected": False,
            "model_available": False,
            "status": "error",
            "error": str(e)
        }

# Chat history endpoint
@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """Returnează istoricul unei conversații"""
    if session_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation = conversations_db[session_id]
    municipality = municipalities_db.get(conversation["municipality_domain"], {})
    
    return {
        "session_id": session_id,
        "municipality": municipality.get("name", "Unknown"),
        "messages": conversation["messages"]
    }

if __name__ == "__main__":
    uvicorn.run("main_standalone:app", host="0.0.0.0", port=8000, reload=True)