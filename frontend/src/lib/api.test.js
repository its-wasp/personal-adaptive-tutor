import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, api, tokenStore } from "./api";

/**
 * Tests for the fetch wrapper every page goes through.
 *
 * fetch is stubbed rather than served, so these pin the wrapper's contract —
 * header handling, error shape, body parsing — without a running backend.
 */

function mockFetch({ status = 200, body = null, text = null } = {}) {
  const payload = text ?? (body === null ? "" : JSON.stringify(body));
  const spy = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    text: () => Promise.resolve(payload),
  });
  global.fetch = spy;
  return spy;
}

beforeEach(() => {
  tokenStore.clear();
});

describe("tokenStore", () => {
  it("round-trips a token", () => {
    tokenStore.set("abc123");
    expect(tokenStore.get()).toBe("abc123");
  });

  it("returns null once cleared", () => {
    tokenStore.set("abc123");
    tokenStore.clear();
    expect(tokenStore.get()).toBeNull();
  });
});

describe("authorization header", () => {
  it("attaches the bearer token when one is stored", async () => {
    tokenStore.set("tok");
    const spy = mockFetch({ body: { ok: true } });

    await api.get("/profile/me");

    expect(spy.mock.calls[0][1].headers.Authorization).toBe("Bearer tok");
  });

  it("omits the header when no token is stored", async () => {
    const spy = mockFetch({ body: {} });

    await api.get("/profile/me");

    expect(spy.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  it("omits the header when auth is explicitly disabled", async () => {
    tokenStore.set("tok");
    const spy = mockFetch({ body: {} });

    await api.post("/auth/login", { email: "a@b.c" }, { auth: false });

    expect(spy.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });
});

describe("request bodies", () => {
  it("serialises the body as JSON", async () => {
    const spy = mockFetch({ body: {} });

    await api.post("/chat/create", { topic_name: "Arrays" });

    const init = spy.mock.calls[0][1];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ topic_name: "Arrays" });
  });

  it("sends no body for GET", async () => {
    const spy = mockFetch({ body: {} });

    await api.get("/chat/sessions");

    expect(spy.mock.calls[0][1].body).toBeUndefined();
  });
});

describe("error handling", () => {
  it("throws ApiError carrying the status", async () => {
    mockFetch({ status: 404, body: { detail: "Chat session not found" } });

    await expect(api.get("/chat/x/conversation")).rejects.toBeInstanceOf(ApiError);
  });

  it("surfaces the server's detail message", async () => {
    mockFetch({ status: 404, body: { detail: "Chat session not found" } });

    await expect(api.get("/chat/x/conversation")).rejects.toMatchObject({
      status: 404,
      detail: "Chat session not found",
    });
  });

  it("falls back to a generic message when there is no detail", async () => {
    mockFetch({ status: 500, body: {} });

    await expect(api.get("/anything")).rejects.toMatchObject({
      detail: "Request failed (500)",
    });
  });

  it("does not throw on a non-JSON error body", async () => {
    mockFetch({ status: 502, text: "Bad Gateway" });

    await expect(api.get("/anything")).rejects.toMatchObject({ status: 502 });
  });
});

describe("response parsing", () => {
  it("returns parsed JSON", async () => {
    mockFetch({ body: { id: 1, title: "Arrays" } });

    await expect(api.get("/chat/sessions")).resolves.toEqual({
      id: 1,
      title: "Arrays",
    });
  });

  it("returns null for an empty body", async () => {
    mockFetch({ text: "" });

    await expect(api.delete("/chat/1")).resolves.toBeNull();
  });

  it("returns raw text when the body isn't JSON", async () => {
    mockFetch({ text: "plain text" });

    await expect(api.get("/anything")).resolves.toBe("plain text");
  });
});
