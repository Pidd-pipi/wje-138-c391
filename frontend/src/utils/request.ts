export class ApiError extends Error {
  status: number;
  data: any;
  constructor(status: number, data: any, fallbackMessage: string) {
    super(data?.detail || fallbackMessage);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) }, ...init });
  if (!response.ok) {
    let data: any = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    throw new ApiError(response.status, data, response.statusText);
  }
  return response.json() as Promise<T>;
}
