from django.shortcuts import render, HttpResponse
from rest_framework import viewsets

from . import models, serializers


class PublicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Publication.objects.all().order_by('-year')
    serializer_class = serializers.PublicationSerializer
