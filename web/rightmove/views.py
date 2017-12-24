import json
from rest_framework.response import Response
from rest_framework import permissions, views, mixins
from django.db.models import Count
from . import models, consts


class SummariseCounts(views.APIView):
    authentication_classes = (permissions.IsAuthenticatedOrReadOnly,)
    def get(self, request, *args, **kwargs):
        ptc = dict(consts.PROPERTY_TYPE_CHOICES)
        qset = models.PropertyUrl.objects.filter(deactivated__isnull=True)
        qset = qset.values('property_type').annotate(count=Count('property_type'))
        res = dict([
            (ptc[t['property_type']], t['count']) for t in qset
        ])
        return Response({'Rightmove': res})
