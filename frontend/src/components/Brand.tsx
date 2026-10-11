import { AudioLines } from 'lucide-react'

export function Brand() {
  return <a href="#" className="brand" aria-label="NaijaVoice AI home">
    <span className="brand-mark"><AudioLines size={23} /></span>
    <span>NaijaVoice<span className="brand-ai"> AI</span></span>
  </a>
}
