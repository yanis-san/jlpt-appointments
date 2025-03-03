import pytest
import os
from dotenv import load_dotenv

# Charger les variables d'environnement de test
load_dotenv('.env.test')

@pytest.fixture(autouse=True)
def app_context():
    """Configure l'environnement de test"""
    os.environ['TESTING'] = 'True' 