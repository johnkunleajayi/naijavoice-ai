import { Moon, Sun, ArrowUpRight } from 'lucide-react'
import { useState } from 'react'
import { Brand } from './Brand'

export function Header() {
  const [dark, setDark] = useState(document.documentElement.classList.contains('dark'))
  function toggleTheme() {
    const next = !dark
    setDark(next)
    document.documentElement.classList.toggle('dark', next)
    try { localStorage.setItem('naijavoice-theme', next ? 'dark' : 'light') } catch { /* Theme still works without storage. */ }
  }
  return <header className="site-header shell">
    <Brand />
    <nav aria-label="Main navigation"><a href="#studio">Voice studio</a><a href="#languages">Our languages</a><a href="#vision">The vision</a></nav>
    <div className="header-actions"><button className="theme-toggle" onClick={toggleTheme} aria-label={`Switch to ${dark ? 'light' : 'dark'} mode`}>
      {dark ? <Sun size={19} /> : <Moon size={19} />}
    </button><a className="header-cta" href="#studio">Explore the studio <ArrowUpRight size={16} /></a></div>
  </header>
}
