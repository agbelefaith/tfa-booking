import { useEffect, useState } from "react";
import { getOpeningHours, saveOpeningHours } from "../../adminApi.js";

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const short = (t) => t.slice(0, 5); // "10:00:00" -> "10:00"

export default function HoursTab() {
  // One list of time blocks per weekday, e.g. week[5] = [{opens_at: "10:00", closes_at: "18:00"}]
  const [week, setWeek] = useState(DAY_NAMES.map(() => []));
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getOpeningHours()
      .then((hours) => {
        const grouped = DAY_NAMES.map(() => []);
        hours.forEach((h) => grouped[h.day_of_week].push({ opens_at: short(h.opens_at), closes_at: short(h.closes_at) }));
        setWeek(grouped);
      })
      .catch((e) => setError(e.message));
  }, []);

  // Change one day's blocks, keeping the other days the same
  const updateDay = (dayIndex, blocks) => {
    setMessage("");
    setWeek(week.map((b, i) => (i === dayIndex ? blocks : b)));
  };

  async function handleSave() {
    setError("");
    const hours = week.flatMap((blocks, day_of_week) => blocks.map((b) => ({ day_of_week, ...b })));
    try {
      await saveOpeningHours(hours);
      setMessage("Saved ✓ Your booking page is updated.");
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section className="card">
      <h2>Opening hours</h2>
      <p className="muted">Add a second block to a day for a break (e.g. 10:00–13:00 and 14:00–18:00).</p>

      {DAY_NAMES.map((name, dayIndex) => {
        const blocks = week[dayIndex];
        return (
          <div key={name} className="hours-row">
            <label className="day-toggle">
              <input
                type="checkbox"
                checked={blocks.length > 0}
                onChange={(e) => updateDay(dayIndex, e.target.checked ? [{ opens_at: "10:00", closes_at: "18:00" }] : [])}
              />
              {name}
            </label>
            <div className="blocks">
              {blocks.length === 0 && <span className="muted">Closed</span>}
              {blocks.map((block, blockIndex) => (
                <div key={blockIndex} className="block">
                  <input
                    type="time"
                    value={block.opens_at}
                    onChange={(e) => updateDay(dayIndex, blocks.map((b, i) => (i === blockIndex ? { ...b, opens_at: e.target.value } : b)))}
                  />
                  <span>to</span>
                  <input
                    type="time"
                    value={block.closes_at}
                    onChange={(e) => updateDay(dayIndex, blocks.map((b, i) => (i === blockIndex ? { ...b, closes_at: e.target.value } : b)))}
                  />
                  <button className="link" onClick={() => updateDay(dayIndex, blocks.filter((_, i) => i !== blockIndex))} aria-label="Remove">✕</button>
                </div>
              ))}
              {blocks.length > 0 && (
                <button className="link" onClick={() => updateDay(dayIndex, [...blocks, { opens_at: "14:00", closes_at: "18:00" }])}>
                  + add block
                </button>
              )}
            </div>
          </div>
        );
      })}

      {error && <p className="error">{error}</p>}
      {message && <p className="success">{message}</p>}
      <button className="button" onClick={handleSave}>Save opening hours</button>
    </section>
  );
}
