import { cookies } from "next/headers";

export async function authHeaders(): Promise<HeadersInit> {
  const cookieStore = await cookies();
  const token = cookieStore.get("scanner_token")?.value;
  return token ? { Authorization: `Bearer ${token}` } : {};
}
