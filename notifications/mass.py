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
    msgs = []

    for i in ['jacek.jasinski8@gmail.com', 'jjasinski.playmaker@gmail.com', 'rafal.kesik@gmail.com']:
        
        message = ('PlayMaker.pro nowa platforma',
                   'Witaj, \n dziękujemy za dołączenie do społęczności PlayMaker.pro\n Przenieśliśmy Twoje konto na ziepłnie nową platformę. Wejdź i sprawdź nowe możliwości klikając w link. https://playmaker.pro/password/reset/?email={i} \n\n\n Pozdrawiamy zespół PlayMaker.pro',
                   
                   'powiadomienia@playmaker.pro', [i])
        msgs.append(message)

    send_mass_mail(msgs, fail_silently=False)
