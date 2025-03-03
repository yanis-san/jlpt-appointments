import pytest
from datetime import datetime, timedelta
from app import app, supabase_client, send_verification_email, generate_verification_code

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():  # Ajouter le contexte d'application
            yield client

@pytest.fixture
def mock_supabase_slots():
    # Créer quelques slots de test
    slots_data = [
        {'date': datetime.now().strftime("%Y-%m-%d"), 'time': '10:00', 'available': True},
        {'date': datetime.now().strftime("%Y-%m-%d"), 'time': '10:30', 'available': True},
        {'date': datetime.now().strftime("%Y-%m-%d"), 'time': '11:00', 'available': False}
    ]
    for slot in slots_data:
        supabase_client.table('slots').insert(slot).execute()
    yield slots_data
    # Nettoyage
    supabase_client.table('slots').delete().neq('id', 0).execute()

def test_get_available_slots(client, mock_supabase_slots):
    """Test la récupération des créneaux disponibles"""
    date = datetime.now().strftime("%Y-%m-%d")
    response = client.get(f'/get-slots?date={date}')
    assert response.status_code == 200
    assert '10:00' in response.data.decode()
    assert '10:30' in response.data.decode()
    assert '11:00' not in response.data.decode()

def test_save_appointment_form(client):
    """Test la soumission du formulaire de rendez-vous"""
    data = {
        'date': datetime.now().strftime("%Y-%m-%d"),
        'time': '10:00',
        'name': 'Test User',
        'phone': '0123456789',
        'email': 'test@example.com',
        'jlpt_level': 'N5',
        'lang': 'fr'
    }
    response = client.post('/save-appointment', data=data)
    assert response.status_code == 200
    # Vérifier le contenu spécifique de verify.html
    assert 'vérification' in response.data.decode().lower()

def test_verification_code_generation():
    """Test la génération du code de vérification"""
    code = generate_verification_code()
    assert len(code) == 6  # Vérifie que le code fait 6 caractères
    assert code.isdigit()  # Vérifie que ce sont des chiffres
    assert int(code) >= 100000  # Vérifie que c'est bien un nombre à 6 chiffres
    assert int(code) <= 999999

def test_verify_code(client):
    """Test la vérification du code"""
    with client.session_transaction() as session:
        session['verification_data'] = {
            'code': '123456',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'time': '10:00',
            'name': 'Test User',
            'phone': '0123456789',
            'email': 'test@example.com',
            'jlpt_level': 'N5',
            'expires': (datetime.now() + timedelta(minutes=10)).isoformat()
        }
    
    response = client.post('/verify-code', data={'code': '123456', 'lang': 'fr'})
    assert response.status_code == 200
    # Vérifier le contenu spécifique de success.html
    assert 'rendez-vous' in response.data.decode().lower()

def test_invalid_verification_code(client):
    """Test un code de vérification invalide"""
    with client.session_transaction() as session:
        session['verification_data'] = {
            'code': '123456',
            'expires': (datetime.now() + timedelta(minutes=10)).isoformat()
        }
    
    response = client.post('/verify-code', data={'code': '999999', 'lang': 'fr'})
    content = response.data.decode().lower()
    assert response.status_code == 200
    
    # Vérifier que la réponse contient la redirection
    assert 'window.location.href = \'/fr\'' in content
    assert 'redirection' in content.lower()

def test_email_sending_with_code(client):
    """Test l'envoi d'email avec le code"""
    with app.app_context():
        # Générer un vrai code
        code = generate_verification_code()
        
        # Tester l'envoi
        email = "test@example.com"
        result = send_verification_email(email, code, 'fr')
        
        # Vérifier que l'envoi a réussi
        assert result == True

def test_unavailable_dates(client, mock_supabase_slots):
    """Test la récupération des dates indisponibles"""
    response = client.get('/get-unavailable-dates')
    assert response.status_code == 200
    dates = response.json
    assert isinstance(dates, list)

def test_initialize_slots():
    """Test l'initialisation des créneaux"""
    with app.app_context():  # Ajouter le contexte d'application
        # D'abord nettoyer la base
        supabase_client.table('slots').delete().neq('id', 0).execute()
        
        # Initialiser les slots
        from app import initialize_supabase_slots
        initialize_supabase_slots()
        
        # Vérifier qu'il y a des slots
        response = supabase_client.table('slots').select('*').execute()
        assert len(response.data) > 0

def test_save_appointment_email_flow(client):
    """Test le flux complet de soumission du formulaire et envoi d'email"""
    data = {
        'date': datetime.now().strftime("%Y-%m-%d"),
        'time': '10:00',
        'name': 'Test User',
        'phone': '0123456789',
        'email': 'test@example.com',
        'jlpt_level': 'N5',
        'lang': 'fr'
    }
    
    response = client.post('/save-appointment', data=data)
    assert response.status_code == 200
    
    # Vérifier que la page de vérification est affichée
    content = response.data.decode().lower()
    assert 'vérification' in content 