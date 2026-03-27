import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const TOKEN_COOKIE = "access_token";

function isProtectedPath(pathname: string) {
  return (
    pathname === "/profile" ||
    pathname === "/members" ||
    pathname.startsWith("/members/") ||
    pathname === "/events" ||
    pathname.startsWith("/events/") ||
    pathname === "/ministries" ||
    pathname.startsWith("/ministries/")
  );
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (!isProtectedPath(pathname)) {
    return NextResponse.next();
  }

  const token = req.cookies.get(TOKEN_COOKIE)?.value;
  if (!token) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/profile/:path*", "/members/:path*", "/events/:path*", "/ministries/:path*"],
};

