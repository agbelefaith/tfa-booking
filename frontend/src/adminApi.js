// Calls to the /admin endpoints. Every one sends your admin key.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const KEY_NAME = "tfa-admin-key";

export const getSavedKey = () => sessionStorage.getItem(KEY_NAME) || "";
export const saveKey = (key) => sessionStorage.setItem(KEY_NAME, key);
export const forgetKey = () => sessionStorage.removeItem(KEY_NAME);

async function adminRequest(path, options = {}) {
  const response = await fetch(`${API_URL}/admin${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", "X-Admin-Key": getSavedKey() },
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
    throw new Error(detail || "Something went wrong");
  }
  return data;
}

export const checkKey = () => adminRequest("/check");
export const getBookings = (start, end) => adminRequest(`/bookings?start=${start}&end=${end}`);
export const cancelBooking = (id) => adminRequest(`/bookings/${id}/cancel`, { method: "POST" });
export const markNoShow = (id) => adminRequest(`/bookings/${id}/no-show`, { method: "POST" });
export const markCompleted = (id) => adminRequest(`/bookings/${id}/complete`, { method: "POST" });
export const getOpeningHours = () => adminRequest("/opening-hours");
export const saveOpeningHours = (hours) =>
  adminRequest("/opening-hours", { method: "PUT", body: JSON.stringify(hours) });
export const getTimeOff = () => adminRequest("/time-off");
export const addTimeOff = (timeOff) =>
  adminRequest("/time-off", { method: "POST", body: JSON.stringify(timeOff) });
export const removeTimeOff = (id) => adminRequest(`/time-off/${id}`, { method: "DELETE" });
