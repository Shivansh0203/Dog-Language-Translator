import ssl
from aiohttp import web

# Serve the existing frontend directory without modifying it.
FRONTEND_DIR = "frontend"

app = web.Application()

# Serve all existing frontend files.
app.router.add_static("/", FRONTEND_DIR, show_index=True)

# HTTPS configuration
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    "certs/pawai-cert.pem",
    "certs/pawai-key.pem"
)

if __name__ == "__main__":
    print("PawAI HTTPS frontend running at:")
    print("https://10.77.184.23:5501")
    print()
    print("Press CTRL+C to stop.")

    web.run_app(
        app,
        host="0.0.0.0",
        port=5501,
        ssl_context=ssl_context
    )