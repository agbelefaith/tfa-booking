import { useEffect, useState } from "react";
import { addTimeOff, getTimeOff, removeTimeOff } from "../../adminApi.js";

const niceDay = (iso) =>
  new Date(iso).toLocaleDateString("en-IE", { weekday: "short", day: "numeric", month: "short", year: "numeric", timeZone: "Europe/Dublin" });

// ends_at is midnight AFTER the last day, so step back a minute to show the last day itself
const lastDayOf = (iso) => new Date(new Date(iso).getTime() - 60_000).toISOString();

export default function TimeOffTab() {
  const [list, setList] = useState([]);
  const [form, setForm] = useState({ first_day: "", last_day: "", reason: "" });
  const [error, setError] = useState("");

  const load = () => getTimeOff().then(setList).catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  async function handleAdd(event) {
    event.preventDefault();
    setError("");
    try {
      await addTimeOff({ ...form, reason: form.reason || null });
      setForm({ first_day: "", last_day: "", reason: "" });
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleRemove(id) {
    if (!window.confirm("Remove this time off? Clients will be able to book these days again.")) return;
    await removeTimeOff(id).catch((e) => setError(e.message));
    load();
  }

  return (
    <section className="card">
      <h2>Time off</h2>
      <p className="muted">Holidays and days off. Clients can't book these days.</p>

      <form className="time-off-form" onSubmit={handleAdd}>
        <label>
          First day
          <input type="date" value={form.first_day} onChange={(e) => setForm({ ...form, first_day: e.target.value, last_day: form.last_day || e.target.value })} required />
        </label>
        <label>
          Last day
          <input type="date" value={form.last_day} min={form.first_day} onChange={(e) => setForm({ ...form, last_day: e.target.value })} required />
        </label>
        <label>
          Reason (optional)
          <input type="text" value={form.reason} maxLength={200} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
        </label>
        <button className="button" type="submit">Add time off</button>
      </form>

      {error && <p className="error">{error}</p>}

      <div className="time-off-list">
        {list.length === 0 && <p className="muted">No time off booked.</p>}
        {list.map((t) => (
          <div key={t.id} className="time-off-item">
            <span>
              {niceDay(t.starts_at)} → {niceDay(lastDayOf(t.ends_at))}
              {t.reason && <span className="muted"> · {t.reason}</span>}
            </span>
            <button className="link" onClick={() => handleRemove(t.id)}>Remove</button>
          </div>
        ))}
      </div>
    </section>
  );
}
