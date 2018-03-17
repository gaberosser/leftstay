import json
from rest_framework.response import Response
from rest_framework import permissions, views, mixins
from django.db.models import Count
from . import models, consts


class SummariseCounts(views.APIView):
    authentication_classes = (permissions.IsAuthenticatedOrReadOnly,)
    def get(self, request, *args, **kwargs):
        # number of active properties by type
        ptc = dict(consts.PROPERTY_TYPE_CHOICES)
        qset = (
            models.PropertyUrl.objects.filter(deactivated__isnull=True)
            .values('property_type').annotate(count=Count('property_type'))
        )
        active_by_type = dict([
            (ptc[t['property_type']], t['count']) for t in qset
        ])
        qset = (
            models.PropertyUrl.objects.filter(deactivated__isnull=False)
            .values('property_type').annotate(count=Count('property_type'))
        )
        inactive_by_type = dict([
            (ptc[t['property_type']], t['count']) for t in qset
        ])
        total_by_type = dict([(k, active_by_type[k] + inactive_by_type[k]) for k in active_by_type])

        return Response({
            'active_by_type': active_by_type,
            'inactive_by_type': inactive_by_type,
            'total_by_type': total_by_type
        })


class PropertyForSaleNumberEntries(views.APIView):
    authentication_classes = (permissions.IsAuthenticated,)
    def get(self, request, *args, **kwargs):
        ## TODO: implement this query
        sql = """
        SELECT X.property_type, X.count num_seen, COUNT(X.count) count
        FROM (
          SELECT p1.property_type, pu.id, COUNT(pu.id) FROM rightmove_propertybase p1
          JOIN rightmove_propertyurl pu on pu.id = p1.url_id
          GROUP BY pu.id, p1.property_type
        ) as X
        GROUP BY X.count, X.property_type
        ORDER BY X.property_type, X.count;
        """

        return Response({})