(() => {
    'use strict';

    const { id, columns } = window.DASHBOARD;
    const PAGE = 15;
    const NUMERIC = new Set(['integer', 'real']);
    const PALETTE = ['#2563eb', '#16a34a', '#f59e0b', '#dc2626', '#7c3aed', '#0891b2', '#db2777', '#65a30d', '#ea580c', '#475569'];

    const $ = (sel) => document.querySelector(sel);
    const groupBy = $('#groupBy'), grain = $('#grain'), metric = $('#metric'), agg = $('#agg'), chartType = $('#chartType');
    const state = { filters: {}, offset: 0, search: '', chart: null };

    const label = (name) => (columns.find((c) => c.name === name) || {}).label || name;
    const fmt = (v) => (v === null || v === undefined ? '' : typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(v));

    function el(tag, text, cls) {
        const e = document.createElement(tag);
        if (text !== undefined) e.textContent = text; // textContent: user data is never parsed as HTML
        if (cls) e.className = cls;
        return e;
    }

    function query(params) {
        const q = new URLSearchParams({ id, ...params });
        Object.entries(state.filters).forEach(([k, v]) => q.append(`filter[${k}]`, v));
        return q.toString();
    }

    async function api(action, params = {}) {
        const res = await fetch(`api.php?action=${action}&${query(params)}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Request failed');
        return data;
    }

    function fillControls() {
        // Group-by options: categories with few distinct values first (they make readable charts), then dates, then the rest.
        const rank = (c) => (c.type === 'text' && c.distinct >= 2 && c.distinct <= 30 ? 0 : c.type === 'date' ? 1 : 2);
        [...columns].sort((a, b) => rank(a) - rank(b) || a.distinct - b.distinct)
            .forEach((c) => groupBy.append(new Option(c.label, c.name)));
        metric.append(new Option('(row count)', ''));
        columns.filter((c) => NUMERIC.has(c.type)).forEach((c) => metric.append(new Option(c.label, c.name)));
        // Defaults: best category column, and the last numeric column (often the "total"/"revenue" measure)
        groupBy.selectedIndex = 0;
        const nums = columns.filter((c) => NUMERIC.has(c.type));
        if (nums.length) metric.value = nums[nums.length - 1].name;
        syncGrain();
    }

    function syncGrain() {
        const col = columns.find((c) => c.name === groupBy.value);
        $('#grainWrap').hidden = !(col && col.type === 'date');
        const dateCol = col && col.type === 'date';
        if (dateCol) chartType.value = 'line';
    }

    function renderChips() {
        const box = $('#chips');
        box.replaceChildren();
        Object.entries(state.filters).forEach(([k, v]) => {
            const chip = el('button', `${label(k)}: ${v}  ✕`, 'chip');
            chip.addEventListener('click', () => { delete state.filters[k]; refresh(); });
            box.append(chip);
        });
    }

    async function renderKpis() {
        const s = await api('summary');
        const box = $('#kpis');
        box.replaceChildren();
        const tile = (title, value, sub) => {
            const t = el('div', undefined, 'kpi');
            t.append(el('div', title, 'kpi-title'), el('div', value, 'kpi-value'));
            if (sub) t.append(el('div', sub, 'kpi-sub'));
            box.append(t);
        };
        tile('Rows', fmt(s.total_rows));
        s.columns.slice(0, 3).forEach((c) => tile(c.label, fmt(c.sum), `avg ${fmt(c.avg)} · min ${fmt(c.min)} · max ${fmt(c.max)}${c.missing ? ` · ${c.missing} missing` : ''}`));
    }

    async function renderChart() {
        const useMetric = metric.value !== '';
        const data = await api('group', {
            group: groupBy.value,
            metric: metric.value,
            agg: useMetric ? agg.value : 'count',
            grain: grain.value,
        });
        const type = chartType.value;
        const title = useMetric ? `${agg.options[agg.selectedIndex].text} of ${label(metric.value)}` : 'Row count';

        if (state.chart) state.chart.destroy();
        state.chart = new Chart($('#chart'), {
            type,
            data: {
                labels: data.labels,
                datasets: [{
                    label: title,
                    data: data.values,
                    backgroundColor: type === 'doughnut' ? data.labels.map((_, i) => PALETTE[i % PALETTE.length]) : PALETTE[0],
                    borderColor: PALETTE[0],
                    tension: 0.25,
                }],
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { display: type === 'doughnut' }, title: { display: true, text: `${title} by ${label(groupBy.value)}` } },
                onClick: (_evt, items) => {
                    const gcol = columns.find((c) => c.name === groupBy.value);
                    const canFilter = gcol.type !== 'date' || grain.value === 'month';
                    if (!items.length || !canFilter) return;
                    state.filters[groupBy.value] = data.labels[items[0].index];
                    refresh();
                },
            },
        });
    }

    async function renderTable() {
        const data = await api('rows', { q: state.search, limit: PAGE, offset: state.offset });
        const table = $('#table');
        table.replaceChildren();
        const head = el('tr');
        columns.forEach((c) => head.append(el('th', c.label, NUMERIC.has(c.type) ? 'num' : '')));
        table.append(el('thead')).firstChild.append(head);
        const body = el('tbody');
        data.rows.forEach((r) => {
            const tr = el('tr');
            columns.forEach((c) => tr.append(el('td', fmt(r[c.name]), NUMERIC.has(c.type) ? 'num' : '')));
            body.append(tr);
        });
        table.append(body);

        const from = data.total ? state.offset + 1 : 0;
        $('#pageInfo').textContent = `${from}–${Math.min(state.offset + PAGE, data.total)} of ${data.total.toLocaleString()}`;
        $('#prev').disabled = state.offset === 0;
        $('#next').disabled = state.offset + PAGE >= data.total;
        $('#export').href = `export.php?${query({})}`;
    }

    async function refresh() {
        renderChips();
        try {
            await Promise.all([renderKpis(), renderChart(), renderTable()]);
        } catch (err) {
            alert(err.message);
        }
    }

    let timer;
    $('#search').addEventListener('input', (e) => {
        clearTimeout(timer);
        timer = setTimeout(() => { state.search = e.target.value.trim(); state.offset = 0; renderTable(); }, 250);
    });
    $('#prev').addEventListener('click', () => { state.offset = Math.max(0, state.offset - PAGE); renderTable(); });
    $('#next').addEventListener('click', () => { state.offset += PAGE; renderTable(); });
    groupBy.addEventListener('change', () => { syncGrain(); renderChart(); });
    [grain, metric, agg, chartType].forEach((c) => c.addEventListener('change', renderChart));

    fillControls();
    refresh();
})();
