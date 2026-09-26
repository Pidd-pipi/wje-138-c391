import { create } from 'zustand';
import type { DispatchOrder } from '../types';
export const useDispatchStore = create<{ orders: DispatchOrder[]; setOrders: (orders: DispatchOrder[]) => void }>((set) => ({ orders: [], setOrders: (orders) => set({ orders }) }));
