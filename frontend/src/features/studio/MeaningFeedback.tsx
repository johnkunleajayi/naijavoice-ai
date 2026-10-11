import { useState } from 'react'

interface Props {
  isGenerating: boolean
  onDismiss: () => void
  onRegenerate: (english: string) => Promise<boolean>
}

export function MeaningFeedback({ isGenerating, onDismiss, onRegenerate }: Props) {
  const [clarifying, setClarifying] = useState(false)
  const [english, setEnglish] = useState('')
  return <div className="meaning-feedback">
    {!clarifying ? <><p>Is this what you meant?</p>
      <div className="feedback-actions"><button onClick={onDismiss}>Yes</button>
        <button onClick={() => setClarifying(true)}>No</button></div>
    </> : <><label htmlFor="clarification">Tell us what you meant in English.</label>
      <textarea id="clarification" value={english} maxLength={500} disabled={isGenerating}
        onChange={event => setEnglish(event.target.value)} />
      <button className="generate-button" disabled={!english.trim() || isGenerating}
        onClick={async () => { if (await onRegenerate(english)) onDismiss() }}>
        {isGenerating ? 'Regenerating…' : 'Regenerate'}
      </button>
    </>}
  </div>
}
