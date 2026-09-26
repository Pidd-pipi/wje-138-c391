import { useCallback, useState } from 'react';
import { DispatchStatus, type DispatchOrder } from '../types';
import { dispatchApi, type CreateDispatchPayload } from '../api/dispatch';
import { ApiError } from '../utils/request';
import type { AssignmentEligibility } from '../types';

export function useDispatch() {
  const [submitting, setSubmitting] = useState(false);

  const canStart = (order: DispatchOrder) =>
    order.status === DispatchStatus.Pending || order.status === DispatchStatus.Assigned;

  const nextStatus = (order: DispatchOrder) =>
    order.status === DispatchStatus.Pending
      ? DispatchStatus.Assigned
      : order.status === DispatchStatus.Assigned
        ? DispatchStatus.InProgress
        : DispatchStatus.Completed;

  /** 建单：冲突时后端返回 409，details 中带能否指派/原因/单号 */
  const createOrder = useCallback(async (payload: CreateDispatchPayload) => {
    setSubmitting(true);
    try {
      return await dispatchApi.create(payload);
    } finally {
      setSubmitting(false);
    }
  }, []);

  /** 发车：合规预检不通过则保持原状态，错误向上抛给页面提示 */
  const startOrder = useCallback(async (order: DispatchOrder) => {
    setSubmitting(true);
    try {
      return await dispatchApi.start(order.id);
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { canStart, nextStatus, createOrder, startOrder, submitting };
}

/** 从 409 错误中取出合规预检结论，供页面展示涉及单号与还缺时间 */
export function complianceFromError(error: unknown): AssignmentEligibility | null {
  if (error instanceof ApiError && error.status === 409 && error.details) {
    return error.details as AssignmentEligibility;
  }
  return null;
}
