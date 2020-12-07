from django.utils.html import format_html
from django.urls import reverse


def linkify(field_name):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """
    def _linkify(obj):
        linked_obj = getattr(obj, field_name)
        if linked_obj is None:
            return '-'
        app_label = linked_obj._meta.app_label
        model_name = linked_obj._meta.model_name
        view_name = f'admin:{app_label}_{model_name}_change'
        link_url = reverse(view_name, args=[linked_obj.pk])
        return format_html('<a href="{}">{}</a>', link_url, linked_obj)

    _linkify.short_description = field_name  # Sets column name
    return _linkify


def generate_map(filename):
    d = []
    import csv
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            d.append(dict(row))
    
    with open('league_filter_map.py', 'w+') as filterfile:
  
        filterfile.write(f'LEAGUE_MAP = {d}')
        
def generate_league_options():
    
    from league_filter_map import LEAGUE_MAP
    out = ''
    lgs = []
    for item in LEAGUE_MAP:
        if item['seniority'] == 'seniorskie':
            league_name = item.get('poziom_rozgrywkowy')
        else:
            league_name = item.get('rocznik')
        if league_name:
            name = league_name.split(' U')[0]
            lgs.append(name)
        
    for lgn in set(lgs):
        out += '<option {% if "' + lgn + '" in request.GET|get_list:"league" %} selected="selected" {% endif %}>' + lgn + '</option>\n'
   
    with open('filteroptions_league', 'w+') as filterfile:
        filterfile.write(out)


def generate_vivo_options():
    
    from league_filter_map import LEAGUE_MAP
    out = ''
    lgs = []
    for item in LEAGUE_MAP:

        vivo_name = item.get('województwo')

        lgs.append(vivo_name)
        
    for lgn in set(lgs):
        out += '<option {% if "' + lgn + '" in request.GET|get_list:"vivo" %} selected="selected" {% endif %}>' + lgn + '</option>\n'
   
    with open('filteroptions_vivo', 'w+') as filterfile:
        filterfile.write(out)
