import { AudioLines, ArrowUpRight } from 'lucide-react'
import { Header } from './components/Header'
import { Brand } from './components/Brand'
import { Hero } from './features/landing/Hero'
import { LanguageSection } from './features/landing/LanguageSection'
import { VoiceStudio } from './features/studio/VoiceStudio'

export default function App() {
  return <><a href="#main" className="skip-link">Skip to content</a><Header /><main id="main"><Hero />
    <div className="values-strip"><div className="shell flex flex-wrap items-center justify-between gap-5"><span>LOCAL LANGUAGES. LIMITLESS EXPRESSION.</span><span><AudioLines size={17} /> Designed for natural speech</span><span>Built around our languages</span><span>Yorùbá first. More to come.</span></div></div>
    <VoiceStudio /><LanguageSection />
    <section id="vision" className="vision shell"><div><p className="eyebrow">TECHNOLOGY WITH A SENSE OF HOME</p><h2>Our voices deserve<br />a place in the future.</h2></div><div><p>From the stories we share to the ideas we bring to life, language connects us. We're building NaijaVoice AI to help Nigerian languages be heard in a digital world.</p><a className="text-link" href="#studio">Be part of the beginning <ArrowUpRight size={17} /></a></div></section>
  </main><footer className="shell"><Brand /><p>Made with purpose. Rooted in Nigeria.</p><span>© {new Date().getFullYear()} NaijaVoice AI</span></footer></>
}
