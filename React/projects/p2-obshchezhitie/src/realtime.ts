import PocketBase from 'pocketbase'
import type { RequestItem } from './requests'

export type RequestEvent = {
  action: string
  record: RequestItem
}

export function subscribeRequests(onEvent: (event: RequestEvent) => void) {
  const pb = new PocketBase('http://localhost:8090')
  return pb.collection('obshchezhitie').subscribe<RequestItem>('*', onEvent)
}
