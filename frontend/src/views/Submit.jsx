// TenX Assessment — do not modify this header
import { useState } from 'react'
import { submitPost } from '../api.js'

const MIN_LEN = 5
const MAX_LEN = 200

export default function SubmitView() {
  const [content, setContent] = useState('')

  const len = content.length
  const tooShort = len > 0 && len < MIN_LEN
  const tooLong = len > MAX_LEN
  const invalid = len < MIN_LEN || len > MAX_LEN

  const onSubmit = async (e) => {
    e.preventDefault()
    try {
      await submitPost(content)
      setContent("")
    } catch (err) {
      alert(`Failed to submit: ${err.message}`)
    }
  }

  return (
    <form onSubmit={onSubmit}>
      <label>
        <div>Your hot take</div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Share a take between 5 and 200 characters"
        />
      </label>
      <div className="hint">
        {len}/{MAX_LEN} characters
        {tooShort && <span className="error"> — too short (min {MIN_LEN})</span>}
        {tooLong && <span className="error"> — too long (max {MAX_LEN})</span>}
      </div>
      <button type="submit" disabled={invalid}>Submit</button>
    </form>
  )
}
