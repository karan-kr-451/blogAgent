interface PipelineFlowProps {
  currentStep?: string
  status?: string
}

const AGENTS = [
  { id: 'crawl',            name: 'Crawler',   icon: '🕷',  desc: 'Web navigation'     },
  { id: 'extract',          name: 'Extractor', icon: '⚙',  desc: 'Content parsing'    },
  { id: 'check_duplicates', name: 'Memory',    icon: '🧠', desc: 'Duplicate check'    },
  { id: 'write',            name: 'Writer',    icon: '✍',  desc: 'Content generation' },
  { id: 'edit',             name: 'Editor',    icon: '✏',  desc: 'Quality review'     },
  { id: 'review',           name: 'Reviewer',  icon: '🔍', desc: 'Originality check'  },
  { id: 'publish',          name: 'Publisher', icon: '📤', desc: 'Publishing draft'   },
]

export default function PipelineFlow({ currentStep, status }: PipelineFlowProps) {
  const activeIndex  = AGENTS.findIndex(a => a.id === currentStep)
  const isRunning    = status === 'running'
  const isCompleted  = status === 'completed'

  const getNodeState = (index: number): 'active' | 'completed' | 'waiting' => {
    if (isRunning) {
      if (index === activeIndex) return 'active'
      if (index < activeIndex)   return 'completed'
    }
    if (isCompleted)             return 'completed'
    return 'waiting'
  }

  return (
    <div className="pipeline-flow">
      {AGENTS.map((agent, index) => {
        const state = getNodeState(index)
        return (
          <div key={agent.id} className={`pipeline-node ${state}`}>
            <div className={`node-dot ${state}`}>
              {state === 'completed' ? '✓' : agent.icon}
            </div>
            <div className="node-info">
              <div className={`node-name ${state}`}>{agent.name}</div>
              <div className={`node-desc ${state}`}>
                {state === 'active' ? 'Processing…' : agent.desc}
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
