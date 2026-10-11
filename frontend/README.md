# VaultGuard Frontend

This folder contains the browser-based client UI for VaultGuard:
- HTML5 & CSS3 with modern cybersecurity dark theme and glassmorphism.
- Vanilla JavaScript utilizing Fetch API with JWT Bearer authentication.
- **Zero-knowledge on the client side**: All encryption, decryption, Shamir Secret Sharing, and key reconstructions are strictly performed by the backend service.

## Running Locally

You can serve this frontend using any simple static HTTP server:

```bash
# Using Python
cd frontend
python -m http.server 5500

# Or using Node http-server / VS Code Live Server
npx serve . -p 5500
```
Then visit `http://127.0.0.1:5500` in your browser.
