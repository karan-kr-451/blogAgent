import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getPipelineStatus, getDrafts, type PipelineStatus } from '../services/api'

interface BlogFile {
  id: string
  title: string
  content: string
  tags: string[]
  word_count: number
  generated_at: string
  file_path: string
  source_url: string
}

function formatRelativeTime(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return dateStr
    const diffMs   = Date.now() - date.getTime()
    const diffMins = Math.floor(diffMs / 60_000)
    const diffHrs  = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHrs / 24)
    if (diffMins < 1)  return 'just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHrs < 24)  return `${diffHrs}h ago`
    return `${diffDays}d ago`
  } catch {
    return dateStr
  }
}

function stripMarkdown(text: string): string {
  return text.replace(/[#*`_~>[\]()!]/g, '').trim()
}

function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton" style={{ height: '0.875rem', width: '82%' }} />
      <div className="skeleton" style={{ height: '0.75rem', width: '100%' }} />
      <div className="skeleton" style={{ height: '0.75rem', width: '90%' }} />
      <div className="skeleton" style={{ height: '0.75rem', width: '70%' }} />
      <div style={{ display: 'flex', gap: '0.4rem', marginTop: '0.25rem' }}>
        <div className="skeleton" style={{ height: '1.1rem', width: '52px', borderRadius: '20px' }} />
        <div className="skeleton" style={{ height: '1.1rem', width: '64px', borderRadius: '20px' }} />
      </div>
    </div>
  )
}

function PipelineBanner({ status }: { status: PipelineStatus | null }) {
  if (!status) return null

  const bannerClass = status.status === 'running'
    ? 'running'
    : status.status === 'completed'
    ? 'completed'
    : status.status === 'error'
    ? 'error'
    : ''

  const bannerText =
    status.status === 'running'   ? 'Pipeline is running'             :
    status.status === 'completed' ? 'Last run completed successfully'  :
    status.status === 'error'     ? 'Last run encountered an error'    :
                                    'Pipeline idle — ready to generate'

  const dotClass = status.status === 'running'   ? 'running'   :
                   status.status === 'completed' ? 'completed' :
                   status.status === 'error'     ? 'error'     :
                                                   'idle'

  return (
    <div className={`pipeline-banner ${bannerClass}`}>
      <div className={`banner-dot ${dotClass}`} />
      <span className="banner-text">{bannerText}</span>
      {status.current_step && (
        <span className="banner-step">{status.current_step}</span>
      )}
    </div>
  )
}

export default function BlogList() {
  const [blogs, setBlogs]                   = useState<BlogFile[]>([])
  const [pipelineStatus, setPipeline]       = useState<PipelineStatus | null>(null)
  const [initialLoading, setInitialLoading] = useState(true)

  useEffect(() => {
    loadAll()
    const interval = setInterval(loadPipeline, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadAll = async () => {
    await Promise.all([loadBlogs(), loadPipeline()])
    setInitialLoading(false)
  }

  const loadBlogs = async () => {
    try {
      const data = await getDrafts()
      if (Array.isArray(data)) setBlogs(data)
    } catch {}
  }

  const loadPipeline = async () => {
    try {
      const data = await getPipelineStatus()
      setPipeline(data)
    } catch {}
  }

  return (
    <div className="main-content">
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Generated Posts</h1>
        <p className="page-subtitle">
          {initialLoading
            ? 'Loading…'
            : blogs.length > 0
            ? `${blogs.length} draft${blogs.length !== 1 ? 's' : ''} saved`
            : 'No posts generated yet'}
        </p>
      </div>

      {/* Pipeline banner */}
      <PipelineBanner status={pipelineStatus} />

      {/* Grid */}
      <div className="blog-grid">
        {initialLoading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : blogs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <div className="empty-title">No posts yet</div>
            <div className="empty-desc">
              Hit <strong style={{ color: 'var(--indigo-light)' }}>Generate New Post</strong> in
              the sidebar to run the agent pipeline and create your first blog post.
            </div>
          </div>
        ) : (
          blogs.map(blog => (
            <Link
              to={`/blog/${blog.id}`}
              key={blog.id}
              className="blog-card"
              id={`blog-card-${blog.id}`}
            >
              <div className="blog-card-title">{blog.title}</div>
              <div className="blog-card-preview">
                {stripMarkdown(blog.content).substring(0, 200)}…
              </div>
              <div className="blog-card-footer">
                <div className="blog-tags">
                  {blog.tags.slice(0, 2).map((tag, i) => (
                    <span key={i} className="tag">{tag}</span>
                  ))}
                </div>
                <div className="blog-card-meta">
                  <span>{blog.word_count.toLocaleString()}w</span>
                  <div className="meta-sep" aria-hidden />
                  <span>{formatRelativeTime(blog.generated_at)}</span>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
