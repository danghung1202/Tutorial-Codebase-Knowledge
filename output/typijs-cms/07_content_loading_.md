# Chapter 7: Content Loading

Welcome back to the typijs-cms tutorial! We've covered a lot of ground: understanding [Chapter 1: Content Data](01_content_data_.md), defining its structure with [Chapter 2: Content Type](02_content_type_.md) and [Chapter 3: Property](03_property_.md), organizing content using [Chapter 4: Tree Navigation](04_tree_navigation_.md) in the editor, editing properties with [Chapter 5: Property Rendering (Editor)](05_property_rendering__editor__.md), and finally displaying content on your website using [Chapter 6: Content Rendering (Front-end)](06_content_rendering__front_end__.md).

But all of this relies on getting the content data from where it's stored (usually a database, accessed via the CMS backend API) into your Angular application, whether that's the CMS editor or your public-facing website.

How does your application reliably and easily fetch a specific page, find the children of a block, or query for items matching certain criteria? This is the job of **Content Loading**.

## What Problem Does Content Loading Solve?

When you build an Angular application, whether it's the typijs CMS editor itself or your front-end website powered by typijs, you constantly need to retrieve pieces of content.

*   The `CmsPageRender` component (from [Chapter 6: Content Rendering (Front-end)](06_content_rendering__front_end__.md)) needs to load the page data for the current URL.
*   A menu component needs to load the children of the start page to build a navigation menu.
*   A component rendering a [Content Area property](05_property_rendering__editor__.md) needs to load the data for all the blocks referenced within that area.
*   A search results page needs to query the backend for pages matching the user's search term.

Manually writing HTTP requests (`HttpClient.get`, `HttpClient.post`) every time you need to fetch content would be repetitive and complex. You'd have to figure out the correct API endpoints, handle authentication, parse responses, and convert the raw data into the structured `ContentData` objects ([Chapter 1: Content Data](01_content_data_.md)) that your components expect.

typijs-cms provides the `ContentLoader` service as an abstraction to simplify this.

## The ContentLoader

The `ContentLoader` is a central service in typijs-cms designed specifically for fetching content items from the backend API. It acts as a unified entry point for all your content retrieval needs.

Think of the `ContentLoader` as the main librarian for your content. You tell the librarian what book (content item) you need, and they know how to find it, get it for you, and hand it over in a format you can easily use. You don't need to know which shelf it's on or how the library is organized internally; you just ask the librarian.

The `ContentLoader` simplifies common tasks like:

*   Getting a single content item by its ID or reference.
*   Getting all the direct children of a content item (like finding all sub-pages of a parent page).
*   Getting all the ancestors of a content item.
*   Performing complex queries to find content matching specific filters.
*   Getting multiple content items by a list of references.

It hides the underlying complexity of talking to different backend APIs for different content types ([Chapter 2: Content Type](02_content_type_.md)) (Pages, Blocks, Media).

## Use Case: Loading Articles on a Blog Page

Let's look at a common front-end use case: displaying a list of articles on a Blog Page.

Imagine you have a `BlogPage` [Content Type](02_content_type_.md) and `ArticlePage` [Content Type](02_content_type_.md). In your website's content tree ([Chapter 4: Tree Navigation](04_tree_navigation_.md)), you organize `ArticlePage` instances as children of the main `BlogPage` instance.

The `BlogComponent` (which renders the `BlogPage` data, as per [Chapter 6: Content Rendering (Front-end)](06_content_rendering__front_end__.md)) needs to load all the child `ArticlePage`s to display them.

Here's how you would use `ContentLoader` in the `BlogComponent`:

```typescript
// cms-demo\src\app\pages\blog\blog.component.ts (Simplified)
import { CmsComponent, ContentLoader } from '@typijs/core';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { ArticlePage } from '../article/article.pagetype'; // Import the ArticlePage class
import { BlogPage } from './blog.pagetype'; // Import the BlogPage class

@Component({
    templateUrl: 'blog.component.html'
})
// This component renders the BlogPage Content Data
export class BlogComponent extends CmsComponent<BlogPage> implements OnInit {

    // We will store the loaded ArticlePage data here
    articles$: Observable<ArticlePage[]>;

    // Inject the ContentLoader service
    constructor(private contentLoader: ContentLoader) {
        super();
    }

    ngOnInit() {
        // Use the ContentLoader to get children of the current BlogPage
        // this.currentContent holds the data for the BlogPage being rendered
        // currentContent.contentLink is a reference to the BlogPage itself
        this.articles$ = this.contentLoader.getChildren<ArticlePage>(this.currentContent.contentLink);

        // This returns an Observable. We typically subscribe to it in the template
        // using the async pipe to display the articles.
    }
}
```

**Explanation:**

1.  We inject the `ContentLoader` service into the component's constructor.
2.  In the `ngOnInit` lifecycle hook (where we know `currentContent` has been set), we call `this.contentLoader.getChildren()`.
3.  We pass `this.currentContent.contentLink` to tell the loader *whose* children we want. `contentLink` is a standard property on `ContentData` objects that uniquely identifies that content item (it's like the Content ID plus its type).
4.  We specify `<ArticlePage>` to tell TypeScript and the loader that we expect the children to be instances of `ArticlePage`. This helps ensure type safety.
5.  `getChildren` returns an `Observable<ArticlePage[]>`. Observables are standard in Angular for handling asynchronous data like HTTP responses. We store this Observable in `articles$`.
6.  In the `blog.component.html` template, we would use Angular's `async` pipe (`<div *ngFor="let article of articles$ | async">`) to automatically subscribe to the Observable, get the list of articles when they arrive from the backend, and loop through them to display each article's details.

This is a very clean and simple way to get content data using `ContentLoader`. You don't see any HTTP calls or URL building here; the `ContentLoader` handles all that complexity.

Let's look at another example from the `LayoutComponent`, which loads the start page and its children for the main menu:

```typescript
// cms-demo\src\app\shared\layout\layout.component.ts (Simplified)
import { ContentLoader, PageData, SiteDefinition } from '@typijs/core';
import { Component, OnInit } from '@angular/core';
import { Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { HomePage } from '../../pages/home/home.pagetype'; // Import HomePage
import { MenuService } from '../menu.service'; // Custom service using ContentLoader

@Component({
    templateUrl: './layout.component.html',
    // ... styles, encapsulation ...
})
export class LayoutComponent implements OnInit {
    startPage$: Observable<HomePage>;
    menuItems$: Observable<any[]>; // Simplified type for MenuItems

    constructor(
        private siteDefinition: SiteDefinition, // Service to get the site's start page reference
        private contentLoader: ContentLoader, // Inject ContentLoader
        private menuService: MenuService // Custom service
        // ... renderer, document ...
        ) { }

    ngOnInit() {
        // Get the reference to the site's start page
        this.startPage$ = this.siteDefinition.getStartPage<HomePage>();

        // Use switchMap to chain observables:
        // Once the start page reference is available (from startPage$),
        // use it to call the menuService to get menu items
        this.menuItems$ = this.startPage$.pipe(
            switchMap((startPage: HomePage) =>
                // menuService internally uses contentLoader.getChildren(startPage.contentLink)
                // and filters/maps the results to MenuItem objects
                this.menuService.getPageVisibleInMenu(startPage)
            )
        );
    }
    // ... ngAfterViewInit ...
}
```
**Explanation:** This snippet shows how `ContentLoader` (or services that use it, like `MenuService`) is used to fetch the site's start page and then its children to build the menu. The `switchMap` operator is commonly used with Observables to first get one piece of data (`startPage`) and *then* use that data to perform another asynchronous operation (get the start page's children via `menuService`).

## How Content Loading Works (Under the Hood)

The `ContentLoader` service is an abstraction layer. It doesn't directly know *how* to fetch a Page versus a Block versus a Media file, because these might involve slightly different backend API endpoints or logic.

Instead, the `ContentLoader` delegates the actual fetching work to specialized services, called **Content Services**. There is typically a dedicated `ContentService` implementation for each major type of content (Pages, Blocks, Media).

Here's the simplified flow when you call `contentLoader.getChildren(...)`:

```mermaid
sequenceDiagram
    participant YourComponent (e.g., BlogComponent)
    participant ContentLoader
    participant ContentServiceResolver
    participant SpecificContentService (e.g., PageService)
    participant CMS Backend API

    YourComponent (e.g., BlogComponent)->>ContentLoader: getChildren(blogPageLink)
    ContentLoader->>ContentLoader: Get type from blogPageLink (e.g., 'Page')
    ContentLoader->>ContentServiceResolver: resolveContentProviderFactory('Page')
    ContentServiceResolver->>ContentServiceResolver: Find the registered service for type 'Page' (e.g., PageService)
    ContentServiceResolver-->>SpecificContentService (e.g., PageService): Return PageService instance
    SpecificContentService (e.g., PageService)->>CMS Backend API: HTTP Request to get children of BlogPage ID
    CMS Backend API-->>SpecificContentService (e.g., PageService): Return raw Page Data for children
    SpecificContentService (e.g., PageService)->>SpecificContentService (e.g., PageService): Map raw data to ContentData objects (ArticlePage[])
    SpecificContentService (e.g., PageService)-->>ContentLoader: Return Observable<ArticlePage[]>
    ContentLoader-->>YourComponent (e.g., BlogComponent): Return Observable<ArticlePage[]>
    YourComponent (e.g., BlogComponent)->>YourComponent (e.g., BlogComponent): Subscribe to Observable, display data
```

This diagram illustrates that `ContentLoader` is the entry point, but it relies on the `ContentServiceResolver` to find the correct `ContentService` implementation, which then performs the actual communication with the backend API.

## Looking at the Code (Simplified)

Let's look at the key services involved.

First, the `ContentLoader` itself:

```typescript
// core\src\services\content\content-loader.service.ts (Simplified)
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ContentReference } from '../../types/content-reference';
import { ContentData } from './models/content-data';
import { ContentServiceResolver } from './content-loader.service'; // Imports the resolver

@Injectable({ providedIn: 'root' })
export class ContentLoader {
    // Injects the resolver
    constructor(private contentServiceResolver: ContentServiceResolver) { }

    // Method to get a single item
    get<T extends ContentData>(contentLink: ContentReference, language?: string): Observable<T> {
        // 1. Resolve the correct ContentService based on the link's type (Page, Block, etc.)
        const contentService = this.contentServiceResolver.resolveContentProviderFactory(contentLink.type);
        // 2. Call the service's method to get the content
        return contentService.getContent(contentLink.id, language).pipe(
            // 3. Map the raw Content object from the service to the specific ContentData type (T)
            map((content: any) => contentService.getContentData(content))
        );
    }

    // Method to get children
    getChildren<T extends ContentData>(contentLink: ContentReference, language?: string, select?: string, loaderOptions?: any): Observable<T[]> {
         // 1. Resolve the correct ContentService based on the link's type
        const contentService = this.contentServiceResolver.resolveContentProviderFactory(contentLink.type);
        // 2. Call the service's method to get children
        return contentService.getContentChildren(contentLink.id, language, select).pipe(
            // 3. Map the array of raw Content objects to an array of specific ContentData types (T[])
            map((children: any[]) => children.map(childContent => contentService.getContentData(childContent)))
        );
    }

    // ... other methods like getDescendents, getAncestors, query, getItems ...
}
```
**Explanation:** The `ContentLoader` methods like `get` and `getChildren` don't contain HTTP logic. They rely entirely on the `contentServiceResolver` to find the appropriate underlying `ContentService` and delegate the call. The `map` operator is used to take the generic `Content` object (which comes back from the backend) and convert it into the more specific `ContentData` class you expect (`T`), using the `getContentData` method provided by the specific `ContentService`.

Next, the `ContentServiceResolver`:

```typescript
// core\src\services\content\content-loader.service.ts (Simplified)
import { Inject, Injectable, InjectionToken } from '@angular/core';
import { ContentService } from './content.service'; // Imports the base ContentService
import { TypeOfContent } from '../../types'; // Type like 'Page', 'Block'

// Injection Token to get all registered ContentService instances
export const CONTENT_SERVICE_PROVIDER: InjectionToken<ContentService<any>[]> = new InjectionToken<ContentService<any>[]>('CONTENT_SERVICE_PROVIDER');

@Injectable({ providedIn: 'root' })
export class ContentServiceResolver {
    // Inject all services provided via the CONTENT_SERVICE_PROVIDER token
    constructor(@Inject(CONTENT_SERVICE_PROVIDER) private contentServices: ContentService<any>[]) { }

    // This method finds the correct service based on the content type string
    resolveContentProviderFactory(typeOfContent: TypeOfContent): ContentService<any> {
        // Find the service whose isMatching method returns true for the given type
        const resolvedService = this.contentServices.find(x => x.isMatching(typeOfContent));
        if (resolvedService) { return resolvedService; }

        // Throw an error if no service is found for the type
        throw new Error(`The CMS can not resolve the Content Service for the content has type of ${typeOfContent}`);
    }
}
```
**Explanation:** This service is responsible for managing a collection of all registered `ContentService` implementations (like `PageService`, `BlockService`, `MediaService`). When asked to `resolveContentProviderFactory` for a specific `typeOfContent` (like `'Page'`), it loops through its collection of services and calls `isMatching()` on each one. The service that says "Yes, I handle 'Page' content" is the one returned. This uses Angular's Dependency Injection system and an `InjectionToken` (`CONTENT_SERVICE_PROVIDER`) to collect all the necessary services.

Finally, the base `ContentService` class defines the contract for what a specific content service must do:

```typescript
// core\src\services\content\content.service.ts (Simplified)
import { Injector } from '@angular/core';
import { Observable } from 'rxjs';
import { TypeOfContent } from '../../types'; // Type like 'Page', 'Block'
import { Content } from './models/content.model'; // Generic Content model from backend
import { ContentData } from './models/content-data'; // Specific ContentData model (PageData, BlockData)

// Abstract base class for all Content Services (PageService, BlockService, etc.)
export abstract class ContentService<T extends Content> {
    // Constructor takes Injector to access other services like HttpClient
    constructor(protected injector: Injector) {
        // ... access HttpClient, etc. ...
    }

    // REQUIRED: Concrete service must implement this to tell the resolver which type it handles
    abstract isMatching(typeOfContent: TypeOfContent): boolean;

    // REQUIRED: Concrete service must implement this to map raw backend Content data to specific ContentData class
    abstract getContentData(content: T): ContentData;

    // Abstract methods for fetching data - concrete services MUST implement these
    // These methods will make the actual HTTP calls using this.httpClient
    abstract getContent(contentId: string, language?: string, select?: string): Observable<T>;
    abstract getContentChildren(parentId: string, language?: string, select?: string): Observable<T[]>;
    abstract getAncestors(contentId: string, language?: string, select?: string): Observable<T[]>;
    // ... other methods like queryContents, getContentItems ...
}
```
**Explanation:** `ContentService` is an `abstract` class, meaning you can't create an instance of it directly. Specific services like `PageService` or `BlockService` extend this class and provide the concrete implementations for the abstract methods (`isMatching`, `getContentData`, `getContent`, `getContentChildren`, etc.). These implementations contain the specific logic and backend API endpoints for fetching their type of content. The `isMatching` method is key for the `ContentServiceResolver`.

This layered design makes `ContentLoader` simple to use from any component, while the `ContentServiceResolver` and specific `ContentService` implementations handle the complexity of talking to the backend for different content types.

## Conclusion

In this chapter, we learned that the `ContentLoader` service is your primary tool for fetching content data ([Chapter 1: Content Data](01_content_data_.md)) from the CMS backend API. It provides simple methods like `get`, `getChildren`, and `query` that hide the underlying complexity of HTTP requests and content type handling. We saw how to use `ContentLoader` in a component to fetch content and how it works internally by delegating requests to specific `ContentService` implementations found by the `ContentServiceResolver`.

Understanding `ContentLoader` is essential for building any part of your application that needs to display or work with content from the CMS. The specific `ContentService` implementations for Pages, Blocks, and Media are part of a broader set of services provided by typijs for interacting with the CMS.

In the next chapter, we'll delve deeper into these **Content Services** and other core services that typijs provides.

[Chapter 8: Content Services](08_content_services_.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)