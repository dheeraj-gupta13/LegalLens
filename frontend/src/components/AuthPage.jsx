import { useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";

export default function AuthPage() {
  const { login, register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (kind) => {
    setBusy(true); setError("");
    try { await (kind === "login" ? login : register)(email, password); }
    catch (e) { setError(e.details?.[0]?.message ? `${e.details[0].field}: ${e.details[0].message}` : e.message); }
    finally { setBusy(false); }
  };

  return (
    <div className="login">
      <div className="pitch">
        <div className="brand">LegalLens</div>
        <h1>Read it <span className="hl">before</span> you sign it.</h1>
        <div className="clause">
          <b>8. Renewal.</b> This agreement <span className="hl">automatically renews for another 12 months</span> unless cancelled in writing 90 days before the end of the term.<br />
          <span className="flag">Worth a closer look: easy to miss the deadline</span>
        </div>
      </div>
      <div className="formside">
        <form className="formcard" onSubmit={(e) => { e.preventDefault(); submit("login"); }}>
          <h2>Welcome</h2>
          <p>Upload a contract or policy and ask it questions in plain language.</p>
          <input type="email" placeholder="Email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input type="password" placeholder="Password (8+ characters)" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <div className="err" role="alert">{error}</div>
          <div className="row">
            <button type="submit" disabled={busy}>Log in</button>
            <button type="button" className="ghost" disabled={busy} onClick={() => submit("register")}>Create account</button>
          </div>
        </form>
      </div>
    </div>
  );
}
