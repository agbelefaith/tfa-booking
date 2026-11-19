export default function ResultPage({ title, message }) {
  return (
    <main className="page">
      <Header />
      <section className="card result">
        <h2>{title}</h2>
        <p>{message}</p>
        <a className="button" href="/">Book another appointment</a>
      </section>
    </main>
  );
}

export function Header() {
  return (
    <header className="header">
      <p className="eyebrow">TFA</p>
      <h1>Nails &amp; Beauty</h1>
      <p className="tagline">Book your appointment</p>
    </header>
  );
}
