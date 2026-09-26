"""车辆档案服务。"""
from fleet_app import models


def serialize_vehicle(vehicle):
    return {
        'id': vehicle.id,
        'plateNo': vehicle.plate_no,
        'type': vehicle.vehicle_type,
        'brandModel': vehicle.brand_model,
        'purchaseDate': vehicle.purchase_date.strftime('%Y-%m-%d') if vehicle.purchase_date else '',
        'insuranceExpireDate': vehicle.insurance_expire_date.strftime('%Y-%m-%d') if vehicle.insurance_expire_date else '',
        'inspectionExpireDate': vehicle.inspection_expire_date.strftime('%Y-%m-%d') if vehicle.inspection_expire_date else '',
        'status': vehicle.status,
        'mileage': vehicle.mileage,
        'tankCapacity': vehicle.tank_capacity,
        'fuelConsumption': vehicle.fuel_consumption,
    }


def list_vehicles():
    ensure_demo_data()
    return [serialize_vehicle(v) for v in models.Vehicle.objects.all().order_by('id')]


def ensure_demo_data():
    ensure_demo_vehicles()


def ensure_demo_vehicles():
    """空库时写入演示车辆。"""
    if models.Vehicle.objects.exists():
        return
    models.Vehicle.objects.bulk_create([
        models.Vehicle(plate_no='沪A-7821', vehicle_type='冷链车', brand_model='东风天锦 KR',
                       purchase_date='2023-03-12', insurance_expire_date='2026-09-30',
                       inspection_expire_date='2026-11-20', status='Available',
                       mileage=88210, tank_capacity=380, fuel_consumption=24.6),
        models.Vehicle(plate_no='苏E-5520', vehicle_type='重卡', brand_model='解放 J6P',
                       purchase_date='2021-08-06', insurance_expire_date='2026-07-15',
                       inspection_expire_date='2026-08-22', status='OnTrip',
                       mileage=210430, tank_capacity=520, fuel_consumption=31.2),
        models.Vehicle(plate_no='浙B-3097', vehicle_type='中卡', brand_model='东风多利卡 D9',
                       purchase_date='2024-01-18', insurance_expire_date='2027-01-20',
                       inspection_expire_date='2027-02-10', status='Available',
                       mileage=46200, tank_capacity=300, fuel_consumption=21.3),
    ])
