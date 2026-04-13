import { useEffect, useRef, useState } from 'react'
import mermaid from 'mermaid'

// Initialize once — custom vibrant theme for dark mode
mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  themeVariables: {
    background: '#0f172a',
    primaryColor: '#8b5cf6',     // Violet
    primaryTextColor: '#ffffff',
    primaryBorderColor: '#c4b5fd',
    secondaryColor: '#ec4899',   // Pink
    tertiaryColor: '#14b8a6',    // Teal
    nodeBorder: '#c4b5fd',
    clusterBkg: '#1e293b',
    clusterBorder: '#334155',
    lineColor: '#fde047',        // Yellow
    textColor: '#e2e8f0',
    fontFamily: '"Inter", system-ui, sans-serif',
  },
  flowchart: { useMaxWidth: true, htmlLabels: true, curve: 'basis' },
  sequence: { useMaxWidth: true },
})

let idCounter = 0

interface Props {
  chart: string
}

export default function MermaidDiagram({ chart }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [svg, setSvg] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    const id = `mermaid-${Date.now()}-${idCounter++}`

    ;(async () => {
      try {
        const { svg: rendered } = await mermaid.render(id, chart.trim())
        if (!cancelled) {
          setSvg(rendered)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) {
          setError(String(err))
          setSvg('')
        }
      }
    })()

    return () => { cancelled = true }
  }, [chart])

  if (error) {
    return (
      <pre className="mermaid-error">
        <code>{chart}</code>
      </pre>
    )
  }

  return (
    <div
      ref={containerRef}
      className="mermaid-diagram"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}
