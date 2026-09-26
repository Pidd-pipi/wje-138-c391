import { create } from 'zustand';
import type { Vehicle } from '../types';
export const useVehicleStore = create<{ vehicles: Vehicle[]; setVehicles: (vehicles: Vehicle[]) => void }>((set) => ({ vehicles: [], setVehicles: (vehicles) => set({ vehicles }) }));
