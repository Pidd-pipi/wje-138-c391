import { VehicleStatus } from './enums';
export type Vehicle = { id: number; plateNo: string; type: string; brandModel: string; purchaseDate: string; insuranceExpireDate: string; inspectionExpireDate: string; status: VehicleStatus; mileage: number; tankCapacity: number; fuelConsumption: number };
