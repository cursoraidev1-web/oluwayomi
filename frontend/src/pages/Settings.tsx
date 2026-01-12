import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { 
  Settings as SettingsIcon,
  Link2,
  Unlink,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Loader2,
  Zap
} from 'lucide-react'
import { socialApi } from '../api/client'
import toast from 'react-hot-toast'

interface SocialAccount {
  id: number
  platform: string
  username: string
  is_active: boolean
  created_at: string
}

export default function Settings() {
  const [searchParams] = useSearchParams()
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [connecting, setConnecting] = useState<string | null>(null)
  
  useEffect(() => {
    // Check for OAuth callback messages
    const connected = searchParams.get('connected')
    const error = searchParams.get('error')
    
    if (connected) {
      toast.success(`${connected} account connected!`)
    }
    if (error) {
      toast.error(`Connection failed: ${error}`)
    }
    
    loadAccounts()
  }, [searchParams])
  
  const loadAccounts = async () => {
    try {
      const data = await socialApi.getAccounts()
      setAccounts(data)
    } catch (error) {
      toast.error('Failed to load accounts')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleConnect = async (platform: string) => {
    setConnecting(platform)
    try {
      let authUrl: string
      
      switch (platform) {
        case 'twitter':
          const twitterRes = await socialApi.connectTwitter()
          authUrl = twitterRes.auth_url
          break
        case 'youtube':
          const youtubeRes = await socialApi.connectYouTube()
          authUrl = youtubeRes.auth_url
          break
        case 'tiktok':
          const tiktokRes = await socialApi.connectTikTok()
          authUrl = tiktokRes.auth_url
          break
        default:
          return
      }
      
      // Redirect to OAuth
      window.location.href = authUrl
    } catch (error) {
      toast.error(`Failed to connect ${platform}`)
      setConnecting(null)
    }
  }
  
  const handleDisconnect = async (accountId: number, platform: string) => {
    if (!window.confirm(`Disconnect your ${platform} account?`)) return
    
    try {
      await socialApi.disconnect(accountId)
      setAccounts(prev => prev.filter(a => a.id !== accountId))
      toast.success(`${platform} disconnected`)
    } catch (error) {
      toast.error('Failed to disconnect account')
    }
  }
  
  const platforms = [
    {
      id: 'twitter',
      name: 'Twitter / X',
      icon: '𝕏',
      color: 'from-slate-700 to-slate-600',
      description: 'Post video tweets to your timeline'
    },
    {
      id: 'youtube',
      name: 'YouTube Shorts',
      icon: '📺',
      color: 'from-red-600 to-red-500',
      description: 'Upload Shorts to your channel'
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: '🎵',
      color: 'from-pink-600 to-purple-600',
      description: 'Post videos to your TikTok profile'
    }
  ]
  
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-slate-400 mt-1">Connect your social media accounts</p>
      </div>
      
      {/* Connected Accounts */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white">Social Media Accounts</h2>
        
        {platforms.map((platform) => {
          const connected = accounts.find(a => a.platform === platform.id)
          
          return (
            <div key={platform.id} className="glass rounded-xl p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${platform.color} flex items-center justify-center`}>
                    <span className="text-2xl">{platform.icon}</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-white">{platform.name}</h3>
                    <p className="text-sm text-slate-400">{platform.description}</p>
                    {connected && (
                      <div className="flex items-center gap-1 mt-1">
                        <CheckCircle className="w-3 h-3 text-green-400" />
                        <span className="text-xs text-green-400">
                          Connected as @{connected.username}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div>
                  {connected ? (
                    <button
                      onClick={() => handleDisconnect(connected.id, platform.name)}
                      className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                    >
                      <Unlink className="w-4 h-4" />
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={() => handleConnect(platform.id)}
                      disabled={connecting === platform.id}
                      className="flex items-center gap-2 px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      {connecting === platform.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Link2 className="w-4 h-4" />
                      )}
                      Connect
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
      
      {/* Setup Instructions */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Setup Instructions</h2>
        
        <div className="space-y-4 text-sm text-slate-300">
          <div>
            <h3 className="font-medium text-white mb-2">Twitter / X</h3>
            <ol className="list-decimal list-inside space-y-1 text-slate-400">
              <li>Go to <a href="https://developer.twitter.com" target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:underline">developer.twitter.com</a></li>
              <li>Create a project and app</li>
              <li>Enable OAuth 2.0 with PKCE</li>
              <li>Add your callback URL</li>
              <li>Copy Client ID and Secret to .env</li>
            </ol>
          </div>
          
          <div>
            <h3 className="font-medium text-white mb-2">YouTube</h3>
            <ol className="list-decimal list-inside space-y-1 text-slate-400">
              <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:underline">Google Cloud Console</a></li>
              <li>Create a project</li>
              <li>Enable YouTube Data API v3</li>
              <li>Create OAuth 2.0 credentials</li>
              <li>Add redirect URI and copy credentials</li>
            </ol>
          </div>
          
          <div>
            <h3 className="font-medium text-white mb-2">TikTok</h3>
            <ol className="list-decimal list-inside space-y-1 text-slate-400">
              <li>Go to <a href="https://developers.tiktok.com" target="_blank" rel="noopener noreferrer" className="text-primary-400 hover:underline">TikTok Developer Portal</a></li>
              <li>Create a developer account</li>
              <li>Create an app</li>
              <li>Apply for Content Posting API access</li>
              <li>Add callback URL and get credentials</li>
            </ol>
          </div>
        </div>
      </div>
      
      {/* No Maintenance Banner */}
      <div className="rounded-xl p-6 bg-gradient-to-r from-primary-500/20 to-purple-500/20 border border-primary-500/30">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center flex-shrink-0">
            <Zap className="w-5 h-5 text-primary-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">No Maintenance Required</h3>
            <p className="text-slate-300 text-sm mt-1">
              ClipForge is designed to be completely maintenance-free:
            </p>
            <ul className="text-sm text-slate-400 mt-2 space-y-1">
              <li>• <strong className="text-slate-300">No subscriptions</strong> - All tools are free and open-source</li>
              <li>• <strong className="text-slate-300">Self-hosted</strong> - Your data stays on your server</li>
              <li>• <strong className="text-slate-300">SQLite database</strong> - No external database to maintain</li>
              <li>• <strong className="text-slate-300">Local processing</strong> - FFmpeg handles all video work</li>
              <li>• <strong className="text-slate-300">Free APIs</strong> - Social media APIs have free tiers</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
