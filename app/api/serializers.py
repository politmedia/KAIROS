import json

from core import models
from core.views import politician_statistic_view
from django.core.urlresolvers import reverse
from easy_thumbnails.files import get_thumbnailer
from rest_framework import serializers


class CandidacySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Candidacy
        fields = (
            'id',
            'is_new',
            'mandate_id',
            'constituency_id'
        )


class PoliticianSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()
    profile_link = serializers.SerializerMethodField()
    statistic = serializers.SerializerMethodField()
    candidacy = CandidacySerializer(many=True)

    def get_thumbnail(self, instance):
        return (
            self.context['request'].build_absolute_uri(
                get_thumbnailer(instance.image)['large'].url)
            if instance.image
            else None
        )

    def get_profile_link(self, instance):
        return self.context['request'].build_absolute_uri(reverse('politician', kwargs={'politician_id': instance.id}))

    def get_statistic(self, instance):
        res = politician_statistic_view(
            self.context['request'], instance.id).content

        result = json.loads(res.decode('utf-8'))

        return {
            'detail': [
                {
                    'value': result['detail']['values'][x],
                    'category': result['detail']['categories'][x]
                }
                for x
                in range(0, len(result['detail']['values']))
                if result['detail']['values']
            ],
            'summary': [
                {
                    'value': {
                        'positive': result['summary']['values']['positive'][x],
                        'negative': result['summary']['values']['negative'][x]
                    },
                    'title': result['summary']['titles'][x]
                }
                for x
                in range(0, len(result['summary']['values']['positive']))
                if result['summary']['values']
            ]
        }

    class Meta:
        model = models.Politician
        fields = (
            'id',
            'first_name',
            'last_name',
            'party_name',
            'party_short',
            'future_plans',
            'past_contributions',
            'image',
            'thumbnail',
            'profile_link',
            'statistic',
            'candidacy'
        )
