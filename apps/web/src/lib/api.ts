import { env } from "../config/env";
import type {
  Booking,
  BookingRequest,
  ChatResponse,
  MetricsSummary,
  ScrapeRefreshResult,
  ScrapedPackage,
  SearchResult,
  TourPackage,
} from "../types/domain";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export function isNotFound(err: unknown): boolean {
  return err instanceof ApiError && err.status === 404;
}

interface RequestOptions {
  token?: string;
  method?: string;
  body?: unknown;
}

async function request(
  baseUrl: string,
  path: string,
  { token, method = "GET", body }: RequestOptions = {},
): Promise<unknown> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.json();
}

export const bookingApi = {
  listPackages: (token?: string) =>
    request(env.apiBaseUrl, "/packages", { token }) as Promise<TourPackage[]>,

  getPackage: (id: string, token?: string) =>
    request(env.apiBaseUrl, `/packages/${id}`, { token }) as Promise<TourPackage>,

  syncExternal: (pkg: TourPackage) =>
    request(env.apiBaseUrl, "/packages/sync", {
      method: "POST",
      body: {
        code: pkg.code,
        title: pkg.title,
        destination: pkg.destination,
        country: pkg.country,
        description: pkg.description,
        category: pkg.category,
        durationDays: pkg.durationDays,
        basePrice: pkg.basePrice,
        currency: pkg.currency,
        rating: pkg.rating,
        source: pkg.source ?? "EXTERNO",
        maxTravelers: pkg.maxTravelers,
        cancelDaysBefore: pkg.cancelDaysBefore,
        cancelRefundPercent: pkg.cancelRefundPercent,
        images: pkg.images,
        startDates: pkg.startDates,
      },
    }) as Promise<TourPackage>,

  createBooking: (payload: BookingRequest, token: string) =>
    request(env.apiBaseUrl, "/bookings", {
      method: "POST",
      body: payload,
      token,
    }) as Promise<Booking>,

  getMyBookings: (token: string) =>
    request(env.apiBaseUrl, "/bookings/me", { token }) as Promise<Booking[]>,

  getBooking: (id: string, token: string) =>
    request(env.apiBaseUrl, `/bookings/${id}`, { token }) as Promise<Booking>,
};

export const searchApi = {
  search: (query: string, token?: string) =>
    request(
      env.searchApiBaseUrl,
      `/search/suggestions?query=${encodeURIComponent(query)}`,
      { token },
    ) as Promise<SearchResult>,

  searchSemantic: (query: string, limit = 10, token?: string) =>
    request(
      env.searchApiBaseUrl,
      `/search/semantic?query=${encodeURIComponent(query)}&limit=${limit}`,
      { token },
    ) as Promise<SearchResult>,

  ensurePackage: (id: string, token?: string) =>
    request(env.searchApiBaseUrl, `/packages/${id}`, { token }) as Promise<TourPackage>,

  recommendations: (userId: string, limit = 5, token?: string) =>
    request(
      env.searchApiBaseUrl,
      `/recommendations/${encodeURIComponent(userId)}?limit=${limit}`,
      { token },
    ) as Promise<TourPackage[]>,

  runScrape: async (token?: string): Promise<void> => {
    await request(env.searchApiBaseUrl, "/scrape/run", {
      method: "POST",
      token,
    });
  },

  listScrapedPackages: (token?: string) =>
    request(env.searchApiBaseUrl, "/scrape/packages", { token }) as Promise<
      ScrapedPackage[]
    >,

  refreshScrape: (token?: string) =>
    request(env.searchApiBaseUrl, "/scrape/refresh", {
      method: "POST",
      token,
    }) as Promise<ScrapeRefreshResult>,

  chat: (message: string, token?: string) =>
    request(env.searchApiBaseUrl, "/assistant/chat", {
      method: "POST",
      body: { message },
      token,
    }) as Promise<ChatResponse>,

  metricsSummary: (token?: string) =>
    request(env.searchApiBaseUrl, "/metrics/summary", { token }) as Promise<MetricsSummary>,
};