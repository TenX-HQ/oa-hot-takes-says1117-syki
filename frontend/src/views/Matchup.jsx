// TenX Assessment — do not modify this header
import { useState, useEffect } from 'react'
import { fetchMatchup, submitVote } from '../api.js'

export default function MatchupView() {
  const [voting, setVoting] = useState(false)
  const [matchup, setMatchup] = useState(null)

  const loadMatchup = async () => {
    try {
      const data = await fetchMatchup()
      setMatchup(data)
    } catch (err) {
      console.error("Failed to load matchup:", err)
    }
  }

  useEffect(() => {
    loadMatchup()
  }, [])

  const onVote = async (winnerId, loserId) => {
    // region: vote-handler
    setVoting(true)
    try {
      await submitVote(winnerId, loserId)
      await loadMatchup()
    } catch (err) {
      alert(`Vote failed: ${err.message}`)
    } finally {
      setVoting(false)
    }
    // endregion: vote-handler
  }

  if (!matchup) return <div>Loading...</div>

  return (
    <div className="matchup">
      <div className="card">
        <p>{matchup.post_a.content}</p>
        <button disabled={voting} onClick={() => onVote(matchup.post_a.id, matchup.post_b.id)}>Pick this one</button>
      </div>
      <div className="card">
        <p>{matchup.post_b.content}</p>
        <button disabled={voting} onClick={() => onVote(matchup.post_b.id, matchup.post_a.id)}>Pick this one</button>
      </div>
    </div>
  )
}
