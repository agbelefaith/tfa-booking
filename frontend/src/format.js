// Small helpers for showing money and times nicely.
export const euros = (cents) =>
  new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR" }).format(cents / 100);

export const timeOfDay = (isoString) =>
  new Date(isoString).toLocaleTimeString("en-IE", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/Dublin",
  });

export const niceDate = (isoDate) =>
  new Date(`${isoDate}T12:00:00`).toLocaleDateString("en-IE", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
