import { PaymentMethod } from './enums';
export type FuelRecord = { id: number; vehicleId: number; date: string; liters: number; unitPrice: number; totalAmount: number; mileage: number; station: string; paymentMethod: PaymentMethod };
