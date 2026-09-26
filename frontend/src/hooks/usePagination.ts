import { useMemo, useState } from 'react';
export function usePagination<T>(items: T[], pageSize = 8) {
  const [page, setPage] = useState(1);
  const total = items.length;
  const data = useMemo(() => items.slice((page - 1) * pageSize, page * pageSize), [items, page, pageSize]);
  return { page, setPage, pageSize, total, data };
}
