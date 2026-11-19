import type { RequestItem } from './requests'

const WEBHOOK_URL = 'http://localhost:5678/webhook/zayavka'

export async function sendRequest(request: RequestItem): Promise<boolean> {
  try {
    const response = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...request, placeLabel: 'Комната' }),
    })
    return response.ok
  } catch {
    return false
  }
}
