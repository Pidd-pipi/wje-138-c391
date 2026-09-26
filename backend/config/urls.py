from django.urls import include, path

urlpatterns = [
    path('api/', include('fleet_app.urls')),
]
