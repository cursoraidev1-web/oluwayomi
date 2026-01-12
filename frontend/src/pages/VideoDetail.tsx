import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  ArrowLeft, 
  Film, 
  Clock, 
  Play,
  Loader2,
  CheckCircle,
  AlertCircle,
  Share2,
  Trash2,
  RefreshCw
} from 'lucide-react'
import { videosApi, clipsApi, socialApi } from '../api/client'
import toast from 'react-hot-toast'

interface Video {
  id: number
  filename: string
  duration: number
  file_size: number
  status: string
  processing_progress: number
  title: string
  description: string
  tags: string[]
  created_at: string
}

interface Clip {
  id: number
  filename: string
  start_time: number
  end_time: number
  duration: number
  score: number
  caption: string
  hashtags: string[]
  status: string
}

export default function VideoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [video, setVideo] = useState<Video | null>(null)
  const [clips, setClips] = useState<Clip[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedClip, setSelectedClip] = useState<Clip | null>(null)
  const [postingClip, setPostingClip] = useState<number | null>(null)
  
  useEffect(() => {
    loadVideo()
    const interval = setInterval(loadVideo, 5000) // Poll for updates
    return () => clearInterval(interval)
  }, [id])
  
  const loadVideo = async () => {
    try {
      const videoData = await videosApi.get(Number(id))
      setVideo(videoData)
      
      if (videoData.status === 'completed') {
        const clipsData = await videosApi.getClips(Number(id))
        setClips(clipsData)
      }
    } catch (error) {
      toast.error('Failed to load video')
      navigate('/')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this video?')) return
    
    try {
      await videosApi.delete(Number(id))
      toast.success('Video deleted')
      navigate('/')
    } catch (error) {
      toast.error('Failed to delete video')
    }
  }
  
  const handleReprocess = async () => {
    try {
      await videosApi.process(Number(id), {
        max_clips: 5,
        min_clip_duration: 15,
        max_clip_duration: 60
      })
      toast.success('Reprocessing started')
      loadVideo()
    } catch (error) {
      toast.error('Failed to reprocess video')
    }
  }
  
  const handlePostClip = async (clip: Clip, platforms: string[]) => {
    setPostingClip(clip.id)
    try {
      const result = await socialApi.post({
        clip_id: clip.id,
        platforms,
        caption: clip.caption,
        hashtags: clip.hashtags
      })
      
      const successes = result.filter((r: any) => r.status === 'posted')
      const failures = result.filter((r: any) => r.status === 'failed')
      
      if (successes.length > 0) {
        toast.success(`Posted to ${successes.map((r: any) => r.platform).join(', ')}`)
      }
      if (failures.length > 0) {
        toast.error(`Failed: ${failures.map((r: any) => r.platform).join(', ')}`)
      }
    } catch (error) {
      toast.error('Failed to post clip')
    } finally {
      setPostingClip(null)
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }
  
  if (!video) return null
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </button>
        
        <div className="flex items-center gap-2">
          <button
            onClick={handleReprocess}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Reprocess
          </button>
          <button
            onClick={handleDelete}
            className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      </div>
      
      {/* Video Info */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-start gap-4">
          <div className="w-20 h-20 bg-slate-700 rounded-xl flex items-center justify-center">
            <Film className="w-8 h-8 text-slate-400" />
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">{video.title || video.filename}</h1>
            <p className="text-slate-400 text-sm mt-1">{video.filename}</p>
            <div className="flex items-center gap-4 mt-3 text-sm text-slate-400">
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {video.duration ? `${Math.floor(video.duration / 60)}:${Math.floor(video.duration % 60).toString().padStart(2, '0')}` : 'N/A'}
              </span>
              <span>
                {video.file_size ? `${(video.file_size / (1024 * 1024)).toFixed(1)} MB` : 'N/A'}
              </span>
            </div>
          </div>
          
          {/* Status */}
          <div className="flex items-center gap-2">
            {video.status === 'completed' && (
              <>
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span className="text-green-400 font-medium">Completed</span>
              </>
            )}
            {video.status === 'processing' && (
              <>
                <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />
                <span className="text-yellow-400 font-medium">
                  Processing {video.processing_progress}%
                </span>
              </>
            )}
            {video.status === 'failed' && (
              <>
                <AlertCircle className="w-5 h-5 text-red-400" />
                <span className="text-red-400 font-medium">Failed</span>
              </>
            )}
            {video.status === 'uploaded' && (
              <span className="text-slate-400 font-medium">Ready to process</span>
            )}
          </div>
        </div>
        
        {/* Progress bar */}
        {video.status === 'processing' && (
          <div className="mt-4">
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div 
                className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${video.processing_progress}%` }}
              />
            </div>
          </div>
        )}
      </div>
      
      {/* Clips */}
      {clips.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">
            Generated Clips ({clips.length})
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {clips.map((clip) => (
              <div key={clip.id} className="glass rounded-xl p-4">
                <div className="flex items-start gap-4">
                  <div className="w-24 h-16 bg-slate-700 rounded-lg flex items-center justify-center relative">
                    <Play className="w-6 h-6 text-slate-400" />
                    <span className="absolute -top-2 -right-2 bg-primary-500 text-white text-xs px-2 py-0.5 rounded-full font-medium">
                      {Math.round(clip.score)}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white line-clamp-2 mb-2">
                      {clip.caption}
                    </p>
                    <div className="flex items-center gap-2 text-xs text-slate-400">
                      <span>{clip.duration.toFixed(1)}s</span>
                      <span>•</span>
                      <span>{clip.start_time.toFixed(1)}s - {clip.end_time.toFixed(1)}s</span>
                    </div>
                    
                    {/* Hashtags */}
                    <div className="flex flex-wrap gap-1 mt-2">
                      {clip.hashtags.slice(0, 5).map((tag, i) => (
                        <span key={i} className="text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-700">
                  <a
                    href={`/api/clips/${clip.id}/download`}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg transition-colors"
                  >
                    <Play className="w-4 h-4" />
                    Download
                  </a>
                  <button
                    onClick={() => setSelectedClip(clip)}
                    disabled={postingClip === clip.id}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary-500 hover:bg-primary-600 text-white text-sm rounded-lg transition-colors disabled:opacity-50"
                  >
                    {postingClip === clip.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Share2 className="w-4 h-4" />
                    )}
                    Post
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {video.status === 'completed' && clips.length === 0 && (
        <div className="glass rounded-xl p-8 text-center">
          <Film className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400">No clips generated</p>
          <button
            onClick={handleReprocess}
            className="mt-4 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
      
      {/* Post Modal */}
      {selectedClip && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="glass rounded-2xl p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-white mb-4">Post Clip</h3>
            
            <p className="text-sm text-slate-400 mb-4">
              Select platforms to post this clip:
            </p>
            
            <div className="space-y-2 mb-6">
              {['twitter', 'youtube', 'tiktok'].map((platform) => (
                <button
                  key={platform}
                  onClick={() => handlePostClip(selectedClip, [platform])}
                  className="w-full flex items-center gap-3 p-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                >
                  <span className="text-2xl">
                    {platform === 'twitter' && '𝕏'}
                    {platform === 'youtube' && '📺'}
                    {platform === 'tiktok' && '🎵'}
                  </span>
                  <span className="text-white capitalize">{platform}</span>
                </button>
              ))}
            </div>
            
            <button
              onClick={() => setSelectedClip(null)}
              className="w-full px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
