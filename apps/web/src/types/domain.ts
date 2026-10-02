export interface CancellationPolicy {
  daysBefore: number;
  refundPercentage: number;
}

export interface TourPackage {
  id: string;
  code: string;
  title: string;
  destination: string;
  country: string;
  description: string;
  category: string;
  durationDays: number;
  basePrice: number;
  currency: string;
  maxTravelers: number;
  images: string[];
  startDates: string[];
  cancelDaysBefore: number;
  cancelRefundPercent: number;
  rating: number;
  active: boolean;
  source: string;
}

export interface BookingRequestItem {
  packageId: string;
  startDate: string;
  travelers: number;
}

export interface BookingRequest {
  items: BookingRequestItem[];
}

export interface Booking {
  id: string;
  userId: string;
  status: "PENDING" | "CONFIRMED" | "PAID" | "CANCELLED";
  currency: string;
  totalPrice: number;
  createdAt: string;
  items: BookingItem[];
}

export interface BookingItem {
  id: string;
  packageId: string;
  packageTitle: string;
  startDate: string;
  travelers: number;
  unitPrice: number;
  subtotal: number;
}

export interface SearchResult {
  packages: TourPackage[];
  suggestions: string[];
  query: string;
}

export interface ScrapedPackage {
  id: number;
  source: string;
  sourceId: string;
  title: string;
  destination: string;
  price: number;
  currency: string;
  url: string;
  scrapedAt: string;
}