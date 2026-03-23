# CHC TRANSPORT SERVICE SAC — Web

Sitio web de transporte terrestre y operador turístico.

## Desarrollo local

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
$env:FLASK_DEBUG="true"; python app.py
```

Abre http://127.0.0.1:5050

## Producción / Vercel

1. **Configura la variable de entorno** `SECRET_KEY` en Vercel (Dashboard → Settings → Environment Variables):
   - Genera una clave segura: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Añade `SECRET_KEY` con ese valor

2. **Despliega**:
   ```bash
   vercel
   ```
   O conecta tu repositorio Git en vercel.com

3. **Nota sobre datos**: En Vercel, las reservas y contactos se guardan en `/tmp` (solo durante la sesión del servidor). Para persistencia real, integra una base de datos (Vercel Postgres, Supabase, etc.).

## Seguridad

- **CSRF**: Protección activa en formularios
- **Rate limiting**: 5 peticiones/minuto en APIs de reserva y contacto
- **Validación**: Campos sanitizados y validados en servidor
- **Debug**: Desactivado en producción (`FLASK_DEBUG=0`)
