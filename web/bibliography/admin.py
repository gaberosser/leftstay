from django.contrib import admin
import models



class AuthorAdmin(admin.ModelAdmin):
    pass


class PublicationAdmin(admin.ModelAdmin):
    pass


class PresentationAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Author, AuthorAdmin)
admin.site.register(models.Publication, PublicationAdmin)
admin.site.register(models.Presentation, PresentationAdmin)
