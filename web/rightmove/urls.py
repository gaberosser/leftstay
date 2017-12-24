from django.conf.urls import url, include
from . import views


urlpatterns = [
    url(r'^count_overview/$', views.SummariseCounts.as_view()),
]