from api import views
from django.conf.urls import include
from django.conf.urls import url
from django.views.generic import TemplateView

from rest_framework import routers

router = routers.DefaultRouter()

router.register(r'politicians', views.PoliticianViewSet, 'politician')

urlpatterns = [
    url(r'v2/', include(router.urls)),
    url(r'v1/$', views.v1, name='v1'),
    url(r'$', TemplateView.as_view(template_name='api/info.html'), name='info')
]
