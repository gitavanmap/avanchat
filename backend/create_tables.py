from models.database import create_tables, engine, Municipality, SessionLocal
import uuid

def init_database():
    print("Creez tabelele...")
    create_tables()
    
    # Adaugă o primărie de test
    db = SessionLocal()
    try:
        # Verifică dacă există deja
        existing = db.query(Municipality).filter(Municipality.id == "bucuresti").first()
        if not existing:
            test_municipality = Municipality(
                id="bucuresti",
                name="Primăria Municipiului București",
                domain="pmb.ro"
            )
            db.add(test_municipality)
            db.commit()
            print("✅ Primăria de test adăugată!")
        else:
            print("✅ Primăria de test există deja!")
            
    except Exception as e:
        print(f"❌ Eroare: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
