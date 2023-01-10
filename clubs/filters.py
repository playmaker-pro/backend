from django.contrib.admin import SimpleListFilter


class IsParentFilter(SimpleListFilter):
    """
    A Django SimpleListFilter subclass that allows the user to filter the queryset
    based on whether the object is the highest parent or not.
    """
    title = "is highest parent"
    parameter_name = "isparent"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples with the values to filter by
        and the display names for the filter. True, False for
        the option will appear in the right sidebar
        """
        return [
            ("true", "True"),
            ("false", "False"),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected value in the filter.
        """
        if self.value() == "true":
            return queryset.distinct().filter(parent__isnull=True)
        if self.value() == 'false':
            return queryset.distinct().filter(parent__isnull=False)


class CountryListFilter(SimpleListFilter):
    """
    A Django SimpleListFilter subclass that allows the user
    to filter the queryset based on the country field.
    """
    title = 'Country'
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples with the values to filter by
        and the display names for the filter. Country full name for
        the option will appear in the right sidebar.
        """
        countries = set([c.country for c in model_admin.model.objects.all()])
        return [(country, country.name) for country in countries]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected value in the filter.
        """
        if self.value():
            return queryset.filter(country=self.value())
        else:
            return queryset


class HasManagerFilter(SimpleListFilter):
    """
    A Django SimpleListFilter subclass that allows the user
    to filter the queryset based on whether the object has a manager or not.
    """
    title = "hasManager"
    parameter_name = "manager"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples with the values to filter
        by and the display names for the filter. True, False for
        the option will appear in the right sidebar
        """

        return [
            ("true", "True"),
            ("false", "False"),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected value in the filter.
        """
        if self.value() == "true":
            return queryset.distinct().filter(manager__isnull=False)
        if self.value():
            return queryset.distinct().filter(manager__isnull=True)


class ZpnListFilter(SimpleListFilter):
    """
    A Django SimpleListFilter subclass that allows the user
    to filter the queryset based on the Zpn field.
    """
    title = "Zpn"
    parameter_name = 'zpn'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples with the values to filter by
        and the display names for the filter. Zpn for
        the option will appear in the right sidebar.
        """
        zpns = set([z.league.zpn for z in model_admin.model.objects.exclude(league__zpn__isnull=True)])
        lookups = [(zpn, zpn) for zpn in zpns]
        lookups.append(("-", "-"))
        return lookups

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the selected value in the filter.
        """
        if self.value():
            if self.value() == '-':
                return queryset.filter(league__zpn=None)
            else:
                return queryset.filter(league__zpn=self.value())
        else:
            return queryset
