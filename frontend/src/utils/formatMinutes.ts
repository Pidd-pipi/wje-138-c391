/** 分钟数格式化为「X小时Y分钟」，与后端口径一致。 */
export function formatMinutes(minutes: number): string {
  const value = Math.max(0, Math.round(minutes));
  const hours = Math.floor(value / 60);
  const mins = value % 60;
  if (hours && mins) return `${hours}小时${mins}分钟`;
  if (hours) return `${hours}小时`;
  return `${mins}分钟`;
}
