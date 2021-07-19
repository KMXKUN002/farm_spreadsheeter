import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

# Using placeholder gmail credentials. Only use gmail SMTP if using gmail credentials.
gmail_user = "lodiconfarmtest@gmail.com"
gmail_pw = "BoozeG0ne"


def create_mail(send_from, send_to, subject, text, filename):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))
    with open(filename, "rb") as f:
        part = MIMEApplication(f.read(),
                               Name=basename(filename))
    part['Content-Disposition'] = 'attachment; filename="%s"' % basename(filename)
    msg.attach(part)

    return msg

def send_mail(send_to, subject, filename):
    text = "See attached excel file of data."
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(gmail_user, gmail_pw)
    msg = create_mail(gmail_user, send_to, subject, text, filename)
    server.sendmail(gmail_user, send_to, msg.as_string())
    server.close()

