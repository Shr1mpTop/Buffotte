import smtplib
from email.message import EmailMessage
import json

with open('email_config.json') as f:
    cfg = json.load(f)

msg = EmailMessage()
msg['Subject'] = 'Test Email from Buffotte'
msg['From'] = cfg['from_address']
msg['To'] = cfg['to_address']
msg.set_content('This is a test email from Buffotte script. If you receive this, email configuration is working.')

try:
    server = smtplib.SMTP(cfg['smtp_server'], cfg['smtp_port'], timeout=20)
    if cfg.get('use_tls', True):
        server.starttls()
    server.login(cfg['username'], cfg['password'])
    server.send_message(msg)
    server.quit()
    print('Test email sent successfully')
except Exception as e:
    print('Test email failed:', e)