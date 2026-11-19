import { useState } from "react";
import { checkKey, forgetKey, getSavedKey, saveKey } from "../../adminApi.js";
import BookingsTab from "./BookingsTab.jsx";
import HoursTab from "./HoursTab.jsx";
import TimeOffTab from "./TimeOffTab.jsx";

const TABS = { bookings: "Bookings", hours: "Opening hours", timeOff: "Time off" };

export default function AdminPage() {
  const [loggedIn, setLoggedIn] = useState(Boolean(getSavedKey()));
  const [tab, setTab] = useState("bookings");

  if (!loggedIn) return <Login onSuccess={() => setLoggedIn(true)} />;

  return (
    <main className="page wide">
      <header className="admin-header">
        <div>
          <p className="eyebrow">TFA</p>
          <h1 className="admin-title">Dashboard</h1>
        </div>
        <button
          className="link"
          onClick={() => {
            forgetKey();
            setLoggedIn(false);
          }}
        >
          Log out
        </button>
      </header>

      <nav className="tabs">
        {Object.entries(TABS).map(([id, label]) => (
          <button key={id} className={`tab ${tab === id ? "selected" : ""}`} onClick={() => setTab(id)}>
            {label}
          </button>
        ))}
      </nav>

      {tab === "bookings" && <BookingsTab />}
      {tab === "hours" && <HoursTab />}
      {tab === "timeOff" && <TimeOffTab />}
    </main>
  );
}

function Login({ onSuccess }) {
  const [key, setKey] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    saveKey(key);
    try {
      await checkKey();
      onSuccess();
    } catch {
      forgetKey();
      setError("That key isn't right.");
    }
  }

  return (
    <main className="page">
      <form className="card login" onSubmit={handleSubmit}>
        <p className="eyebrow">TFA</p>
        <h2>Dashboard login</h2>
        <label>
          Admin key
          <input type="password" value={key} onChange={(e) => setKey(e.target.value)} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="button" type="submit">Log in</button>
      </form>
    </main>
  );
}
