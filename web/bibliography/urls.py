from django.conf.urls import url, include
from rest_framework import routers
import views


router = routers.DefaultRouter()
router.register(r'publications', views.PublicationViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]