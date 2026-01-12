import { useEffect, useState } from 'react'
import { 
  Film, 
  Play,
  Share2,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  Loader2,
  Edit3,
  Check,
  X
} from 'lucide-react'
import { clipsApi, socialApi } from '../api/client'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

interface Clip {
  id: number
  video_id: number
  filename: string
  start_time: number
  end_time: number
  duration: number
  score: number
  caption: string
  hashtags: string[]
  status: string
  created_at: string
}

export default function Clips() {
  const [clips, setClips] = useState<Clip[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'score' | 'date'>('score')
  const [editingClip, setEditingClip] = useState<number | null>(null)
  const [editCaption, setEditCaption] = useState('')
  const [postingClip, setPostingClip] = useState<number | null>(null)
  
  useEffect(() => {
    loadClips()
  }, [])
  
  const loadClips = async () => {
    try {
      const data = await clipsApi.list()
      setClips(data)
    } catch (error) {
      toast.error('Failed to load clips')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleDelete = async (clipId: number) => {
    if (!window.confirm('Delete this clip?')) return
    
    try {
      await clipsApi.delete(clipId)
      setClips(prev => prev.filter(c => c.id !== clipId))
      toast.success('Clip deleted')
    } catch (error) {
      toast.error('Failed to delete clip')
    }
  }
  
  const handleUpdateCaption = async (clipId: number) => {
    try {
      const updated = await clipsApi.update(clipId, { caption: editCaption })
      setClips(prev => prev.map(c => c.id === clipId ? { ...c, caption: updated.caption } : c))
      setEditingClip(null)
      toast.success('Caption updated')
    } catch (error) {
      toast.error('Failed to update caption')
    }
  }
  
  const handleRegenerateContent = async (clipId: number) => {
    try {
      const updated = await clipsApi.regenerateContent(clipId, {})
      setClips(prev => prev.map(c => c.id === clipId ? { ...c, caption: updated.caption, hashtags: updated.hashtags } : c))
      toast.success('Content regenerated')
    } catch (error) {
      toast.error('Failed to regenerate content')
    }
  }
  
  const handlePost = async (clip: Clip, platform: string) => {
    setPostingClip(clip.id)
    try {
      const result = await socialApi.post({
        clip_id: clip.id,
        platforms: [platform],
        caption: clip.caption,
        hashtags: clip.hashtags
      })
      
      if (result[0]?.status === 'posted') {
        toast.success(`Posted to ${platform}!`)
      } else {
        toast.error(result[0]?.error_message || `Failed to post to ${platform}`)
      }
    } catch (error) {
      toast.error('Failed to post clip')
    } finally {
      setPostingClip(null)
    }
  }
  
  // Filter and sort clips
  const filteredClips = clips
    .filter(clip => 
      clip.caption?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      clip.hashtags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    )
    .sort((a, b) => {
      if (sortBy === 'score') return (b.score || 0) - (a.score || 0)
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Clips</h1>
          <p className="text-slate-400 mt-1">{clips.length} clips generated</p>
        </div>
      </div>
      
      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search clips..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-11 pr-4 py-2.5 text-white placeholder-slate-400 focus:outline-none focus:border-primary-500"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-slate-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'score' | 'date')}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-primary-500"
          >
            <option value="score">Sort by Score</option>
            <option value="date">Sort by Date</option>
          </select>
        </div>
      </div>
      
      {/* Clips Grid */}
      {filteredClips.length === 0 ? (
        <div className="glass rounded-xl p-12 text-center">
          <Film className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <p className="text-xl font-medium text-white mb-2">No clips found</p>
          <p className="text-slate-400">
            {clips.length === 0 
              ? 'Upload and process a video to generate clips'
              : 'Try a different search term'
            }
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredClips.map((clip) => (
            <div key={clip.id} className="glass rounded-xl overflow-hidden">
              {/* Video Preview */}
              <div className="relative aspect-video bg-slate-800">
                <video
                  src={`/api/clips/${clip.id}/download`}
                  className="w-full h-full object-cover"
                  controls
                />
                <div className="absolute top-2 right-2 bg-primary-500 text-white text-sm px-2 py-1 rounded-lg font-medium">
                  Score: {Math.round(clip.score || 0)}
                </div>
              </div>
              
              {/* Content */}
              <div className="p-4">
                {/* Caption */}
                {editingClip === clip.id ? (
                  <div className="space-y-2">
                    <textarea
                      value={editCaption}
                      onChange={(e) => setEditCaption(e.target.value)}
                      className="w-full bg-slate-700 border border-slate-600 rounded-lg p-3 text-white text-sm resize-none focus:outline-none focus:border-primary-500"
                      rows={3}
                    />
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleUpdateCaption(clip.id)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white text-sm rounded-lg transition-colors"
                      >
                        <Check className="w-4 h-4" />
                        Save
                      </button>
                      <button
                        onClick={() => setEditingClip(null)}
                        className="flex items-center gap-1 px-3 py-1.5 bg-slate-600 hover:bg-slate-500 text-white text-sm rounded-lg transition-colors"
                      >
                        <X className="w-4 h-4" />
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="group relative">
                    <p className="text-sm text-white line-clamp-2">
                      {clip.caption}
                    </p>
                    <button
                      onClick={() => {
                        setEditingClip(clip.id)
                        setEditCaption(clip.caption)
                      }}
                      className="absolute -top-1 -right-1 p-1.5 bg-slate-700 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <Edit3 className="w-3 h-3 text-slate-400" />
                    </button>
                  </div>
                )}
                
                {/* Hashtags */}
                <div className="flex flex-wrap gap-1 mt-3">
                  {clip.hashtags.slice(0, 6).map((tag, i) => (
                    <span key={i} className="text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded">
                      #{tag}
                    </span>
                  ))}
                  {clip.hashtags.length > 6 && (
                    <span className="text-xs text-slate-400">+{clip.hashtags.length - 6}</span>
                  )}
                </div>
                
                {/* Meta */}
                <div className="flex items-center gap-3 mt-3 text-xs text-slate-400">
                  <span>{clip.duration.toFixed(1)}s</span>
                  <span>•</span>
                  <span>{format(new Date(clip.created_at), 'MMM d, yyyy')}</span>
                </div>
                
                {/* Actions */}
                <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-700">
                  <button
                    onClick={() => handleRegenerateContent(clip.id)}
                    className="flex items-center gap-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg transition-colors"
                    title="Regenerate caption & hashtags"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  
                  <div className="flex-1 flex items-center gap-1">
                    {['twitter', 'youtube', 'tiktok'].map((platform) => (
                      <button
                        key={platform}
                        onClick={() => handlePost(clip, platform)}
                        disabled={postingClip === clip.id}
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-2 bg-primary-500/20 hover:bg-primary-500/30 text-primary-400 text-sm rounded-lg transition-colors disabled:opacity-50"
                        title={`Post to ${platform}`}
                      >
                        {postingClip === clip.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <>
                            {platform === 'twitter' && '𝕏'}
                            {platform === 'youtube' && '📺'}
                            {platform === 'tiktok' && '🎵'}
                          </>
                        )}
                      </button>
                    ))}
                  </div>
                  
                  <a
                    href={`/api/clips/${clip.id}/download`}
                    download
                    className="flex items-center gap-1 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg transition-colors"
                    title="Download"
                  >
                    <Play className="w-4 h-4" />
                  </a>
                  
                  <button
                    onClick={() => handleDelete(clip.id)}
                    className="flex items-center gap-1 px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 text-sm rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
