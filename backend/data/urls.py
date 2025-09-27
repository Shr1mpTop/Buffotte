from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'items', views.ItemViewSet)
router.register(r'kline', views.KlineDataViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('stats/', views.overall_stats, name='overall_stats'),
]