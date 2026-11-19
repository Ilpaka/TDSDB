import type { NewRequest, RequestItem, Status } from './requests'

const API_URL = 'http://localhost:8090/api/collections/obshchezhitie/records'

async function callApi(url: string, options?: RequestInit): Promise<Response> {
  let response: Response
  try {
    response = await fetch(url, options)
  } catch {
    throw new Error('Сервер заявок не отвечает. Проверьте, что PocketBase запущен.')
  }
  if (!response.ok) {
    throw new Error(`Сервер отклонил запрос: код ${response.status}.`)
  }
  return response
}

export async function fetchRequests(): Promise<RequestItem[]> {
  const records: RequestItem[] = []
  let page = 1
  let totalPages: number
  do {
    const response = await callApi(`${API_URL}?sort=-created,-id&perPage=200&page=${page}`)
    const data = await response.json()
    records.push(...data.items)
    totalPages = data.totalPages
    page += 1
  } while (page <= totalPages)
  return records
}

export async function createRequest(data: NewRequest): Promise<RequestItem> {
  const response = await callApi(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...data, status: 'Новая' }),
  })
  return response.json()
}

export async function updateStatus(id: string, status: Status): Promise<RequestItem> {
  const response = await callApi(`${API_URL}/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })
  return response.json()
}

export async function deleteRequest(id: string): Promise<void> {
  await callApi(`${API_URL}/${id}`, { method: 'DELETE' })
}
