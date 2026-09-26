from django.contrib import admin
from fleet_app import models
admin.site.register(models.Vehicle)
admin.site.register(models.Driver)
admin.site.register(models.DispatchOrder)
admin.site.register(models.MaintenanceRecord)
admin.site.register(models.FuelRecord)
