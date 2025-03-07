from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_mail import Mail, Message
from datetime import datetime, timedelta
from flask_cors import CORS
import random
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
import qrcode
from io import BytesIO
import os
from reportlab.lib.utils import ImageReader
from supabase import create_client
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
CORS(app)

# Charger les configurations depuis .env
load_dotenv()

app.secret_key = os.getenv('SECRET_KEY')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Configuration Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase_client = create_client(supabase_url, supabase_key)

csrf = CSRFProtect(app)  # Activer la protection CSRF

translations = {
    'fr': {
        'title': "Prise de rendez-vous pour l'inscription à l'examen JLPT",
        'date': "Date",
        'timeSlot': "",
        'fullName': "Nom complet",
        'phone': "Téléphone",
        'email': "Email",
        'jlptLevel': "Niveau JLPT",
        'selectLevel': "Sélectionnez un niveau",
        'confirm': "Confirmer le rendez-vous",
        'success': "Rendez-vous enregistré avec succès",
        'error': "Veuillez remplir tous les champs correctement",
        'verification_title': "Vérification de l'email",
        'verification_message': "Un code de vérification a été envoyé à votre adresse email. Veuillez le saisir ci-dessous.",
        'verify_code': "Vérifier le code",
        'already_booked': "Cette adresse email a déjà un rendez-vous",
        'session_expired': "Session expirée",
        'code_expired': "Code expiré",
        'invalid_code': "Code incorrect",
        'email_subject': "Code de vérification JLPT",
        'email_body': "Votre code de vérification pour le rendez-vous JLPT est : {code}\n\nCe code est valable pendant 10 minutes.",
        'email_error': "Erreur lors de l'envoi de l'email. Veuillez réessayer.",
        'redirecting': "Redirection dans 3 secondes...",
    },
    'en': {
        'title': "Appointment booking for JLPT exam registration",
        'date': "Date",
        'timeSlot': "Time Slot",
        'fullName': "Full Name",
        'phone': "Phone",
        'email': "Email",
        'jlptLevel': "JLPT Level",
        'selectLevel': "Select a level",
        'confirm': "Confirm Appointment",
        'success': "Appointment successfully registered",
        'error': "Please fill all fields correctly",
        'email_subject': "JLPT Verification Code",
        'email_body': "Your verification code for JLPT appointment is: {code}\n\nThis code is valid for 10 minutes.",
        'email_error': "Error sending email. Please try again.",
        'verification_title': "Vérification de l'email",
        'verification_message': "Un code de vérification a été envoyé à votre adresse email. Veuillez le saisir ci-dessous.",
        'verify_code': "Vérifier le code",
        'already_booked': "Cette adresse email a déjà un rendez-vous",
        'session_expired': "Session expirée",
        'code_expired': "Code expiré",
        'invalid_code': "Code incorrect",
        'redirecting': "Redirecting in 3 seconds...",
    },
    'ja': {
        'title': "JLPT試験申し込みの予約",
        'date': "日付",
        'timeSlot': "時間帯",
        'fullName': "氏名",
        'phone': "電話番号",
        'email': "メールアドレス",
        'jlptLevel': "JLPT レベル",
        'selectLevel': "レベルを選択してください",
        'confirm': "予約を確認する",
        'success': "予約が完了しました",
        'error': "すべての項目を正しく入力してください",
        'email_subject': "あなたのJLPT検定確認コード",
        'email_body': "ここにあなたのJLPT検定確認コードがあります: {code}",
        'email_error': "メール送信エラー",
        'verification_title': "Vérification de l'email",
        'verification_message': "Un code de vérification a été envoyé à votre adresse email. Veuillez le saisir ci-dessous.",
        'verify_code': "Vérifier le code",
        'already_booked': "Cette adresse email a déjà un rendez-vous",
        'session_expired': "Session expirée",
        'code_expired': "Code expiré",
        'invalid_code': "Code incorrect",
        'redirecting': "3秒後にリダイレクトします...",
    },
    'ar': {
        'title': "JLPT حجز موعد للتسجيل في اختبار",
        'date': "التاريخ",
        'timeSlot': "الموعد",
        'fullName': "الاسم الكامل",
        'phone': "رقم الهاتف",
        'email': "البريد الإلكتروني",
        'jlptLevel': "مستوى JLPT",
        'selectLevel': "اختر المستوى",
        'confirm': "تأكيد الموعد",
        'success': "تم تسجيل الموعد بنجاح",
        'error': "يرجى ملء جميع الحقول بشكل صحيح",
        'email_subject': "رمز التحقق من JLPT",
        'email_body': "هنا رمز التحقق من JLPT: {code}",
        'email_error': "خطأ عند إرسال البريد الإلكتروني",
        'verification_title': "Vérification de l'email",
        'verification_message': "Un code de vérification a été envoyé إلى عنوان بريدك الإلكتروني. يرجى إدخاله أدناه.",
        'verify_code': "Vérifier le code",
        'already_booked': "Cette adresse email a déjà un rendez-vous",
        'session_expired': "Session expirée",
        'code_expired': "Code expiré",
        'invalid_code': "Code incorrect",
        'redirecting': "...إعادة توجيه في 3 ثوان",
    }
}

def initialize_supabase_slots():
    try:
        # Supprimer tous les slots existants
        supabase_client.table('slots').delete().neq('id', 0).execute()
        
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime(2025, 3, 25)
        
        slots_to_insert = []
        current_date = start_date
        
        while current_date <= end_date:
            if (current_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) 
                and current_date.weekday() != 6):  # Pas de dimanches
                current_time = datetime.strptime(f"{current_date.strftime('%Y-%m-%d')} 09:30", "%Y-%m-%d %H:%M")
                end_time = datetime.strptime(f"{current_date.strftime('%Y-%m-%d')} 16:30", "%Y-%m-%d %H:%M")
                
                while current_time <= end_time:
                    slots_to_insert.append({
                        'date': current_time.strftime("%Y-%m-%d"),
                        'time': current_time.strftime("%H:%M"),
                        'available': True
                    })
                    current_time += timedelta(minutes=30)
            
            current_date += timedelta(days=1)
        
        # Insérer les slots par lots de 1000
        for i in range(0, len(slots_to_insert), 1000):
            batch = slots_to_insert[i:i+1000]
            supabase_client.table('slots').insert(batch).execute()
        
        print("Base de données Supabase initialisée avec succès")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")

def get_available_slots_for_date(date):
    try:
        response = supabase_client.table('slots') \
            .select('time') \
            .eq('date', date) \
            .eq('available', True) \
            .execute()
        return [slot['time'] for slot in response.data]
    except Exception as e:
        print(f"Erreur lors de la récupération des slots : {e}")
        return []

@app.route('/')
def home():
    return redirect('/fr')  # Redirection par défaut vers la version française

@app.route('/fr')
def fr():
    return render_template('index.html', t=translations['fr'], lang='fr')

@app.route('/en')
def en():
    return render_template('index.html', t=translations['en'], lang='en')

@app.route('/ja')
def ja():
    return render_template('index.html', t=translations['ja'], lang='ja')

@app.route('/ar')
def ar():
    return render_template('index.html', t=translations['ar'], lang='ar')

@app.route('/get-slots')
def get_slots():
    date = request.args.get('date')
    lang = request.args.get('lang', 'fr')
    slots = get_available_slots_for_date(date)
    return render_template('slots.html', slots=slots, t=translations[lang])

def generate_verification_code():
    return str(random.randint(100000, 999999))

def send_verification_email(email, code, lang):
    try:
        subject = translations[lang]['email_subject']
        body = translations[lang]['email_body'].format(code=code)
        
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur d'envoi d'email: {e}")
        return False

@app.route('/save-appointment', methods=['POST'])
def save_appointment():
    lang = request.form.get('lang', 'fr')
    if lang not in translations:
        lang = 'fr'
        
    date = request.form.get('date')
    time = request.form.get('time')
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    jlpt_level = request.form.get('jlpt_level')

    print(f"Données reçues: date={date}, time={time}, name={name}, phone={phone}, email={email}, jlpt_level={jlpt_level}")  # Debug

    if not all([date, time, name, phone, email, jlpt_level]):
        print("Champs manquants:", {
            'date': bool(date),
            'time': bool(time),
            'name': bool(name),
            'phone': bool(phone),
            'email': bool(email),
            'jlpt_level': bool(jlpt_level)
        })  # Debug
        return render_template('error.html', 
                             t=translations[lang], 
                             lang=lang,
                             error_message="Tous les champs sont requis")

    # Générer et envoyer le code de vérification
    verification_code = generate_verification_code()
    send_verification_email(email, verification_code, lang)

    # Stocker les données dans la session
    session['verification_data'] = {
        'code': verification_code,
        'date': date,
        'time': time,
        'name': name,
        'phone': phone,
        'email': email,
        'jlpt_level': jlpt_level,
        'expires': (datetime.now() + timedelta(minutes=10)).isoformat()
    }

    print("Code de vérification généré:", verification_code)  # Debug
    print("Données stockées dans la session:", session['verification_data'])  # Debug

    return render_template('verify.html', t=translations[lang], lang=lang)

def generate_appointment_pdf(data, lang):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Fond blanc
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=True)

    # Logo
    logo_path = "logo_horizontal.png"
    img = ImageReader(logo_path)
    logo_width = 10*cm
    logo_height = 2.5*cm  # Réduit un peu la hauteur
    x = (width - logo_width) / 2
    y_logo = height - 3*cm
    c.drawImage(img, x, y_logo, width=logo_width, height=logo_height, mask='auto')
    
    # Titre
    c.setFillColor(colors.black)  # Remettre la couleur en noir pour le texte
    c.setFont("Helvetica-Bold", 20)
    y_title = y_logo - 2*cm
    c.drawString(2*cm, y_title, "JLPT - Confirmation de rendez-vous")
    
    # Informations du rendez-vous
    c.setFont("Helvetica", 12)
    y = y_title - 2*cm  # Commencer les détails 2cm sous le titre
    
    details = [
        f"Nom : {data['name']}",
        f"Email : {data['email']}",
        f"Téléphone : {data['phone']}",
        f"Date : {data['date']}",
        f"Heure : {data['time']}",
        f"Niveau JLPT : {data['jlpt_level']}",
        "\nLieu : Institut Torii",
    ]
    
    # Debug : imprimer les données
    print("Données pour le PDF:", data)
    
    for line in details:
        c.drawString(2*cm, y, line)
        y -= 1*cm  # Espacement d'1cm entre chaque ligne
    
    # QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data("https://maps.app.goo.gl/NRyzbD337Rrkokh5A")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    temp_qr_path = "temp_qr.png"
    qr_img.save(temp_qr_path)
    
    c.drawString(2*cm, y-1*cm, "Scannez pour la localisation :")
    c.drawImage(temp_qr_path, 2*cm, y-7*cm, width=5*cm, height=5*cm)
    
    os.remove(temp_qr_path)
    
    c.save()
    buffer.seek(0)
    return buffer

def send_confirmation_email(email, pdf_buffer, lang):
    try:
        msg = Message(
            subject="Confirmation de rendez-vous JLPT",
            recipients=[email],
            body="Veuillez trouver ci-joint votre confirmation de rendez-vous."
        )
        
        # Ajouter le PDF en pièce jointe
        msg.attach(
            "confirmation_rdv.pdf",
            "application/pdf",
            pdf_buffer.getvalue()
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erreur d'envoi d'email: {e}")
        return False

@app.route('/verify-code', methods=['POST'])
def verify_code():
    lang = request.form.get('lang', 'fr')
    submitted_code = request.form.get('code')
    
    verification_data = session.get('verification_data')
    if not verification_data:
        return render_template('error.html', t=translations[lang], lang=lang)

    if datetime.now() > datetime.fromisoformat(verification_data['expires']):
        session.pop('verification_data', None)
        return render_template('error.html', t=translations[lang], lang=lang)

    if submitted_code != verification_data['code']:
        return render_template('error.html', t=translations[lang], lang=lang)

    try:
        # Mettre à jour le slot comme non disponible
        supabase_client.table('slots') \
            .update({'available': False}) \
            .eq('date', verification_data['date']) \
            .eq('time', verification_data['time']) \
            .execute()
        
        # Sauvegarder le rendez-vous
        supabase_client.table('appointments') \
            .insert({
                'date': verification_data['date'],
                'time': verification_data['time'],
                'name': verification_data['name'],
                'phone': verification_data['phone'],
                'email': verification_data['email'],
                'jlpt_level': verification_data['jlpt_level']
            }) \
            .execute()
        
        # Générer et envoyer le PDF de confirmation
        pdf_buffer = generate_appointment_pdf(verification_data, lang)
        send_confirmation_email(verification_data['email'], pdf_buffer, lang)
        
        session.pop('verification_data', None)
        
        # Afficher la page de succès
        return render_template('success.html', t=translations[lang], lang=lang)
    except Exception as e:
        print(f"Erreur : {e}")
        return render_template('error.html', t=translations[lang], lang=lang)

@app.route('/change-language')
def change_language():
    lang = request.args.get('lang', 'fr')
    if lang not in translations:
        lang = 'fr'
    return render_template('index.html', t=translations[lang], lang=lang)

@app.route('/get-unavailable-dates')
def get_unavailable_dates():
    try:
        response = supabase_client.table('slots') \
            .select('date') \
            .eq('available', False) \
            .execute()
        return jsonify([slot['date'] for slot in response.data])
    except Exception as e:
        print(f"Erreur lors de la récupération des dates indisponibles : {e}")
        return jsonify([])

# Initialiser la base de données au démarrage de l'application
initialize_supabase_slots()

# Au démarrage de l'application
if __name__ == '__main__':
    app.run(debug=False) 