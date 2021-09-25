




def instructions():
    '''
    
    
    Dodanie mappingów dla teamów bez mappingu (to teamy tworzone na potrzeby coachów i clubów, dlatego nie mieliśmy ich nazw z meta danych) - ręczne JJ
    > Dodanie mappingów clubów na podstawie mappingów teamów, które są przypięte do clubów - shell RK
    > Wygenerowanie aktualnej listy teamów do dodania (wszystkie ligi, distinct, lower na nazwie). Dodajemy code,  seniority, plec, - shell RK
    Unifikacja nazw dla teamów - ręczne JJ 
    Utworzenie listy clubów po unifikacji - ręczne JJ
    Porównanie listy clubów do aktualnej bazy, wykluczenie duplikatów - ręczne JJ
    > Wgranie clubów - shell RK
    Porównujemy mappingi z bazy s51 z mappingami wygenerowanymi z s38 (teamy) - ręczne JJ 
    > Dodajmy do csv teamid, mapper, wyświetlana nazwa na s51 - zarówno jako read i write. - RK
    Wykluczenie duplikatów (niektórym teamom zmienił się code, dlatego wykluczymy nowe rekordy i dla aktualnych zrobimy update code). Zrobię to poprzez ściągnięcie CSV i zaczytanie z powrotem.  - ręczne JJ
    Wystawienie listy teamów do wgrania - JJ
    > Wgranie teamów po unifikacji i podpięcie pod cluby - shell RK 


    Case'y
        team z (RW) mapujemy tak, że wycinamy mu znaki ' (RW)'
        team z fragmentem tekstu (małe litery) 'wycofa' nie uwzględniamy w analizie
        team z fragmentem tekstu (małe litery) 'wyklucz' nie uwzględniamy w analizie
        team z fragmentem tekstu (małe litery) 'pauza' nie uwzględniamy w analizie
        team z fragmentem tekstu (małe litery) 'przenies' nie uwzględniamy w analizie
        team z (Dziewczyny) mapujemy tak, że wycinamy mu znaki ' (Dziewczyny)'
        team z (B) mapujemy tak, że wycinamy mu znaki ' (B)'
        team z (S) mapujemy tak, że wycinamy mu znaki ' (S)'
        team z (DZ) mapujemy tak, że wycinamy mu znaki ' (DZ)'
        team z (dz) mapujemy tak, że wycinamy mu znaki ' (dz)'
        team z (K) mapujemy tak, że wycinamy mu znaki ' (K)'
        team z (J) mapujemy tak, że wycinamy mu znaki ' (J)'
        team z (Jr.) mapujemy tak, że wycinamy mu znaki ' (Jr.)'
        team z (jun) mapujemy tak, że wycinamy mu znaki ' (jun)'

    '''
    from data.models import Team
    
    