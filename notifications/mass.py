from django.core import mail
    
def send_mass():
    connection = mail.get_connection()

    connection.open()
    
    email2 = mail.EmailMessage(
        'That’s your subject #2',
        'That’s your message body #2',
        'from@yourdjangoapp.com',
        ['to@yourbestuser2.com'],
    )
    email3 = mail.EmailMessage(
        'That’s your subject #3',
        'That’s your message body #3',
        'from@yourdjangoapp.com',
        ['to@yourbestuser3.com'],
    )

    connection.send_messages([email2, email3])
    connection.close()


from django.core.mail import send_mass_mail

def send_mass_basic():
    message1 = ('Subject here', 'Here is the message', 'from@example.com', ['first@example.com', 'other@example.com'])
    message2 = ('Another Subject', 'Here is another message', 'from@example.com', ['second@test.com'])
    send_mass_mail((message1, message2), fail_silently=False)