import React from 'react'

const API_BASE = 'https://image-import-api.onrender.com'

function App() {
  const [folderUrl, setFolderUrl] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState('')
  const [images, setImages] = React.useState([])
  const [total, setTotal] = React.useState(0)
  const [limit, setLimit] = React.useState(10)
  const [offset, setOffset] = React.useState(0)
  const [currentJob, setCurrentJob] = React.useState(null)
  const [jobs, setJobs] = React.useState([])

  const fetchImages = React.useCallback(async (l = limit, o = offset) => {
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/images?limit=${l}&offset=${o}`)
      const data = await res.json()
      setImages(data.items || [])
      setTotal(data.total ?? (data.items ? data.items.length : 0))
      setLimit(data.limit ?? l)
      setOffset(data.offset ?? o)
    } catch (e) {
      setError('Failed to load images')
    } finally {
      setLoading(false)
    }
  }, [limit, offset])

  const fetchJobs = React.useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs`)
      const data = await res.json()
      setJobs(data.jobs || [])
    } catch (e) {
      console.error('Failed to fetch jobs:', e)
    }
  }, [])

  React.useEffect(() => { 
    fetchImages()
    fetchJobs()
  }, [])

  // Poll for job updates when there's an active job
  React.useEffect(() => {
    if (!currentJob) return
    
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/jobs/${currentJob.id}`)
        const job = await res.json()
        setCurrentJob(job)
        
        if (job.status === 'finished' || job.status === 'failed') {
          clearInterval(interval)
          fetchImages() // Refresh images list
          fetchJobs() // Refresh jobs list
          setCurrentJob(null) // Clear current job
        }
      } catch (e) {
        console.error('Failed to fetch job status:', e)
      }
    }, 2000)
    
    return () => clearInterval(interval)
  }, [currentJob, fetchImages, fetchJobs])

  // Auto-refresh images every 5 seconds when there's an active job
  React.useEffect(() => {
    if (!currentJob) return
    
    const interval = setInterval(() => {
      fetchImages()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [currentJob, fetchImages])

  const onImport = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch(`${API_BASE}/import/google-drive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_url: folderUrl })
      })
      if (!res.ok) throw new Error('Import failed')
      const data = await res.json()
      setCurrentJob({ id: data.job_id, status: 'queued' })
      setFolderUrl('') // Clear form
    } catch (e) {
      setError('Import failed')
    } finally {
      setLoading(false)
    }
  }

  const canPrev = offset > 0
  const canNext = offset + limit < total

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-gray-100 font-sans">
      <div className="max-w-6xl mx-auto p-5">
        <h2 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent p-3">
          Image Import System
        </h2>
        
        {/* Current Job Status */}
        {currentJob && (
          <div className={`p-4 mb-6 rounded-xl border shadow-lg transition-all duration-300 ${
            currentJob.status === 'failed' 
              ? 'bg-red-900/20 border-red-500/50 backdrop-blur-sm' 
              : 'bg-green-900/20 border-green-500/50 backdrop-blur-sm'
          }`}>
            <div className="flex items-center justify-between">
              <strong className="text-lg">Current Job:</strong>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                currentJob.status === 'failed' ? 'bg-red-500 text-white' : 'bg-green-500 text-white'
              }`}>
                {currentJob.status}
              </span>
            </div>
            {currentJob.status === 'started' && currentJob.progress && (
              <div className="mt-3">
                <div className="bg-gray-700 h-3 rounded-full overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-green-400 to-blue-500 h-full rounded-full transition-all duration-500 ease-out" 
                    style={{ width: `${currentJob.progress}%` }}
                  />
                </div>
                <small className="text-gray-400 mt-1 block">{currentJob.progress}% complete</small>
              </div>
            )}
          </div>
        )}

        <form onSubmit={onImport} className="flex gap-3 mb-6 p-4 bg-gray-800/50 rounded-xl backdrop-blur-sm border border-gray-700/50">
          <input
            type="url"
            placeholder="Enter Google Drive folder URL..."
            value={folderUrl}
            onChange={e => setFolderUrl(e.target.value)}
            className="flex-1 px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-100 placeholder-gray-400 transition-all duration-200"
            required
            disabled={loading || currentJob}
          />
          <button 
            type="submit" 
            disabled={loading || currentJob}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 disabled:cursor-not-allowed shadow-lg hover:shadow-xl transition-all duration-200 transform hover:-translate-y-0.5"
          >
            {loading ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Importing...
              </span>
            ) : 'Import'}
          </button>
        </form>
        {error && <p className="text-red-400 mb-6 bg-red-900/20 p-3 rounded-lg border border-red-500/30">{error}</p>}

        <div className="flex justify-between items-center mb-8 text-gray-400">
          <div className="text-xl">Total Images: {total}</div>
          <div className="space-x-3">
            <button 
              disabled={!canPrev || loading} 
              onClick={() => fetchImages(limit, Math.max(0, offset - limit))}
              className="px-4 py-2 bg-gray-700 text-gray-100 rounded-lg hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed transition-all duration-200"
            >
              ← Prev
            </button>
            <button 
              disabled={!canNext || loading} 
              onClick={() => fetchImages(limit, offset + limit)}
              className="px-4 py-2 bg-gray-700 text-gray-100 rounded-lg hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed transition-all duration-200"
            >
              Next →
            </button>
          </div>
        </div>

        {/* Images Grid - Enhanced Card Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {images.map(img => (
            <div 
              key={img.id} 
              className="group bg-gray-800 border border-gray-700 rounded-xl overflow-hidden shadow-lg hover:shadow-2xl hover:-translate-y-2 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="relative overflow-hidden">
                <img 
                  src={img.url} 
                  alt={img.name} 
                  className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-500" 
                  onError={(e) => { e.currentTarget.style.display = 'none' }}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </div>
              <div className="p-5">
                <h3 className="font-bold text-gray-100 mb-2 truncate group-hover:truncate-none transition-all duration-200">
                  {img.name}
                </h3>
                <p className="text-sm text-gray-400 mb-3">{img.mime_type} · {img.size} bytes</p>
                <a 
                  href={img.url} 
                  target="_blank" 
                  rel="noreferrer"
                  className="inline-flex items-center text-blue-400 hover:text-blue-300 text-sm font-medium transition-colors duration-200"
                >
                  Open in New Tab
                  <svg className="ml-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Jobs - Enhanced */}
        {jobs.length > 0 && (
          <div className="space-y-4">
            <h3 className="text-2xl font-semibold mb-6 bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">
              Recent Jobs
            </h3>
            <div className="space-y-4">
              {jobs.slice(0, 5).map(job => (
                <div 
                  key={job.id} 
                  className={`p-5 rounded-xl border-l-4 shadow-md hover:shadow-xl transition-all duration-300 ${
                    job.status === 'finished' 
                      ? 'bg-green-900/20 border-l-green-500' 
                      : job.status === 'failed' 
                      ? 'bg-red-900/20 border-l-red-500' 
                      : job.status === 'started' 
                      ? 'bg-blue-900/20 border-l-blue-500' 
                      : 'bg-gray-800/20 border-l-gray-500'
                  }`}
                >
                  <div className="flex justify-between items-center mb-3">
                    <div className="flex items-center space-x-3">
                      <strong className="text-gray-100">Job {job.id.slice(0, 8)}</strong>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                        job.status === 'finished' 
                          ? 'bg-green-500 text-white' 
                          : job.status === 'failed' 
                          ? 'bg-red-500 text-white' 
                          : job.status === 'started' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-500 text-white'
                      }`}>
                        {job.status.toUpperCase()}
                      </span>
                    </div>
                    <small className="text-gray-500">
                      {job.created_at ? new Date(job.created_at).toLocaleString() : 'Unknown'}
                    </small>
                  </div>
                  {job.result && (
                    <div className="text-sm text-gray-400 bg-gray-800/30 p-3 rounded-lg">
                      <span className="text-green-400 font-medium">{job.result.imported || 0}</span> imported, 
                      <span className="text-blue-400 font-medium ml-1">{job.result.updated || 0}</span> updated
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App