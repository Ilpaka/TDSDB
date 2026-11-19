import { createContext, useContext } from 'react'
import type { NewRequest, RequestItem, Status } from './requests'

export type Board = {
  requests: RequestItem[]
  loading: boolean
  error: string
  newCount: number
  notice: string
  retry: () => void
  handleAdd: (data: NewRequest) => Promise<void>
  handleNext: (id: string, status: Status) => Promise<void>
  handleRemove: (id: string) => Promise<boolean>
}

export const BoardContext = createContext<Board | null>(null)

export function useBoard(): Board {
  const board = useContext(BoardContext)
  if (board === null) {
    throw new Error('useBoard вызван вне BoardProvider')
  }
  return board
}
