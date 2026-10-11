export async function translateToYoruba(text: string, signal: AbortSignal): Promise<string> {
  const response = await fetch('/api/translate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ text }), signal,
  })
  if (!response.ok) throw new Error('Translation failed')
  const result: unknown = await response.json()
  if (!result || typeof result !== 'object' || !('text' in result)
    || typeof result.text !== 'string' || !result.text.trim()) {
    throw new Error('Invalid translation')
  }
  return result.text
}
