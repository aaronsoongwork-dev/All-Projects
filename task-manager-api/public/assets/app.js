(() => {
    'use strict';

    const STATUSES = [
        { key: 'todo', title: 'To do' },
        { key: 'doing', title: 'In progress' },
        { key: 'done', title: 'Done' },
    ];
    const state = { user: null, csrf: '', tasks: [], users: [] };
    const app = document.getElementById('app');

    // ---------- tiny helpers ----------
    // h('div', {class:'x', onclick: fn}, 'text', childNode): builds DOM safely (text is never parsed as HTML).
    function h(tag, props = {}, ...children) {
        const node = document.createElement(tag);
        for (const [k, v] of Object.entries(props)) {
            if (v === false || v === null || v === undefined) continue;
            if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
            else if (k === 'class') node.className = v;
            else if (k === 'value') node.value = v;
            else node.setAttribute(k, v === true ? '' : v);
        }
        for (const c of children.flat()) {
            if (c === null || c === undefined || c === false) continue;
            node.append(c.nodeType ? c : document.createTextNode(String(c)));
        }
        return node;
    }

    function toast(message, isError = false) {
        const t = document.getElementById('toast');
        t.textContent = message;
        t.className = 'toast' + (isError ? ' error' : '');
        t.hidden = false;
        clearTimeout(toast.timer);
        toast.timer = setTimeout(() => { t.hidden = true; }, 3500);
    }

    async function api(method, path, body) {
        const opts = { method, credentials: 'same-origin', headers: {} };
        if (method !== 'GET') {
            opts.headers['Content-Type'] = 'application/json';
            opts.headers['X-CSRF-Token'] = state.csrf;
            opts.body = JSON.stringify(body ?? {});
        }
        const res = await fetch(path, opts);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            const err = new Error(data.error || `Request failed (${res.status})`);
            err.fields = data.fields || {};
            err.status = res.status;
            throw err;
        }
        if (data.csrf) state.csrf = data.csrf;
        return data;
    }

    function errorText(err) {
        const extra = Object.values(err.fields || {}).join(' ');
        return extra ? `${err.message} ${extra}` : err.message;
    }

    // ---------- auth view ----------
    function renderAuth(mode = 'login') {
        const isLogin = mode === 'login';
        const msg = h('p', { class: 'alert', hidden: true });
        const form = h('form', { class: 'card auth', novalidate: true },
            h('h1', {}, isLogin ? 'Sign in' : 'Create account'),
            !isLogin && h('label', {}, 'Name', h('input', { name: 'name', autocomplete: 'name', required: true })),
            h('label', {}, 'Email', h('input', { name: 'email', type: 'email', autocomplete: 'email', required: true })),
            h('label', {}, 'Password', h('input', {
                name: 'password', type: 'password', required: true,
                autocomplete: isLogin ? 'current-password' : 'new-password',
            })),
            !isLogin && h('p', { class: 'muted small' }, '8-72 characters. The first account created becomes the admin.'),
            msg,
            h('button', { class: 'btn', type: 'submit' }, isLogin ? 'Sign in' : 'Sign up'),
            h('p', { class: 'muted small' },
                isLogin ? 'No account? ' : 'Have an account? ',
                h('a', { href: '#', onclick: (e) => { e.preventDefault(); renderAuth(isLogin ? 'register' : 'login'); } },
                    isLogin ? 'Create one' : 'Sign in'))
        );
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const body = Object.fromEntries(new FormData(form));
            try {
                const data = await api('POST', isLogin ? '/api/login' : '/api/register', body);
                state.user = data.user;
                await loadBoard();
            } catch (err) {
                msg.textContent = errorText(err);
                msg.hidden = false;
            }
        });
        app.replaceChildren(form);
        form.querySelector('input').focus();
    }

    // ---------- board view ----------
    async function loadBoard() {
        const [t, u] = await Promise.all([api('GET', '/api/tasks'), api('GET', '/api/users')]);
        state.tasks = t.tasks;
        state.users = u.users;
        renderBoard();
    }

    function renderHeader() {
        const who = document.getElementById('who');
        who.hidden = !state.user;
        who.replaceChildren();
        if (!state.user) return;
        who.append(
            `${state.user.name} `, h('span', { class: 'badge' }, state.user.role), ' ',
            state.user.role === 'admin' && h('button', { class: 'btn small ghost', onclick: openTeam }, 'Team'), ' ',
            h('button', { class: 'btn small ghost', onclick: signOut }, 'Sign out')
        );
    }

    function assigneeSelect(selected, name = 'assignee_id') {
        return h('select', { name },
            h('option', { value: '' }, 'Unassigned'),
            state.users.map((u) => h('option', { value: u.id, selected: u.id === selected }, u.name)));
    }

    function renderBoard() {
        renderHeader();

        const titleInput = h('input', { name: 'title', placeholder: 'New task title...', maxlength: '120', required: true });
        const assignee = assigneeSelect(null);
        const addForm = h('form', { class: 'row add' }, titleInput, assignee, h('button', { class: 'btn', type: 'submit' }, 'Add task'));
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await api('POST', '/api/tasks', { title: titleInput.value, assignee_id: assignee.value ? Number(assignee.value) : null });
                titleInput.value = '';
                await loadBoard();
            } catch (err) { toast(errorText(err), true); }
        });

        const columns = STATUSES.map((s) => column(s));
        app.replaceChildren(addForm, h('div', { class: 'board' }, columns));
    }

    function column({ key, title }) {
        const tasks = state.tasks.filter((t) => t.status === key);
        const list = h('div', { class: 'list', 'data-status': key });

        list.addEventListener('dragover', (e) => { e.preventDefault(); list.classList.add('over'); });
        list.addEventListener('dragleave', () => list.classList.remove('over'));
        list.addEventListener('drop', async (e) => {
            e.preventDefault();
            list.classList.remove('over');
            const id = Number(e.dataTransfer.getData('text/plain'));
            if (!id) return;
            // Index among the other cards = number of cards whose vertical midpoint is above the drop point.
            const others = [...list.querySelectorAll('.card-task')].filter((c) => Number(c.dataset.id) !== id);
            const position = others.filter((c) => {
                const r = c.getBoundingClientRect();
                return e.clientY > r.top + r.height / 2;
            }).length;
            try {
                await api('PATCH', `/api/tasks/${id}`, { status: key, position });
            } catch (err) { toast(errorText(err), true); }
            await loadBoard();
        });

        tasks.forEach((t) => list.append(card(t)));
        return h('section', { class: 'col' }, h('h2', {}, title, ' ', h('span', { class: 'count' }, tasks.length)), list);
    }

    function card(t) {
        const node = h('article', { class: 'card-task' + (t.can_edit ? '' : ' locked'), 'data-id': t.id, draggable: t.can_edit },
            h('div', { class: 'title' }, t.title),
            t.description && h('div', { class: 'desc' }, t.description),
            h('div', { class: 'meta' },
                h('span', {}, t.assignee_name ? `\u{1F464} ${t.assignee_name}` : 'Unassigned'),
                h('span', { class: 'muted' }, `by ${t.creator_name}`)),
            t.can_edit && h('div', { class: 'actions' },
                h('button', { class: 'btn small ghost', onclick: () => openEdit(t) }, 'Edit'),
                h('button', { class: 'btn small danger', onclick: () => removeTask(t) }, 'Delete'))
        );
        node.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', String(t.id));
            e.dataTransfer.effectAllowed = 'move';
            node.classList.add('dragging');
        });
        node.addEventListener('dragend', () => node.classList.remove('dragging'));
        return node;
    }

    async function removeTask(t) {
        if (!confirm(`Delete "${t.title}"?`)) return;
        try { await api('DELETE', `/api/tasks/${t.id}`); await loadBoard(); }
        catch (err) { toast(errorText(err), true); }
    }

    function openEdit(t) {
        const form = h('form', { method: 'dialog', class: 'edit' },
            h('h2', {}, 'Edit task'),
            h('label', {}, 'Title', h('input', { name: 'title', value: t.title, maxlength: '120', required: true })),
            h('label', {}, 'Description', h('textarea', { name: 'description', rows: '4', maxlength: '2000' }, t.description)),
            h('label', {}, 'Assignee', assigneeSelect(t.assignee_id)),
            // A plain dropdown also lets keyboard and touch users move tasks (drag & drop is mouse-only).
            h('label', {}, 'Status', h('select', { name: 'status' },
                STATUSES.map((s) => h('option', { value: s.key, selected: s.key === t.status }, s.title)))),
            h('div', { class: 'row end' },
                h('button', { class: 'btn ghost', type: 'button', onclick: () => dialog.close() }, 'Cancel'),
                h('button', { class: 'btn', type: 'submit' }, 'Save'))
        );
        const dialog = h('dialog', {}, form);
        dialog.addEventListener('close', () => dialog.remove());
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const f = new FormData(form);
            const body = {
                title: f.get('title'),
                description: f.get('description'),
                assignee_id: f.get('assignee_id') ? Number(f.get('assignee_id')) : null,
            };
            if (f.get('status') !== t.status) body.status = f.get('status');
            try { await api('PATCH', `/api/tasks/${t.id}`, body); dialog.close(); await loadBoard(); }
            catch (err) { toast(errorText(err), true); }
        });
        document.body.append(dialog);
        dialog.showModal();
    }

    function openTeam() {
        const rows = state.users.map((u) => {
            const select = h('select', {},
                ['member', 'admin'].map((r) => h('option', { value: r, selected: r === u.role }, r)));
            select.addEventListener('change', async () => {
                try { await api('PATCH', `/api/users/${u.id}`, { role: select.value }); toast('Role updated'); await loadBoard(); }
                catch (err) { select.value = u.role; toast(errorText(err), true); }
            });
            return h('tr', {}, h('td', {}, u.name), h('td', { class: 'muted' }, u.email || ''), h('td', {}, select));
        });
        const dialog = h('dialog', {},
            h('h2', {}, 'Team'),
            h('table', {}, h('tbody', {}, rows)),
            h('div', { class: 'row end' }, h('button', { class: 'btn', onclick: () => dialog.close() }, 'Close')));
        dialog.addEventListener('close', () => dialog.remove());
        document.body.append(dialog);
        dialog.showModal();
    }

    async function signOut() {
        await api('POST', '/api/logout');
        const me = await api('GET', '/api/me'); // fresh CSRF token for the next login
        state.user = null;
        renderHeader();
        renderAuth('login');
    }

    // ---------- boot ----------
    (async function init() {
        try {
            const me = await api('GET', '/api/me');
            state.user = me.user;
            if (state.user) await loadBoard();
            else { renderHeader(); renderAuth('login'); }
        } catch (err) {
            app.replaceChildren(h('p', { class: 'alert' }, 'Could not reach the API. ' + err.message));
        }
    })();
})();
