import {
  BriefcaseBusiness,
  Building2,
  CalendarClock,
  ChevronRight,
  CircleUserRound,
  ExternalLink,
  LogOut,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { type FormEvent, type ReactNode, useCallback, useEffect, useMemo, useState } from "react";

import { ApiError, api } from "./api";
import type {
  Application,
  ApplicationEvent,
  ApplicationInput,
  ApplicationStatus,
  Company,
  EventType,
  User,
} from "./types";

const TOKEN_KEY = "job-tracker-token";

const statuses: ApplicationStatus[] = [
  "saved", "applied", "screening", "interview", "technical_interview",
  "final_interview", "offer", "accepted", "rejected", "withdrawn",
];

const manualEventTypes: Array<{ value: EventType; label: string }> = [
  { value: "note_added", label: "Note" },
  { value: "interview_scheduled", label: "Interview scheduled" },
  { value: "interview_completed", label: "Interview completed" },
  { value: "offer_received", label: "Offer received" },
];

const labelize = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const formatDate = (value: string) => new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));

function errorMessage(error: unknown) {
  if (error instanceof ApiError) {
    return `${error.message}${error.requestId ? ` · Request ${error.requestId}` : ""}`;
  }
  return "Something went wrong. Check that the API is available and try again.";
}

function AuthScreen({ onAuthenticated }: { onAuthenticated: (token: string) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") await api.register(email, password);
      const result = await api.login(email, password);
      onAuthenticated(result.access_token);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-story">
        <div className="brand-lockup"><span className="brand-mark">JT</span><span>Job Tracker</span></div>
        <div className="auth-copy">
          <p className="eyebrow light">A calmer job search</p>
          <h1>Turn every application into a clear next step.</h1>
          <p>One focused workspace for roles, companies, interviews and the conversations that move your search forward.</p>
        </div>
        <div className="auth-proof"><span>Private by design</span><span>Timeline built in</span><span>Search-ready</span></div>
      </section>
      <section className="auth-panel">
        <form className="auth-card" onSubmit={submit}>
          <p className="eyebrow">{mode === "login" ? "Welcome back" : "Create your workspace"}</p>
          <h2>{mode === "login" ? "Sign in to continue" : "Start tracking with clarity"}</h2>
          <label>Email<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
          <label>Password<input type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={mode === "register" ? 8 : 1} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="primary-button wide" disabled={busy}>{busy ? "Working…" : mode === "login" ? "Sign in" : "Create account"}</button>
          <button className="text-button" type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
            {mode === "login" ? "New here? Create an account" : "Already have an account? Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

function Modal({ title, children, onClose }: { title: string; children: ReactNode; onClose: () => void }) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <header><h2 id="modal-title">{title}</h2><button className="icon-button" onClick={onClose} aria-label="Close"><X size={20} /></button></header>
        {children}
      </section>
    </div>
  );
}

function ApplicationForm({ companies, application, onSave, onCancel }: {
  companies: Company[];
  application?: Application;
  onSave: (data: ApplicationInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [data, setData] = useState<ApplicationInput>({
    company_id: application?.company_id || companies[0]?.id || "",
    position: application?.position || "",
    status: application?.status || "saved",
    source: application?.source || "linkedin",
    work_model: application?.work_model || "remote",
    location: application?.location || "",
    job_url: application?.job_url || "",
    notes: application?.notes || "",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try { await onSave(data); } catch (caught) { setError(errorMessage(caught)); setBusy(false); }
  }

  return (
    <form className="entity-form" onSubmit={submit}>
      <div className="form-grid">
        <label className="span-2">Position<input value={data.position} onChange={(event) => setData({ ...data, position: event.target.value })} required maxLength={200} /></label>
        <label>Company<select value={data.company_id} onChange={(event) => setData({ ...data, company_id: event.target.value })} required><option value="" disabled>Select a company</option>{companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}</select></label>
        <label>Status<select value={data.status} onChange={(event) => setData({ ...data, status: event.target.value as ApplicationStatus })}>{statuses.map((status) => <option key={status} value={status}>{labelize(status)}</option>)}</select></label>
        <label>Source<select value={data.source || ""} onChange={(event) => setData({ ...data, source: event.target.value || null })}><option value="">Not set</option><option value="linkedin">LinkedIn</option><option value="indeed">Indeed</option><option value="company_website">Company website</option><option value="recruiter">Recruiter</option><option value="referral">Referral</option><option value="other">Other</option></select></label>
        <label>Work model<select value={data.work_model || ""} onChange={(event) => setData({ ...data, work_model: event.target.value || null })}><option value="">Not set</option><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="onsite">On-site</option></select></label>
        <label>Location<input value={data.location || ""} onChange={(event) => setData({ ...data, location: event.target.value })} /></label>
        <label>Job URL<input type="url" value={data.job_url || ""} onChange={(event) => setData({ ...data, job_url: event.target.value })} /></label>
        <label className="span-2">Notes<textarea rows={4} value={data.notes || ""} onChange={(event) => setData({ ...data, notes: event.target.value })} /></label>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="form-actions"><button type="button" className="secondary-button" onClick={onCancel}>Cancel</button><button className="primary-button" disabled={busy || !companies.length}>{busy ? "Saving…" : "Save application"}</button></div>
    </form>
  );
}

function CompanyForm({ onSave, onCancel }: { onSave: (data: { name: string; website?: string; industry?: string; location?: string }) => Promise<void>; onCancel: () => void }) {
  const [data, setData] = useState({ name: "", website: "", industry: "", location: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) { event.preventDefault(); setBusy(true); setError(""); try { await onSave(data); } catch (caught) { setError(errorMessage(caught)); setBusy(false); } }
  return <form className="entity-form" onSubmit={submit}><div className="form-grid"><label className="span-2">Company name<input value={data.name} onChange={(event) => setData({ ...data, name: event.target.value })} required /></label><label>Industry<input value={data.industry} onChange={(event) => setData({ ...data, industry: event.target.value })} /></label><label>Location<input value={data.location} onChange={(event) => setData({ ...data, location: event.target.value })} /></label><label className="span-2">Website<input type="url" value={data.website} onChange={(event) => setData({ ...data, website: event.target.value })} /></label></div>{error && <p className="form-error" role="alert">{error}</p>}<div className="form-actions"><button type="button" className="secondary-button" onClick={onCancel}>Cancel</button><button className="primary-button" disabled={busy}>{busy ? "Saving…" : "Add company"}</button></div></form>;
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || "");
  const [user, setUser] = useState<User | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [view, setView] = useState<"applications" | "companies">("applications");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<ApplicationStatus | "">("");
  const [loading, setLoading] = useState(Boolean(token));
  const [error, setError] = useState("");
  const [applicationModal, setApplicationModal] = useState<Application | "new" | null>(null);
  const [companyModal, setCompanyModal] = useState(false);
  const [selected, setSelected] = useState<Application | null>(null);
  const [events, setEvents] = useState<ApplicationEvent[]>([]);
  const [eventNote, setEventNote] = useState("");
  const [eventType, setEventType] = useState<EventType>("note_added");

  const logout = useCallback(() => { sessionStorage.removeItem(TOKEN_KEY); setToken(""); setUser(null); setSelected(null); }, []);

  const loadWorkspace = useCallback(async () => {
    if (!token) return;
    setLoading(true); setError("");
    try {
      const [currentUser, companyList, page] = await Promise.all([api.me(token), api.companies(token), api.applications(token, { search: search.trim() || undefined, status })]);
      setUser(currentUser); setCompanies(companyList); setApplications(page.items); setTotal(page.total);
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) logout();
      else setError(errorMessage(caught));
    } finally { setLoading(false); }
  }, [logout, search, status, token]);

  useEffect(() => { const timer = window.setTimeout(() => { void loadWorkspace(); }, 250); return () => window.clearTimeout(timer); }, [loadWorkspace]);
  useEffect(() => { if (token && selected) void api.events(token, selected.id).then(setEvents).catch((caught) => setError(errorMessage(caught))); }, [selected, token]);

  const companyById = useMemo(() => new Map(companies.map((company) => [company.id, company])), [companies]);
  const summary = useMemo(() => ({
    saved: applications.filter((item) => item.status === "saved").length,
    active: applications.filter((item) => !["saved", "accepted", "rejected", "withdrawn"].includes(item.status)).length,
    interviews: applications.filter((item) => ["interview", "technical_interview", "final_interview"].includes(item.status)).length,
    offers: applications.filter((item) => ["offer", "accepted"].includes(item.status)).length,
  }), [applications]);

  function authenticate(accessToken: string) { sessionStorage.setItem(TOKEN_KEY, accessToken); setToken(accessToken); }
  async function saveApplication(data: ApplicationInput) { if (!token) return; if (applicationModal && applicationModal !== "new") await api.updateApplication(token, applicationModal.id, data); else await api.createApplication(token, data); setApplicationModal(null); await loadWorkspace(); }
  async function saveCompany(data: { name: string; website?: string; industry?: string; location?: string }) { if (!token) return; await api.createCompany(token, data); setCompanyModal(false); await loadWorkspace(); }
  async function removeApplication(application: Application) { if (!token || !window.confirm(`Delete ${application.position}? This also removes its timeline.`)) return; await api.deleteApplication(token, application.id); setSelected(null); await loadWorkspace(); }
  async function addEvent(event: FormEvent) { event.preventDefault(); if (!token || !selected || !eventNote.trim()) return; try { await api.createEvent(token, selected.id, eventType, eventNote.trim()); setEventNote(""); setEvents(await api.events(token, selected.id)); } catch (caught) { setError(errorMessage(caught)); } }

  if (!token) return <AuthScreen onAuthenticated={authenticate} />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark" aria-label="Job Application Tracker">JT</div>
        <nav aria-label="Primary navigation">
          <button className={`nav-button ${view === "applications" ? "active" : ""}`} onClick={() => setView("applications")} aria-label="Applications"><BriefcaseBusiness size={20} /></button>
          <button className={`nav-button ${view === "companies" ? "active" : ""}`} onClick={() => setView("companies")} aria-label="Companies"><Building2 size={20} /></button>
        </nav>
        <button className="user-avatar" onClick={logout} aria-label="Sign out"><LogOut size={16} /></button>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div><p className="eyebrow">{new Intl.DateTimeFormat("en-GB", { weekday: "long", day: "numeric", month: "long" }).format(new Date())}</p><h1>{view === "applications" ? "Your job search, in focus." : "Companies worth knowing."}</h1><p className="subtitle">{user?.email || "Loading your workspace…"}</p></div>
          <button className="primary-button" onClick={() => view === "applications" ? setApplicationModal("new") : setCompanyModal(true)}><Plus size={18} />Add {view === "applications" ? "application" : "company"}</button>
        </header>

        {error && <div className="alert" role="alert"><span>{error}</span><button onClick={() => setError("")} aria-label="Dismiss"><X size={16} /></button></div>}

        {view === "applications" ? <>
          <section className="stat-grid" aria-label="Pipeline summary">
            {[{ label: "Saved", value: summary.saved, tone: "slate" }, { label: "In progress", value: summary.active, tone: "blue" }, { label: "Interviews", value: summary.interviews, tone: "amber" }, { label: "Offers", value: summary.offers, tone: "green" }].map((item) => <article className="stat-card" key={item.label}><span className={`status-dot ${item.tone}`} /><div><strong>{item.value}</strong><span>{item.label}</span></div></article>)}
          </section>
          <section className="applications-panel">
            <div className="panel-heading"><div><p className="eyebrow">Pipeline · {total} total</p><h2>Applications</h2></div><div className="filters"><label className="search-field"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} aria-label="Search applications" placeholder="Search role or company" /></label><select aria-label="Filter by status" value={status} onChange={(event) => setStatus(event.target.value as ApplicationStatus | "")}><option value="">All statuses</option>{statuses.map((item) => <option value={item} key={item}>{labelize(item)}</option>)}</select></div></div>
            {loading ? <div className="empty-state">Loading your pipeline…</div> : applications.length === 0 ? <div className="empty-state"><BriefcaseBusiness size={30} /><h3>No applications found</h3><p>Add your first role or adjust the current filters.</p><button className="secondary-button" onClick={() => setApplicationModal("new")}>Add an application</button></div> : <div className="table-shell"><div className="table-header row"><span>Role</span><span>Status</span><span>Location</span><span>Updated</span></div>{applications.map((application) => <button className="application-row row" key={application.id} onClick={() => setSelected(application)}><div><strong>{application.position}</strong><span>{companyById.get(application.company_id)?.name || "Unknown company"}</span></div><span className={`status-pill status-${application.status}`}>{labelize(application.status)}</span><span>{application.work_model ? `${labelize(application.work_model)}${application.location ? ` · ${application.location}` : ""}` : application.location || "—"}</span><span>{formatDate(application.updated_at)}</span></button>)}</div>}
          </section>
        </> : <section className="companies-grid">{companies.length === 0 ? <div className="empty-state full"><Building2 size={30} /><h3>No companies yet</h3><p>Create a company before adding an application.</p><button className="secondary-button" onClick={() => setCompanyModal(true)}>Add a company</button></div> : companies.map((company) => <article className="company-card" key={company.id}><div className="company-icon"><Building2 size={20} /></div><div><h2>{company.name}</h2><p>{company.industry || "Industry not set"}</p><span>{company.location || "Location not set"}</span></div>{company.website && <a href={company.website} target="_blank" rel="noreferrer" aria-label={`Visit ${company.name}`}><ExternalLink size={18} /></a>}</article>)}</section>}
      </main>

      {selected && <aside className="detail-panel" aria-label={`${selected.position} details`}><header><div><p className="eyebrow">Application detail</p><h2>{selected.position}</h2><p>{companyById.get(selected.company_id)?.name}</p></div><button className="icon-button" onClick={() => setSelected(null)} aria-label="Close details"><X size={20} /></button></header><div className="detail-actions"><button className="secondary-button" onClick={() => setApplicationModal(selected)}>Edit</button>{selected.job_url && <a className="secondary-button" href={selected.job_url} target="_blank" rel="noreferrer">View role <ExternalLink size={15} /></a>}<button className="danger-button" onClick={() => void removeApplication(selected)}><Trash2 size={16} /></button></div><section className="detail-summary"><span className={`status-pill status-${selected.status}`}>{labelize(selected.status)}</span><p>{selected.notes || "No application notes yet."}</p></section><section className="timeline"><div className="section-title"><CalendarClock size={18} /><h3>Timeline</h3></div><form className="event-form" onSubmit={addEvent}><select aria-label="Event type" value={eventType} onChange={(event) => setEventType(event.target.value as EventType)}>{manualEventTypes.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select><textarea aria-label="Event note" placeholder="Add context or the next step…" rows={3} value={eventNote} onChange={(event) => setEventNote(event.target.value)} /><button className="primary-button" disabled={!eventNote.trim()}>Add to timeline</button></form><div className="timeline-list">{events.map((item) => <article key={item.id}><span className="timeline-node" /><div><strong>{labelize(item.event_type)}</strong><time>{formatDate(item.occurred_at)}</time><p>{item.notes || (item.to_status ? `${labelize(item.from_status || "none")} → ${labelize(item.to_status)}` : "Recorded automatically")}</p></div></article>)}</div></section></aside>}

      {applicationModal && <Modal title={applicationModal === "new" ? "Add application" : "Edit application"} onClose={() => setApplicationModal(null)}>{companies.length ? <ApplicationForm companies={companies} application={applicationModal === "new" ? undefined : applicationModal} onSave={saveApplication} onCancel={() => setApplicationModal(null)} /> : <div className="empty-state"><Building2 size={28} /><h3>Add a company first</h3><p>Applications need a company to keep your pipeline organised.</p><button className="primary-button" onClick={() => { setApplicationModal(null); setCompanyModal(true); }}>Add company <ChevronRight size={16} /></button></div>}</Modal>}
      {companyModal && <Modal title="Add company" onClose={() => setCompanyModal(false)}><CompanyForm onSave={saveCompany} onCancel={() => setCompanyModal(false)} /></Modal>}
      <span className="sr-only"><CircleUserRound />Authenticated workspace</span>
    </div>
  );
}

export default App;
