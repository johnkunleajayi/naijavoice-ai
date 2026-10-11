import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { VoiceStudio } from './VoiceStudio'

const wav = () => new Response(new Blob(['RIFF-test-WAVE'], { type: 'audio/wav' }), {
  status: 200, headers: { 'Content-Type': 'audio/wav' },
})

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(wav()))
  vi.stubGlobal('URL', Object.assign(class extends URL {}, {
    createObjectURL: vi.fn().mockReturnValue('blob:speech'),
    revokeObjectURL: vi.fn(),
  }))
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue(undefined)
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {})
})

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

const generate = () => screen.getByRole('button', { name: 'Generate speech' }) as HTMLButtonElement

it('posts entered text and Yoruba, receives a Blob, and autoplays with controls', async () => {
  render(<VoiceStudio />)
  fireEvent.change(screen.getByLabelText('Give your words a voice'), { target: { value: 'Ẹ káàárọ̀' } })
  fireEvent.click(generate())
  await waitFor(() => expect(screen.getByLabelText('Generated Yoruba speech')).toBeTruthy())
  const [url, request] = vi.mocked(fetch).mock.calls[0]
  expect(url).toBe('/api/tts')
  expect(request?.method).toBe('POST')
  expect(JSON.parse(request?.body as string)).toEqual({ text: 'Ẹ káàárọ̀', language: 'yo' })
  expect(URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
  expect(HTMLMediaElement.prototype.play).toHaveBeenCalledOnce()
  expect((screen.getByLabelText('Generated Yoruba speech') as HTMLAudioElement).controls).toBe(true)
})

it('shows loading and prevents duplicate generation', async () => {
  let finish!: (response: Response) => void
  vi.mocked(fetch).mockImplementation(() => new Promise(resolve => { finish = resolve }))
  render(<VoiceStudio />)
  fireEvent.click(generate())
  expect((screen.getByRole('button', { name: 'Generating…' }) as HTMLButtonElement).disabled).toBe(true)
  expect(screen.getByRole('status').textContent).toContain('Generating your speech')
  expect(fetch).toHaveBeenCalledOnce()
  finish(wav())
  await waitFor(() => expect(generate().disabled).toBe(false))
})

describe('generation failure', () => {
  it.each(['http', 'offline', 'invalid'])('shows a friendly retryable error for %s', async failure => {
    if (failure === 'http') vi.mocked(fetch).mockResolvedValue(new Response('private detail', { status: 503 }))
    if (failure === 'offline') vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'))
    if (failure === 'invalid') vi.mocked(fetch).mockResolvedValue(new Response('<html>Error</html>'))
    render(<VoiceStudio />)
    fireEvent.click(generate())
    expect((await screen.findByRole('alert')).textContent).toContain('Please try again')
    expect(generate().disabled).toBe(false)
    expect(screen.queryByLabelText('Generated Yoruba speech')).toBeNull()
  })
})

it.each(['ig', 'ha'])('disables %s generation and marks it coming soon', language => {
  render(<VoiceStudio />)
  fireEvent.change(screen.getByLabelText('Speech language'), { target: { value: language } })
  expect(generate().disabled).toBe(true)
  expect(screen.getByText(/speech is coming soon/)).toBeTruthy()
  fireEvent.click(generate())
  expect(fetch).not.toHaveBeenCalled()
})

it('disables whitespace-only text', () => {
  render(<VoiceStudio />)
  fireEvent.change(screen.getByLabelText('Give your words a voice'), { target: { value: '  ' } })
  expect(generate().disabled).toBe(true)
})

it('provides a play prompt if autoplay is blocked', async () => {
  vi.mocked(HTMLMediaElement.prototype.play).mockRejectedValue(new Error('Autoplay blocked'))
  render(<VoiceStudio />)
  fireEvent.click(generate())
  expect(await screen.findByText('Your speech is ready. Press play to listen.')).toBeTruthy()
  expect(screen.getByLabelText('Generated Yoruba speech')).toBeTruthy()
})

it('cancels stale generation on language change', async () => {
  let finish!: (response: Response) => void
  vi.mocked(fetch).mockImplementation(() => new Promise(resolve => { finish = resolve }))
  render(<VoiceStudio />)
  fireEvent.click(generate())
  const signal = vi.mocked(fetch).mock.calls[0][1]?.signal
  fireEvent.change(screen.getByLabelText('Speech language'), { target: { value: 'ig' } })
  expect(signal?.aborted).toBe(true)
  finish(wav())
  await waitFor(() => expect(screen.queryByRole('status')).toBeNull())
  expect(URL.createObjectURL).not.toHaveBeenCalled()
})

it('releases generated object URLs and stops audio when input changes', async () => {
  render(<VoiceStudio />)
  fireEvent.click(generate())
  await screen.findByLabelText('Generated Yoruba speech')
  fireEvent.change(screen.getByLabelText('Give your words a voice'), { target: { value: 'New text' } })
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:speech')
  expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled()
  expect(screen.queryByLabelText('Generated Yoruba speech')).toBeNull()
})

it('cancels in-flight requests on unmount', () => {
  vi.mocked(fetch).mockImplementation(() => new Promise(() => {}))
  const { unmount } = render(<VoiceStudio />)
  fireEvent.click(generate())
  const signal = vi.mocked(fetch).mock.calls[0][1]?.signal
  unmount()
  expect(signal?.aborted).toBe(true)
})

const translated = 'Mo fẹ́ kọ̀wé lédè Yorùbá dáadáa.'
const translationResponse = () => new Response(JSON.stringify({ text: translated }), {
  headers: { 'Content-Type': 'application/json' },
})
const englishMode = () => fireEvent.click(screen.getByRole('button', { name: 'English → Yoruba' }))

it('translates English, displays Yoruba, then sends that exact text to TTS', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(translationResponse()).mockResolvedValueOnce(wav())
  render(<VoiceStudio />)
  englishMode()
  fireEvent.change(screen.getByLabelText('Tell us in English'), { target: { value: 'I want to write in Yoruba very well.' } })
  fireEvent.click(generate())
  await screen.findByLabelText('Generated Yoruba speech')
  expect(screen.getByText('Yoruba translation')).toBeTruthy()
  expect(screen.getByText(translated)).toBeTruthy()
  expect(vi.mocked(fetch).mock.calls.map(call => call[0])).toEqual(['/api/translate', '/api/tts'])
  expect(JSON.parse(vi.mocked(fetch).mock.calls[0][1]?.body as string)).toEqual({ text: 'I want to write in Yoruba very well.' })
  expect(JSON.parse(vi.mocked(fetch).mock.calls[1][1]?.body as string)).toEqual({ text: translated, language: 'yo' })
  expect(screen.queryByText('Is this what you meant?')).toBeNull()
})

it('asks for meaning after Yoruba speech and Yes dismisses the question', async () => {
  render(<VoiceStudio />)
  fireEvent.click(generate())
  await screen.findByText('Is this what you meant?')
  fireEvent.click(screen.getByRole('button', { name: 'Yes' }))
  expect(screen.queryByText('Is this what you meant?')).toBeNull()
  expect(fetch).toHaveBeenCalledOnce()
})

it('No translates clarification and regenerates audio, releasing the old URL', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(wav()).mockResolvedValueOnce(translationResponse()).mockResolvedValueOnce(wav())
  vi.mocked(URL.createObjectURL).mockReturnValueOnce('blob:first').mockReturnValueOnce('blob:second')
  render(<VoiceStudio />)
  fireEvent.click(generate())
  await screen.findByText('Is this what you meant?')
  fireEvent.click(screen.getByRole('button', { name: 'No' }))
  const regenerate = screen.getByRole('button', { name: 'Regenerate' }) as HTMLButtonElement
  expect(regenerate.disabled).toBe(true)
  fireEvent.change(screen.getByLabelText('Tell us what you meant in English.'), { target: { value: 'I want to write in Yoruba very well.' } })
  fireEvent.click(regenerate)
  await waitFor(() => expect((screen.getByLabelText('Generated Yoruba speech') as HTMLAudioElement).getAttribute('src')).toBe('blob:second'))
  expect(vi.mocked(fetch).mock.calls.map(call => call[0])).toEqual(['/api/tts', '/api/translate', '/api/tts'])
  expect(JSON.parse(vi.mocked(fetch).mock.calls[2][1]?.body as string)).toEqual({ text: translated, language: 'yo' })
  expect(screen.getByText(translated)).toBeTruthy()
  expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:first')
  expect(HTMLMediaElement.prototype.play).toHaveBeenCalledTimes(2)
  expect(screen.queryByLabelText('Tell us what you meant in English.')).toBeNull()
})

it.each(['http', 'invalid', 'offline'])('handles translation %s failure without TTS', async failure => {
  if (failure === 'http') vi.mocked(fetch).mockResolvedValue(new Response('error', { status: 503 }))
  if (failure === 'invalid') vi.mocked(fetch).mockResolvedValue(new Response(JSON.stringify({ text: ' ' })))
  if (failure === 'offline') vi.mocked(fetch).mockRejectedValue(new TypeError('offline'))
  render(<VoiceStudio />)
  englishMode()
  fireEvent.click(generate())
  expect((await screen.findByRole('alert')).textContent).toContain('translate your text')
  expect(fetch).toHaveBeenCalledOnce()
  expect(generate().disabled).toBe(false)
})

it('keeps the translation visible if subsequent TTS fails', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(translationResponse()).mockResolvedValueOnce(new Response('offline', { status: 503 }))
  render(<VoiceStudio />)
  englishMode()
  fireEvent.click(generate())
  expect((await screen.findByRole('alert')).textContent).toContain('generate your speech')
  expect(screen.getByText(translated)).toBeTruthy()
  expect(screen.queryByLabelText('Generated Yoruba speech')).toBeNull()
})

it('cancels pending translation on mode switch and does not start stale TTS', async () => {
  let finish!: (response: Response) => void
  vi.mocked(fetch).mockImplementation(() => new Promise(resolve => { finish = resolve }))
  render(<VoiceStudio />)
  englishMode()
  fireEvent.click(generate())
  const signal = vi.mocked(fetch).mock.calls[0][1]?.signal
  fireEvent.click(screen.getByRole('button', { name: /^Yoruba$/ }))
  expect(signal?.aborted).toBe(true)
  finish(translationResponse())
  await waitFor(() => expect(generate().disabled).toBe(false))
  expect(fetch).toHaveBeenCalledOnce()
  expect(screen.queryByText('Yoruba translation')).toBeNull()
})

it('keeps clarification available for retry when regeneration fails', async () => {
  vi.mocked(fetch).mockResolvedValueOnce(wav()).mockResolvedValueOnce(new Response('offline', { status: 503 }))
  render(<VoiceStudio />)
  fireEvent.click(generate())
  await screen.findByText('Is this what you meant?')
  fireEvent.click(screen.getByRole('button', { name: 'No' }))
  fireEvent.change(screen.getByLabelText('Tell us what you meant in English.'), { target: { value: 'My intended meaning' } })
  fireEvent.click(screen.getByRole('button', { name: 'Regenerate' }))
  await screen.findByRole('alert')
  expect((screen.getByLabelText('Tell us what you meant in English.') as HTMLTextAreaElement).value).toBe('My intended meaning')
  expect((screen.getByRole('button', { name: 'Regenerate' }) as HTMLButtonElement).disabled).toBe(false)
})
