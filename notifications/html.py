from django.core.mail import send_mail
subject = 'That’s your subject' 
html_message = render_to_string('mail_template.html', {'context': 'values'})
plain_message = strip_tags(html_message)
from_email = 'from@yourdjangoapp.com>' 
to = 'to@yourbestuser.com' 

mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)