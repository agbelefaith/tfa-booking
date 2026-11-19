import { useEffect, useState } from "react";
import {
  createBooking,
  getAddOns,
  getAvailability,
  getBookingPolicy,
  getOpeningDays,
  getServices,
  startCheckout,
} from "../api.js";
import { euros, niceDate, timeOfDay } from "../format.js";
import Calendar from "./Calendar.jsx";
import { Header } from "./ResultPage.jsx";

export default function BookingPage() {
  // What we loaded from the API
  const [services, setServices] = useState([]);
  const [addOns, setAddOns] = useState([]);
  const [openWeekdays, setOpenWeekdays] = useState([]);
  const [depositSetting, setDepositSetting] = useState(0);
  const [slots, setSlots] = useState([]);

  // What the client has chosen
  const [serviceId, setServiceId] = useState(null);
  const [addOnIds, setAddOnIds] = useState([]);
  const [day, setDay] = useState(null);
  const [startsAt, setStartsAt] = useState(null);
  const [details, setDetails] = useState({ name: "", email: "", phone: "" });

  // Page status
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  // If booking worked but payment didn't start, remember it so "try again" doesn't book twice
  const [heldBookingId, setHeldBookingId] = useState(null);

  // 1. Load services and add-ons once, when the page opens.
  useEffect(() => {
    Promise.all([getServices(), getAddOns(), getOpeningDays(), getBookingPolicy()])
      .then(([s, a, open, policy]) => {
        setServices(s);
        setAddOns(a);
        setOpenWeekdays(open);
        setDepositSetting(policy.deposit_cents);
      })
      .catch(() => setError("Can't reach the booking system. Is the backend running?"));
  }, []);

  // 2. Whenever the service, add-ons or day change, load free times.
  useEffect(() => {
    if (!serviceId || !day) return;
    setLoadingSlots(true);
    setStartsAt(null);
    setHeldBookingId(null);
    getAvailability(day, serviceId, addOnIds)
      .then(setSlots)
      .catch((e) => setError(e.message))
      .finally(() => setLoadingSlots(false));
  }, [serviceId, addOnIds, day]);

  const service = services.find((s) => s.id === serviceId);
  // Plain sets can't have nail art, so only show the extras this treatment allows.
  const allowedAddOns = addOns.filter((a) => service?.allows_nail_art || !a.is_nail_art);
  const chosenAddOns = allowedAddOns.filter((a) => addOnIds.includes(a.id));
  const total = (service?.price_cents ?? 0) + chosenAddOns.reduce((sum, a) => sum + a.price_cents, 0);
  const minutes = (service?.duration_minutes ?? 0) + chosenAddOns.reduce((sum, a) => sum + a.extra_minutes, 0);
  // Same rule as the server: the set deposit, but never more than the total
  const deposit = Math.min(depositSetting, total);
  const canPay = service && startsAt && details.name && details.email && details.phone && !submitting;

  function pickService(s) {
    setServiceId(s.id);
    // Switching to a plain set drops any nail art already picked.
    if (!s.allows_nail_art) {
      setAddOnIds((ids) => ids.filter((id) => !addOns.find((a) => a.id === id)?.is_nail_art));
    }
  }

  function toggleAddOn(id) {
    setAddOnIds((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]));
  }

  // 3. Book the slot, then send the client to Stripe to pay the deposit.
  async function handlePay(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      let bookingId = heldBookingId;
      if (!bookingId) {
        const booking = await createBooking({
          service_id: serviceId,
          add_on_ids: addOnIds,
          starts_at: startsAt,
          ...details,
        });
        bookingId = booking.id;
        setHeldBookingId(bookingId);
      }
      const { checkout_url } = await startCheckout(bookingId);
      window.location.href = checkout_url; // off to Stripe's payment page
    } catch (e) {
      setError(e.message);
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <Header />

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2><span className="step">1</span> Choose your treatment</h2>
        <div className="grid">
          {services.map((s) => (
            <button
              key={s.id}
              className={`option ${s.id === serviceId ? "selected" : ""}`}
              onClick={() => pickService(s)}
            >
              <strong>{s.name}</strong>
              <span>{s.duration_minutes} min · {euros(s.price_cents)}</span>
            </button>
          ))}
        </div>
      </section>

      {service && allowedAddOns.length > 0 && (
        <section className="card">
          <h2><span className="step">2</span> Add extras <small>(optional)</small></h2>
          <div className="chips">
            {allowedAddOns.map((a) => (
              <button
                key={a.id}
                className={`chip ${addOnIds.includes(a.id) ? "selected" : ""}`}
                onClick={() => toggleAddOn(a.id)}
              >
                {a.name} +{euros(a.price_cents)}
              </button>
            ))}
          </div>
        </section>
      )}

      {service && (
        <section className="card">
          <h2><span className="step">3</span> Pick a day and time</h2>
          <Calendar selected={day} onSelect={setDay} openWeekdays={openWeekdays} />
          {day && (
            <div className="slots">
              <p className="slots-title">Times on {niceDate(day)}</p>
              {loadingSlots && <p className="muted">Checking free times…</p>}
              {!loadingSlots && slots.length === 0 && <p className="muted">No free times this day. Try another.</p>}
              {!loadingSlots &&
                slots.map((slot) => (
                  <button
                    key={slot}
                    className={`chip ${slot === startsAt ? "selected" : ""}`}
                    onClick={() => {
                      setStartsAt(slot);
                      setHeldBookingId(null);
                    }}
                  >
                    {timeOfDay(slot)}
                  </button>
                ))}
            </div>
          )}
        </section>
      )}

      {startsAt && (
        <form className="card" onSubmit={handlePay}>
          <h2><span className="step">4</span> Your details</h2>
          {["name", "email", "phone"].map((field) => (
            <label key={field}>
              {field[0].toUpperCase() + field.slice(1)}
              <input
                type={field === "email" ? "email" : field === "phone" ? "tel" : "text"}
                value={details[field]}
                onChange={(e) => setDetails({ ...details, [field]: e.target.value })}
                required
              />
            </label>
          ))}

          <div className="summary">
            <p>{service.name}{chosenAddOns.map((a) => ` + ${a.name}`).join("")}</p>
            <p>{niceDate(day)} at {timeOfDay(startsAt)} · {minutes} min</p>
            <p>Total {euros(total)} · <strong>Deposit today {euros(deposit)}</strong></p>
            <p className="muted">Deposits are non-refundable.</p>
          </div>

          {error && <p className="error">{error}</p>}

          <button className="button" type="submit" disabled={!canPay}>
            {submitting ? "Taking you to payment…" : `Pay ${euros(deposit)} deposit`}
          </button>
        </form>
      )}
    </main>
  );
}
