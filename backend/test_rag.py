from ai.rag_system import rag_system
import os

def test_rag_system():
    print("🧪 Testez sistemul RAG...")
    
    # Test 1: Verifica conexiunea la Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("✅ Ollama conectat")
        else:
            print("❌ Ollama nu răspunde")
            return
    except Exception as e:
        print(f"❌ Eroare Ollama: {e}")
        return
    
    # Test 2: Testează căutarea (fără documente)
    results = rag_system.search_documents("taxa pe cladiri", "bucuresti")
    print(f"📄 Căutare test: {len(results)} rezultate")
    
    # Test 3: Testează generarea de răspuns
    test_docs = [{
        'content': 'Taxa pe clădiri este de 0.2% din valoarea cadastrală conform HCL 45/2024.',
        'metadata': {'source': 'HCL_45_2024.pdf', 'page': '15'}
    }]
    
    response = rag_system.generate_response("Care este taxa pe clădiri?", test_docs)
    print(f"🤖 Răspuns test: {response['response'][:100]}...")
    print(f"📚 Surse: {response['sources']}")
    
    print("✅ Sistemul RAG funcționează!")

if __name__ == "__main__":
    test_rag_system()
