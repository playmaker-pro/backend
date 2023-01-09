from django.contrib.admin import SimpleListFilter
from django.contrib.admin.filters import FieldListFilter


class IsParentFilter(SimpleListFilter):
    title = "is highest parent"
    parameter_name = "isparent"

    def lookups(self, request, model_admin):

        return [
            ("true", "True"),
            ("false", "False"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.distinct().filter(parent__isnull=True)
        if self.value() == 'false':
            return queryset.distinct().filter(parent__isnull=False)


class CountryListFilter(SimpleListFilter):
    title = 'Country'
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        countries = set([c.country for c in model_admin.model.objects.all()])
        return [(country, country.name) for country in countries]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(country=self.value())
        else:
            return queryset


class HasManagerFilter(SimpleListFilter):
    title = "hasManager"
    parameter_name = "manager"

    def lookups(self, request, model_admin):

        return [
            ("true", "True"),
            ("false", "False"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.distinct().filter(manager__isnull=False)
        if self.value():
            return queryset.distinct().filter(manager__isnull=True)


class ZpnListFilter(SimpleListFilter):
    title = "Zpn"
    parameter_name = 'zpn'

    def lookups(self, request, model_admin):
        zpns = set([z.league.zpn for z in model_admin.model.objects.exclude(league__zpn__isnull=True)])
        lookups = [(zpn, zpn) for zpn in zpns]
        lookups.append(("-", "-"))
        return lookups

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == '-':
                return queryset.filter(league__zpn=None)
            else:
                return queryset.filter(league__zpn=self.value())
        else:
            return queryset
