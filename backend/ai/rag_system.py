import os
import uuid
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from pypdf import PdfReader
import requests
import json
from .embeddings import embeddings_model
from dotenv import load_dotenv
import re
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

load_dotenv('../.env')

class RAGSystem:
    def __init__(self):
        # Inițializează Chroma DB
        self.chroma_path = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
        os.makedirs(self.chroma_path, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.chroma_path)
        
        # Ollama settings
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    def get_or_create_collection(self, municipality_id: str):
        """Obține sau creează colecția pentru o primărie"""
        collection_name = f"docs_{municipality_id}"
        try:
            collection = self.client.get_collection(name=collection_name)
        except:
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"municipality": municipality_id}
            )
        return collection
    
    async def process_html_url(self, url: str, municipality_id: str, custom_title: str = None) -> bool:
        """
        Procesează o pagină HTML de pe orice site web și o adaugă în baza de vectori
        """
        try:
            print(f"📄 Procesez HTML de pe: {url}")
            
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
                    print(f"⚠️ Conținut insuficient pentru {url}")
                    return False
                
                # Împarte textul în chunks
                chunks = self._split_text(content_text, chunk_size=500, overlap=50)
                
                # Creează embeddings
                embeddings = embeddings_model.embed_texts(chunks)
                
                # Adaugă în Chroma
                collection = self.get_or_create_collection(municipality_id)
                
                source_name = f"{urlparse(url).netloc}_{title[:50]}"
                ids = [f"{source_name}_{i}_{str(uuid.uuid4())[:8]}" for i in range(len(chunks))]
                metadatas = [
                    {
                        "source": title,
                        "url": url,
                        "source_type": "html",
                        "chunk_id": i,
                        "municipality": municipality_id,
                        "domain": urlparse(url).netloc
                    }
                    for i, chunk in enumerate(chunks)
                ]
                
                collection.add(
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas,
                    ids=ids
                )
                
                print(f"✅ HTML procesat: {title} - {len(chunks)} chunks")
                return True
                
        except Exception as e:
            print(f"❌ Eroare procesare HTML {url}: {e}")
            return False
    
    async def process_multiple_html_urls(self, urls: List[str], municipality_id: str, titles: List[str] = None) -> Dict[str, Any]:
        """
        Procesează mai multe URL-uri HTML în paralel
        """
        if titles and len(titles) != len(urls):
            titles = None
            
        tasks = []
        for i, url in enumerate(urls):
            title = titles[i] if titles else None
            tasks.append(self.process_html_url(url, municipality_id, title))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = 0
        failed = 0
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed += 1
                errors.append(f"{urls[i]}: {str(result)}")
            elif result:
                successful += 1
            else:
                failed += 1
                errors.append(f"{urls[i]}: Conținut insuficient")
        
        return {
            "total_urls": len(urls),
            "successful": successful,
            "failed": failed,
            "errors": errors
        }
    
    def _extract_clean_content(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extrage conținutul curat din HTML, eliminând navigația și elementele irelevante
        """
        # Elimină script-uri, stiluri, și alte elemente irelevante
        for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'meta', 'link']):
            tag.decompose()
        
        # Elimină divuri comune pentru ads și social media
        for class_name in ['advertisement', 'ads', 'social', 'share', 'comments', 'sidebar', 'menu']:
            for tag in soup.find_all(attrs={'class': re.compile(class_name, re.I)}):
                tag.decompose()
        
        # Încearcă să găsească conținutul principal
        content_text = ""
        
        # Strategii de extragere în ordinea priorității
        content_selectors = [
            'article',
            '.main-content',
            '.content',
            '.post-content',
            '.article-content',
            '.entry-content',
            '#content',
            '#main',
            'main',
            '.container',
            '.wrapper'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                content_text = content_element.get_text()
                if len(content_text.strip()) > 200:  # Conținut substanțial
                    break
        
        # Fallback - ia tot din body dacă nu găsește conținut specific
        if not content_text or len(content_text.strip()) < 200:
            body = soup.find('body')
            content_text = body.get_text() if body else soup.get_text()
        
        # Curăță textul
        return self._clean_text(content_text, url)
    
    def _clean_text(self, text: str, url: str = "") -> str:
        """
        Curăță și normalizează textul extras
        """
        # Elimină caractere speciale și normalizează spațiile
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s\-.,;:!?()\/\[\]"\'%€$]', '', text)
        
        # Elimină linii foarte scurte (probabil navigație/UI)
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Păstrează doar liniile cu conținut substanțial
            if (len(line) > 30 and 
                not line.lower().startswith(('copyright', '©', 'all rights', 'terms', 'privacy', 'cookie')) and
                not re.match(r'^[\s\d\-\.]+$', line)):  # Elimină linii cu doar numere/punctuație
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Adaugă informații despre sursa web
        if url:
            domain = urlparse(url).netloc
            result = f"Sursa: {domain}\nURL: {url}\n\n{result}"
        
        return result
    
    def process_pdf(self, pdf_path: str, municipality_id: str, filename: str) -> bool:
        """Procesează un PDF și îl adaugă în baza de vectori"""
        try:
            # Citește PDF
            reader = PdfReader(pdf_path)
            full_text = ""
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                full_text += f"\n--- Pagina {page_num + 1} ---\n{text}"
            
            # Împarte textul în chunks
            chunks = self._split_text(full_text, chunk_size=500, overlap=50)
            
            # Creează embeddings
            embeddings = embeddings_model.embed_texts(chunks)
            
            # Adaugă în Chroma
            collection = self.get_or_create_collection(municipality_id)
            
            ids = [f"{filename}_{i}_{str(uuid.uuid4())[:8]}" for i in range(len(chunks))]
            metadatas = [
                {
                    "source": filename,
                    "source_type": "pdf",
                    "chunk_id": i,
                    "municipality": municipality_id,
                    "page": self._extract_page_from_chunk(chunk)
                }
                for i, chunk in enumerate(chunks)
            ]
            
            collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ PDF procesat: {filename} - {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Eroare procesare PDF {filename}: {e}")
            return False
    
    def process_text_content(self, text_content: str, municipality_id: str, title: str, source_type: str = "text") -> bool:
        """
        Procesează conținut text direct (pentru cazuri când ai deja textul extras)
        """
        try:
            if len(text_content.strip()) < 100:
                print(f"⚠️ Conținut text insuficient pentru {title}")
                return False
            
            # Împarte textul în chunks
            chunks = self._split_text(text_content, chunk_size=500, overlap=50)
            
            # Creează embeddings
            embeddings = embeddings_model.embed_texts(chunks)
            
            # Adaugă în Chroma
            collection = self.get_or_create_collection(municipality_id)
            
            source_name = title.replace(' ', '_')[:50]
            ids = [f"{source_name}_{i}_{str(uuid.uuid4())[:8]}" for i in range(len(chunks))]
            metadatas = [
                {
                    "source": title,
                    "source_type": source_type,
                    "chunk_id": i,
                    "municipality": municipality_id
                }
                for i, chunk in enumerate(chunks)
            ]
            
            collection.add(
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ Text procesat: {title} - {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"❌ Eroare procesare text {title}: {e}")
            return False
    
    def search_documents(self, query: str, municipality_id: str, n_results: int = 5) -> List[Dict]:
        """Caută în documente răspunsuri relevante"""
        try:
            collection = self.get_or_create_collection(municipality_id)
            
            # Creează embedding pentru query
            query_embedding = embeddings_model.embed_query(query)
            
            # Caută în Chroma
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Formatează rezultatele
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'distance': results['distances'][0][i] if results['distances'] else None,
                        'source_type': metadata.get('source_type', 'unknown'),
                        'url': metadata.get('url', ''),
                        'domain': metadata.get('domain', '')
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ Eroare căutare: {e}")
            return []
    
    def generate_response(self, query: str, context_docs: List[Dict]) -> Dict[str, Any]:
        """Generează răspuns folosind Ollama cu context îmbunătățit"""
        try:
            # Construiește contextul cu informații despre surse
            context = ""
            sources = []
            
            for doc in context_docs:
                source_info = f"{doc['metadata']['source']}"
                
                # Adaugă informații specifice tipului de sursă
                if doc['metadata'].get('source_type') == 'html':
                    if doc['metadata'].get('url'):
                        source_info += f" (web: {doc['metadata']['domain']})"
                elif doc['metadata'].get('source_type') == 'pdf':
                    if 'page' in doc['metadata'] and doc['metadata']['page']:
                        source_info += f", pagina {doc['metadata']['page']}"
                
                context += f"\nSursa: {source_info}\nConținut: {doc['content']}\n"
                sources.append(source_info)
            
            # Prompt îmbunătățit pentru model
            prompt = f"""
Ești un asistent AI specializat în legislația fiscală românească pentru primării.

Context din documente oficiale (PDF, web, text):
{context}

Întrebare: {query}

Instrucțiuni:
1. Răspunde DOAR pe baza informațiilor din context
2. Dacă nu găsești informația în context, spune că nu ai informația necesară
3. Citează sursa informației (document, pagină, sau site web)
4. Răspunde în română, clear și concis
5. Folosește un ton oficial dar accesibil
6. Dacă informația vine de pe web, menționează că este de pe site-ul oficial

Răspuns:
"""

            # Apel la Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 400
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result['response'].strip(),
                    "sources": list(set(sources)),
                    "context_used": len(context_docs),
                    "source_types": list(set([doc['metadata'].get('source_type', 'unknown') for doc in context_docs]))
                }
            else:
                return {
                    "response": "Scuze, am întâmpinat o problemă tehnică. Încercați din nou.",
                    "sources": [],
                    "context_used": 0,
                    "source_types": []
                }
                
        except Exception as e:
            print(f"❌ Eroare generare răspuns: {e}")
            return {
                "response": "Scuze, am întâmpinat o problemă tehnică. Încercați din nou.",
                "sources": [],
                "context_used": 0,
                "source_types": []
            }
    
    def list_documents(self, municipality_id: str) -> List[Dict]:
        """
        Listează toate documentele procesate pentru o primărie
        """
        try:
            collection = self.get_or_create_collection(municipality_id)
            
            # Obține toate documentele
            all_docs = collection.get()
            
            # Grupează după sursă pentru a evita duplicatele
            sources = {}
            for i, metadata in enumerate(all_docs['metadatas']):
                source_key = metadata['source']
                if source_key not in sources:
                    sources[source_key] = {
                        'source': metadata['source'],
                        'source_type': metadata.get('source_type', 'unknown'),
                        'url': metadata.get('url', ''),
                        'domain': metadata.get('domain', ''),
                        'chunk_count': 0
                    }
                sources[source_key]['chunk_count'] += 1
            
            return list(sources.values())
            
        except Exception as e:
            print(f"❌ Eroare listare documente: {e}")
            return []
    
    def _split_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Împarte textul în chunks cu overlap"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk.strip())
                
        return chunks
    
    def _extract_page_from_chunk(self, chunk: str) -> str:
        """Extrage numărul paginii din chunk"""
        page_match = re.search(r'--- Pagina (\d+) ---', chunk)
        return page_match.group(1) if page_match else ""

# Singleton instance
rag_system = RAGSystem()