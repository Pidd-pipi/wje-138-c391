import { DispatchStatus, type DispatchOrder } from '../types';
import { dispatchApi } from '../api/dispatch';
import { ApiError } from '../utils/request';

export type StartResult =
  | { ok: true; order: DispatchOrder }
  | { ok: false; message: string; violations: any[] };

export function useDispatch() {
  const canStart = (order: DispatchOrder) =>
    order.status === DispatchStatus.Assigned || order.status === DispatchStatus.Pending;

  const nextStatus = (order: DispatchOrder) =>
    order.status === DispatchStatus.Pending
      ? DispatchStatus.Assigned
      : order.status === DispatchStatus.Assigned
        ? DispatchStatus.InProgress
        : DispatchStatus.Completed;

  /** 发车：后端合规预检不过时返回结构化冲突，单据保持原状不进入执行。 */
  const start = async (id: number): Promise<StartResult> => {
    try {
      const order = await dispatchApi.start(id);
      return { ok: true, order };
    } catch (err) {
      if (err instanceof ApiError) {
        return {
          ok: false,
          message: err.message,
          violations: err.data?.violations ?? []
        };
      }
      return { ok: false, message: (err as Error).message, violations: [] };
    }
  };

  return { canStart, nextStatus, start };
}
