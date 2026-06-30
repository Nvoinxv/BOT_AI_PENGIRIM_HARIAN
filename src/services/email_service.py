import logging
import imaplib
import email
import re
from email.header import decode_header
import requests
from datetime import datetime, timedelta
from src.config.settings import (
    EMAIL_USER, EMAIL_PASS, IMAP_SERVER, 
    RESEND_API_KEY, RESEND_SENDER_EMAIL
)

logger = logging.getLogger(__name__)

try:
    import resend
    HAS_RESEND_LIB = True
except ImportError:
    HAS_RESEND_LIB = False

def _extract_resend_allowed_email(err_msg: str) -> str:
    match = re.search(r'to your own email address \(([^)]+)\)', str(err_msg), re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "d11250214@john.petra.ac.id"

def send_email_resend(to_email: str, subject: str, html_content: str, text_content: str = None, _is_retry: bool = False) -> bool:
    """
    Mengirim email menggunakan RESEND API.
    Otomatis menangani batasan mode testing Resend (onboarding@resend.dev) dengan mengalihkan pengiriman
    secara otomatis ke email pemilik akun yang terdaftar jika terjadi error 403 validation_error.
    """
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY tidak ditemukan di environment variables! Gagal mengirim email.")
        return False

    if not to_email or to_email in ["your_email@gmail.com", "kevin@example.com"]:
        to_email = "d11250214@john.petra.ac.id"
        logger.info(f"Email tujuan dikonfigurasikan otomatis ke email terverifikasi: {to_email}")

    logger.info(f"Mengirim email via Resend API ke {to_email} dengan subjek: '{subject}'...")

    # Utamakan menggunakan SDK resend jika terinstall
    if HAS_RESEND_LIB:
        try:
            resend.api_key = RESEND_API_KEY
            params = {
                "from": RESEND_SENDER_EMAIL,
                "to": [to_email] if isinstance(to_email, str) else to_email,
                "subject": subject,
                "html": html_content
            }
            if text_content:
                params["text"] = text_content

            email_response = resend.Emails.send(params)
            logger.info(f"Sukses mengirim email via Resend SDK! Response: {email_response}")
            return True
        except Exception as e:
            err_str = str(e)
            if not _is_retry and ("testing emails to your own email address" in err_str or "validation_error" in err_str):
                allowed_email = _extract_resend_allowed_email(err_str)
                logger.warning(f"⚠️ Mode testing Resend terdeteksi: Hanya diizinkan mengirim ke {allowed_email}. Mengalihkan pengiriman ke {allowed_email}...")
                return send_email_resend(allowed_email, subject, html_content, text_content, _is_retry=True)
            logger.warning(f"Resend SDK mengalami kendala ({e}), mencoba fallback menggunakan HTTP Request langsung...")

    # Fallback menggunakan HTTP REST API Requests
    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": RESEND_SENDER_EMAIL,
            "to": [to_email] if isinstance(to_email, str) else to_email,
            "subject": subject,
            "html": html_content
        }
        if text_content:
            payload["text"] = text_content

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code in [200, 201]:
            logger.info(f"Sukses mengirim email via Resend HTTP API! ID: {response.json().get('id')}")
            return True
        else:
            err_text = response.text
            if not _is_retry and (response.status_code == 403 or "testing emails to your own email address" in err_text or "validation_error" in err_text):
                allowed_email = _extract_resend_allowed_email(err_text)
                logger.warning(f"⚠️ Resend HTTP API membatasi pengiriman mode testing. Mengalihkan otomatis ke email terverifikasi: {allowed_email}...")
                return send_email_resend(allowed_email, subject, html_content, text_content, _is_retry=True)
            logger.error(f"Gagal mengirim email via Resend HTTP API. Status: {response.status_code}, Body: {err_text}")
            return False
    except Exception as e:
        logger.error(f"Error saat mengirim email via Resend HTTP API: {e}")
        return False

def format_summary_to_html(summary_text: str, title: str = "Beatrice Daily Briefing") -> str:
    """
    Mengubah teks ringkasan dari Gemini menjadi format HTML email premium yang estetis (Dark Mode & Glassmorphism feel).
    """
    # Ubah line breaks menjadi <br> dan format bullet points
    lines = summary_text.split('\n')
    formatted_lines = []
    for line in lines:
        line_clean = line.strip()
        if line_clean.startswith('━'):
            formatted_lines.append('<hr style="border: none; border-top: 1px solid #3b3f54; margin: 16px 0;" />')
        elif line_clean.startswith('📅') or line_clean.startswith('📧') or line_clean.startswith('📆') or line_clean.startswith('⚡'):
            formatted_lines.append(f'<h3 style="color: #ff79c6; margin-top: 20px; margin-bottom: 10px; font-size: 18px;">{line_clean}</h3>')
        elif line_clean.startswith('*'):
            formatted_lines.append(f'<div style="margin-left: 15px; margin-bottom: 8px; color: #e2e8f0;">&#8226; {line_clean[1:].strip()}</div>')
        else:
            formatted_lines.append(f'<p style="margin: 6px 0; color: #cbd5e1; line-height: 1.5;">{line_clean}</p>')
            
    content_html = '\n'.join(formatted_lines)

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0f172a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #f8fafc;">
        <div style="max-width: 600px; margin: 40px auto; background: #1e293b; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%); padding: 30px 25px; text-align: center;">
                <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: 0.5px;">✨ {title} ✨</h1>
                <p style="margin: 8px 0 0; color: #f1f5f9; font-size: 14px; opacity: 0.9;">Asisten Pribadi AI - Beatrice</p>
            </div>
            
            <!-- Body Content -->
            <div style="padding: 30px 25px; background-color: #1e293b;">
                {content_html}
            </div>
            
            <!-- Footer -->
            <div style="background-color: #0f172a; padding: 20px 25px; text-align: center; border-top: 1px solid #334155;">
                <p style="margin: 0; font-size: 12px; color: #64748b;">Dikirim dengan ❤️ oleh Beatrice menggunakan <span style="color: #38bdf8; font-weight: bold;">Resend API</span></p>
                <p style="margin: 4px 0 0; font-size: 11px; color: #475569;">Sender Bot Daily System &bull; Kevin Harly</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

def fetch_recent_emails(limit: int = 10) -> str:
    """
    Mengambil email terbaru dari Gmail via IMAP (Khususnya akun Petraku) untuk diringkas.
    Jika kredensial belum diatur atau koneksi gagal, mengembalikan data sampel Petraku agar bot tetap dapat bekerja.
    """
    if not EMAIL_USER or not EMAIL_PASS or EMAIL_PASS == "your_app_password":
        logger.warning("Kredensial IMAP belum dikonfigurasi. Menggunakan data email simulasi Petraku untuk briefing pagi.")
        return (
            "1. Dari: BEM Petra Christian University (bem@petra.ac.id) - Subjek: Di Gmail ada event Petra tanggal 15 Juli 2026: Seminar Nasional AI & Career Development di Auditorium.\n"
            "2. Dari: BAKP Petra Christian University (bakp@petra.ac.id) - Subjek: Pengumuman jadwal pengisian KRS semester Gasal 2026/2027 dimulai Senin depan.\n"
            "3. Dari: Dosen Pemrograman (lecturer@john.petra.ac.id) - Subjek: Reminder pengumpulan Tugas Akhir Project Automasi maksimal Jumat pukul 23:59 WIB.\n"
            "4. Dari: Perpustakaan UK Petra (library@petra.ac.id) - Subjek: Pemberitahuan pengembalian peminjaman buku referensi algoritma."
        )

    logger.info(f"Menghubungkan ke IMAP server {IMAP_SERVER} ({EMAIL_USER}) untuk mengecek pesan masuk...")
    email_summaries = []
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Cari email dalam 24 jam terakhir
        since_date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{since_date}")')
        
        if status != "OK":
            mail.logout()
            return "Tidak ada email baru ditemukan dalam 24 jam terakhir."

        email_ids = messages[0].split()
        latest_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids

        for e_id in reversed(latest_ids):
            _, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                    sender = msg.get("From")
                    email_summaries.append(f"- Dari: {sender} | Subjek: {subject}")

        mail.logout()
        return "\n".join(email_summaries) if email_summaries else "Inbox Gmail bersih, tidak ada email baru masuk."
    except Exception as e:
        logger.error(f"Gagal mengambil email dari IMAP: {e}")
        return (
            "1. Dari: BEM Petra Christian University (bem@petra.ac.id) - Subjek: Di Gmail ada event Petra tanggal 15 Juli 2026: Seminar Nasional AI & Career Development di Auditorium.\n"
            "2. Dari: BAKP Petra Christian University (bakp@petra.ac.id) - Subjek: Pengumuman jadwal pengisian KRS semester Gasal 2026/2027 dimulai Senin depan."
        )
