import { create } from 'zustand';
import type { Driver } from '../types';
export const useDriverStore = create<{ drivers: Driver[]; setDrivers: (drivers: Driver[]) => void }>((set) => ({ drivers: [], setDrivers: (drivers) => set({ drivers }) }));
