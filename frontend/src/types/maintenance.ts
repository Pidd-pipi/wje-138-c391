import { MaintenanceType } from './enums';
export type MaintenanceRecord = { id: number; vehicleId: number; type: MaintenanceType; items: string[]; cost: number; vendor: string; date: string; nextMileage: number; nextDate: string; status: 'Scheduled' | 'InProgress' | 'Completed' };
