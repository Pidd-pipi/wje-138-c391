import { DispatchStatus, type DispatchOrder } from '../types';
export function useDispatch() {
  const canStart = (order: DispatchOrder) => order.status === DispatchStatus.Assigned;
  const nextStatus = (order: DispatchOrder) => order.status === DispatchStatus.Pending ? DispatchStatus.Assigned : order.status === DispatchStatus.Assigned ? DispatchStatus.InProgress : DispatchStatus.Completed;
  return { canStart, nextStatus };
}
