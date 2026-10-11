export async function generateSpeech(text: string, signal: AbortSignal): Promise<Blob> {
  const response = await fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'audio/wav' },
    body: JSON.stringify({ text, language: 'yo' }),
    signal,
  })
  if (!response.ok) throw new Error('Speech generation failed')
  const audio = await response.blob()
  if (!audio.size || !audio.type.toLowerCase().startsWith('audio/')) {
    throw new Error('Invalid audio response')
  }
  return audio
}
