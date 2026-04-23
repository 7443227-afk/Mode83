#!/usr/bin/env python3
"""
Script de test pour les fonctionnalités de base de données
"""

import sys
import os

# Ajouter le répertoire parent au chemin pour pouvoir importer le module de base de données
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import init_database, create_tables, add_assertion, get_assertion_by_id, import_assertions_from_directory, sync_assertion_record
import uuid
import json

def test_database():
    """Teste les fonctionnalités de la base de données."""
    print("Test des fonctionnalités de la base de données...")
    
    # Initialiser la base de données
    db_path = "badge83/data/test_registry.db"
    conn = init_database(db_path)
    
    # Créer les tables
    create_tables(conn)
    print("Base de données initialisée avec succès")
    
    # Données de test
    test_data = {
        'assertion_id': 'test-assertion-' + str(uuid.uuid4())[:8],
        'assertion_data': {'name': 'Test Badge', 'issuer': 'Test Issuer'},
        'issued_on': '2026-04-23',
        'name': 'Test User',
        'email': 'test@example.com',
        'name_hash': 'hashed_name',
        'email_hash': 'hashed_email'
    }
    
    # Ajouter une assertion de test
    assertion_id = add_assertion(conn, test_data)
    print(f"Assertion ajoutée avec l'identifiant : {assertion_id}")
    
    # Récupérer l'assertion
    result = get_assertion_by_id(conn, test_data['assertion_id'])
    if result:
        print("Assertion récupérée avec succès :")
        print(result)
    else:
        print("Échec de la récupération de l'assertion")
    
    sample_json_path = os.path.join("badge83", "data", f"{test_data['assertion_id']}.json")
    with open(sample_json_path, "w", encoding="utf-8") as handle:
        json.dump({
            "id": f"https://mode83.local/assertions/{test_data['assertion_id']}",
            "type": "Assertion",
            "issuedOn": test_data["issued_on"],
            "admin_recipient": {"name": test_data["name"], "email": test_data["email"]},
            "search": {"name_hash": test_data["name_hash"], "email_hash": test_data["email_hash"]},
        }, handle)

    sync_assertion_record(test_data['assertion_id'], {
        "id": f"https://mode83.local/assertions/{test_data['assertion_id']}",
        "type": "Assertion",
        "issuedOn": test_data["issued_on"],
        "admin_recipient": {"name": test_data["name"], "email": test_data["email"]},
        "search": {"name_hash": test_data["name_hash"], "email_hash": test_data["email_hash"]},
    }, db_path)
    import_stats = import_assertions_from_directory("badge83/data", db_path)
    print(f"Import stats: {import_stats}")

    # Fermer la connexion
    conn.close()
    
    # Nettoyer la base de test
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Base de test supprimée")
    if os.path.exists(sample_json_path):
        os.remove(sample_json_path)
    
    print("Test de la base de données terminé")

if __name__ == "__main__":
    test_database()