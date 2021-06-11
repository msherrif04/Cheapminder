from email.mime.text import MIMEText
import smtplib

def send_mail(email,quote, author, book):
    from_email=""
    from_password=""
    to_email=email

    subject="Your Daily Highlight"
    message =   "<strong>Hi, there. Here is your daily highlight</strong><div><div><h1>%s</h1><p>%s</p><blockquote>%s</blockquote></div></div>" % (book,author, quote)

    msg = MIMEText(message, 'html')
    msg['Subject'] = subject
    msg['To']=  ",".join(to_email)
    msg['from'] = from_email
    
    gmail=smtplib.SMTP('smtp.gmail.com', 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_email, from_password)
    gmail.send_message(msg)

