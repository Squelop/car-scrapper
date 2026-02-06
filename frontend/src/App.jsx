import { useState, useEffect } from 'react'
import { Car, BarChart3, Search } from 'lucide-react'
import ListingsTable from './components/ListingsTable'
import Charts from './components/Charts'

function App() {
    const [listings, setListings] = useState([])
    const [loading, setLoading] = useState(false)
    const [searchUrl, setSearchUrl] = useState("")

    const fetchListings = async () => {
        try {
            setLoading(true)

            // Try static data first (for GitHub Pages deployment)
            try {
                const staticRes = await fetch('/data/listings.json')
                if (staticRes.ok) {
                    const data = await staticRes.json()
                    setListings(data)
                    console.log('Loaded data from static file')
                    return
                }
            } catch (staticError) {
                console.log('Static data not available, trying API...')
            }

            // Fallback to API (for local development)
            const res = await fetch('/api/listings')
            const data = await res.json()
            setListings(data)
        } catch (error) {
            console.error("Failed to fetch listings:", error)
        } finally {
            setLoading(false)
        }
    }


    const handleScrape = async (e) => {
        e.preventDefault()
        if (!searchUrl) return;
        try {
            await fetch(`/api/scrape?search_url=${encodeURIComponent(searchUrl)}`, {
                method: 'POST'
            })
            alert("Scraping started! Check back in a few moments.")
        } catch (error) {
            console.error("Scrape failed:", error)
        }
    }

    useEffect(() => {
        fetchListings()
        const interval = setInterval(fetchListings, 10000) // Poll every 10s
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="min-h-screen bg-slate-50 text-slate-900">
            <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm">
                <div className="flex items-center gap-2">
                    <div className="bg-blue-600 p-2 rounded-lg text-white">
                        <Car size={24} />
                    </div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                        Car Market Insights
                    </h1>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-sm text-slate-500">
                        Total Listings: <span className="font-bold text-slate-900">{listings.length}</span>
                    </div>
                </div>
            </header>

            <main className="p-6 max-w-7xl mx-auto space-y-6">

                {/* Scrape Controls */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Search size={20} className="text-blue-500" />
                        New Search
                    </h2>
                    <form onSubmit={handleScrape} className="flex gap-4">
                        <input
                            type="text"
                            placeholder="Paste Otomoto search URL here..."
                            className="flex-1 border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            value={searchUrl}
                            onChange={(e) => setSearchUrl(e.target.value)}
                        />
                        <button
                            type="submit"
                            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                        >
                            Start Scraping
                        </button>
                    </form>
                </div>

                {/* Charts Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <Charts listings={listings} />
                </div>

                {/* Data Table */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                    <div className="p-6 border-b border-slate-100">
                        <h2 className="text-lg font-semibold">Recent Listings</h2>
                    </div>
                    <ListingsTable listings={listings} />
                </div>

            </main>
        </div>
    )
}

export default App
