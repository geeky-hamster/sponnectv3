from flask_mail import Mail, Message
from flask import current_app as app, render_template
import logging
import os
from datetime import datetime

mail = Mail()

def render_template_with_defaults(template_name, **context):
    """
    Render a template with default context values that are useful across all emails
    
    Args:
        template_name (str): The name of the template to render
        **context: Additional context variables to pass to the template
    
    Returns:
        str: The rendered template HTML
    """
    # Add global defaults to all templates
    defaults = {
        'frontend_url': os.environ.get('FRONTEND_URL', 'http://localhost:5173'),
        'current_year': datetime.now().year,
        'now': datetime.now
    }
    
    # Don't override user-provided variables with defaults
    for key, value in defaults.items():
        if key not in context:
            context[key] = value
            
    return render_template(template_name, **context)

def send_template_email(subject, to, template_name, context, cc=None, bcc=None, attachments=None):
    """
    Send an email using a template
    
    Args:
        subject (str): Email subject
        to (str or list): Recipient(s) email address
        template_name (str): The name of the template to render
        context (dict): Variables to pass to the template
        cc (str or list, optional): CC recipient(s)
        bcc (str or list, optional): BCC recipient(s)
        attachments (list, optional): List of attachment tuples (filename, mimetype, data)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Render the template with defaults
        html = render_template_with_defaults(template_name, **context)
        
        # Send the email
        return send_email(subject, to, html, cc, bcc, attachments)
    except Exception as e:
        logging.error(f"Failed to send template email to {to}: {str(e)}")
        return False

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