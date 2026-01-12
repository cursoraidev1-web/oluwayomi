import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  Upload, 
  Film, 
  Share2, 
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  Play
} from 'lucide-react'
import { videosApi, clipsApi, socialApi } from '../api/client'
import { format } from 'date-fns'

interface Video {
  id: number
  filename: string
  duration: number
  status: string
  processing_progress: number
  created_at: string
}

interface Clip {
  id: number
  video_id: number
  filename: string
  duration: number
  score: number
  caption: string
  status: string
  created_at: string
}

interface Stats {
  totalVideos: number
  totalClips: number
  pendingPosts: number
  completedPosts: number
}

export default function Dashboard() {
  const [videos, setVideos] = useState<Video[]>([])
  const [clips, setClips] = useState<Clip[]>([])
  const [stats, setStats] = useState<Stats>({
    totalVideos: 0,
    totalClips: 0,
    pendingPosts: 0,
    completedPosts: 0
  })
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    try {
      const [videosData, clipsData, postsData] = await Promise.all([
        videosApi.list(),
        clipsApi.list(),
        socialApi.getPosts()
      ])
      
      setVideos(videosData)
      setClips(clipsData)
      
      setStats({
        totalVideos: videosData.length,
        totalClips: clipsData.length,
        pendingPosts: postsData.filter((p: any) => p.status === 'pending').length,
        completedPosts: postsData.filter((p: any) => p.status === 'posted').length
      })
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  const statCards = [
    { label: 'Total Videos', value: stats.totalVideos, icon: Film, color: 'from-blue-500 to-cyan-500' },
    { label: 'Generated Clips', value: stats.totalClips, icon: Play, color: 'from-purple-500 to-pink-500' },
    { label: 'Pending Posts', value: stats.pendingPosts, icon: Clock, color: 'from-yellow-500 to-orange-500' },
    { label: 'Posted', value: stats.completedPosts, icon: CheckCircle, color: 'from-green-500 to-emerald-500' },
  ]
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-400" />
      default:
        return <Clock className="w-4 h-4 text-slate-400" />
    }
  }
  
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-32 rounded-2xl shimmer" />
          ))}
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Overview of your video clips and posts</p>
        </div>
        <Link
          to="/upload"
          className="flex items-center gap-2 bg-gradient-to-r from-primary-500 to-purple-600 hover:from-primary-600 hover:to-purple-700 text-white font-medium py-2.5 px-5 rounded-xl transition-all duration-200"
        >
          <Upload className="w-4 h-4" />
          Upload Video
        </Link>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => (
          <div key={index} className="glass rounded-2xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">{stat.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Recent Videos & Clips */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Videos */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Recent Videos</h2>
            <Link to="/upload" className="text-sm text-primary-400 hover:text-primary-300">
              View all
            </Link>
          </div>
          
          {videos.length === 0 ? (
            <div className="text-center py-8">
              <Film className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No videos yet</p>
              <Link to="/upload" className="text-primary-400 text-sm hover:text-primary-300">
                Upload your first video
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {videos.slice(0, 5).map((video) => (
                <Link
                  key={video.id}
                  to={`/videos/${video.id}`}
                  className="flex items-center gap-4 p-3 rounded-xl hover:bg-slate-700/50 transition-colors"
                >
                  <div className="w-16 h-10 bg-slate-700 rounded-lg flex items-center justify-center">
                    <Film className="w-5 h-5 text-slate-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {video.filename}
                    </p>
                    <p className="text-xs text-slate-400">
                      {video.duration ? `${Math.floor(video.duration / 60)}:${Math.floor(video.duration % 60).toString().padStart(2, '0')}` : 'Processing...'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(video.status)}
                    {video.status === 'processing' && (
                      <span className="text-xs text-yellow-400">{video.processing_progress}%</span>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
        
        {/* Top Clips */}
        <div className="glass rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Top Clips</h2>
            <Link to="/clips" className="text-sm text-primary-400 hover:text-primary-300">
              View all
            </Link>
          </div>
          
          {clips.length === 0 ? (
            <div className="text-center py-8">
              <Play className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No clips generated yet</p>
              <p className="text-slate-500 text-sm">Process a video to create clips</p>
            </div>
          ) : (
            <div className="space-y-3">
              {clips
                .sort((a, b) => (b.score || 0) - (a.score || 0))
                .slice(0, 5)
                .map((clip) => (
                  <div
                    key={clip.id}
                    className="flex items-center gap-4 p-3 rounded-xl hover:bg-slate-700/50 transition-colors"
                  >
                    <div className="w-16 h-10 bg-slate-700 rounded-lg flex items-center justify-center relative">
                      <Play className="w-5 h-5 text-slate-400" />
                      <span className="absolute -top-1 -right-1 bg-primary-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                        {Math.round(clip.score || 0)}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">
                        {clip.caption?.slice(0, 50) || clip.filename}
                      </p>
                      <p className="text-xs text-slate-400">
                        {clip.duration?.toFixed(1)}s • {format(new Date(clip.created_at), 'MMM d')}
                      </p>
                    </div>
                    <Share2 className="w-4 h-4 text-slate-400" />
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Quick Actions */}
      <div className="glass rounded-2xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/upload"
            className="flex items-center gap-4 p-4 rounded-xl bg-slate-700/50 hover:bg-slate-700 transition-colors"
          >
            <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
              <Upload className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <p className="font-medium text-white">Upload Video</p>
              <p className="text-xs text-slate-400">Add a new video to process</p>
            </div>
          </Link>
          
          <Link
            to="/clips"
            className="flex items-center gap-4 p-4 rounded-xl bg-slate-700/50 hover:bg-slate-700 transition-colors"
          >
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <Film className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <p className="font-medium text-white">View Clips</p>
              <p className="text-xs text-slate-400">Browse generated clips</p>
            </div>
          </Link>
          
          <Link
            to="/settings"
            className="flex items-center gap-4 p-4 rounded-xl bg-slate-700/50 hover:bg-slate-700 transition-colors"
          >
            <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
              <Share2 className="w-5 h-5 text-green-400" />
            </div>
            <div>
              <p className="font-medium text-white">Connect Accounts</p>
              <p className="text-xs text-slate-400">Link social media</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}
