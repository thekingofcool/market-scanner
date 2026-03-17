/**
 * Cloudflare Worker - Market Scanner Static Host
 * Serves frontend/data/market.json and static assets
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    let path = url.pathname;

    // Default to index.html
    if (path === "/" || path === "") {
      path = "/index.html";
    }

    // Serve from static assets (KV or Assets binding)
    try {
      // If using Cloudflare Pages, this is automatic.
      // For Workers with Assets:
      const asset = await env.ASSETS.fetch(request);
      
      // Add CORS and cache headers for JSON data
      const headers = new Headers(asset.headers);
      if (path.endsWith(".json")) {
        headers.set("Cache-Control", "public, max-age=3600"); // 1 hour cache
        headers.set("Access-Control-Allow-Origin", "*");
      }
      
      return new Response(asset.body, {
        status: asset.status,
        headers,
      });
    } catch (e) {
      return new Response("Not Found", { status: 404 });
    }
  },
};
