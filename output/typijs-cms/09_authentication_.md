# Chapter 9: Authentication

Welcome back! In our last chapter, [Chapter 8: Content Services](08_content_services_.md), we explored the specialized services (`PageService`, `BlockService`, etc.) that handle the direct communication with the CMS backend API to fetch, create, update, and manage your content data ([Chapter 1: Content Data](01_content_data_.md)).

Working with content like creating a new page or deleting an old block is sensitive. You wouldn't want just anyone to be able to perform these actions! You need to ensure that only authenticated and authorized users can access the CMS admin portal and interact with your content via the backend API.

This is where the concept of **Authentication** comes in. Authentication is the process of verifying a user's identity – essentially, proving that you are who you say you are. Once authenticated, the system can then decide what you're allowed to do (this is called Authorization, which often goes hand-in-hand with authentication, like checking user roles).

## What Problem Does Authentication Solve?

Imagine the CMS admin portal. This is where you manage all your valuable website content. Without authentication, anyone could potentially access the portal, navigate the content tree ([Chapter 4: Tree Navigation](04_tree_navigation_.md)), edit properties ([Chapter 5: Property Rendering (Editor)](05_property_rendering__editor__.md)), publish pages, or even delete entire sections of your site. This is clearly unacceptable!

Authentication provides the necessary security gate. It ensures that only users with valid credentials (like a username and password) can log in and gain access to the restricted parts of the application, like the CMS editor.

Furthermore, even once you're inside the editor, every action you take that involves the backend (saving a change, publishing, loading children via `ContentLoader` which uses `ContentServices`) requires the backend to know *who* is making the request. Authentication ensures that your identity is attached to these requests, allowing the backend to verify you are logged in and have the necessary permissions (Authorization) before performing the action.

typijs-cms addresses this using a standard authentication pattern involving **JWT (JSON Web Tokens)** and three key Angular services: `AuthService`, `AuthGuard`, and `AuthInterceptor`.

## Key Concepts

1.  **`AuthService`**: This is the central service in typijs-cms responsible for managing the user's authentication state. It handles the login process (sending credentials to the backend), logout, and dealing with refresh tokens to keep the user logged in without constantly re-entering credentials. It holds the user's authentication status, including their JWT access token.
    *   **JWT (JSON Web Token)**: This is a standard way to securely transmit information between parties as a JSON object. In authentication, a JWT is often used as the "access token". After a user logs in, the backend generates a JWT containing information about the user (like their ID and roles) and sends it back to the client. The client then includes this token in subsequent requests to the backend to prove their identity. The token is digitally signed, so the backend can verify that it hasn't been tampered with. JWTs have an expiration time for security.
    *   **Refresh Tokens**: Since JWTs expire, re-logging in frequently would be annoying. Refresh tokens are longer-lived tokens also issued by the backend during login. They are used *only* to obtain a *new* access token when the current one expires, without requiring the user to re-enter their username and password. `AuthService` handles this token refreshing process automatically in the background.

2.  **`AuthGuard`**: This is an Angular service designed to protect routes in your application. You attach an `AuthGuard` to specific routes (like all routes under `/admin`). Before navigating to a protected route, Angular's router asks the `AuthGuard` if the user is allowed to proceed (`canActivate` method). The `AuthGuard` checks if the user is authenticated (by asking the `AuthService`). If not, it redirects them to the login page. It can also perform basic authorization checks based on user roles defined in the route's data.

3.  **`AuthInterceptor`**: This is a special type of Angular service that intercepts outgoing HTTP requests from your application and incoming HTTP responses. The `AuthInterceptor` in typijs-cms is configured to automatically add the user's JWT access token to the `Authorization` header of any request going to the CMS backend API. This means you don't have to manually add the token to every single `HttpClient` call made by services like `PageService` or `ContentLoader`; the interceptor does it for you seamlessly. It also catches specific error responses from the backend, like `401 Unauthorized` (meaning the token is invalid or missing), and can trigger actions like logging the user out.

These three components work together to handle the complete authentication flow in the CMS portal.

## Use Case: Accessing the CMS Admin Portal and Saving a Change

Let's walk through how these concepts work together when a user wants to access the CMS editor and then saves a change to a page.

**Scenario 1: First time accessing the CMS admin portal (`/admin`)**

1.  The user tries to navigate to `/admin` in their browser.
2.  Angular's router sees that the `/admin` route (and its child routes) are protected by the `AuthGuard`.
3.  The router calls the `canActivate` method of the `AuthGuard`.
4.  The `AuthGuard` asks the `AuthService`: "Is the user currently logged in (`isLoggedIn`)?".
5.  The `AuthService` checks its internal state (has it received and stored a valid token?). Since the user hasn't logged in yet, `isLoggedIn` is false.
6.  The `AuthGuard` receives `false`, indicating the user cannot activate the route.
7.  The `AuthGuard` redirects the user to the CMS login page (e.g., `/admin/login`), typically adding the original `/admin` URL as a `returnUrl` query parameter.
8.  The user arrives at the `CmsLoginComponent`.

**Scenario 2: Logging in**

1.  On the login page, the user enters their username and password into the form managed by `CmsLoginComponent`.
2.  The user clicks the "Login" button.
3.  `CmsLoginComponent` calls the `login()` method of the `AuthService`, passing the entered username and password.
4.  The `AuthService.login()` method uses Angular's `HttpClient` to send a `POST` request containing the credentials to the backend authentication API endpoint (e.g., `/api/auth/login`).
5.  The `AuthInterceptor` **intercepts** this outgoing request. It checks if the user is logged in (`AuthService.isLoggedIn`) and if the request is going to the API (`request.url.startsWith(baseApiUrl)`). Since this is the login request itself and the user is not yet logged in, the interceptor *does not* add an `Authorization` header. It lets the request pass through to the backend.
6.  The backend receives the credentials, verifies them against its user database.
7.  If successful, the backend generates a JWT access token and a refresh token, and sends them back in the HTTP response.
8.  The `AuthService.login()` method receives the successful response containing the tokens.
9.  `AuthService` extracts the tokens, parses the JWT to get user details (ID, roles, expiry date), creates an `AuthStatus` object, stores the token and status internally (e.g., in a BehaviorSubject and potentially browser storage), and starts a timer to automatically request a new access token using the refresh token just before the current access token expires (`startRefreshTokenTimer`).
10. `AuthService.login()`'s Observable completes successfully.
11. `CmsLoginComponent` receives the success notification. It reads the `returnUrl` query parameter (`/admin`) and navigates the user back to the initially requested URL.

**Scenario 3: Accessing the protected route after logging in**

1.  The user tries to navigate to `/admin` again.
2.  The `AuthGuard`'s `canActivate` method is called again.
3.  `AuthGuard` asks `AuthService.isLoggedIn`.
4.  This time, `AuthService` has a stored token and `isLoggedIn` returns `true`.
5.  The `AuthGuard` receives `true` and allows the user to proceed to the `/admin` route. The user can now see the CMS editor UI.

**Scenario 4: Saving a change (e.g., updating page properties)**

1.  The user makes changes in the editor form for a page and clicks "Save".
2.  The CMS editor UI gathers the updated [Content Data](01_content_data_.md) and calls a method on `PageService` (e.g., `pageService.updateContent(...)`) to send the changes to the backend API.
3.  `PageService` uses `HttpClient` to send a `PUT` request to the backend API endpoint (e.g., `/api/page/{pageId}`).
4.  The `AuthInterceptor` **intercepts** this outgoing request.
5.  It checks if the user is logged in (`AuthService.isLoggedIn`) – which is true – and if the request is going to the API – which is true.
6.  The interceptor gets the current JWT access token from `AuthService.authStatus`.
7.  It clones the outgoing `HttpClient` request and adds an `Authorization: Bearer [your-jwt-token]` header.
8.  The modified request (with the token) is sent to the backend.
9.  The backend receives the request. Before processing it, its security layer extracts the JWT from the `Authorization` header, verifies its signature, checks if it has expired, and identifies the user associated with the token.
10. If the token is valid and the user is identified, the backend proceeds to process the request (e.g., save the page changes), potentially performing authorization checks (does this user have permission to update *this* page?).
11. If the token is missing, invalid, or expired, the backend returns a `401 Unauthorized` (or sometimes `403 Forbidden`) error.
12. The `AuthInterceptor` **intercepts** the incoming `401` error response. It sees a `401` error for an authenticated user (`AuthService.isLoggedIn` is true).
13. The interceptor triggers a logout via `AuthService.logout()` (which clears the stored token) and redirects the user back to the login page, starting the cycle over. This ensures that if the token expires or becomes invalid while the user is active, they are gracefully logged out.

Here's a sequence diagram summarizing the flow after login, when an API request is made:

```mermaid
sequenceDiagram
    participant CMS Editor UI
    participant Specific Content Service (e.g., PageService)
    participant AuthInterceptor
    participant AuthService
    participant CMS Backend API

    CMS Editor UI->>Specific Content Service (e.g., PageService): Call updateContent(data)
    Specific Content Service (e.g., PageService)->>AuthInterceptor: HttpClient sends HTTP request
    AuthInterceptor->>AuthService: Check isLoggedIn
    AuthService-->>AuthInterceptor: Return true (User is logged in)
    AuthInterceptor->>AuthService: Get AuthStatus (including token)
    AuthService-->>AuthInterceptor: Return AuthStatus
    AuthInterceptor->>AuthInterceptor: Add "Authorization: Bearer [token]" header to request
    AuthInterceptor-->>CMS Backend API: Forward modified HTTP request
    CMS Backend API->>CMS Backend API: Verify token
    alt Token Valid
        CMS Backend API->>CMS Backend API: Process request (e.g., Save Content)
        CMS Backend API-->>AuthInterceptor: Return Success Response (e.g., 200 OK)
        AuthInterceptor-->>Specific Content Service (e.g., PageService): Forward Success Response
        Specific Content Service (e.g., PageService)-->>CMS Editor UI: Return Success (Content Saved)
    else Token Invalid/Expired
        CMS Backend API-->>AuthInterceptor: Return 401 Unauthorized Error
        AuthInterceptor->>AuthService: Call logout()
        AuthService->>AuthService: Clear token, stop timer etc.
        AuthInterceptor->>AuthInterceptor: Redirect to Login Page
        AuthInterceptor--xSpecific Content Service (e.g., PageService): Propagate Error (handled by calling component)
        Specific Content Service (e.g., PageService)-->>CMS Editor UI: Propagate Error
    end
```

This intricate process happens automatically in the background thanks to the `AuthService`, `AuthGuard`, and `AuthInterceptor`, allowing you to focus on building your CMS features without worrying about manually handling tokens for every single backend call.

## Looking at the Code (Simplified)

Let's look at simplified versions of the code snippets provided to see how these pieces are structured.

**1. `AuthStatus` Model (`core\src\auth\auth.model.ts`)**

```typescript
// core\src\auth\auth.model.ts (Simplified)
export type TokenPayload = {
    roles?: string[] // User roles extracted from the token
    sub: string // Subject, usually the User ID
    iat: number // Issued At timestamp
    exp: number // Expiration timestamp
    [key: string]: any // Other potential data in the token
};

export class AuthStatus {
    userId: string;
    roles: string[];
    token?: string;
    expiry?: Date; // Expiry date converted from timestamp

    constructor(token: string) {
        // Parse the token (base64 decode the payload part)
        const jwtToken: TokenPayload = JSON.parse(atob(token.split('.')[1]));
        this.userId = jwtToken.sub;
        this.roles = jwtToken.roles;
        this.expiry = new Date(jwtToken.exp * 1000); // Convert seconds to milliseconds
        this.token = token;
    }
}
```
**Explanation:** The `AuthStatus` class is a simple model to hold the relevant authentication information derived from the JWT after a successful login. It parses the token in its constructor to extract the user ID, roles, and expiry date.

**2. `AuthService` (`core\src\auth\auth.service.ts`)**

```typescript
// core\src\auth\auth.service.ts (Simplified)
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { map, switchMap } from 'rxjs/operators';
import { AuthStatus, TokenResponse } from './auth.model'; // Import AuthStatus model

@Injectable({ providedIn: 'root' }) // Makes this service available application-wide
export class AuthService {
    // BehaviorSubject to hold the current AuthStatus, emitting updates
    private authSubject: BehaviorSubject<AuthStatus>;
    // Public Observable exposing the auth status stream
    authStatus$: Observable<AuthStatus>;

    // Getter to easily access the *current* auth status value
    get authStatus(): AuthStatus {
        return this.authSubject.value;
    }

    // Getter to quickly check if a user is logged in
    get isLoggedIn(): boolean {
        return this.authStatus && this.authStatus.token ? true : false;
    }

    protected apiUrl: string; // Backend API URL for auth
    private refreshTokenTimeout; // Timer for auto-refreshing token

    constructor(private httpClient: HttpClient) { // Inject HttpClient to talk to backend
        // Initialize the BehaviorSubject with null (not logged in initially)
        this.authSubject = new BehaviorSubject<AuthStatus>(null);
        // Create the public observable stream
        this.authStatus$ = this.authSubject.asObservable();
        // Basic setup for apiUrl (simplified)
        this.apiUrl = `${this.baseApiUrl}/auth`; // baseApiUrl comes from ConfigService, simplified here
    }

    // Handles sending credentials to backend login endpoint
    login(username: string, password: string): Observable<AuthStatus> {
        const loginData = { username, password };
        return this.httpClient.post<TokenResponse>(`${this.apiUrl}/login`, loginData)
            .pipe(map(tokenResponse => {
                // On successful login, create AuthStatus, update BehaviorSubject, start refresh timer
                const authStatus = new AuthStatus(tokenResponse.token);
                this.authSubject.next(authStatus); // Emits the new status to observers
                this.startRefreshTokenTimer(); // Start auto-refresh
                return authStatus; // Return the status
            }));
    }

    // Handles logging the user out
    logout() {
        // Call backend endpoint to invalidate refresh token (optional but good practice)
        this.httpClient.post<any>(`${this.apiUrl}/revoke-token`, {}).subscribe();
        // Clear the AuthStatus in the BehaviorSubject (marks user as logged out)
        this.authSubject.next(null);
        // Stop the auto-refresh timer
        this.stopRefreshTokenTimer();
    }

    // Requests a new access token using the refresh token
    refreshToken(): Observable<AuthStatus> {
        // Call backend endpoint to get a new token (often needs the refresh token sent via cookie/body)
        return this.httpClient.post<TokenResponse>(`${this.apiUrl}/refresh-token`, {}) // Simplified body
            .pipe(map((tokenResponse) => {
                if (tokenResponse && tokenResponse.token) {
                    // If successful, update status and restart timer
                    const authStatus = new AuthStatus(tokenResponse.token);
                    this.authSubject.next(authStatus);
                    this.startRefreshTokenTimer();
                    return authStatus;
                }
                return null; // Handle case where refresh token is invalid/expired
            }));
    }

    // Helper to start the token auto-refresh timer
    private startRefreshTokenTimer() {
        if (this.authStatus) {
            // Calculate timeout based on token expiry (e.g., 1 minute before expiry)
            const expires = this.authStatus.expiry.getTime();
            const timeout = expires - Date.now() - (60 * 1000); // Refresh 60 seconds early
            this.refreshTokenTimeout = setTimeout(() => this.refreshToken().subscribe(), timeout);
        }
    }

    // Helper to stop the timer
    private stopRefreshTokenTimer() {
        if (this.refreshTokenTimeout) { clearTimeout(this.refreshTokenTimeout); }
    }
    // ... other methods for setupAdmin, canSetupAdmin etc. ...
}
```
**Explanation:** `AuthService` is the core state manager. It holds the `AuthStatus` in a `BehaviorSubject`, allowing any part of the application to subscribe to changes in the login state via `authStatus$`. The `isLoggedIn` getter is a convenience. The `login` method sends credentials and processes the response, updating the state. `logout` clears the state. `refreshToken` handles renewing the token. The timer methods automate the refresh process.

**3. `CmsLoginComponent` (`core\src\auth\login\login.component.ts`)**

```typescript
// core\src\auth\login\login.component.ts (Simplified)
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms'; // For creating the form
import { ActivatedRoute } from '@angular/router'; // To get returnUrl
import { BrowserLocationService } from '../../browser/browser-location.service'; // For navigation
import { AuthService } from '../auth.service'; // Inject AuthService

@Component({
    templateUrl: './login.component.html', // The login form HTML
    // ... styles ...
})
export class CmsLoginComponent implements OnInit {
    loginForm: FormGroup;
    loading = false; // State for showing loading indicator
    submitted = false; // State for form submission
    returnUrl: string; // Where to go after login
    error = ''; // To display login errors

    // Getter to easily access form controls
    get f() { return this.loginForm.controls; }

    constructor(
        private route: ActivatedRoute, // Provides info about the current route
        private formBuilder: FormBuilder, // Helper for creating Angular forms
        private locationService: BrowserLocationService, // Helper for browser navigation
        private authService: AuthService) { // Inject AuthService
    }

    ngOnInit() {
        // Build the login form with username and password fields and validation
        this.loginForm = this.formBuilder.group({
            username: ['', Validators.required],
            password: ['', Validators.required]
        });

        // Get the returnUrl from the route query parameters (if present)
        this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/';
    }

    // Called when the login form is submitted
    onSubmit() {
        this.submitted = true;

        // Stop if the form has validation errors
        if (this.loginForm.invalid) {
            return;
        }

        this.loading = true; // Start loading indicator
        // Call the login method on AuthService
        this.authService.login(this.f.username.value, this.f.password.value)
            .subscribe({
                next: () => {
                    // On successful login, navigate to the returnUrl
                    this.locationService.navigate(this.returnUrl);
                },
                error: error => {
                    // On error, display the error and stop loading
                    this.error = error; // Simplified: real error handling is more complex
                    this.loading = false;
                }
            });
    }
}
```
**Explanation:** This is a standard Angular component for a login form. It injects `AuthService`, builds a reactive form, and on submission, calls `authService.login()`. Based on the Observable's result, it either navigates away or displays an error.

**4. `AuthGuard` (`core\src\auth\auth.guard.ts`)**

```typescript
// core\src\auth\auth.guard.ts (Simplified)
import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router'; // Guard interface and route info
import { BrowserLocationService } from '../browser/browser-location.service'; // For navigation
import { AuthService } from './auth.service'; // Inject AuthService

@Injectable({ providedIn: 'root' }) // Makes this guard available application-wide
export class AuthGuard implements CanActivate { // Implements the CanActivate interface
    constructor(
        private authService: AuthService, // Inject AuthService
        private locationService: BrowserLocationService, // For redirection
        // @Inject(ADMIN_ROUTE) private adminPath: string // Injection token for admin path, used for login URL
    ) { /* Simplified path logic */ }

    // The main method the Angular router calls
    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
        // Check if the user is logged in using AuthService
        if (this.authService.isLoggedIn) {
            // Optional: Check if the user has required roles for this specific route
            const authStatus = this.authService.authStatus;
            const roleMatch = this.checkRoleMatch(authStatus.roles, route);
            if (!roleMatch) {
                 // User is logged in but doesn't have the right role
                 alert('You do not have the permissions to view this resource'); // Basic message
                 // Optionally navigate to a permission denied page
            }
            return roleMatch; // Allow if logged in AND roles match (or no role required)
        } else {
            // If not logged in, redirect to the login page
            // Store the current URL as returnUrl so the user comes back here after login
            const loginUrl = `/admin/login?returnUrl=${state.url}`; // Simplified adminPath
            this.locationService.navigate(loginUrl);
            return false; // Prevent navigation to the requested route
        }
    }

    // Helper method for checking if user roles match roles defined in route data
    private checkRoleMatch(userRoles: string[], route?: ActivatedRouteSnapshot): boolean {
        if (route && route.data && route.data.role) {
            // If the route has a 'role' property in its data, check if userRoles includes it
            // Note: This is a basic single-role check. More complex checks might be needed.
            return userRoles.includes(route.data.role);
        }
        return true; // If no specific role is required for the route, allow access
    }
}
```
**Explanation:** `AuthGuard` is used in Angular's routing configuration. When a user tries to access a route protected by this guard, the `canActivate` method is called. It simply checks `authService.isLoggedIn`. If false, it redirects using `BrowserLocationService.navigate` and returns `false` to stop the navigation. If true, it optionally checks for roles and returns `true` allowing access.

**5. `AuthInterceptor` (`core\src\auth\auth.interceptor.ts`)**

```typescript
// core\src\auth\auth.interceptor.ts (Simplified)
import { HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http'; // Http types
import { Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs'; // RxJS for Observables
import { catchError } from 'rxjs/operators'; // RxJS operator for error handling

import { ConfigService } from '../config/config.service'; // To get base API URL
import { BrowserLocationService } from '../browser/browser-location.service'; // For redirection
import { AuthService } from './auth.service'; // Inject AuthService

@Injectable() // Mark as injectable
export class AuthInterceptor implements HttpInterceptor { // Implement HttpInterceptor interface
    constructor(
        private authService: AuthService, // Inject AuthService
        private configService: ConfigService, // To check if the request is to the API
        private locationService: BrowserLocationService, // For redirection
        // @Inject(ADMIN_ROUTE) private adminPath: string // For login path
    ) { /* Simplified path logic */ }

    // The main method that intercepts requests
    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        // First, try to add the authorization header
        const authRequest = this.setAuthorizationHeader(request);
        // Then, handle the modified request and catch potential errors
        return next.handle(authRequest).pipe(catchError((error: HttpErrorResponse) => this.handleAuthError(error)));
    }

    // Helper to add the Auth header
    private setAuthorizationHeader(request: HttpRequest<any>): HttpRequest<any> {
        // Check if user is logged in AND the request is to the CMS API
        const isApiUrl = request.url.startsWith(this.configService.baseApiUrl);
        if (this.authService.isLoggedIn && isApiUrl) {
            // Clone the request and set the Authorization header with the Bearer token
            return request.clone({ setHeaders: { Authorization: `Bearer ${this.authService.authStatus.token}` } });
        }
        return request; // If not logged in or not an API request, return the original request
    }

    // Helper to handle HTTP errors, specifically 401
    private handleAuthError(error: HttpErrorResponse): Observable<any> {
        // If the error is 401 and the user *was* logged in (meaning the token expired/is invalid)
        if (error.status === 401 && this.authService.isLoggedIn) {
            // Log the user out via AuthService
            this.authService.logout();
            // Redirect to the login page, including the current URL as returnUrl
            const loginUrl = `/admin/login?returnUrl=${this.locationService.path()}`; // Simplified path/adminPath
            this.locationService.navigate(loginUrl);
            // Note: Returning throwError(error) here is important so the calling component/service also knows the request failed.
        }
        // For any other error status, just rethrow the error
        return throwError(error);
    }
}
```
**Explanation:** `AuthInterceptor` is registered with Angular's `HttpClientModule`. It intercepts requests using the `intercept` method. It calls `setAuthorizationHeader` to potentially add the token based on the user's login status and the request URL. It then pipes the request through `next.handle` and uses `catchError` to call `handleAuthError` if an HTTP error occurs. `handleAuthError` specifically looks for a 401 error when the user was logged in, triggering a logout and redirect.

Together, these three services provide a robust authentication layer for the typijs-cms admin portal, ensuring secure access and communication with the backend API using the standard JWT mechanism.

## Conclusion

In this chapter, we explored the critical concept of **Authentication** in typijs-cms. We learned how it secures the CMS admin portal and API communication by verifying user identity. The core components involved are:
*   `AuthService`: Manages login, logout, user status, and automatic JWT refreshing.
*   `AuthGuard`: Protects routes by checking if the user is authenticated before allowing navigation.
*   `AuthInterceptor`: Automatically adds the user's JWT to outgoing API requests and handles unauthorized responses.

This system, leveraging JWT, ensures that only authenticated users can access restricted areas and perform actions via the backend, allowing you to confidently manage your content securely.

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)