// TenX Assessment — do not modify this header
import { useEffect, useState } from 'react'
import { fetchLeaderboard } from '../api.js'

const TABS = [
  { mode: 'recent', label: 'New', subtitle: 'Sorted by submission time' },
  { mode: 'best', label: 'Top-rated', subtitle: 'Highest win rate with confidence' },
  { mode: 'hot', label: 'Trending', subtitle: 'Recent engagement × win rate' },
  { mode: 'controversial', label: 'Divisive', subtitle: 'Close win/loss splits with high vote volume' },
]

export default function LeaderboardView() {
  const [activeSort, setActiveSort] = useState('best')
  const [entries, setEntries] = useState([])

  useEffect(() => {
    // region: leaderboard-sync
    const load = async () => {
      try {
        const data = await fetchLeaderboard(activeSort)
        setEntries(data)
      } catch (err) {
        console.error("Failed to load leaderboard:", err)
      }
    }
    load()
    // endregion: leaderboard-sync
  }, [activeSort])

  const active = TABS.find((t) => t.mode === activeSort)

  return (
    <div className="leaderboard">
      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.mode}
            className={t.mode === activeSort ? 'active' : ''}
            onClick={() => setActiveSort(t.mode)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      {active && <p className="subtitle">{active.subtitle}</p>}
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Content</th>
            <th>Wins</th>
            <th>Losses</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.id}>
              <td>{e.rank}</td>
              <td>{e.content}</td>
              <td>{e.wins}</td>
              <td>{e.losses}</td>
              <td>{e.score.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
