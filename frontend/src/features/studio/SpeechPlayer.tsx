import { useEffect, useRef, useState } from 'react'

export function SpeechPlayer({ src }: { src: string }) {
  const player = useRef<HTMLAudioElement>(null)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    const audio = player.current
    let active = true
    audio?.play().catch(() => {
      if (active) setNotice('Your speech is ready. Press play to listen.')
    })
    return () => { active = false; audio?.pause() }
  }, [src])

  return <div className="speech-player">
    <audio ref={player} src={src} controls aria-label="Generated Yoruba speech"
      onError={() => setNotice('This audio could not be played. Please generate it again.')} />
    {notice && <p role="status">{notice}</p>}
  </div>
}
