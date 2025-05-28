import { useState, useEffect, useRef, useCallback } from 'react'

export default function useProgressSequence() {
  const [message, setMessage] = useState<string | null>(null)
  const [isActive, setIsActive] = useState(false)
  const sequenceRef = useRef<string[]>([])
  const indexRef = useRef(0)
  const timerRef = useRef<NodeJS.Timeout | null>(null)
  
  const start = useCallback((sequence: string[]) => {
    // Reset and start new sequence
    stop()
    sequenceRef.current = sequence
    indexRef.current = 0
    setIsActive(true)
    
    if (sequence.length > 0) {
      setMessage(sequence[0])
    }
  }, [])
  
  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
    setIsActive(false)
    setMessage(null)
    indexRef.current = 0
  }, [])
  
  useEffect(() => {
    if (!isActive || sequenceRef.current.length === 0) return
    
    timerRef.current = setInterval(() => {
      indexRef.current = (indexRef.current + 1) % sequenceRef.current.length
      setMessage(sequenceRef.current[indexRef.current])
    }, 2000)
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [isActive])
  
  return { message, start, stop, isActive }
}