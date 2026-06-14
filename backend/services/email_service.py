"""
Email service — uses Flask's built-in smtplib.
For development, emails are printed to console (no real SMTP needed).
For production, set MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD in config/env.
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def _send(to_email, subject, html_body):
    """Send an email. In dev mode (no SMTP configured), prints to console."""
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_user   = current_app.config.get('MAIL_USERNAME')
    mail_pass   = current_app.config.get('MAIL_PASSWORD')
    mail_port   = current_app.config.get('MAIL_PORT', 587)
    mail_from   = current_app.config.get('MAIL_FROM', 'noreply@smartbank.com')

    if not mail_server or not mail_user:
        # Dev mode — print to terminal
        print("\n" + "="*60)
        print(f"[EMAIL] To: {to_email}")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Body (HTML stripped):")
        import re
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


def send_verification_email(user, token, base_url):
    link = f"{base_url}/verify-email/{token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#f8fafc;border-radius:12px;">
      <h2 style="color:#1E3A8A;margin-bottom:8px;">💳 SmartBank</h2>
      <h3 style="color:#0F172A;">Verify your email address</h3>
      <p style="color:#64748B;line-height:1.6;">
        Hi {user.full_name}, thanks for registering! Click the button below to verify your email and activate your account.
      </p>
      <a href="{link}" style="display:inline-block;margin:20px 0;padding:12px 28px;
         background:#2563EB;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">
        Verify Email
      </a>
      <p style="color:#94A3B8;font-size:12px;">
        Or copy this link: {link}<br>This link does not expire.
      </p>
    </div>
    """
    return _send(user.email, "Verify your SmartBank email", html)


def send_password_reset_email(user, token, base_url):
    link = f"{base_url}/reset-password/{token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#f8fafc;border-radius:12px;">
      <h2 style="color:#1E3A8A;margin-bottom:8px;">💳 SmartBank</h2>
      <h3 style="color:#0F172A;">Reset your password</h3>
      <p style="color:#64748B;line-height:1.6;">
        Hi {user.full_name}, we received a request to reset your password. Click below to set a new one.
      </p>
      <a href="{link}" style="display:inline-block;margin:20px 0;padding:12px 28px;
         background:#2563EB;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">
        Reset Password
      </a>
      <p style="color:#94A3B8;font-size:12px;">
        This link expires in <strong>1 hour</strong>. If you didn't request this, ignore this email.
      </p>
    </div>
    """
    return _send(user.email, "Reset your SmartBank password", html)


# ── Phase 3: Transaction / Notification Emails ─────────────────────

_ICONS = {
    'deposit':            ('💰', '#10B981'),
    'withdrawal':         ('💸', '#EF4444'),
    'transfer_sent':      ('↗️', '#2563EB'),
    'transfer_received':  ('↘️', '#10B981'),
    'password_changed':   ('🔒', '#F59E0B'),
    'account_frozen':     ('🚫', '#EF4444'),
    'account_unfrozen':   ('✅', '#10B981'),
}


def send_transaction_email(user, title, message, ntype='info'):
    """
    Generic notification email used for deposits, withdrawals, transfers,
    password changes, and account freeze/unfreeze events.
    """
    icon, color = _ICONS.get(ntype, ('🔔', '#2563EB'))
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#f8fafc;border-radius:12px;">
      <h2 style="color:#1E3A8A;margin-bottom:8px;">💳 SmartBank</h2>
      <div style="display:flex;align-items:center;gap:10px;margin:12px 0;">
        <span style="font-size:28px;">{icon}</span>
        <h3 style="color:{color};margin:0;">{title}</h3>
      </div>
      <p style="color:#0F172A;line-height:1.7;font-size:15px;">
        Hi {user.full_name},<br><br>{message}
      </p>
      <p style="color:#94A3B8;font-size:12px;margin-top:24px;">
        This is an automated notification from SmartBank. If you did not perform this action,
        please contact support immediately or freeze your account from the admin panel.
      </p>
    </div>
    """
    return _send(user.email, f"SmartBank — {title}", html)
