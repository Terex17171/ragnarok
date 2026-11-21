# Ragnarok Monster Rush

## Deploy on Render
1. Create a GitHub repository and upload index.html, server.py, and render.yaml to its root.
2. In https://dashboard.render.com/ select New > Blueprint and connect the repository.
3. Review and deploy. Open the public URL shown by Render.
4. Create a room and copy its invite link to friends.

No API keys or third-party Python packages required. Monster names are fetched from rAthena at startup; sprites are fetched from Divine Pride by browsers. External availability and sprite coverage are not guaranteed. Rooms are in memory and disappear on restart. Use a single server instance. Free hosting may sleep when idle.

Local: python server.py then open http://localhost:8000.
