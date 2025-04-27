from flask_mail import Mail, Message
from flask import current_app as app
import logging

mail = Mail()

def send_email(subject, to, body=None, cc=None, bcc=None, attachments=None):
    """
    Send email using Flask-Mail
    
    Args:
        subject (str): Email subject
        to (str or list): Recipient(s) email address
        body (str, optional): HTML content of the email
        cc (str or list, optional): CC recipient(s)
        bcc (str or list, optional): BCC recipient(s)
        attachments (list, optional): List of attachment tuples (filename, mimetype, data)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    sender = app.config.get('MAIL_DEFAULT_SENDER', 'noreply@sponnect.com')
    try:
        msg = Message(subject, recipients=[to] if isinstance(to, str) else to, sender=sender, html=body)
        
        # Add CC if provided
        if cc:
            msg.cc = [cc] if isinstance(cc, str) else cc
            
        # Add BCC if provided
        if bcc:
            msg.bcc = [bcc] if isinstance(bcc, str) else bcc
            
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                filename, mimetype, data = attachment
                msg.attach(filename=filename, content_type=mimetype, data=data)
                
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email to {to}: {str(e)}")
        print(f"Email delivery failed: {str(e)}")
        return False 