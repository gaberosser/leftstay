from django.conf.urls import url
import views


urlpatterns = [
    url('^publications$', views.publications, name='publications'),
    url('^presentations$', views.presentations, name='presentations'),
]