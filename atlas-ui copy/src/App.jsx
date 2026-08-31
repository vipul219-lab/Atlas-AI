import { useState } from "react";
import { Bot, Code2, FileText, Image, Video, Send, Shield, UserPlus, Info, LogOut, Paperclip, Sparkles } from "lucide-react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:9000";
const modes = [
  { id: "chat", label: "Chat", icon: Bot, description: "Ask anything" },
  { id: "code", label: "Code", icon: Code2, description: "Build and debug" },
  { id: "document", label: "Document", icon: FileText, description: "Analyze a PDF" },
  { id: "image", label: "Image", icon: Image, description: "Create an image" },
  { id: "video", label: "Video", icon: Video, description: "Create a video" },
];

export default function App() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [loginForm, setLoginForm] = useState({ username: "admin", password: "admin123" });
  const [newUser, setNewUser] = useState({ username: "", password: "", role: "user" });
  const [mode, setMode] = useState("chat");
  const [message, setMessage] = useState("");
  const [pdf, setPdf] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [aboutOpen, setAboutOpen] = useState(true);
  const headers = { token: `Bearer ${token}` };
  const selectedMode = modes.find((item) => item.id === mode);

  async function readResponse(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  }

  async function login(event) {
    event.preventDefault(); setError("");
    try {
      const response = await fetch(`${API_URL}/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(loginForm) });
      const data = await readResponse(response);
      setToken(data.access_token); setUser({ username: loginForm.username, role: data.role }); setNotice("Welcome to Atlas");
    } catch (err) { setError(err.message); }
  }

  async function createUser(event) {
    event.preventDefault(); setError("");
    try {
      const response = await fetch(`${API_URL}/admin/users`, { method: "POST", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify(newUser) });
      await readResponse(response); setNewUser({ username: "", password: "", role: "user" }); setNotice("Account created successfully");
    } catch (err) { setError(err.message); }
  }

  async function sendMessage(event) {
    event.preventDefault();
    if (!message.trim() || loading) return;
    setLoading(true); setError(""); setNotice("");
    try {
      let response;
      if (mode === "document") {
        if (!pdf) throw new Error("Choose a PDF before analyzing a document");
        const formData = new FormData(); formData.append("prompt", message); formData.append("file", pdf);
        response = await fetch(`${API_URL}/analyze/document`, { method: "POST", headers, body: formData });
      } else {
        response = await fetch(`${API_URL}/chat`, { method: "POST", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify({ message, mode }) });
      }
      const data = await readResponse(response);
      setHistory((previous) => [...previous, { mode, user: message, assistant: data.answer }]); setMessage(""); setPdf(null);
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  }

  function logout() { setToken(""); setUser(null); setHistory([]); setMessage(""); }

  if (!user) return (
    <main className="login-page"><section className="login-panel">
      <div className="brand login-brand"><div className="logo"><img src="/bdl-logo.png" alt="BDL" /></div><div><h1>Atlas</h1><p>Multi-model AI gateway</p></div></div>
      <div className="eyebrow"><Sparkles size={14} /> LOCAL AI WORKSPACE</div>
      <form onSubmit={login} className="login-form"><label>Username<input value={loginForm.username} onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })} /></label><label>Password<input value={loginForm.password} onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })} type="password" /></label><button className="primary-button" type="submit">Enter Atlas</button></form>
      {error && <p className="error-message">{error}</p>}<small className="login-hint">Demo admin: admin / admin123</small>
    </section></main>
  );

  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand compact"><div className="logo"><img src="/bdl-logo.png" alt="BDL" /></div><div><h1>Atlas</h1><p>AI Gateway</p></div></div>
      <div className="user-strip"><div className="avatar">{user.username[0].toUpperCase()}</div><div><strong>{user.username}</strong><span>{user.role}</span></div></div>
      <button className="about-button" onClick={() => setAboutOpen(!aboutOpen)}><Info size={17} /> About Atlas</button>
      <p className="section-label">WORKSPACE</p>
      <nav className="mode-list">{modes.map((item) => { const Icon = item.icon; return <button key={item.id} className={mode === item.id && !aboutOpen ? "active" : ""} onClick={() => { setMode(item.id); setAboutOpen(false); }}><Icon size={18} /><span><strong>{item.label}</strong><small>{item.description}</small></span></button>; })}</nav>
      {user.role === "admin" && <form className="admin-box" onSubmit={createUser}><p className="section-label">ADMIN</p><h2><UserPlus size={16} /> Create account</h2><input placeholder="Username" value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} /><input placeholder="Password" type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} /><select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}><option value="user">User</option><option value="admin">Admin</option></select><button className="secondary-button" type="submit">Create account</button></form>}
      <button className="logout-button" onClick={logout}><LogOut size={16} /> Sign out</button>
    </aside>
    <section className="workspace"><header className="topbar"><div><p className="eyebrow"><Shield size={14} /> SECURE LOCAL ROUTING</p><h2>{aboutOpen ? "Welcome to Atlas" : `${selectedMode.label} workspace`}</h2></div><span className="status-dot">Services ready</span></header>
      {aboutOpen ? <section className="about-page"><div className="hero-copy"><p className="eyebrow"><Sparkles size={14} /> ONE GATEWAY. MANY MODELS.</p><h3>Build, analyze, and create with Atlas.</h3><p>Atlas is a local-first AI workspace that routes each task to the right model while keeping authentication and safety controls in one backend.</p><button className="primary-button" onClick={() => { setAboutOpen(false); setMode("chat"); }}>Open workspace <Send size={16} /></button></div><div className="about-grid"><article><Bot size={20} /><h4>Text intelligence</h4><p>Chat and code assistance powered by your local text model.</p></article><article><FileText size={20} /><h4>Document analysis</h4><p>Upload a PDF and ask focused questions about its contents.</p></article><article><Image size={20} /><h4>Creative tools</h4><p>Image and video routes are ready for connected diffusion servers.</p></article></div></section> : <><section className="chat-history">{history.length === 0 && <div className="empty-state"><selectedMode.icon size={30} /><h3>Start in {selectedMode.label}</h3><p>{selectedMode.description}. Your conversation will appear here.</p></div>}{history.map((item, index) => <div key={index} className="chat-pair"><div className="bubble user"><span>You</span>{item.user}</div><div className="bubble assistant"><span>Atlas · {item.mode}</span><pre>{item.assistant}</pre></div></div>)}</section><form className="composer" onSubmit={sendMessage}>{mode === "document" && <label className="file-picker"><Paperclip size={16} />{pdf ? pdf.name : "Attach PDF"}<input type="file" accept="application/pdf" onChange={(e) => setPdf(e.target.files[0])} /></label>}<textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder={mode === "document" ? "Ask a question about your PDF..." : `Enter a ${mode} prompt...`} /><button className="primary-button send-button" type="submit" disabled={loading}><Send size={17} />{loading ? "Working..." : "Send"}</button></form></>}
      {(error || notice) && <div className={error ? "toast error-message" : "toast notice-message"}>{error || notice}</div>}
    </section>
  </main>;
}
