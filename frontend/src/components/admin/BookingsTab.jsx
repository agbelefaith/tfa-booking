import { useEffect, useState } from "react";
import { cancelBooking, getBookings, markCompleted, markNoShow } from "../../adminApi.js";
import { euros, timeOfDay } from "../../format.js";

const toKey = (date) => date.toLocaleDateString("en-CA");

// The Monday of the week `date` is in
function mondayOf(date) {
  const monday = new Date(date);
  monday.setHours(0, 0, 0, 0);
  monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
  return monday;
}

const addDays = (date, days) => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
};

const STATUS_LABELS = {
  pending: "Awaiting deposit",
  confirmed: "Confirmed",
  completed: "Completed",
  no_show: "No-show",
  cancelled: "Cancelled by client",
  business_cancelled: "Cancelled by you (refunded)",
};

export default function BookingsTab() {
  const [weekStart, setWeekStart] = useState(mondayOf(new Date()));
  const [bookings, setBookings] = useState([]);
  const [error, setError] = useState("");

  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  function load() {
    getBookings(toKey(weekStart), toKey(addDays(weekStart, 7)))
      .then(setBookings)
      .catch((e) => setError(e.message));
  }
  useEffect(load, [weekStart]);

  async function act(action, booking, question) {
    if (question && !window.confirm(question)) return;
    setError("");
    try {
      await action(booking.id);
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  const weekLabel = `${days[0].toLocaleDateString("en-IE", { day: "numeric", month: "short" })} – ${days[6].toLocaleDateString("en-IE", { day: "numeric", month: "short" })}`;

  return (
    <section>
      <div className="week-nav">
        <button className="nav" onClick={() => setWeekStart(addDays(weekStart, -7))} aria-label="Previous week">‹</button>
        <span>{weekLabel}</span>
        <button className="nav" onClick={() => setWeekStart(addDays(weekStart, 7))} aria-label="Next week">›</button>
        <button className="link" onClick={() => setWeekStart(mondayOf(new Date()))}>This week</button>
      </div>

      {error && <p className="error">{error}</p>}

      {days.map((day) => {
        const dayBookings = bookings.filter((b) => toKey(new Date(b.starts_at)) === toKey(day));
        return (
          <div key={toKey(day)} className="agenda-day">
            <h3>{day.toLocaleDateString("en-IE", { weekday: "long", day: "numeric", month: "short" })}</h3>
            {dayBookings.length === 0 && <p className="muted">No bookings</p>}
            {dayBookings.map((b) => {
              const started = new Date(b.starts_at) <= new Date();
              const active = b.status === "pending" || b.status === "confirmed";
              return (
                <article key={b.id} className={`booking ${active ? "" : "faded"}`}>
                  <div className="booking-time">
                    {timeOfDay(b.starts_at)}
                    <small>{timeOfDay(b.ends_at)}</small>
                  </div>
                  <div className="booking-info">
                    <strong>{b.customer_name}</strong>
                    <span>{b.service_name}{b.add_on_names.map((n) => ` + ${n}`).join("")}</span>
                    <span className="muted">
                      <a href={`tel:${b.customer_phone}`}>{b.customer_phone}</a> ·{" "}
                      <a href={`mailto:${b.customer_email}`}>{b.customer_email}</a>
                    </span>
                    <span className="muted">Total {euros(b.total_cents)} · deposit {euros(b.deposit_cents)}</span>
                  </div>
                  <div className="booking-side">
                    <span className={`badge ${b.status}`}>{STATUS_LABELS[b.status] || b.status}</span>
                    {b.status === "confirmed" && started && (
                      <>
                        <button className="chip" onClick={() => act(markCompleted, b)}>Done ✓</button>
                        <button className="chip" onClick={() => act(markNoShow, b, `Mark ${b.customer_name} as a no-show? You keep the deposit.`)}>No-show</button>
                      </>
                    )}
                    {active && !started && (
                      <button
                        className="chip danger"
                        onClick={() =>
                          act(
                            cancelBooking,
                            b,
                            b.status === "confirmed"
                              ? `Cancel ${b.customer_name}'s booking? Their deposit will be refunded.`
                              : `Cancel ${b.customer_name}'s unpaid booking?`
                          )
                        }
                      >
                        {b.status === "confirmed" ? "Cancel + refund" : "Cancel"}
                      </button>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        );
      })}
    </section>
  );
}
