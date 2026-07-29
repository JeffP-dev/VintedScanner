import os
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Ceci est un test d'envoi depuis GitHub Actions.")
msg["Subject"] = "Test VintedScanner"
msg["From"] = os.environ.get("SMTP_FROM_ADDRESS")
msg["To"] = os.environ.get("SMTP_TO")

with smtplib.SMTP(os.environ.get("SMTP_SERVER", "mail.zaclys.net"), 587) as server:
    server.starttls()
    server.login(os.environ.get("SMTP_USERNAME"), os.environ.get("SMTP_PSW"))
    server.sendmail(os.environ.get("SMTP_FROM_ADDRESS")
print("Email envoyé avec succès !")
