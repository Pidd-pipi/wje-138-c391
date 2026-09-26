def list_orders():
    return [
        {'id': 1, 'orderNo': 'DSP-20260612-0001', 'vehicleId': 1, 'driverId': 1, 'origin': '上海青浦仓', 'destination': '杭州萧山仓', 'planDepartAt': '2026-06-12 09:00', 'planArriveAt': '2026-06-12 13:30', 'cargo': '冷链食品', 'weight': 8200, 'freight': 7200, 'status': 'Assigned', 'creatorId': 1, 'note': '优先发车'},
        {'id': 2, 'orderNo': 'DSP-20260612-0002', 'vehicleId': 2, 'driverId': 2, 'origin': '苏州园区', 'destination': '宁波北仑', 'planDepartAt': '2026-06-12 14:00', 'planArriveAt': '2026-06-12 20:30', 'cargo': '建筑材料', 'weight': 16000, 'freight': 9800, 'status': 'InProgress', 'creatorId': 1, 'note': ''},
    ]

def create_order(payload):
    data = list_orders()[0] | payload
    data['id'] = 99
    return data
