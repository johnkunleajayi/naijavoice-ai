import { ArrowUpRight } from 'lucide-react'
import { languages } from '../studio/languages'

export function LanguageSection() {
  return <section id="languages" className="language-section shell" aria-labelledby="languages-title">
    <div className="section-heading"><div><p className="eyebrow">MANY LANGUAGES. ONE HOME.</p><h2 id="languages-title">Made for the way we speak.</h2></div><p>Beginning with Yorùbá.<br />Growing with Nigeria.</p></div>
    <div className="language-grid">{languages.map((language, index) => <article className={`language-card ${index === 0 ? 'current' : ''}`} key={language.id}>
      <div className="flex items-center justify-between"><span className="language-number">0{index + 1}</span><span className="language-status">{index === 0 && <span className="status-dot" />}{language.status}</span></div>
      <h3>{language.name}</h3><p>{['Rich tones. Familiar expression.', 'A voice for every story.', 'Connection beyond boundaries.'][index]}</p>
      <span className="language-caption">{index === 0 ? 'First in development' : 'Planned for the future'} <ArrowUpRight size={17} /></span>
    </article>)}</div>
  </section>
}
