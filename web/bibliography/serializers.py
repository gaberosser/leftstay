from rest_framework import serializers
from . import models


class PublicationAuthorshipSerializer(serializers.ModelSerializer):
    # first_name = serializers.ReadOnlyField(source="author.first_name")
    # last_name = serializers.ReadOnlyField(source="author.last_name")
    full_name = serializers.SerializerMethodField()
    bold = serializers.ReadOnlyField(source="author.make_bold")

    class Meta:
        model = models.PublicationAuthorship
        fields = (
            'full_name',
            # 'first_name',
            # 'last_name',
            # 'order',
            'bold',
        )

    def get_full_name(self, obj):
        ln = obj.author.last_name
        init = [t[0].upper() for t in obj.author.first_name.split()]
        if obj.author.middle_initials is not None:
            init += [t[0].upper() for t in obj.author.middle_initials]
        init = ''.join("%s. " % t for t in init).strip()
        return "%s, %s" % (ln, init)


class PublicationSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

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

    def get_title(self, obj):
        ttl = obj.title.strip()
        if ttl[-1] not in {'.', '?', '!'}:
            ttl += '.'
        return ttl

    def get_authors(self, obj):
        ordered_qset = obj.publicationauthorship_set.order_by('order')
        return PublicationAuthorshipSerializer(ordered_qset, many=True).data
