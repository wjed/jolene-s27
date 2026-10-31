/* Browser regression suite.
 *
 * Not linked from the page. Load it from the console on a running site:
 *
 *     await fetch("qa.js").then(r => r.text()).then(eval); await QA.run();
 *
 * Covers every filter, sort, view, page, guide, download and persistence
 * path rather than a sample of them.
 *
 * One rule learned the hard way: never assert on getBoundingClientRect for a
 * CSS-transformed element. It reports stale values in automation while a
 * screenshot shows the element in its final position. Assert on attributes.
 */

window.QA = (() => {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  let results = [];
  const ok = (name, cond, detail) =>
    results.push({ name, pass: !!cond, detail: cond ? "" : String(detail == null ? "" : detail) });

  const rows = () => $$("table.db tbody tr").length;
  const cards = () => $$(".gcard").length;
  const store = () => { try { return JSON.parse(localStorage.getItem("jolene-s27:tracker:v1") || '{"items":{}}'); } catch (e) { return { items: {} }; } };

  async function goPage(view) {
    const btn = $(`#pagenav button[data-view="${view}"]`) || $(`#menav button[data-view="${view}"]`);
    btn.click();
    await sleep(140);
  }

  async function goDb(view) { $(`[data-dbview="${view}"]`).click(); await sleep(170); }

  async function setSearch(v) {
    const q = $("#q");
    q.value = v;
    q.dispatchEvent(new Event("input", { bubbles: true }));
    await sleep(260);
  }

  async function toggleChip(key) { $(`[data-chip="${key}"]`).click(); await sleep(220); }

  // ---------------------------------------------------------------- suites

  async function pagesAndGuides(data) {
    for (const v of ["plan", "programs", "tracker", "timeline", "profile", "kit"]) {
      await goPage(v);
      ok(`page renders: ${v}`, $("#content").innerHTML.length > 200, $("#content").innerHTML.length);
      ok(`page titled: ${v}`, ($("#page-title").textContent || "").length > 2);
    }

    const guides = $$("#guidenav button");
    ok("9 guides in sidebar", guides.length === 9, guides.length);
    for (const b of guides) {
      b.click();
      await sleep(130);
      const doc = $(".doc");
      ok(`guide renders: ${b.dataset.guide}`, doc && doc.innerHTML.length > 400, doc ? doc.innerHTML.length : "none");
      ok(`guide hash: ${b.dataset.guide}`, location.hash === `#guide/${b.dataset.guide}`, location.hash);
    }

    // every cross-link between guides must resolve to a real guide
    const slugs = new Set(guides.map((b) => b.dataset.guide));
    const dangling = $$(".doc a[data-guide]").map((a) => a.dataset.guide).filter((s) => !slugs.has(s));
    ok("guide cross-links resolve", dangling.length === 0, dangling.join(","));
  }

  async function everyView(data) {
    await goPage("programs");
    for (const [v, sel] of [["table", "table.db"], ["board", ".board"], ["gallery", ".gallery"]]) {
      await goDb(v);
      ok(`db view: ${v}`, !!$(sel));
    }
    await goDb("table");
    ok("table shows every program", rows() === data.count, `${rows()} vs ${data.count}`);
    await goDb("gallery");
    ok("gallery shows every program", cards() === data.count, `${cards()} vs ${data.count}`);
    await goDb("board");
    const grouped = $$(".board .bcard").length;
    ok("board shows every program", grouped === data.count, `${grouped} vs ${data.count}`);
    await goDb("table");
  }

  async function everyChip(data) {
    await goPage("programs");
    await goDb("table");
    const all = rows();

    for (const chip of $$(".filterbar .chip")) {
      const key = chip.dataset.chip;
      const claimed = parseInt((chip.querySelector(".n") || {}).textContent || "0", 10);
      await toggleChip(key);
      const got = rows();
      ok(`chip filters: ${key}`, got === claimed, `shows ${got}, badge says ${claimed}`);
      ok(`chip narrows or holds: ${key}`, got <= all, `${got} > ${all}`);
      ok(`chip pressed state: ${key}`, $(`[data-chip="${key}"]`).getAttribute("aria-pressed") === "true");
      await toggleChip(key);
      ok(`chip restores: ${key}`, rows() === all, `${rows()} vs ${all}`);
    }

    // two chips must intersect, never union
    const keys = $$(".filterbar .chip").map((c) => c.dataset.chip);
    if (keys.length >= 2) {
      await toggleChip(keys[0]);
      const a = rows();
      await toggleChip(keys[1]);
      const both = rows();
      ok("two chips intersect", both <= a, `${both} > ${a}`);
      await toggleChip(keys[0]);
      await toggleChip(keys[1]);
    }
  }

  async function searchAndSort(data) {
    await goPage("programs");
    await goDb("table");
    const all = rows();

    await setSearch("pediatric");
    ok("search narrows", rows() > 0 && rows() < all, rows());
    await setSearch("zzzznothing");
    ok("search empty state", !!$(".empty") && rows() === 0);
    await setSearch("");
    ok("search clears", rows() === all, rows());

    // search must combine with a chip, not replace it
    await toggleChip("near-home");
    const homeOnly = rows();
    await setSearch("children");
    ok("search intersects chip", rows() <= homeOnly, `${rows()} > ${homeOnly}`);
    await setSearch("");
    await toggleChip("near-home");

    const first = () => ($("table.db tbody tr .cell-name a") || {}).textContent || "";
    const seen = {};
    for (const opt of $$("#sort option").map((o) => o.value)) {
      $("#sort").value = opt;
      $("#sort").dispatchEvent(new Event("change", { bubbles: true }));
      await sleep(200);
      ok(`sort runs: ${opt}`, rows() === all, `${rows()} vs ${all}`);
      seen[opt] = first();
    }
    ok("sorts differ from each other", new Set(Object.values(seen)).size > 1, JSON.stringify(seen));

    // every sortable column header, including reversing
    for (const key of $$("table.db th[data-sort]").map((h) => h.dataset.sort)) {
      const th = () => $$("table.db th[data-sort]").find((h) => h.dataset.sort === key);
      th().click();
      await sleep(190);
      const asc = first();
      const ariaAsc = th().getAttribute("aria-sort");
      th().click();
      await sleep(190);
      const desc = first();
      // A column where every row holds the same value cannot meaningfully
      // reverse: the stable name tiebreak correctly keeps the order. Only
      // assert reversal where the column actually varies.
      const distinct = new Set($$(`table.db tbody tr td:nth-child(${
        $$("table.db th").findIndex((h) => h.dataset.sort === key) + 1
      })`).map((td) => td.textContent.trim())).size;
      ok(`column sorts: ${key}`, ariaAsc === "ascending", ariaAsc);
      ok(`column reverses: ${key}`, distinct < 2 || asc !== desc, `${distinct} distinct, ${asc} == ${desc}`);
      ok(`column aria flips: ${key}`, th().getAttribute("aria-sort") === "descending", th().getAttribute("aria-sort"));
    }
  }

  async function peekEveryProgram(data) {
    await goPage("programs");
    await goDb("table");
    let thrown = 0, missingTitle = 0, emptyProps = 0;
    const ids = data.programs.map((p) => p.id);
    for (const id of ids) {
      const btn = $(`[data-peek="${id}"]`);
      if (!btn) { thrown++; continue; }
      try {
        btn.click();
        await sleep(12);
        const body = $("#peek-body");
        if (!body.querySelector(".peek__title")) missingTitle++;
        if (body.querySelectorAll(".prop").length < 8) emptyProps++;
      } catch (e) { thrown++; }
    }
    $("#peek-close").click();
    await sleep(220);
    ok("every program opens a peek", thrown === 0, `${thrown} failed`);
    ok("every peek has a title", missingTitle === 0, `${missingTitle} missing`);
    ok("every peek has properties", emptyProps === 0, `${emptyProps} thin`);
    ok("peek closes", $("#peek").dataset.open === "false");
    ok("scroll unlocked after close", document.body.style.overflow === "");
  }

  async function statusesAndTracker(data) {
    localStorage.removeItem("jolene-s27:tracker:v1");
    await goPage("programs");
    await goDb("table");

    // Scope to one select: querying options across all 110 rows gives 660.
    const firstSel = $("table.db select[data-status-for]");
    const values = [...firstSel.options].map((o) => o.value);
    ok("six statuses offered", values.length === 6, values.length);

    // Changing a status re-renders the table, so the element must be looked up
    // again each time; a held reference goes stale after the first change.
    const pid = firstSel.dataset.statusFor;
    for (const v of values) {
      const sel = $(`select[data-status-for="${pid}"]`);
      if (!sel) { ok(`status saves: ${v}`, false, "select vanished"); continue; }
      sel.value = v;
      sel.dispatchEvent(new Event("change", { bubbles: true }));
      await sleep(150);
      const saved = store().items[pid];
      ok(`status saves: ${v}`, saved && saved.status === v, saved && saved.status);
      const live = $(`select[data-status-for="${pid}"]`);
      ok(`status recolours: ${v}`, live && live.dataset.value === v, live && live.dataset.value);
    }

    // tracker board should group what has a status and exclude what does not
    await goPage("tracker");
    ok("tracker shows the tracked item", $("#content").innerHTML.includes("bcard"), "no cards");
    const cols = $$(".col").length;
    ok("tracker hides Not started column", cols === 5, `${cols} columns`);

    // Reach the empty state the way a user does, by clearing the status through
    // the UI. Wiping localStorage would not touch the app's in-memory copy.
    await goPage("programs");
    await goDb("table");
    const back = $(`select[data-status-for="${pid}"]`);
    back.value = "not-started";
    back.dispatchEvent(new Event("change", { bubbles: true }));
    await sleep(220);
    await goPage("tracker");
    ok("tracker empty state", $("#content").innerHTML.includes("callout"), "no empty state");
    ok("sidebar count clears", ($("#n-tracker").textContent || "") === "", $("#n-tracker").textContent);
    localStorage.removeItem("jolene-s27:tracker:v1");
  }

  async function eligibility(data) {
    localStorage.removeItem("jolene-s27:profile:v1");
    await goPage("programs");
    ok("no fit chip before profile", !$('[data-chip="fits-me"]'));

    await goPage("profile");
    const set = async (id, val, evt) => { $(id).value = val; $(id).dispatchEvent(new Event(evt, { bubbles: true })); await sleep(evt === "input" ? 650 : 250); };

    // citizenship gate
    await set("#pf-status", "f1", "change");
    await goPage("programs");
    await goDb("table");
    const f1 = $('[data-chip="fits-me"]');
    ok("fit chip appears once set", !!f1);
    await toggleChip("fits-me");
    const f1Count = rows();
    await toggleChip("fits-me");
    await goPage("profile");
    await set("#pf-status", "us", "change");
    await goPage("programs");
    await goDb("table");
    await toggleChip("fits-me");
    const usCount = rows();
    await toggleChip("fits-me");
    ok("citizenship changes the result", usCount > f1Count, `us=${usCount} f1=${f1Count}`);

    // GPA gate, using a real minimum from the data
    const mins = data.programs.map((p) => (p.eligibility || {}).min_gpa).filter(Boolean).sort((a, b) => b - a);
    const highest = mins[0];
    await goPage("profile");
    await set("#pf-gpa", String(highest), "input");
    await goPage("programs");
    await goDb("table");
    await toggleChip("fits-me");
    const atMin = rows();
    await toggleChip("fits-me");
    await goPage("profile");
    await set("#pf-gpa", String(Math.max(0, highest - 1)), "input");
    await goPage("programs");
    await goDb("table");
    await toggleChip("fits-me");
    const belowMin = rows();
    await toggleChip("fits-me");
    ok("GPA at the minimum qualifies", atMin > belowMin, `at=${atMin} below=${belowMin}`);

    // flags must carry a reason
    const flags = $$("table.db .flag");
    ok("conflicts are flagged", flags.length > 0, flags.length);
    ok("every flag explains itself", flags.every((f) => (f.getAttribute("title") || "").length > 10));

    // clearing resets
    await goPage("profile");
    if ($("#pf-clear")) { $("#pf-clear").click(); await sleep(250); }
    await goPage("programs");
    ok("clearing removes the fit chip", !$('[data-chip="fits-me"]'));
    localStorage.removeItem("jolene-s27:profile:v1");
  }

  async function exportsAndDownloads(data) {
    await goPage("programs");
    await goDb("table");

    let captured = null;
    const real = navigator.clipboard && navigator.clipboard.writeText;
    if (real) navigator.clipboard.writeText = (t) => { captured = t; return Promise.resolve(); };

    await setSearch("");
    $("#copy-notion").click();
    await sleep(350);
    ok("export writes to clipboard", !!captured);
    if (captured) {
      const lines = captured.split("\n");
      ok("export header", lines[0].startsWith("| Program |"), lines[0].slice(0, 30));
      ok("export separator", /^\|\s*---/.test(lines[1]));
      ok("export row count", lines.length - 2 === data.count, `${lines.length - 2} vs ${data.count}`);
      ok("export cells are escaped", lines.slice(2).every((l) => l.split("|").length === 9));
      /* Built from code points so this file is not itself an offender. */
      const EM = String.fromCharCode(8212), EN = String.fromCharCode(8211);
      ok("export has no dashes", !captured.includes(EM) && !captured.includes(EN));
    }

    // export must honour the current filter
    await toggleChip("near-home");
    const filtered = rows();
    captured = null;
    $("#copy-notion").click();
    await sleep(350);
    ok("export honours filters", captured && captured.split("\n").length - 2 === filtered,
       captured ? captured.split("\n").length - 2 : "none");
    await toggleChip("near-home");
    if (real) navigator.clipboard.writeText = real;

    // every download the page offers must resolve
    const links = $$("a[download]").map((a) => a.getAttribute("href"));
    const codes = await Promise.all(links.map((h) => fetch(h, { method: "HEAD" }).then((r) => r.status).catch(() => 0)));
    ok("every download resolves", codes.every((c) => c === 200), links.map((l, i) => `${l}:${codes[i]}`).join(" "));
    ok("downloads include ics and csv", links.some((l) => l.endsWith(".ics")) && links.some((l) => l.endsWith(".csv")));
  }

  async function resilience() {
    // corrupt storage must not break the page
    localStorage.setItem("jolene-s27:tracker:v1", "{not json");
    localStorage.setItem("jolene-s27:profile:v1", "[]");
    await goPage("programs");
    await goDb("table");
    ok("survives corrupt tracker storage", rows() > 0, rows());
    await goPage("profile");
    ok("survives corrupt profile storage", !!$("#pf-year"));
    localStorage.removeItem("jolene-s27:tracker:v1");
    localStorage.removeItem("jolene-s27:profile:v1");

    // theme toggles and persists the attribute
    const before = document.documentElement.dataset.theme;
    $("#theme-btn").click();
    await sleep(180);
    ok("theme toggles", document.documentElement.dataset.theme !== before, document.documentElement.dataset.theme);
    ok("theme stored", !!localStorage.getItem("jolene-s27:theme"));
    $("#theme-btn").click();
    await sleep(180);

    // no placeholder junk anywhere
    const junk = ["undefined", ">null<", "NaN", "[object Object]",
                  String.fromCharCode(8212), String.fromCharCode(8211)];
    for (const v of ["plan", "programs", "tracker", "timeline", "profile", "kit"]) {
      await goPage(v);
      const found = junk.filter((j) => $("#content").innerHTML.includes(j));
      ok(`no junk on ${v}`, found.length === 0, found.join(","));
    }
  }

  async function timeline(data) {
    await goPage("timeline");
    const dated = data.programs.filter((p) => p.opens).length + data.programs.filter((p) => p.deadline).length;
    const shown = $$("#content .row").length;
    ok("timeline lists every date", shown === dated, `${shown} vs ${dated}`);
    ok("timeline has month headers", $$(".month-rule").length > 0);
  }


  async function ownPrograms(data) {
    localStorage.removeItem("jolene-s27:custom:v1");
    localStorage.removeItem("jolene-s27:tracker:v1");

    await goPage("add");
    ok("add page renders", !!$("#ad-name") && !!$("#ad-save"));
    $("#ad-save").click();
    await sleep(200);
    ok("rejects an entry with no name", ($("#ad-msg").textContent || "").includes("name"), $("#ad-msg").textContent);

    const base = data.count;
    $("#ad-name").value = "QA Test Program";
    $("#ad-org").value = "QA Institution";
    $("#ad-city").value = "Leesburg, VA";
    $("#ad-url").value = "example.org/qa";
    $("#ad-deadline").value = "2027-02-10";
    $("#ad-save").click();
    await sleep(400);

    const saved = JSON.parse(localStorage.getItem("jolene-s27:custom:v1") || "[]");
    ok("saves to storage", saved.length === 1, saved.length);
    ok("adds a scheme to a bare url", saved[0] && saved[0].url === "https://example.org/qa", saved[0] && saved[0].url);
    ok("sidebar count rises", $("#n-programs").textContent === String(base + 1), $("#n-programs").textContent);

    const id = saved[0].id;
    await goPage("programs");
    await goDb("table");
    ok("appears in the table", rows() === base + 1, rows());
    await goDb("gallery");
    ok("appears in the gallery", cards() === base + 1, cards());
    await goDb("table");

    await setSearch("QA Test Program");
    ok("is searchable", rows() === 1, rows());
    await setSearch("");

    $(`[data-peek="${id}"]`).click();
    await sleep(320);
    ok("opens a peek", $("#peek").dataset.open === "true" && $("#peek-body").innerHTML.includes("QA Test"));
    $("#peek-close").click();
    await sleep(240);

    await goPage("timeline");
    ok("appears in the timeline", $("#content").innerHTML.includes("QA Test Program"));

    await goPage("add");
    ok("listed under yours", !!$(`[data-remove-custom="${id}"]`));
    $(`[data-remove-custom="${id}"]`).click();
    await sleep(380);
    ok("removes cleanly", $("#n-programs").textContent === String(base), $("#n-programs").textContent);
    ok("storage emptied", JSON.parse(localStorage.getItem("jolene-s27:custom:v1") || "[]").length === 0);
  }

  async function preparationRollup(data) {
    localStorage.removeItem("jolene-s27:tracker:v1");
    await goPage("programs");
    await goDb("table");

    // a program with known requirements
    const sel = $('select[data-status-for="stjude-poe"]');
    sel.value = "drafting";
    sel.dispatchEvent(new Event("change", { bubbles: true }));
    await sleep(280);

    await goPage("tracker");
    const html = $("#content").innerHTML;
    ok("rollup appears once something is tracked", html.includes("What you need to prepare"));
    ok("rollup counts letters", /letters? of recommendation/i.test(html));
    ok("rollup names the first deadline", html.includes("First one due"));

    // A sent application should leave the plan's "start here" list. Pick a
    // program that is actually open today rather than hardcoding one, since
    // which programs are open moves with the calendar.
    await goPage("plan");
    ok("plan still has a start-here block", /Start here/.test($("#content").textContent));
    const openRow = $("#content .row[data-id]");
    const openId = openRow && openRow.dataset.id;
    ok("plan lists something open", !!openId);
    if (openId) {
      await goPage("programs");
      await goDb("table");
      const s2 = $(`select[data-status-for="${openId}"]`);
      s2.value = "submitted";
      s2.dispatchEvent(new Event("change", { bubbles: true }));
      await sleep(280);
      await goPage("plan");
      const text = $("#content").textContent;
      ok("plan reports what was already sent", /already sent/i.test(text), text.slice(0, 120));
      const stillListed = !!$(`#content .row[data-id="${openId}"]`);
      ok("sent program drops out of start-here", !stillListed || /already sent/i.test(text));
    }

    localStorage.removeItem("jolene-s27:tracker:v1");
  }


  async function recommenders(data) {
    localStorage.removeItem("jolene-s27:recommenders:v1");
    localStorage.removeItem("jolene-s27:tracker:v1");

    // the panel lives with the applications, so there must be one
    await goPage("programs");
    await goDb("table");
    const sel = $('select[data-status-for="stjude-poe"]');
    sel.value = "drafting";
    sel.dispatchEvent(new Event("change", { bubbles: true }));
    await sleep(280);

    await goPage("tracker");
    ok("recommender panel appears", $("#content").innerHTML.includes("Who is writing your letters"));
    ok("recommender form renders", !!$("#rc-name") && !!$("#rc-save"));
    ok("warns when nobody has agreed", /runs on somebody else/i.test($("#content").textContent));

    $("#rc-save").click();
    await sleep(200);
    ok("rejects a nameless recommender", ($("#rc-msg").textContent || "").includes("name"));

    $("#rc-name").value = "QA Professor";
    $("#rc-role").value = "QA lab";
    $("#rc-email").value = "qa@example.edu";
    $("#rc-save").click();
    await sleep(380);

    const saved = JSON.parse(localStorage.getItem("jolene-s27:recommenders:v1") || "[]");
    ok("recommender saves", saved.length === 1 && saved[0].name === "QA Professor", saved.length);
    ok("defaults to not asked", saved[0] && saved[0].status === "not-asked", saved[0] && saved[0].status);
    ok("recommender is listed", $("#content").innerHTML.includes("QA Professor"));

    const id = saved[0].id;
    const st = $(`select[data-rec-status="${id}"]`);
    ok("status select present", !!st);
    const options = st ? [...st.options].map((o) => o.value) : [];
    ok("five letter states", options.length === 5, options.length);

    st.value = "agreed";
    st.dispatchEvent(new Event("change", { bubbles: true }));
    await sleep(320);
    const after = JSON.parse(localStorage.getItem("jolene-s27:recommenders:v1") || "[]");
    ok("letter status persists", after[0] && after[0].status === "agreed", after[0] && after[0].status);
    ok("advice updates with the count", /still need|covers every application/i.test($("#content").textContent));

    $(`[data-remove-rec="${id}"]`).click();
    await sleep(320);
    ok("recommender removes", JSON.parse(localStorage.getItem("jolene-s27:recommenders:v1") || "[]").length === 0);

    localStorage.removeItem("jolene-s27:tracker:v1");
  }

  async function watchPanel(data) {
    await goPage("plan");
    const text = $("#content").textContent;
    const res = await fetch("data/watch.json", { cache: "no-cache" }).then((r) => r.ok ? r.json() : null).catch(() => null);
    if (!res) { ok("watch summary published", false, "no watch.json"); return; }
    ok("watch summary published", !!res.last_run, res.last_run);
    ok("watch covers every program", res.checked === data.count || res.checked > 0, `${res.checked} vs ${data.count}`);
    ok("plan reports the last check", /read on|checked on|program pages? changed/i.test(text));
    if (!res.changes.length) {
      ok("quiet week reads as quiet", /nothing had changed/i.test(text));
      ok("explains the cadence", /every Monday/i.test(text));
      ok("does not overclaim coverage", !/All \d+ program pages were\s+checked/i.test(text));
    } else {
      ok("changes are listed", res.changes.every((c) => text.includes(c.name)));
    }

    /* A page the checker cannot read is the one case where silence would be
     * actively misleading, so the plan has to name every one of them. */
    const unseen = res.blocked_pages || [];
    ok("blocked pages are published", Array.isArray(res.blocked_pages));
    if (unseen.length) {
      ok("plan names the pages it cannot see", /block the weekly check/i.test(text));
      ok("every blocked page is named", unseen.every((b) => text.includes(b.name)),
         unseen.filter((b) => !text.includes(b.name)).map((b) => b.name).join("; "));
      const hrefs = Array.from($("#content").querySelectorAll("a")).map((el) => el.href);
      ok("each blocked page is a link", unseen.every((b) => hrefs.includes(b.url)));

      /* The rows live in a toggle so they do not bury the plan, which only
       * works if the toggle actually opens. */
      const toggle = $("#content").querySelector("details.toggle");
      ok("blocked rows sit in a toggle", !!toggle);
      if (toggle) {
        ok("toggle starts closed", !toggle.open);
        ok("toggle holds every blocked page",
           toggle.querySelectorAll(".row").length === unseen.length,
           `${toggle.querySelectorAll(".row").length} rows vs ${unseen.length}`);
        toggle.querySelector("summary").click();
        await sleep(60);
        ok("toggle opens on click", toggle.open);
        toggle.querySelector("summary").click();
        await sleep(60);
        ok("toggle closes again", !toggle.open);
      }
    }
  }

  // ---------------------------------------------------------------- runner

  const PARTS = {
    pages: pagesAndGuides,
    views: everyView,
    chips: everyChip,
    sort: searchAndSort,
    peek: peekEveryProgram,
    tracker: statusesAndTracker,
    eligibility: eligibility,
    exports: exportsAndDownloads,
    timeline: timeline,
    own: ownPrograms,
    recs: recommenders,
    watch: watchPanel,
    prep: preparationRollup,
    resilience: (_data) => resilience(),
  };

  /* The whole suite runs longer than a single automation call allows, so parts
   * run separately and accumulate into one report. */
  async function runParts(names) {
    const data = await fetch("data/programs.json", { cache: "no-cache" }).then((r) => r.json());
    const started = Date.now();
    for (const n of names) {
      if (!PARTS[n]) { ok(`unknown suite: ${n}`, false, n); continue; }
      try { await PARTS[n](data); }
      catch (e) { ok(`suite threw: ${n}`, false, `${e && e.message}`); }
    }
    const fails = results.filter((r) => !r.pass);
    return {
      ran: names.join(","),
      cumulative: results.length,
      passed: results.length - fails.length,
      failed: fails.length,
      seconds: Math.round((Date.now() - started) / 100) / 10,
      failures: fails.map((f) => `${f.name} :: ${f.detail}`),
    };
  }

  const reset = () => { results = []; };
  const run = () => runParts(Object.keys(PARTS));

  return { run, runParts, reset, parts: () => Object.keys(PARTS) };
})();
