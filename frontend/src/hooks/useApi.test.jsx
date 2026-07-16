import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useApiGet, useApiMutation } from "./useApi";
import { ApiError, api } from "../lib/api";

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual("../lib/api");
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  };
});

beforeEach(() => {
  for (const fn of Object.values(api)) fn.mockReset();
});

describe("useApiGet", () => {
  it("fetches on mount and exposes the result", async () => {
    api.get.mockResolvedValue({ id: 1 });

    const { result } = renderHook(() => useApiGet("/profile/me"));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(api.get).toHaveBeenCalledWith("/profile/me");
    expect(result.current.data).toEqual({ id: 1 });
    expect(result.current.error).toBeNull();
  });

  it("starts in a loading state", () => {
    api.get.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useApiGet("/profile/me"));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
  });

  it("does not fetch when skipped", () => {
    renderHook(() => useApiGet("/graph/dsa", { skip: true }));

    expect(api.get).not.toHaveBeenCalled();
  });

  it("reports loading as false when skipped", () => {
    const { result } = renderHook(() => useApiGet("/graph/dsa", { skip: true }));

    expect(result.current.loading).toBe(false);
  });

  it("captures an ApiError without throwing", async () => {
    api.get.mockRejectedValue(new ApiError(404, "not found"));

    const { result } = renderHook(() => useApiGet("/chat/x/conversation"));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toMatchObject({ status: 404, detail: "not found" });
    expect(result.current.data).toBeNull();
  });

  it("wraps a non-ApiError rejection", async () => {
    api.get.mockRejectedValue(new Error("network down"));

    const { result } = renderHook(() => useApiGet("/anything"));

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.error).toBeInstanceOf(ApiError);
  });

  it("refetches on demand", async () => {
    api.get.mockResolvedValue({ n: 1 });
    const { result } = renderHook(() => useApiGet("/review/due"));
    await waitFor(() => expect(result.current.loading).toBe(false));

    api.get.mockResolvedValue({ n: 2 });
    await act(() => result.current.refetch());

    await waitFor(() => expect(result.current.data).toEqual({ n: 2 }));
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it("refetches when the path changes", async () => {
    api.get.mockResolvedValue({});
    const { rerender } = renderHook(({ path }) => useApiGet(path), {
      initialProps: { path: "/chat/1/conversation" },
    });
    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(1));

    rerender({ path: "/chat/2/conversation" });

    await waitFor(() => expect(api.get).toHaveBeenCalledTimes(2));
    expect(api.get).toHaveBeenLastCalledWith("/chat/2/conversation");
  });

  it("ignores a slow response for a path that has been replaced", async () => {
    // The guard that stops session A's conversation landing in session B's view.
    let resolveFirst;
    api.get.mockImplementationOnce(
      () => new Promise((resolve) => { resolveFirst = resolve; })
    );
    api.get.mockResolvedValueOnce({ session: "second" });

    const { result, rerender } = renderHook(({ path }) => useApiGet(path), {
      initialProps: { path: "/chat/1/conversation" },
    });
    rerender({ path: "/chat/2/conversation" });
    await waitFor(() => expect(result.current.data).toEqual({ session: "second" }));

    await act(async () => { resolveFirst({ session: "first" }); });

    expect(result.current.data).toEqual({ session: "second" });
  });
});

describe("useApiMutation", () => {
  it("dispatches to the matching api method", async () => {
    api.post.mockResolvedValue({ id: "s1" });
    const { result } = renderHook(() => useApiMutation());

    let returned;
    await act(async () => {
      returned = await result.current.mutate("POST", "/chat/create", { topic_name: "Arrays" });
    });

    expect(api.post).toHaveBeenCalledWith("/chat/create", { topic_name: "Arrays" });
    expect(returned).toEqual({ id: "s1" });
  });

  it("accepts a lowercase method name", async () => {
    api.delete.mockResolvedValue(null);
    const { result } = renderHook(() => useApiMutation());

    await act(async () => { await result.current.mutate("delete", "/chat/1"); });

    expect(api.delete).toHaveBeenCalledWith("/chat/1");
  });

  it("omits the body when none is given", async () => {
    api.get.mockResolvedValue({});
    const { result } = renderHook(() => useApiMutation());

    await act(async () => { await result.current.mutate("GET", "/profile/me"); });

    expect(api.get).toHaveBeenCalledWith("/profile/me");
  });

  it("rethrows and records the failure", async () => {
    api.post.mockRejectedValue(new ApiError(502, "tutor unavailable"));
    const { result } = renderHook(() => useApiMutation());

    await act(async () => {
      await expect(result.current.mutate("POST", "/chat/create", {})).rejects.toMatchObject({
        status: 502,
      });
    });

    expect(result.current.error).toMatchObject({ status: 502 });
  });

  it("clears loading after a failure", async () => {
    api.post.mockRejectedValue(new ApiError(500, "boom"));
    const { result } = renderHook(() => useApiMutation());

    await act(async () => {
      await result.current.mutate("POST", "/x", {}).catch(() => {});
    });

    expect(result.current.loading).toBe(false);
  });

  it("rejects an unsupported method", async () => {
    const { result } = renderHook(() => useApiMutation());

    await act(async () => {
      await expect(result.current.mutate("PATCH", "/x", {})).rejects.toBeTruthy();
    });
  });
});
