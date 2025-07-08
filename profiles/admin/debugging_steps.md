# Kroki debugowania PlayerProfileAdmin

## 1. Sprawdź logi Django
```bash
# Włącz DEBUG w settings
DEBUG = True

# Uruchom serwer i sprawdź logi
python manage.py runserver --verbosity=2
```

## 2. Postupne wyłączanie elementów w PlayerProfileAdmin:

### Krok 1: Wyłącz wszystkie actions
```python
actions = []
```

### Krok 2: Uprost list_display
```python
list_display = ("pk", "user", "slug")
```

### Krok 3: Uprost autocomplete_fields
```python
autocomplete_fields = ("user",)
```

### Krok 4: Uprost readonly_fields
```python
readonly_fields = ("uuid",)
```

### Krok 5: Sprawdź czy problem jest z konkretnym polem
Dodawaj po jednym polu z powrotem i testuj

## 3. Sprawdź bazę danych
```python
# W Django shell
python manage.py shell

from profiles.models import PlayerProfile
# Sprawdź czy są problemy z konkretnym rekordem
PlayerProfile.objects.all().count()
PlayerProfile.objects.first()
```

## 4. Sprawdź foreign keys
Możliwe że problem jest z relacjami do nieistniejących obiektów
```python
# Sprawdź orphaned records
PlayerProfile.objects.filter(team_object__isnull=False, team_object__pk__isnull=True)
```
