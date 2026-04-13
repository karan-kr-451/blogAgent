import { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import MermaidDiagram from './MermaidDiagram'

interface BlogPost {
  id: string
  title: string
  content: string
  tags: string[]
  word_count: number
  generated_at: string
  source_url: string
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr)
    if (isNaN(d.getTime())) return dateStr
    return d.toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

function DetailSkeleton() {
  return (
    <div className="blog-detail-wrap">
      <div className="skeleton" style={{ height: '0.8rem', width: '64px', marginBottom: '2rem', borderRadius: '6px' }} />
      <div className="skeleton" style={{ height: '1.875rem', width: '75%', marginBottom: '0.625rem' }} />
      <div className="skeleton" style={{ height: '1.875rem', width: '55%', marginBottom: '1.375rem' }} />
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.75rem' }}>
        <div className="skeleton" style={{ height: '0.75rem', width: '100px' }} />
        <div className="skeleton" style={{ height: '0.75rem', width: '60px' }} />
      </div>
      {[100, 95, 88, 100, 76, 92, 80, 100, 70].map((w, i) => (
        <div
          key={i}
          className="skeleton"
          style={{
            height: '0.8rem',
            width: `${w}%`,
            marginBottom: '0.55rem',
          }}
        />
      ))}
    </div>
  )
}

export default function BlogDetail() {
  const { id }  = useParams()
  const [blog, setBlog]     = useState<BlogPost | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadBlog()
  }, [id])

  const loadBlog = async () => {
    console.log("Loading blog for ID:", id);
    if (!id) {
      console.warn("No ID provided in params");
      return
    }
    setLoading(true)
    setError(null)

    try {
      console.log("Fetching drafts from API...");
      const res    = await fetch('http://127.0.0.1:8000/drafts')
      if (!res.ok) throw new Error(`API returned ${res.status}: ${res.statusText}`)
      
      const drafts = await res.json()
      console.log("Fetched drafts count:", drafts?.length);
      
      const found  = drafts.find((d: BlogPost) => {
        // Log individual matches if needed, but be careful with large arrays
        return d.id === id
      })
      
      if (found) {
        console.log("Found blog post:", found.title);
        setBlog(found)
      } else {
        console.warn("No blog post found matching ID:", id);
        // Fallback: try finding by stem if ID mismatch
        const secondaryMatch = drafts.find((d: BlogPost) => d.id.includes(id) || id.includes(d.id));
        if (secondaryMatch) {
           console.log("Found secondary match:", secondaryMatch.title);
           setBlog(secondaryMatch);
        } else {
           setBlog(null);
        }
      }
    } catch (err: any) {
      console.error("Failed to load blog:", err)
      setError(err.message || 'Failed to fetch blog post')
    } finally {
      setLoading(false)
    }
  }

  const blogMarkdown = useMemo(() => (
    <ReactMarkdown
      components={{
        code({ node, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '')
          if (match && match[1] === 'mermaid') {
            return <MermaidDiagram chart={String(children).replace(/\n$/, '')} />
          }
          return (
            <code className={className} {...props}>
              {children}
            </code>
          )
        }
      }}
    >
      {blog?.content || ''}
    </ReactMarkdown>
  ), [blog?.content])

  if (loading) return <DetailSkeleton />

  if (!blog) {
    return (
      <div className="blog-detail-wrap">
        <Link to="/" className="back-link">← Back to Posts</Link>
        <div className="empty-state" style={{ borderStyle: 'solid', marginTop: '1rem' }}>
          <div className="empty-icon">🔍</div>
          <div className="empty-title">Post not found</div>
          <div className="empty-desc">
            This draft may have been deleted or the ID is invalid.
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="blog-detail-wrap">
      <Link to="/" className="back-link" id="back-to-posts">
        ← Back to Posts
      </Link>

      <h1 className="blog-detail-title">{blog.title}</h1>

      <div className="blog-detail-meta">
        <span>📅 {formatDate(blog.generated_at)}</span>
        <span>·</span>
        <span>{blog.word_count.toLocaleString()} words</span>
        {blog.source_url && (
          <>
            <span>·</span>
            <a
              href={blog.source_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              🔗 Source
            </a>
          </>
        )}
      </div>

      {blog.tags.length > 0 && (
        <div className="blog-detail-tags">
          {blog.tags.map((tag, i) => (
            <span key={i} className="tag">{tag}</span>
          ))}
        </div>
      )}

      <article className="blog-content">
        {blogMarkdown}
      </article>
    </div>
  )
}
