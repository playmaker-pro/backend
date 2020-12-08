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


def send_mass_basic(emails=None):
    msgs = []
    if not emails:
        emails = ['jacek.jasinski8@gmail.com', 'jjasinski.playmaker@gmail.com', 'rafal.kesik@gmail.com']
    for i in emails:
        
        message = ('PlayMaker.pro nowa platforma',
                   f'Witaj, \n\n Dziękujemy za dołączenie do społeczności PlayMaker.pro\n\n Przenieśliśmy Twoje konto na zupełnie nową platformę. Wejdź i sprawdź nowe możliwości klikając w poniższy link. \n\n https://playmaker.pro/password/reset/?email={i} \n\n\n Pozdrawiamy zespół PlayMaker.pro',
                   
                   'playmaker.pro@playmaker.pro', [i])
        msgs.append(message)

    send_mass_mail(msgs, fail_silently=False)
