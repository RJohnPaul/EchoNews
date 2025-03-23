import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// This function can be marked `async` if using `await` inside
export function middleware(request: NextRequest) {
  // Paths that don't require authentication
  const publicPaths = ['/login'];
  
  // Check if the current path is a public path
  const isPublicPath = publicPaths.some(path => 
    request.nextUrl.pathname.startsWith(path)
  );
  
  // Check if the user is authenticated by looking for a token in cookies
  // Note: middleware runs on the server, so we can't use localStorage here
  const token = request.cookies.get('isLoggedIn')?.value;
  
  // If the path requires authentication and the user is not authenticated,
  // redirect to login
  if (!isPublicPath && !token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  
  // If the user is authenticated and trying to access login,
  // redirect to the home page
  if (isPublicPath && token) {
    return NextResponse.redirect(new URL('/', request.url));
  }
  
  return NextResponse.next();
}

// Configure which paths this middleware applies to
export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};