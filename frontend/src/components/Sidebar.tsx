import { useState, useEffect } from 'react'
import { getPipelineStatus, getStats, triggerPipeline, type PipelineStatus, type SystemStats } from '../services/api'
import PipelineFlow from './PipelineFlow'

export default function Sidebar() {
  const [stats, setStats]               = useState<SystemStats | null>(null)
  const [pipelineStatus, setPipeline]   = useState<PipelineStatus | null>(null)
  const [postCount, setPostCount]       = useState<number | null>(null)
  const [isOnline, setIsOnline]         = useState(false)
  const [generating, setGenerating]     = useState(false)
  const [lastPoll, setLastPoll]         = useState<Date | null>(null)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [statsData, statusData, draftsRes] = await Promise.all([
        getStats(),
        getPipelineStatus(),
        fetch('http://127.0.0.1:8000/drafts').then(r => r.json()),
      ])
      setStats(statsData)
      setPipeline(statusData)
      setPostCount(Array.isArray(draftsRes) ? draftsRes.length : 0)
      setIsOnline(true)
      setLastPoll(new Date())
    } catch {
      setIsOnline(false)
    }
  }

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      await triggerPipeline()
      // re-poll sooner after triggering
      setTimeout(loadData, 1500)
    } catch (err) {
      console.error('Failed to trigger pipeline:', err)
    } finally {
      setGenerating(false)
    }
  }

  const isRunning = pipelineStatus?.status === 'running'
  const btnDisabled = generating || isRunning

  const formatPollTime = () => {
    if (!lastPoll) return ''
    return lastPoll.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  return (
    <aside className="sidebar">
      {/* ── Header ── */}
      <div className="sidebar-header">
        <div className="sidebar-brand">
          <div className="brand-icon" role="img" aria-label="Robot">🤖</div>
          <div>
            <div className="brand-name">Blog Agent</div>
            <div className="brand-sub">Autonomous Content System</div>
          </div>
        </div>
        <div className="live-indicator">
          <div className={`live-dot ${isOnline ? '' : 'offline'}`} />
          {isOnline
            ? `Live · ${formatPollTime()}`
            : 'API offline'}
        </div>
      </div>

      {/* ── Stats 2×2 ── */}
      <div className="sidebar-section">
        <div className="section-label">System Stats</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value indigo">
              {postCount !== null ? postCount : '—'}
            </div>
            <div className="stat-label">Drafts Saved</div>
          </div>
          <div className="stat-card">
            <div className="stat-value emerald">
              {stats ? `${stats.success_rate}%` : '—'}
            </div>
            <div className="stat-label">Success Rate</div>
          </div>
          <div className="stat-card">
            <div className="stat-value amber">
              {stats ? stats.total_processed : '—'}
            </div>
            <div className="stat-label">Processed</div>
          </div>
          <div className="stat-card">
            <div className="stat-value violet">
              {stats ? stats.duplicates_detected : '—'}
            </div>
            <div className="stat-label">Dupes Skipped</div>
          </div>
        </div>
      </div>

      {/* ── Pipeline ── */}
      <div className="sidebar-section" style={{ flex: 1 }}>
        <div className="section-label">Agent Pipeline</div>
        <PipelineFlow
          currentStep={pipelineStatus?.current_step}
          status={pipelineStatus?.status}
        />
      </div>

      {/* ── Generate ── */}
      <div className="sidebar-footer">
        <button
          id="generate-pipeline-btn"
          className={`generate-btn ${btnDisabled ? 'running' : ''}`}
          onClick={handleGenerate}
          disabled={btnDisabled}
          aria-label="Trigger blog generation pipeline"
        >
          {btnDisabled ? (
            <>
              <div className="spinner" />
              {isRunning ? 'Pipeline Running…' : 'Starting…'}
            </>
          ) : (
            <>
              <span aria-hidden>⚡</span>
              Generate New Post
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
