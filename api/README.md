



# Ustalenia:
1. Cała praca idze na poczet tego brancha.  CIF-new-fe  --> CIF-nazwa

Skupcie się na tym co się dzieje w:  `api/` oraz `users/apis.py`  oraz `users/api_urls.py` oraz `users/serializers.py`




1. Wszystkie GENERYCZNE rzeczy związane z API idą do /api -> odpowiedni modul albo paczka np. errors.py.
   Jendka nie staramy się wszystkiego robić generycznie za wszelką cene.

3. routing odbywa się przez   `api/urls.py` -->   `path("api/v3/", include(api_urls)),`  czy to będzie faktycznie v3 jeszcze będziemy się zastanawiać

4. Używamy GenericViewSet w budowaniu api i jedynie w wybrancyh miejscach korzytamy z zbudowanych w DRF auto-magicznych CURD api method.

5. Każdy EnpointAPi zaczynamy od konsultacji z FE i ze mną za pomocą zadania (sub-tasku) `Anaylse & Design`

    5.1 Otrzymawszy zadanie przygotowujecie mock implementacji/ plan opisany jako `description` w wyżęj wymienionym zadaniu - w razie wątpliwości szybki call- jak dostaniecie "accepted" słownie to zabieracie się za implementacje.

    5.2 po uzgodnieniu tego jak ma wygladać flow zaczyna się implementacja -> robimy szkielet czyli
        doprowadzamy kod do staniu że da się odpytać API (postmanem) i dostajemy odp za-mockowaną
        tj.  Response([{"name": "tema1"}])
        ten moment nie powinnien zawierać zandej logiki, poprostu przetarte scieżki jak co ma wygladać
        sprawdzacie sami dla siebie czy to ma sens - w razie problemów szbyki `call`

    5.3 [opcjonalnie] jeśli zostanie to zrobione i zaakceptowane wdrażamy to na Staging. do testów ewentualnych przez FE
    5.4 następuje implementacja szczegółów

    podział effortu:

    5.1: 10%  - szybki call... macie już przygotowane flow przedstawiwacie pomysl np.     # 1. pytam usera o to   # 2. if coś to to  # 3. zwracam serialziowane dane
    5.2: 25%  - tzn ze szbyko sprawdzamy ustalenia i je prototypujemy (powstaje zalązek testów)
    5.3: 5%  - tzn po wdrożeniu pro-aktywnie pytamy FE czy już widział i czy mozemy isc dalej (wiadomo ze możecie część rzeczy robić które nie należa do definicji interaface)
    5.4: 60%  - tu lecimy już ze wszystkim



# TODOsy:
W nawiasie (api) oznacza tą część domeny/appki która pasuje do przeniesienia.
W przypadku gdy TeamSearchApi pochodzi z clubs (importujemy z clubs.api.TeamSearchAPI) mam na mysli przenieśc url'e


    Task(-1): [Kuba]
    -----
    tests need to work.



    Task0:  [Krzysiek]
    ------

    do przeniesienia:

    path("teams_search", TeamSearchApi.as_view(), name="teams_search"),    --> clubs/ (api)
    path("teams_history_search", TeamHistorySearchApi.as_view()),          --> clubs/ (api)
    path("clubs_search", ClubSearchApi.as_view(), name="clubs_search"),    --> clubs/ (api)
    path("playerupdate", WebhookPlayer.as_view(), name="player_webhook"),  --> profiles/ (api)
    path("api-token-auth/", views.obtain_auth_token),                      --> api/




    Task1: POST users/register  {..}     [Lukasz]
    fizycznie tworzymy usera.
    -------
        w RESPONSE zwracamy { ... } usera ze-serializowanego (chodzi o dostanie ID)

        RegisterUserSerializer:
        id:
        first_name:
        last_name:


        wg. UX mamy jedno pole:

        first_last_name -> oczywiście je decodujemy split(' ') poprostu.


        Tworzenie nowego usera się odbywa obecnie tak:
           -> class CustomSignupForm(SignupForm):
              -> EmailAdress (do veryfikacji)
              -> send mail
           -> def pre_save_user(sender, instance, **kwargs):
           -> i to co się dzieje w signals w profiles

        1) Tworzymy własny nowy adapter - dla spójności nazwijmy to UserService w users/services.py
           ! Należy dokładnie przeglądnąć co się dzieje w Allauth adapter z CustomSignupForm.
           ! Service nie powinnien bazować na "request" (tak jak w tym momencie działa):
                user = adapter.new_user(request)

           na tą chwile Service powinnien moć:
            - stworzyć Usera,
            - moc "opcjonalnie verifikowac userowi email" czyli confirm_mail = True / fale jeśli jest true
              to robimy tak jak w users.signals (ta czesc zaa-komentowana)
            - wysyla emaila (do potwierdzenia)
            - tworzy users__EmailAddress z emailem i true/false(do potwierdzenia)

        2) Tworzymy Endpoint API w users/apis.py (+urle)
            uwaga endpoint powinnien nie wymagać auth do obsługi

        3) Odpinamy  - tj. komentujemy to i zostawiamy @todo jako deprecated

        ```@receiver(post_save, sender=settings.AUTH_USER_MODEL)
        def create_profile_handler(sender, instance, created, **kwargs):
        ```

        4) Nowy user ma declared_role = None (to popsuje pare rzeczy w obecnym FE ale na to nie zwracamy uwagi)

            oraz state = STATE_NEW

        5) Testy na API.
            np. tylko POST jest allowed

        6) Błędy związane z flow - mają zwracać odp JSON (zoabcz: api.errors)

    Task2: POST user/confirmation/{key}  {...}  - TBD
    ------


    Task3:  GET /roles     [KRZYSIEK]
    ------
    1) tworzymy
    w roles/apis.py - oddajemy views do API
      roles/api_urls.py

    2) dodajemy routing w api/urls.py

    3) Poprostu {} w Response()
    i tu zwyczajnei zwracamy to co roles/definitions.py (tu lekko do doprecyzowaia)

    chodzi o to by NAZWY użīwane przy kroku tworzenia proflu pochodziły z BE a nie z FE by nie bylo pomyłek

    4) Testy API



    Task4:
    ------

    Touch-Refactoring Inquieres services

    z profiles/signals.py przenosimy:

    `create_default_basic_plan_if_not_present`
    `create_default_basic_plan_for_coach_if_not_present`
    `set_user_inquiry_plan`

    do Inquires/services.py::InqueireSerivce




    Task5:  [Kuba]
    -------
    POST /profiles  {user_id: xxx:  rola: xxx ... }
    W tym kroku możemy dać wszyskie dane albo tylko stworzyć empty profile dla danej roli.
    w zasadzie wszystko co sie dzieje tu:  (czyli Tworzymy profil Userowi i dodajemy Role z danym profilem. )

    Zwróć uwage że w Task4 `set_user_inquiry_plan(instance)` przeniesiony został w inne miejsce.
    ```
    @receiver(post_save, sender=settings.AUTH_USER_MODEL)
    def create_profile_handler(sender, instance, created, **kwargs):
    ```
     (wiadomo - new-> to ten scenariusz , jak już jest to tylko zwracamy)
    jeśli user ma już profil o zadanej roli -> zwracamy te dane i status 200


    response --> zwracamy {profile zeserializowany} (201)

    1) jak wyżej ->profles/apis.py
                  profiles/api_urls.py
                  profiles/serialziers.py

    2) tuningujemy profiles/services.py
    dodajemy typing, dodajemy docstrings - i dodajemy notke deprecated do "set_initial_verification"

    3) Testy API

    Uwaga:  ten serializer nie może być ModelSerialzierem, najlepiej by byl wspolny dla wszyskich rol.



    Task6: (powiązany z Task5)
    -------
    PUT /profiles    { .... } używamy tego samego Serizalizera tych samych rzeczy co z POST /profiles

    dodajemy tylko methode udapte która


    Task7 (powiązany z Task5 i Task6):
    ------
    GET /profiles/{profile_id}  -> response ze-serializowany profil



    Task8
    -----

    Przemodelowanie API pod atuh i odświeżanie toekna.

    obecnie tu jest to: resources/api-token-auth/

    POST /login
    POST /logout
    POST /login/refresh token


    -------Nie na teraz -------------
    Task:
    ----
    Budowa API teams-search

    Task:
    Budowa API countries

    Task:
    Budowa

    Task:
    -----
    Budowa feature-set

    Task:
    ------
    Dodajemy eventy do Userowej tabeli

    Task5:
    ------
    do modelu Usera dodajemy UUID
        zmieniamy serialziers
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        dodajemy


    Task6:
    ------
    change uniquess of User.suername to User.email
