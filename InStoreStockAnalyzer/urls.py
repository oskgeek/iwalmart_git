from django.conf.urls import url

from InStoreStockAnalyzer import views

urlpatterns = [
    url(r'^populate_departments/$', views.populate_departments, name='departments'),
]
