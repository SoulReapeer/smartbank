import smtplib, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def _send(to_email, subject, html_body):
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_user   = current_app.config.get('MAIL_USERNAME')
    mail_pass   = current_app.config.get('MAIL_PASSWORD')
    mail_port   = current_app.config.get('MAIL_PORT', 587)
    mail_from   = current_app.config.get('MAIL_FROM', 'noreply@smartbank.com')

    if not mail_server or not mail_user:
        print("\n" + "="*60)
        print(f"[EMAIL] To: {to_email}")
        print(f"[EMAIL] Subject: {subject}")
        print(re.sub(r'<[^>]+>', '', html_body).strip())
        print("="*60 + "\n")
        return True

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = mail_from
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(mail_server, mail_port) as server:
            server.starttls()
            server.login(mail_user, mail_pass)
            server.sendmail(mail_from, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def send_otp_email(user, otp, expiry_minutes=5):
    """Phase 4 OTP verification email — no links, just the 6-digit code."""
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#f8fafc;border-radius:12px;">
      <h2 style="color:#1E3A8A;margin-bottom:8px;">💳 SmartBank</h2>
      <h3 style="color:#0F172A;">Verify Your Email Address</h3>
      <p style="color:#64748B;line-height:1.6;">
        Hi {user.full_name}, enter the verification code below to activate your account.
      </p>
      <div style="margin:28px 0;text-align:center;">
        <div style="display:inline-block;background:#1E3A8A;color:#fff;font-size:36px;
                    font-weight:800;letter-spacing:14px;padding:20px 36px;border-radius:12px;
                    font-family:monospace;">
          {otp}
        </div>
      </div>
      <p style="color:#94A3B8;font-size:13px;">
        This code expires in <strong>{expiry_minutes} minutes</strong> and can only be used once.
        If you didn't register for SmartBank, you can safely ignore this email.
      </p>
    </div>
    """
    return _send(user.email, "SmartBank — Your Verification Code", html)


def send_password_reset_email(user, token, base_url):
    link = f"{base_url}/reset-password/{token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#f8fafc;border-radius:12px;">
      <h2 style="color:#1E3A8A;margin-bottom:8px;">💳 SmartBank</h2>
      <h3 style="color:#0F172A;">Reset your password</h3>
      <p style="color:#64748B;line-height:1.6;">Hi {user.full_name}, click below to set a new password.</p>
      <a href="{link}" style="display:inline-block;margin:20px 0;padding:12px 28px;
         background:#2563EB;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">
        Reset Password
      </a>
      <p style="color:#94A3B8;font-size:12px;">Expires in 1 hour. If you didn't request this, ignore this email.</p>
    </div>
    """
    return _send(user.email, "SmartBank — Reset your password", html)


_ICONS = {
    'deposit':'💰','withdrawal':'💸','transfer_sent':'↗️','transfer_received':'↘️',
    'password_changed':'🔒','account_frozen':'🚫','account_unfrozen':'✅',
}

def send_transaction_email(user, title, message, ntype='info'):
    icon, color = _ICONS.get(ntype, ('🔔','#2563EB')), '#2563EB'
    if isinstance(icon, tuple):
        icon, color = icon
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#f8fafc;border-radius:12px;">
      <h2 style="color:#1E3A8A;margin-bottom:8px;">💳 SmartBank</h2>
      <div style="display:flex;align-items:center;gap:10px;margin:12px 0;">
        <span style="font-size:28px;">{icon}</span>
        <h3 style="color:{color};margin:0;">{title}</h3>
      </div>
      <p style="color:#0F172A;line-height:1.7;font-size:15px;">Hi {user.full_name},<br><br>{message}</p>
      <p style="color:#94A3B8;font-size:12px;margin-top:24px;">
        Automated notification from SmartBank.
      </p>
    </div>
    """
    return _send(user.email, f"SmartBank — {title}", html)
