from rest_framework import serializers
from . import models


class PublicationAuthorshipSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    bold = serializers.ReadOnlyField(source="author.make_bold")

    class Meta:
        model = models.PublicationAuthorship
        fields = (
            'first_name',
            'last_name',
            'order',
            'bold',
        )


class PublicationSerializer(serializers.ModelSerializer):
    authors = PublicationAuthorshipSerializer(source='publicationauthorship_set', many=True, read_only=True)

    class Meta:
        model = models.Publication
        fields = (
            'title',
            'authors',
            'year',
            'journal',
            'volume',
            'edition',
            'page_start',
            'page_end',
        )

