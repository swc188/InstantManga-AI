export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export class ApiError extends Error {
  code: number

  constructor(code: number, message: string) {
    super(message)
    this.code = code
  }
}

export async function request<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const resp = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const body = (await resp.json()) as ApiResponse<T>
  if (!resp.ok || body.code !== 0) {
    throw new ApiError(body.code ?? resp.status, body.message ?? '请求失败')
  }
  return body.data
}
