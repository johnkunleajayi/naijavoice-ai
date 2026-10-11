import { useState } from 'react'
import { ArrowUpRight, AudioLines, Info, RotateCcw, Sparkles } from 'lucide-react'
import { languages } from './languages'
import { useSpeechGeneration } from './useSpeechGeneration'
import { SpeechPlayer } from './SpeechPlayer'
import { MeaningFeedback } from './MeaningFeedback'

export function VoiceStudio() {
  const [languageId, setLanguageId] = useState('yo')
  const language = languages.find(item => item.id === languageId) ?? languages[0]
  const [text, setText] = useState<string>(languages[0].sample)
  const speech = useSpeechGeneration()
  const [mode, setMode] = useState<'yoruba' | 'english'>('yoruba')
  const [askMeaning, setAskMeaning] = useState(false)
  function reset() { speech.reset(); setAskMeaning(false) }
  const sample = mode === 'english' ? 'I want to write in Yoruba very well.' : language.sample
  async function generate() {
    setAskMeaning(false)
    const success = await speech.generate(text, languageId, mode === 'english')
    if (success && mode === 'yoruba') setAskMeaning(true)
  }
  const isYoruba = languageId === 'yo'
  return <section className="studio-section shell" id="studio" aria-labelledby="studio-title">
    <div className="section-heading"><div><p className="eyebrow">YOUR WORDS, A FAMILIAR VOICE</p><h2 id="studio-title">Imagine how it could sound.</h2></div><span className="preview-badge"><Sparkles size={14} /> Studio preview</span></div>
    <div className="studio-card">
      <div className="studio-editor">
        <div className="editor-toolbar"><label htmlFor="language">Speech language</label><select id="language" value={languageId} onChange={event => { reset(); const next = languages.find(item => item.id === event.target.value)!; setLanguageId(next.id); setText(mode === 'english' ? 'I want to write in Yoruba very well.' : next.sample) }}>
          {languages.map(item => <option key={item.id} value={item.id}>{item.label} — {item.status}</option>)}
        </select></div>
        <div className="input-modes" role="group" aria-label="Yoruba input mode">
          <button aria-pressed={mode === 'yoruba'} onClick={() => { reset(); setMode('yoruba'); setText(language.sample) }}>Yoruba</button>
          <button aria-pressed={mode === 'english'} disabled={!isYoruba}
            onClick={() => { reset(); setMode('english'); setText('I want to write in Yoruba very well.') }}>English → Yoruba</button>
        </div>
        {mode === 'yoruba' && <p className="input-hint">Type Yoruba with or without tone marks.</p>}
        <label className="input-label" htmlFor="speech-text">{mode === 'english' ? 'Tell us in English' : 'Give your words a voice'}</label>
        <textarea id="speech-text" value={text} onChange={event => { reset(); setText(event.target.value) }} maxLength={500} spellCheck={false} />
        <div className="editor-bottom"><button className="text-link" onClick={() => { reset(); setText(sample) }}><RotateCcw size={14} /> Use sample text</button><span>{text.length} / 500</span></div>
      </div>
      <div className="studio-output"><div className="output-top"><span className="small-label">VOICE PREVIEW</span><span className="language-chip">{language.name}</span></div>
        <div className="output-icon"><AudioLines size={32} strokeWidth={1.5} /></div>
        <h3>Your next story starts here.</h3><p>Write something that sounds like you.<br />Bring your Yorùbá words to life.</p>
        <button className="generate-button" disabled={!isYoruba || !text.trim() || speech.isGenerating}
          onClick={() => void generate()} aria-busy={speech.isGenerating}>
          <Sparkles size={16} /> {speech.isGenerating ? 'Generating…' : 'Generate speech'} <ArrowUpRight size={16} />
        </button>
        {speech.isGenerating && <p role="status">Generating your speech. This may take a moment.</p>}
        {speech.error && <p className="speech-error" role="alert">{speech.error}</p>}
        {speech.translation && <div className="yoruba-translation" aria-live="polite"><h4>Yoruba translation</h4><p>{speech.translation}</p></div>}
        {speech.audioUrl && <SpeechPlayer key={speech.audioUrl} src={speech.audioUrl} />}
        {askMeaning && isYoruba && <MeaningFeedback isGenerating={speech.isGenerating}
          onDismiss={() => setAskMeaning(false)} onRegenerate={english => speech.generate(english, languageId, true)} />}
        <p className="preview-info"><Info size={13} /> {isYoruba ? 'Yorùbá speech generation is available.' : `${language.label} speech is coming soon.`}</p>
      </div>
    </div>
    <p className="studio-footnote">Your text is sent to NaijaVoice AI to generate speech. Yorùbá is available; Igbo and Hausa are coming soon.</p>
  </section>
}
