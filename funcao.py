import smtplib
import threading
from email.mime.text import MIMEText

def valida_senha(senha):
    tem_maiuscula = False
    tem_minuscula = False
    tem_numero = False
    tem_especial = False
    tem_oito = False
    senha_forte = False

    for s in senha:
        if s.isupper():
            tem_maiuscula = True
        if s.islower():
            tem_minuscula = True
        if s.isdigit():
            tem_numero = True
        if not s.isalnum():
            tem_especial = True
        if len(senha) >= 8:
            tem_oito = True
    if tem_maiuscula and tem_minuscula and tem_numero and tem_especial and tem_oito:
        senha_forte = True
    return senha_forte

def enviando_email(destinatario, assunto, mensagem):
    user = "laisrscurso@gmail.com"
    senha = "fkvh zoyg pujv zpdp"

    msg = MIMEText (mensagem)
    msg['Subject'] = assunto
    msg['From'] = user
    msg['To'] = destinatario

    server = smtplib.SMTP('stpm.gmail', 587)
    server.starttls()
    server.login(user, senha)
    server.send_message(msg)
    server.quit()
