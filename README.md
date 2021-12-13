

# PlayMaker.pro 


Backend is a backend side for PlayMaker project. It is built with [Python][3]

This project has the following basic apps:

* App1 (short desc)
* App2 (short desc)
* App3 (short desc)

## Installation

### Quick start

To set up a development environment quickly, first install Python 3. It
comes with virtualenv built-in. So create a virtual env by:

    1. `$ python3 -m venv pm`
    2. `$ . pm/bin/activate`

Install all dependencies:

    pip install -r requirements.txt

Run migrations:

    python manage.py migrate

Run development server

    python manage.py runserver



# Project bootstrap


### Setting redirects 

File contains rules for redirecting pages. 

```bash
redirects.yaml
```

redirects.yaml:

```yaml
trener-klub/: /scouting/
```

### Install Google Analitics tags.

To enable trakcing codes (Goggle analytics or Fb pixel) you need to create new file ga.html in a following location:
```python
backend/templates/ga.html
```

ga.html
```javascript
!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=code"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
        ....
</script>

<!-- Facebook Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
.....
/></noscript>
```

### Detailed instructions

Take a look at the docs for more information.

[0]: https://www.python.org/
[1]: https://www.djangoproject.com/
