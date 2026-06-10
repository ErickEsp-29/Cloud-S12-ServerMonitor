const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = 3000;

// Archivos estáticos (el dashboard HTML)
app.use(express.static('public'));

// Redirigir /api/* al Servicio B (procesamiento)
app.use('/api', createProxyMiddleware({
  target: 'http://servicio-b:8000',
  changeOrigin: true,
  on: {
    error: (err, req, res) => {
      res.status(502).json({ error: 'Servicio B no disponible' });
    }
  }
}));

app.listen(PORT, () => {
  console.log(`✅ Servicio A (Frontend/Gateway) corriendo en puerto ${PORT}`);
  console.log(`   Dashboard disponible en http://localhost:${PORT}`);
});