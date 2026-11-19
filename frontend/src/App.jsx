import BookingPage from "./components/BookingPage.jsx";
import ResultPage from "./components/ResultPage.jsx";

// A tiny "router": pick a page based on the URL path.
export default function App() {
  const path = window.location.pathname;

  if (path === "/booking/success") {
    return (
      <ResultPage
        title="You're booked in ✨"
        message="Your deposit is paid. A confirmation is on its way to your email. See you soon!"
      />
    );
  }
  if (path === "/booking/cancelled") {
    return (
      <ResultPage
        title="Payment cancelled"
        message="No money was taken. Your slot is held for 30 minutes if you'd like to try again."
      />
    );
  }
  return <BookingPage />;
}
