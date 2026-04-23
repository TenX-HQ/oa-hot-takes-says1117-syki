// TenX Assessment — do not modify this header
import { useState } from 'react'
import MatchupView from './views/Matchup.jsx'
import SubmitView from './views/Submit.jsx'
import LeaderboardView from './views/Leaderboard.jsx'

export default function App() {
  const [tab, setTab] = useState('matchup')

  return (
    <div className="container">
      <h1>Hot Takes Tournament</h1>
      <nav>
        <button className={tab === 'matchup' ? 'active' : ''} onClick={() => setTab('matchup')}>Matchup</button>
        <button className={tab === 'submit' ? 'active' : ''} onClick={() => setTab('submit')}>Submit</button>
        <button className={tab === 'leaderboard' ? 'active' : ''} onClick={() => setTab('leaderboard')}>Leaderboard</button>
      </nav>
      {tab === 'matchup' && <MatchupView />}
      {tab === 'submit' && <SubmitView />}
      {tab === 'leaderboard' && <LeaderboardView />}
    </div>
  )
}
