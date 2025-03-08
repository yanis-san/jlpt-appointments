from flask import Flask, request, jsonify, render_template, redirect, url_for, session, make_response
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
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
import pymysql.cursors

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
csrf = CSRFProtect(app)

# Configuration MySQL
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# Ajouter les translations après la configuration MySQL
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
        'available_slots': "Horaires disponibles",
        'no_available_slots': "Aucun horaire disponible",
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
        'verification_title': "Email verification",
        'verification_message': "A verification code has been sent to your email address. Please enter it below.",
        'verify_code': "Verify code",
        'already_booked': "This email address already has an appointment",
        'session_expired': "Session expired",
        'code_expired': "Code expired",
        'invalid_code': "Invalid code",
        'email_subject': "JLPT Verification Code",
        'email_body': "Your verification code for JLPT appointment is: {code}\n\nThis code is valid for 10 minutes.",
        'email_error': "Error sending email. Please try again.",
        'redirecting': "Redirecting in 3 seconds...",
        'available_slots': "Available time slots",
        'no_available_slots': "No available time slots",
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
        'verification_title': "メール認証",
        'verification_message': "認証コードをメールで送信しました。下記に入力してください。",
        'verify_code': "コードを確認",
        'already_booked': "このメールアドレスは既に予約済みです",
        'session_expired': "セッションが切れました",
        'code_expired': "コードの有効期限が切れました",
        'invalid_code': "無効なコード",
        'email_subject': "JLPT認証コード",
        'email_body': "JLPTの予約認証コード: {code}\n\nこのコードは10分間有効です。",
        'email_error': "メール送信エラー。もう一度お試しください。",
        'redirecting': "3秒後にリダイレクトします...",
        'available_slots': "利用可能な時間帯",
        'no_available_slots': "利用可能な時間帯がありません",
    },
    'ar': {
        'title': "حجز موعد لتسجيل اختبار JLPT",
        'date': "التاريخ",
        'timeSlot': "الوقت",
        'fullName': "الاسم الكامل",
        'phone': "الهاتف",
        'email': "البريد الإلكتروني",
        'jlptLevel': "مستوى JLPT",
        'selectLevel': "اختر المستوى",
        'confirm': "تأكيد الموعد",
        'success': "تم تسجيل الموعد بنجاح",
        'error': "يرجى ملء جميع الحقول بشكل صحيح",
        'verification_title': "التحقق من البريد الإلكتروني",
        'verification_message': "تم إرسال رمز التحقق إلى بريدك الإلكتروني. يرجى إدخاله أدناه.",
        'verify_code': "التحقق من الرمز",
        'already_booked': "هذا البريد الإلكتروني لديه موعد بالفعل",
        'session_expired': "انتهت الجلسة",
        'code_expired': "انتهت صلاحية الرمز",
        'invalid_code': "رمز غير صالح",
        'email_subject': "رمز التحقق JLPT",
        'email_body': "رمز التحقق الخاص بموعد JLPT هو: {code}\n\nهذا الرمز صالح لمدة 10 دقائق.",
        'email_error': "خطأ في إرسال البريد الإلكتروني. يرجى المحاولة مرة أخرى.",
        'redirecting': "إعادة توجيه في 3 ثوان...",
        'available_slots': "المواعيد المتاحة",
        'no_available_slots': "لا توجد مواعيد متاحة",
    }
}

# Au début du fichier, définir le chemin du logo
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
LOGO_PATH = os.path.join(STATIC_DIR, 'images', 'logo_horizontal.png')

def initialize_mysql_database():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Créer la table slots si elle n'existe pas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS slots (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    available BOOLEAN DEFAULT TRUE,
                    INDEX idx_date_time (date, time)
                )
            ''')
            
            # Créer la table appointments si elle n'existe pas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(50) NOT NULL,
                    email VARCHAR(255) NOT NULL,
                    jlpt_level VARCHAR(2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_email (email)
                )
            ''')
            
            # Vérifier s'il y a déjà des slots
            cursor.execute('SELECT COUNT(*) as count FROM slots')
            result = cursor.fetchone()
            
            # Initialiser les slots seulement si la table est vide
            if result['count'] == 0:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime(2025, 3, 25)
                
                current_date = start_date
                while current_date <= end_date:
                    if (current_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) 
                        and current_date.weekday() != 6):
                        current_time = datetime.strptime(f"{current_date.strftime('%Y-%m-%d')} 09:30", "%Y-%m-%d %H:%M")
                        end_time = datetime.strptime(f"{current_date.strftime('%Y-%m-%d')} 16:30", "%Y-%m-%d %H:%M")
                        
                        while current_time <= end_time:
                            cursor.execute('''
                                INSERT INTO slots (date, time, available) 
                                VALUES (%s, %s, %s)
                            ''', (
                                current_time.strftime("%Y-%m-%d"),
                                current_time.strftime("%H:%M"),
                                True
                            ))
                            current_time += timedelta(minutes=30)
                    
                    current_date += timedelta(days=1)
                
                connection.commit()
                print("Slots initialisés avec succès")
            else:
                print("Les slots existent déjà, pas de réinitialisation nécessaire")
            
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
    finally:
        connection.close()

def get_available_slots_for_date(date):
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Arrondir à la demi-heure suivante
            now = datetime.now()
            minutes = now.minute
            if minutes < 30:
                next_slot = now.replace(minute=30, second=0, microsecond=0)
            else:
                next_slot = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

            current_date = now.date()
            query_date = datetime.strptime(date, '%Y-%m-%d').date()

            query = '''
                SELECT s.time, COUNT(a.id) as registration_count
                FROM slots s
                LEFT JOIN appointments a ON s.date = a.date AND s.time = a.time
                WHERE s.date = %s
                AND (s.date > %s OR (s.date = %s AND s.time >= %s))
                GROUP BY s.time
                ORDER BY s.time
            '''
            
            cursor.execute(query, (
                date,
                current_date,
                current_date,
                next_slot.time()
            ))
            
            slots = cursor.fetchall()
            
            # Convertir les timedelta en heures formatées
            result = []
            for slot in slots:
                seconds = slot['time'].total_seconds()
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                formatted_time = f"{hours:02d}:{minutes:02d}"
                result.append(formatted_time)
            
            return result
            
    except Exception as e:
        print(f"Erreur détaillée lors de la récupération des slots : {str(e)}")
        return []
    finally:
        connection.close()

def get_language():
    return request.args.get('lang', 'fr')

@app.route('/')
def index():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            current_time = datetime.now().time()
            current_date = datetime.now().date()
            
            cursor.execute('''
                SELECT s.date, s.time, COUNT(a.id) as registration_count
                FROM slots s
                LEFT JOIN appointments a ON s.date = a.date AND s.time = a.time
                WHERE (s.date > %s OR (s.date = %s AND s.time > %s))
                GROUP BY s.date, s.time
                ORDER BY s.date, s.time
            ''', (
                current_date,
                current_date,
                current_time
            ))
            
            time_slots = cursor.fetchall()
            
            lang = get_language()
            return render_template('index.html', 
                                 time_slots=time_slots, 
                                 t=translations[lang],
                                 lang=lang)
    except Exception as e:
        print(f"Erreur lors de la récupération des créneaux : {e}")
        lang = get_language()
        return render_template('error.html', 
                             message="Erreur lors du chargement des créneaux",
                             t=translations[lang],
                             lang=lang)
    finally:
        connection.close()

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
    print(f"Langue reçue : {lang}")  # Debug
    
    slots = get_available_slots_for_date(date)
    
    # S'assurer que la langue existe dans les traductions
    if lang not in translations:
        lang = 'fr'
        
    return render_template('slots.html', 
                         slots=slots, 
                         t=translations[lang],
                         lang=lang)

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
    img = ImageReader(LOGO_PATH)
    logo_width = 9*cm
    logo_height = 2.5*cm
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
        return redirect(url_for('fr'))

    if datetime.now() > datetime.fromisoformat(verification_data['expires']):
        session.pop('verification_data', None)
        return redirect(url_for('fr'))

    if submitted_code != verification_data['code']:
        return redirect(url_for('fr'))

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO appointments (date, time, name, phone, email, jlpt_level)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                verification_data['date'],
                verification_data['time'],
                verification_data['name'],
                verification_data['phone'],
                verification_data['email'],
                verification_data['jlpt_level']
            ))
            
            connection.commit()
            
            # Générer et envoyer le PDF de confirmation
            pdf_buffer = generate_appointment_pdf(verification_data, lang)
            send_confirmation_email(verification_data['email'], pdf_buffer, lang)
            
            session.pop('verification_data', None)
            
            return redirect(url_for('fr'))
            
    except Exception as e:
        print(f"Erreur : {e}")
        connection.rollback()
        return redirect(url_for('fr'))
    finally:
        connection.close()

@app.route('/change-language')
def change_language():
    lang = request.args.get('lang', 'fr')
    if lang not in translations:
        lang = 'fr'
    return render_template('index.html', t=translations[lang], lang=lang)

@app.route('/get-unavailable-dates')
def get_unavailable_dates():
    # Cette route peut maintenant retourner une liste vide 
    # puisque tous les créneaux sont toujours disponibles
    return jsonify([])

@app.route('/submit_registration', methods=['POST'])
def submit_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        time_slot = request.form.get('time')
        
        # Créer une nouvelle inscription
        new_registration = {
            'name': name,
            'email': email,
            'phone': phone,
            'time': time_slot
        }
        
        # Ajouter l'inscription à la base de données
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
                INSERT INTO appointments (date, time, name, phone, email, jlpt_level)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                time_slot,
                time_slot,
                name,
                phone,
                email,
                'N'  # Assuming a default level
            ))
            connection.commit()
        
        return redirect(url_for('success'))

# Initialiser la base de données au démarrage
initialize_mysql_database()

# Au démarrage de l'application
if __name__ == '__main__':
    app.run(debug=False) 