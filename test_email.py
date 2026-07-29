import os
import smtplib
from email.mime.text import MIMEText

msg = MIMEText("Ceci est un test d'envoi depuis GitHub Actions.")
msg["Subject"] = "Test VintedScanner"
msg["From"] = os.environ.get("SMTP_USERNAME")
msg["To"] = os.environ.get("SMTP_TO")

with smtplib.SMTP(os.environ.get("SMTP_SERVER", "mail.zaclys.net"), 587) as server:
    server.starttls()
    server.login(os.environ.get("SMTP_USERNAME"), os.environ.get("SMTP_PSW"))
    server.sendmail(msg["From"], [msg["To"]], msg.as_string())

print("Email envoyé avec succès !")
