import { DriverStatus } from './enums';
export type Driver = { id: number; name: string; phone: string; licenseType: 'C1' | 'B2' | 'A2' | 'A1'; licenseExpireDate: string; hireDate: string; status: DriverStatus; drivingHours: number; violationCount: number };
