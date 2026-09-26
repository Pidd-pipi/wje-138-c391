import { create } from 'zustand';
import type { MaintenanceRecord } from '../types';
export const useMaintenanceStore = create<{ records: MaintenanceRecord[]; setRecords: (records: MaintenanceRecord[]) => void }>((set) => ({ records: [], setRecords: (records) => set({ records }) }));
