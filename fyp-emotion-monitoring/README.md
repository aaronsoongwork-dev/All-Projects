# EmotionMonitor

Multimodal speech emotion recognition — a React frontend talking to a FastAPI
backend that serves a trained audio+text fusion model, with Supabase for auth
and persistence.

```
                    ┌─────────────────┐
                    │  React Frontend │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ (1) live WebSocket audio    │ (2) auth
              │     + file upload           │
              ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │     FastAPI      │  writes  │    Supabase      │
    │ Whisper + WavLM  │─────────▶│ Postgres · Auth  │
    │   + emoberta     │  reports │ Storage · JWT    │
    └──────────────────┘          └──────────────────┘
```

The frontend never writes reports directly — FastAPI owns persistence using
the service role key, so results can't be forged from the browser. The browser
only uses Supabase for signing in; it sends the resulting JWT to FastAPI, which
verifies it on every request.

## Running it locally

You need **two terminals**. Everything below works without a trained
checkpoint or a Supabase project — see "Degraded modes" for what that costs.

### 1. Backend

**Python 3.12 is required** — `torch==2.5.1` publishes no wheels for 3.13+,
so a newer interpreter fails at `pip install` with a confusing "no matching
distribution" error. If `python3.12 --version` doesn't work:
`brew install python@3.12` (macOS), `sudo apt install python3.12` (Ubuntu),
or grab it from python.org (Windows).

```bash
cd backend
python3.12 -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# ffmpeg is required for decoding uploaded audio:
#   macOS:  brew install ffmpeg
#   Ubuntu: sudo apt install ffmpeg
#   Windows: choco install ffmpeg

cp .env.example .env      # defaults are set up for local dev — works as-is
uvicorn main:app --reload --port 8000
```

The first startup takes a minute or so — numba compiles a cache on its first
import. Later starts are quick.

Check it: <http://localhost:8000/api/health> should return JSON, and
<http://localhost:8000/docs> gives you a browsable API.

### 2. Frontend

```bash
pnpm install
cp .env.example .env      # works as-is for local dev
pnpm dev
```

Open <http://localhost:5173>. Vite proxies `/api` and `/ws` to port 8000, so
there's no CORS setup and no URLs to configure.

## Degraded modes

The app is designed to run before every piece exists, and to *say so* rather
than quietly showing fake data as if it were real.

| Missing | What happens | How the UI shows it |
|---|---|---|
| Trained checkpoint | `USE_MOCK_MODEL` kicks in — randomised predictions, canned transcripts | Amber "Mock mode" banner, "Placeholder" tag on results |
| Supabase credentials | Login accepts anything; reports aren't saved | "Local Development Mode" box on the login page |
| Backend not running | No analysis possible | Red "Backend unreachable" banner, controls disabled |

**Mock mode is on by default** in `.env.example`. Turn it off once you have a
checkpoint:

```bash
mkdir -p backend/checkpoints
cp /path/to/outputs/models/iemocap_stage2_model.pt backend/checkpoints/iemocap_stage2_model.pt
# then set USE_MOCK_MODEL=false in backend/.env
```

Verify the model on its own before involving the API — much faster to debug:

```bash
cd backend && python test_model_loads.py path/to/clip.wav
```

## Going to real auth

1. Create a Supabase project.
2. In `backend/.env`: set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
   `SUPABASE_JWT_SECRET`, and **`DISABLE_AUTH=false`**.
3. In `.env` (frontend): set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
4. In the Supabase dashboard, create:
   - table `emotion_reports` — `id` (uuid, pk, default `gen_random_uuid()`),
     `user_id` (uuid → `auth.users`), `data` (jsonb),
     `created_at` (timestamptz, default `now()`)
   - storage bucket `audio-uploads`
   - RLS on `emotion_reports`: `user_id = auth.uid()` for select

> `DISABLE_AUTH=true` accepts every request without a token. It exists so the
> team can work before Supabase is set up — never deploy with it on. The
> backend prints a warning at startup while it's enabled.

## Layout

```
backend/
  main.py                  REST routes, startup, static hosting
  websocket_handler.py     live session protocol
  auth.py                  Supabase JWT verification (+ dev bypass)
  storage.py               Supabase reads/writes (no-ops when unconfigured)
  config.py                all env-driven settings
  models/
    emotion_model.py       FusionEmotionModel + load/predict
    stt.py                 Whisper wrapper
    audio_utils.py         format conversion, windowing, resampling

frontend/src/app/
  api/                     ← everything that talks to the backend
    types.ts               wire types, mirrors FastAPI responses
    adapters.ts            backend labels → UI shapes  (see note below)
    client.ts              REST calls
    liveSession.ts         mic capture + live WebSocket
    reports.ts             stored reports → Session objects
  contexts/                auth + session-store hydration
  components/              pages
```

## Known gaps

- **The UI has six emotions; the model predicts four.** `fearful` and
  `surprised` are placeholders and always read 0. The mapping is isolated in
  `frontend/src/app/api/adapters.ts` — that file's header explains exactly what
  to change when narrowing the UI to four.
- **There are no per-modality emotion predictions.** The architecture has a
  single classifier over the fused vector, so "audio says X, text says Y" isn't
  something this model can produce. The UI instead shows the model's real
  learned trust weighting between the two branches. Adding genuine per-modality
  outputs means auxiliary heads at training time, not a backend change.
- **Live audio is uncompressed** PCM16 (~32 KB/s upstream). Fine locally; would
  need Opus framing over a slow network.
