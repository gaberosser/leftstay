from django.shortcuts import render, HttpResponse
from django.core import serializers
from . import models


def publications(request):
    qset = models.Publication.objects.all()
    data = serializers.serialize('json', qset)
    return HttpResponse(data, content_type='application/json')


def presentations(request):
    pass