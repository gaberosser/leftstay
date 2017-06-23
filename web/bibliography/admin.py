from django.contrib.gis import admin

import models


class PublicationAuthorshipInline(admin.TabularInline):
    model = models.PublicationAuthorship


class AuthorAdmin(admin.ModelAdmin):
    pass


class PublicationAdmin(admin.ModelAdmin):
    inlines = (PublicationAuthorshipInline,)


class PresentationAdmin(admin.GeoModelAdmin):
    pass



admin.site.register(models.Author, AuthorAdmin)
admin.site.register(models.Publication, PublicationAdmin)
admin.site.register(models.Presentation, PresentationAdmin)
