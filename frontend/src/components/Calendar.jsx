import { useState } from "react";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const BOOK_AHEAD_DAYS = 60;

// "YYYY-MM-DD" for a date (the format the API wants)
const toKey = (date) => date.toLocaleDateString("en-CA");

// JavaScript counts Sunday as 0; Python (and our API) counts Monday as 0.
const mondayFirst = (date) => (date.getDay() + 6) % 7;

export default function Calendar({ selected, onSelect, openWeekdays }) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const lastDay = new Date(today);
  lastDay.setDate(today.getDate() + BOOK_AHEAD_DAYS);

  // Which month is showing (always the 1st of that month)
  const [month, setMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const year = month.getFullYear();
  const monthIndex = month.getMonth();
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();

  // Empty boxes before the 1st, so it lands under the right weekday
  const blanks = Array(mondayFirst(month)).fill(null);
  const days = Array.from({ length: daysInMonth }, (_, i) => new Date(year, monthIndex, i + 1));

  const canGoBack = month > new Date(today.getFullYear(), today.getMonth(), 1);
  const canGoForward = new Date(year, monthIndex + 1, 1) <= lastDay;

  const isBookable = (date) =>
    date >= today && date <= lastDay && openWeekdays.includes(mondayFirst(date));

  return (
    <div className="calendar">
      <div className="calendar-header">
        <button
          className="nav"
          onClick={() => setMonth(new Date(year, monthIndex - 1, 1))}
          disabled={!canGoBack}
          aria-label="Previous month"
        >
          ‹
        </button>
        <span>{month.toLocaleDateString("en-IE", { month: "long", year: "numeric" })}</span>
        <button
          className="nav"
          onClick={() => setMonth(new Date(year, monthIndex + 1, 1))}
          disabled={!canGoForward}
          aria-label="Next month"
        >
          ›
        </button>
      </div>

      <div className="calendar-grid">
        {WEEKDAYS.map((name) => (
          <span key={name} className="weekday">{name}</span>
        ))}
        {blanks.map((_, i) => (
          <span key={`blank-${i}`} />
        ))}
        {days.map((date) => {
          const key = toKey(date);
          const classes = ["date"];
          if (key === selected) classes.push("selected");
          if (key === toKey(today)) classes.push("today");
          return (
            <button
              key={key}
              className={classes.join(" ")}
              disabled={!isBookable(date)}
              onClick={() => onSelect(key)}
            >
              {date.getDate()}
            </button>
          );
        })}
      </div>
    </div>
  );
}
