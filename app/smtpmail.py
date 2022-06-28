from os import getenv, path
import smtplib
from email.message import EmailMessage
import magic
import mimetypes

class SMTPClient:
    def __init__(self):
        self.SMTP_SERVER, self.SMTP_PORT, self.MAIL_ACCOUNT, self.MAIL_PASSWORD, self.MAIL_FROM = self.__load_env()
        self.toAddresses = []
        self.bccAddresses = []
        self.ccAddresses = []
        self.subject = 'Messagem automáticamente enviada pelo sistema'
        self.senderEmail = self.MAIL_FROM
        self.htmlMessage = ''
        self.textMessage = ''
        self.attachments = []
    
    def __load_env(self):
        if getenv('ENV') != 'production':
            from os.path import join, dirname, basename
            from dotenv import load_dotenv
            dotenv_path = join(dirname(__file__), 'email.env')
            load_dotenv(dotenv_path)

        SMTP_SERVER = getenv('SMTP_SERVER')
        SMTP_PORT = getenv('SMTP_PORT')
        MAIL_ACCOUNT = getenv('MAIL_ACCOUNT')
        MAIL_PASSWORD = getenv('MAIL_PASSWORD')
        MAIL_FROM = getenv('MAIL_FROM')

        return SMTP_SERVER, SMTP_PORT, MAIL_ACCOUNT, MAIL_PASSWORD, MAIL_FROM

    def send(self):
        
        if len(self.toAddresses) == 0:
            print('Enter an email address for toAddresses')
            return False

        message = EmailMessage()
        message['Subject'] = self.subject
        message['From'] = self.senderEmail
        message['To'] = self.toAddresses
        message['Bcc'] = ', '.join(self.bccAddresses)
        message['Cc'] = ', '.join(self.ccAddresses)
        message.set_content(self.textMessage)
        message.add_alternative(self.htmlMessage, subtype='html')
        
        for file_path in self.attachments:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            
            file_name = path.basename(file_path)
            file_type = magic.from_buffer(file_data, mime=True)
            extenssion = mimetypes.guess_extension(file_type)

            message.add_attachment(file_data, maintype=file_type, subtype=extenssion, filename=file_name)

        smtp = smtplib.SMTP(host=self.SMTP_SERVER, port=self.SMTP_PORT)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(self.MAIL_ACCOUNT, self.MAIL_PASSWORD)
        
        try:
            print('Sending email...')
            smtp.send_message(message)
            print('Email sent!')
            smtp.quit()
            return True
        except Exception as error:
            print(error)
            return False
       