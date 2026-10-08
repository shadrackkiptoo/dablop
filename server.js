import express from 'express';
import cors from 'cors';
import { createClient } from '@supabase/supabase-js';

const app = express();
const PORT = Number(process.env.PORT || 3000);

app.use(cors());
app.use(express.json({ limit: '2mb' }));

const supabaseUrl = (process.env.SUPABASE_URL || '').trim();
const supabaseKey = (process.env.SUPABASE_SERVICE_ROLE_KEY || '').trim();
const clientAuthSecret = (process.env.CLIENT_AUTH_SECRET || '').trim();
const memoryLogs = [];
const supabase = supabaseUrl && supabaseKey ? createClient(supabaseUrl, supabaseKey) : null;

if (!supabaseUrl || !supabaseKey) {
  console.warn('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are not set. Falling back to in-memory log storage.');
}

if (!clientAuthSecret) {
  console.warn('CLIENT_AUTH_SECRET is not set. Remote clients will be rejected until it is configured.');
}

const isAuthorized = (req) => {
  const authHeader = req.headers.authorization || '';
  return Boolean(clientAuthSecret) && authHeader === `Bearer ${clientAuthSecret}`;
};

app.post('/api/telemetry', async (req, res) => {
  if (!isAuthorized(req)) {
    return res.status(401).json({ error: 'Unauthorized Tor client connection' });
  }

  const payload = {
    ...req.body,
    created_at: new Date().toISOString(),
  };

  try {
    if (supabase) {
      const { error } = await supabase.from('remote_logs').insert([payload]);
      if (error) {
        throw error;
      }
    } else {
      memoryLogs.unshift(payload);
      if (memoryLogs.length > 200) {
        memoryLogs.length = 200;
      }
    }

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Telemetry insert failed:', error);
    return res.status(500).json({ error: error.message || 'Telemetry storage failed' });
  }
});

app.get('/health', (req, res) => {
  res.status(200).json({ ok: true, service: 'tor-render-pipeline' });
});

app.get('/', (req, res) => {
  res.status(200).json({ ok: true, service: 'tor-render-pipeline', mode: 'api-only' });
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
