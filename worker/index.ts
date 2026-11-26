/**
 * api.alphacolorlab.com on Cloudflare: every request goes to a single container
 * running `sony-alpha-viet-mcp --http --read-only` (Dockerfile). The server is stateless
 * (stateless_http, read-only data-sample/), so one named instance is enough.
 */
import { DurableObject } from "cloudflare:workers";

interface Env {
  API: DurableObjectNamespace<ApiContainer>;
}

const PORT = 8080;
const IDLE_MS = 15 * 60 * 1000; // stop the container after 15 idle minutes
const READY_MS = 60 * 1000; // a cold start (Python imports) must finish within this

export class ApiContainer extends DurableObject<Env> {
  private starting: Promise<void> | null = null;

  private ensureRunning(): Promise<void> {
    const c = this.ctx.container!;
    if (c.running && !this.starting) return Promise.resolve();
    this.starting ??= (async () => {
      if (!c.running) {
        c.start({
          image: c.images.base,
          instance: "basic",
          enableInternet: false, // public mode never fetches URLs (SONY_VN_NO_NET)
          // the container sees Host "container"; let the MCP DNS-rebinding check accept it
          env: { SONY_VN_HOSTS: "container,container:*" },
        });
        c.monitor().catch((e) => console.error("container exited", e));
      }
      await c.setInactivityTimeout(IDLE_MS);
      const deadline = Date.now() + READY_MS;
      for (;;) {
        try {
          const r = await c.getTcpPort(PORT).fetch("http://container/");
          await r.body?.cancel();
          if (r.status < 500) return;
        } catch {
          // not listening yet
        }
        if (Date.now() > deadline) throw new Error("container not ready");
        await scheduler.wait(250);
      }
    })().finally(() => {
      this.starting = null;
    });
    return this.starting;
  }

  async fetch(request: Request): Promise<Response> {
    try {
      await this.ensureRunning();
    } catch (e) {
      console.error(e);
      return new Response("API đang khởi động, thử lại sau vài giây.", {
        status: 503,
        headers: { "retry-after": "5", "content-type": "text/plain; charset=utf-8" },
      });
    }
    const url = new URL(request.url);
    url.protocol = "http:";
    url.host = "container";
    const forwarded = new Request(url, request);
    forwarded.headers.delete("host");
    return this.ctx.container!.getTcpPort(PORT).fetch(forwarded);
  }
}

export default {
  fetch(request, env) {
    return env.API.getByName("api").fetch(request);
  },
} satisfies ExportedHandler<Env>;
