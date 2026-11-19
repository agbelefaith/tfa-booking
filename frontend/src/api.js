// Every call to the backend lives here, so components stay simple.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    // FastAPI puts error messages in "detail"
    const message = typeof data.detail === "string" ? data.detail : "Something went wrong";
    throw new Error(message);
  }
  return data;
}

export const getServices = () => request("/services");
export const getAddOns = () => request("/add-ons");
export const getOpeningDays = () => request("/opening-days");
export const getBookingPolicy = () => request("/booking-policy");

export function getAvailability(day, serviceId, addOnIds) {
  const params = new URLSearchParams({ day, service_id: serviceId });
  addOnIds.forEach((id) => params.append("add_on_ids", id));
  return request(`/availability?${params}`);
}

export const createBooking = (booking) =>
  request("/bookings", { method: "POST", body: JSON.stringify(booking) });

export const startCheckout = (bookingId) =>
  request(`/bookings/${bookingId}/checkout`, { method: "POST" });
