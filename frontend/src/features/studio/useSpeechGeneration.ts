import { useEffect, useRef, useState } from 'react'
import { generateSpeech } from './ttsApi'
import { translateToYoruba } from './translationApi'

export function useSpeechGeneration() {
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState('')
  const [translation, setTranslation] = useState('')
  const request = useRef<AbortController | null>(null)

  useEffect(() => () => request.current?.abort(), [])
  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
  }, [audioUrl])

  function reset() {
    request.current?.abort()
    request.current = null
    setIsGenerating(false)
    setAudioUrl(null)
    setError('')
    setTranslation('')
  }

  async function generate(text: string, language: string, translate = false): Promise<boolean> {
    if (language !== 'yo' || !text.trim() || request.current) return false
    const controller = new AbortController()
    request.current = controller
    setIsGenerating(true)
    setError('')
    setAudioUrl(null)
    setTranslation('')
    let stage = translate ? 'translation' : 'speech'
    try {
      const yoruba = translate ? await translateToYoruba(text, controller.signal) : text
      if (controller.signal.aborted) return false
      if (translate) setTranslation(yoruba)
      stage = 'speech'
      const audio = await generateSpeech(yoruba, controller.signal)
      if (controller.signal.aborted) return false
      setAudioUrl(URL.createObjectURL(audio))
      return true
    } catch {
      if (!controller.signal.aborted) {
        setError(stage === 'translation'
          ? 'We couldn’t translate your text. Please try again in a moment.'
          : 'We couldn’t generate your speech. Please try again in a moment.')
      }
      return false
    } finally {
      if (request.current === controller) {
        request.current = null
        setIsGenerating(false)
      }
    }
  }

  return { audioUrl, isGenerating, error, translation, generate, reset }
}
