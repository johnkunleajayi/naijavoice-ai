import { ArrowDown, ArrowUpRight } from 'lucide-react'

export function Hero() {
  return <section className="hero shell" aria-labelledby="hero-title">
    <div className="hero-copy">
      <p className="eyebrow"><span className="status-dot" /> ROOTED IN NIGERIA. BUILT FOR EXPRESSION.</p>
      <h1 id="hero-title">Our languages.<br />Our stories.<br /><span>Now, our voice.</span></h1>
      <p className="hero-description">A new voice for Nigerian languages. Turn your words into expressive AI speech — starting with Yorùbá.</p>
      <div className="hero-actions"><a className="primary-button" href="#studio">Explore voice studio <ArrowUpRight size={18} /></a><a className="text-link" href="#vision">Meet the vision <ArrowDown size={16} /></a></div>
      <div className="hero-note"><span className="flag" aria-label="Nigerian flag" /> Nigerian roots. A world of possibilities.</div>
    </div>
    <div className="voice-art" aria-label="Abstract sound waves celebrating Nigerian voices" role="img">
      <div className="art-grid" /><div className="art-circle circle-one" /><div className="art-circle circle-two" />
      <div className="art-label"><span className="status-dot" /> THE SOUND OF HOME</div>
      <div className="art-greeting">Ẹ káàbọ̀<span>You're welcome here.</span></div>
      <div className="art-wave">{Array.from({length: 49}, (_, i) => <i key={i} style={{height: `${18 + Math.abs(Math.sin(i * .57) * Math.cos(i * .19)) * 128}px`}} />)}</div>
      <div className="art-bottom"><span>01 / YORÙBÁ</span><span>Language. Identity. Connection.</span></div>
    </div>
  </section>
}
