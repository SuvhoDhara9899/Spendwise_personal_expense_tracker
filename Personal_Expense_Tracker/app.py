
# SpendWise Personal Expense Tracker. Uses only Python standard library.
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from datetime import datetime, date
import json, html, uuid, mimetypes, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
DATA = BASE / "data" / "expenses.json"
UPLOADS = BASE / "uploads"
CATEGORIES = ["Food", "Travel", "Education", "Shopping", "Entertainment", "Bills", "Health", "Groceries", "Other"]
COLORS = ["#6657e8", "#19a77a", "#f0a23a", "#e65387", "#299bb5", "#8b5cf6", "#d97706", "#0f766e", "#64748b"]

def load_data():
    try:
        value = json.loads(DATA.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []

def save_data(items):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

def e(v): return html.escape(str(v), quote=True)
def money(v): return "₹{:,.2f}".format(float(v))

def totals(items):
    total = sum(float(x["amount"]) for x in items)
    months, cats = {}, {}
    for x in items:
        key = x["date"][:7]
        months[key] = months.get(key, 0) + float(x["amount"])
        cats[x["category"]] = cats.get(x["category"], 0) + float(x["amount"])
    return total, sorted(months.items()), sorted(cats.items(), key=lambda z:z[1], reverse=True)


CHARTS = BASE / "static" / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

def create_charts(items):
    """Regenerate all charts from the latest saved expense records."""
    total, months, cats = totals(items)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.titleweight": "bold",
        "axes.titlesize": 13,
        "axes.labelcolor": "#788394",
        "xtick.color": "#788394",
        "ytick.color": "#788394",
        "text.color": "#182230",
    })

    # Monthly line chart
    fig, ax = plt.subplots(figsize=(8, 3.2), dpi=120)
    if months:
        labels = [m for m, _ in months]
        values = [v for _, v in months]
        ax.plot(labels, values, color="#6657e8", marker="o", linewidth=2.8,
                markersize=7, markerfacecolor="#ffffff", markeredgewidth=2)
        ax.fill_between(range(len(values)), values, color="#6657e8", alpha=0.12)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.grid(axis="y", alpha=0.22)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#e9edf3")
        ax.set_ylabel("Amount (₹)")
        ax.margins(x=0.08, y=0.22)
    else:
        ax.text(0.5, 0.5, "Add expenses to see your monthly trend",
                ha="center", va="center", color="#788394", transform=ax.transAxes)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(CHARTS / "monthly.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Category bar chart
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=120)
    if cats:
        ordered = list(reversed(cats[:9]))
        labels = [k for k, _ in ordered]
        values = [v for _, v in ordered]
        colors = ["#6657e8", "#19a77a", "#f0a23a", "#e65387", "#299bb5",
                  "#8b5cf6", "#d97706", "#0f766e", "#64748b"][:len(values)]
        bars = ax.barh(labels, values, color=colors, height=0.62)
        ax.bar_label(bars, labels=[f"₹{v:,.0f}" for v in values], padding=5, fontsize=8)
        ax.grid(axis="x", alpha=0.2)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#e9edf3")
        ax.set_xlabel("Amount (₹)")
        ax.margins(x=0.2)
    else:
        ax.text(0.5, 0.5, "Add expenses to see category comparison",
                ha="center", va="center", color="#788394", transform=ax.transAxes)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(CHARTS / "category_bar.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Category donut chart
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=120)
    if cats:
        labels = [k for k, _ in cats[:7]]
        values = [v for _, v in cats[:7]]
        colors = ["#6657e8", "#19a77a", "#f0a23a", "#e65387", "#299bb5",
                  "#8b5cf6", "#64748b"][:len(values)]
        wedges, _ = ax.pie(values, startangle=90, colors=colors,
                           wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 2})
        ax.text(0, 0, f"₹{total:,.0f}", ha="center", va="center",
                fontsize=12, fontweight="bold", color="#182230")
        ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.88, 0.5),
                  frameon=False, fontsize=8)
    else:
        ax.text(0.5, 0.5, "No category data yet",
                ha="center", va="center", color="#788394", transform=ax.transAxes)
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(CHARTS / "category_donut.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

def chart_image(filename, alt):
    # A changing query string plus no-cache headers prevents old chart images
    # from being displayed after a new expense is added or deleted.
    return (f'<img class="chart-image" src="/charts/{filename}?v={time.time_ns()}" '
            f'alt="{e(alt)}">')

CSS_PATH=BASE/"static"/"style.css"
class Handler(BaseHTTPRequestHandler):
    def html(self, body, status=200):
        raw=body.encode()
        self.send_response(status); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def go(self,path):
        self.send_response(303); self.send_header("Location",path); self.end_headers()
    def page(self,title,active,content):
        nav=[("Dashboard","/","dash"),("Transactions","/transactions","tx"),("Add Expense","/add","add"),("Analysis","/analysis","analysis")]
        links="".join(f'<a class="{"active" if active==key else ""}" href="{url}">{label}</a>' for label,url,key in nav)
        return f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | SpendWise</title><link rel="stylesheet" href="/static/style.css"></head><body><div class="layout"><aside class="sidebar"><div class="brand">Spend<span>Wise</span></div><nav class="nav">{links}</nav><div class="side-note">Personal Expense Tracker<br>Records are saved on this computer.</div></aside><main>{content}</main></div></body></html>'
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=="/static/style.css":
            raw=CSS_PATH.read_bytes(); self.send_response(200); self.send_header("Content-Type","text/css"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw); return
        if p.path.startswith("/charts/"):
            chart_file=CHARTS/Path(p.path).name
            if chart_file.exists() and chart_file.is_file():
                raw=chart_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type","image/png")
                self.send_header("Cache-Control","no-store, no-cache, must-revalidate, max-age=0")
                self.send_header("Pragma","no-cache")
                self.send_header("Content-Length",str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            self.send_error(404); return
        if p.path.startswith("/uploads/"):
            f=UPLOADS/Path(p.path).name
            if f.exists():
                raw=f.read_bytes(); self.send_response(200); self.send_header("Content-Type",mimetypes.guess_type(f.name)[0] or "application/octet-stream"); self.send_header("Content-Length",str(len(raw))); self.end_headers(); self.wfile.write(raw); return
            self.send_error(404); return
        items=load_data()
        if p.path=="/": self.dashboard(items)
        elif p.path=="/transactions": self.transactions(items,parse_qs(p.query))
        elif p.path=="/add": self.add_form()
        elif p.path=="/analysis": self.analysis(items)
        else: self.send_error(404)
    def dashboard(self,items):
        create_charts(items)
        total,months,cats=totals(items); now=date.today().strftime("%Y-%m")
        month_total=dict(months).get(now,0); avg=total/len(items) if items else 0
        hi=max(items,key=lambda x:float(x["amount"])) if items else None
        lo=min(items,key=lambda x:float(x["amount"])) if items else None
        recent=sorted(items,key=lambda x:(x["date"],x["created"]),reverse=True)[:5]
        recent_html="".join(f'<div class="recent"><div><strong>{e(x["description"])}</strong><small>{e(x["category"])} · {e(x["date"])}</small></div><b>{money(x["amount"])}</b></div>' for x in recent) or '<div class="empty">No expenses recorded yet.</div>'
        content=f'''<div class="topline"><div><h1>Dashboard</h1><p class="sub">Your spending at a glance. Charts refresh whenever records change.</p></div><a class="btn green" href="/add">＋ Add expense</a></div>
        <section class="cards"><div class="metric"><div class="label">Total Expenditure</div><div class="number">{money(total)}</div><div class="hint">All recorded expenses</div></div><div class="metric"><div class="label">This Month</div><div class="number">{money(month_total)}</div><div class="hint">{e(now)}</div></div><div class="metric"><div class="label">Transactions</div><div class="number">{len(items)}</div><div class="hint">Saved records</div></div><div class="metric"><div class="label">Average Expense</div><div class="number">{money(avg)}</div><div class="hint">Per transaction</div></div></section>
        <section class="grid2"><div class="panel chart"><h2>Monthly Expenditure Trend</h2>{chart_image("monthly.png","Monthly expenditure line chart")}</div><div class="panel chart"><h2>Category Distribution</h2>{chart_image("category_donut.png","Category distribution donut chart")}</div></section>
        <section class="grid2"><div class="panel chart"><h2>Category-wise Expenditure</h2>{chart_image("category_bar.png","Category-wise expenditure bar chart")}</div><div class="panel"><h2>Recent Expenses</h2>{recent_html}<p><a href="/transactions">View all transactions →</a></p></div></section>
        <section class="cards"><div class="metric"><div class="label">Highest Expense</div><div class="number">{money(hi["amount"]) if hi else "—"}</div><div class="hint">{e(hi["description"]) if hi else "No data"}</div></div><div class="metric"><div class="label">Lowest Expense</div><div class="number">{money(lo["amount"]) if lo else "—"}</div><div class="hint">{e(lo["description"]) if lo else "No data"}</div></div><div class="metric"><div class="label">Categories Used</div><div class="number">{len(cats)}</div><div class="hint">Different categories</div></div><div class="metric"><div class="label">Saved Records</div><div class="number">{len(items)}</div><div class="hint">Stored in JSON file</div></div></section>'''
        self.html(self.page("Dashboard","dash",content))
    def transactions(self,items,q):
        search=q.get("search",[""])[0].lower().strip(); cat=q.get("category",[""])[0]; sort=q.get("sort",["date_desc"])[0]
        rows=[x for x in items if (not search or search in x["description"].lower() or search in x["category"].lower()) and (not cat or x["category"]==cat)]
        if sort=="amount_desc": rows.sort(key=lambda x:float(x["amount"]),reverse=True)
        elif sort=="amount_asc": rows.sort(key=lambda x:float(x["amount"]))
        elif sort=="date_asc": rows.sort(key=lambda x:x["date"])
        else: rows.sort(key=lambda x:(x["date"],x["created"]),reverse=True)
        trs=[]
        for x in rows:
            receipt=f'<a href="/uploads/{e(x["receipt"])}" target="_blank">View file</a>' if x.get("receipt") else "—"
            trs.append(f'<tr><td>{e(x["date"])}</td><td class="amount">{money(x["amount"])}</td><td>{e(x["description"])}</td><td><span class="tag">{e(x["category"])}</span></td><td>{receipt}</td><td><form method="post" action="/delete"><input type="hidden" name="id" value="{e(x["id"])}"><button class="btn danger" type="submit">Delete</button></form></td></tr>')
        opts=''.join(f'<option value="{e(c)}" {"selected" if cat==c else ""}>{e(c)}</option>' for c in CATEGORIES)
        content=f'''<div class="topline"><div><h1>Transactions</h1><p class="sub">Search, filter, sort, review and delete expenses.</p></div><a class="btn green" href="/add">＋ Add new transaction</a></div><div class="panel"><form class="toolbar" method="get"><input class="field" name="search" placeholder="Search expenses" value="{e(q.get("search",[""])[0])}"><select class="field" name="category"><option value="">All categories</option>{opts}</select><select class="field" name="sort"><option value="date_desc" {"selected" if sort=="date_desc" else ""}>Newest first</option><option value="date_asc" {"selected" if sort=="date_asc" else ""}>Oldest first</option><option value="amount_desc" {"selected" if sort=="amount_desc" else ""}>Amount: high to low</option><option value="amount_asc" {"selected" if sort=="amount_asc" else ""}>Amount: low to high</option></select><button class="btn">Apply</button><a class="btn light" href="/transactions">Reset</a></form><div class="table-wrap"><table class="table"><thead><tr><th>DATE</th><th>AMOUNT</th><th>DESCRIPTION</th><th>CATEGORY</th><th>BILL / FILE</th><th>ACTION</th></tr></thead><tbody>{"".join(trs) or '<tr><td colspan="6" class="empty">No matching expenses found.</td></tr>'}</tbody></table></div><p class="sub">Showing {len(rows)} of {len(items)} records</p></div>'''
        self.html(self.page("Transactions","tx",content))
    def add_form(self,error=""):
        opts="".join(f'<option>{e(c)}</option>' for c in CATEGORIES)
        content=f'''<div class="topline"><div><h1>Add Expense</h1><p class="sub">Enter a payment and attach its bill or receipt if available.</p></div><a class="btn light" href="/transactions">Cancel</a></div>{f'<div class="notice">{e(error)}</div>' if error else ""}<div class="panel form-panel"><form method="post" action="/add" enctype="multipart/form-data"><div class="form-grid"><div class="form-group"><label>Amount (₹) *</label><input class="field" name="amount" type="number" min="0.01" step="0.01" placeholder="e.g. 250.00" required></div><div class="form-group"><label>Date *</label><input class="field" name="date" type="date" value="{date.today().isoformat()}" required></div><div class="form-group"><label>Category *</label><select name="category" required>{opts}</select></div><div class="form-group"><label>Description *</label><input class="field" name="description" maxlength="100" placeholder="e.g. Lunch, bus ticket, books" required></div><div class="form-group full"><label>Bill / Expense file (optional)</label><div class="upload"><b>Upload receipt or expense photo</b><p class="help">JPG, JPEG, PNG or PDF · Maximum 8 MB</p><input type="file" name="receipt" accept=".jpg,.jpeg,.png,.pdf"></div></div><div class="full"><button class="btn green">Save Expense</button> <a class="btn light" href="/">Cancel</a></div></div></form></div>'''
        self.html(self.page("Add Expense","add",content))
    def analysis(self,items):
        create_charts(items)
        total,months,cats=totals(items); avg=total/len(items) if items else 0
        hi=max(items,key=lambda x:float(x["amount"])) if items else None; lo=min(items,key=lambda x:float(x["amount"])) if items else None
        month_rows="".join(f'<tr><td>{e(k)}</td><td class="amount">{money(v)}</td></tr>' for k,v in months) or '<tr><td colspan="2" class="empty">No monthly records yet.</td></tr>'
        cat_rows="".join(f'<div class="recent"><div><strong>{e(k)}</strong><small>{(v/total*100 if total else 0):.1f}% of total</small></div><b>{money(v)}</b></div>' for k,v in cats) or '<div class="empty">No expense data available.</div>'
        content=f'''<div class="topline"><div><h1>Analysis & Reports</h1><p class="sub">Insights calculated from your saved expense records.</p></div><a class="btn green" href="/add">＋ Add expense</a></div><section class="cards"><div class="metric"><div class="label">Total Expenditure</div><div class="number">{money(total)}</div></div><div class="metric"><div class="label">Average Expense</div><div class="number">{money(avg)}</div></div><div class="metric"><div class="label">Highest Expense</div><div class="number">{money(hi["amount"]) if hi else "—"}</div><div class="hint">{e(hi["description"]) if hi else "No data"}</div></div><div class="metric"><div class="label">Lowest Expense</div><div class="number">{money(lo["amount"]) if lo else "—"}</div><div class="hint">{e(lo["description"]) if lo else "No data"}</div></div></section><section class="grid2"><div class="panel chart"><h2>Monthly Trend — Line Plot</h2>{chart_image("monthly.png","Monthly expenditure line chart")}</div><div class="panel chart"><h2>Category Share — Donut Chart</h2>{chart_image("category_donut.png","Category distribution donut chart")}</div></section><section class="grid2"><div class="panel chart"><h2>Category Comparison — Bar Chart</h2>{chart_image("category_bar.png","Category-wise expenditure bar chart")}</div><div class="panel"><h2>Category Summary</h2>{cat_rows}</div></section><div class="panel"><h2>Monthly Summary</h2><div class="table-wrap"><table class="table"><thead><tr><th>MONTH</th><th>TOTAL EXPENDITURE</th></tr></thead><tbody>{month_rows}</tbody></table></div></div>'''
        self.html(self.page("Analysis","analysis",content))
    def read_fields(self):
        length=int(self.headers.get("Content-Length","0"))
        if length>12*1024*1024: raise ValueError("Request is too large.")
        raw=self.rfile.read(length); ctype=self.headers.get("Content-Type","")
        if "multipart/form-data" in ctype:
            msg=BytesParser(policy=default).parsebytes((f"Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n").encode()+raw); fields={}
            for part in msg.iter_parts():
                name=part.get_param("name",header="content-disposition"); filename=part.get_filename(); payload=part.get_payload(decode=True) or b""
                fields[name]={"filename":filename,"data":payload} if filename else payload.decode("utf-8",errors="replace")
            return fields
        return {k:v[0] for k,v in parse_qs(raw.decode(),keep_blank_values=True).items()}
    def do_POST(self):
        p=urlparse(self.path)
        try: f=self.read_fields()
        except ValueError as ex: self.add_form(str(ex)); return
        items=load_data()
        if p.path=="/add":
            try: amount=float(f.get("amount",""))
            except ValueError: amount=0
            d=f.get("date",""); desc=f.get("description","").strip(); cat=f.get("category","")
            try: datetime.strptime(d,"%Y-%m-%d")
            except ValueError: self.add_form("Please enter a valid date."); return
            if amount<=0 or amount>100000000: self.add_form("Amount must be a valid number greater than zero."); return
            if not desc: self.add_form("Please enter a description."); return
            if cat not in CATEGORIES: self.add_form("Please select a valid category."); return
            receipt=""; upload=f.get("receipt")
            if upload and upload.get("data"):
                ext=Path(upload["filename"]).suffix.lower()
                if ext not in [".jpg",".jpeg",".png",".pdf"]: self.add_form("Unsupported file type. Upload JPG, PNG or PDF."); return
                if len(upload["data"])>8*1024*1024: self.add_form("File is larger than 8 MB."); return
                receipt=uuid.uuid4().hex+ext; UPLOADS.mkdir(exist_ok=True); (UPLOADS/receipt).write_bytes(upload["data"])
            items.append({"id":uuid.uuid4().hex,"date":d,"amount":round(amount,2),"description":desc,"category":cat,"receipt":receipt,"created":datetime.now().isoformat(timespec="seconds")})
            save_data(items); self.go("/transactions"); return
        if p.path=="/delete":
            rid=f.get("id",""); target=next((x for x in items if x["id"]==rid),None)
            if target and target.get("receipt"): (UPLOADS/target["receipt"]).unlink(missing_ok=True)
            save_data([x for x in items if x["id"]!=rid]); self.go("/transactions"); return
        self.send_error(404)

def main():
    host,port="127.0.0.1",8000
    print("\\nSpendWise Personal Expense Tracker")
    print(f"Open in browser: http://{host}:{port}")
    print("Press Ctrl+C to stop.\\n")
    ThreadingHTTPServer((host,port),Handler).serve_forever()

if __name__=="__main__": main()
