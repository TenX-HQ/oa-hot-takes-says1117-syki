// TenX Assessment — do not modify this header
// Shared fetch helpers — mirror the backend HTTP contract. No React state
// or UI logic here; views consume these helpers directly.

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, opts = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function fetchPosts() {
  return request("/posts");
}

export async function submitPost(content) {
  return request("/posts", {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function fetchMatchup() {
  return request("/matchup");
}

export async function submitVote(winnerId, loserId) {
  return request("/matchup/vote", {
    method: "POST",
    body: JSON.stringify({ winner_id: winnerId, loser_id: loserId }),
  });
}

export async function fetchLeaderboard(sort = "best") {
  return request(`/leaderboard?sort=${sort}`);
}
