import { DispatchStatus } from './enums';
export type DispatchOrder = { id: number; orderNo: string; vehicleId: number; driverId: number; origin: string; destination: string; planDepartAt: string; planArriveAt: string; actualDepartAt?: string; actualArriveAt?: string; cargo: string; weight: number; freight: number; status: DispatchStatus; creatorId: number; note?: string };
