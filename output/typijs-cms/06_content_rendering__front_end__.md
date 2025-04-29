# Chapter 6: Content Rendering (Front-end)

Welcome back! In the previous chapter, [Chapter 5: Property Rendering (Editor)](05_property_rendering__editor__.md), we learned how the CMS editor dynamically builds the forms you use to *edit* your content, based on the property definitions ([Chapter 3: Property](03_property_.md)) and their UI Hints.

Now, imagine you've finished editing your beautiful "About Us" page, published it, and a visitor navigates to `/about-us` on your website. The CMS has the saved [Content Data](01_content_data_.md) for that page ([Chapter 1: Content Data](01_content_data_.md)), but how does it take that raw data – the text strings, image URLs, lists of blocks – and turn it into the final HTML page that the visitor sees?

This is the concept of **Content Rendering (Front-end)**. It's the process of taking the stored [Content Data](01_content_data_.md) and displaying it on the public-facing website.

## What Problem Does Front-end Rendering Solve?

Your website's front-end needs to be built using modern web technologies, typically single-page application frameworks like Angular (which typijs-cms uses). You want to display different types of content ([Chapter 2: Content Type](02_content_type_.md)) – a Standard Page looks different from a Blog Post, which looks different from a Product Page. Even within a single page, different properties ([Chapter 3: Property](03_property_.md)) need to be displayed correctly – text needs to be shown as text, an image needs an `<img>` tag, a list of blocks needs to render each block.

typijs-cms provides a structure to connect your [Content Type](02_content_type_.md) blueprints to specific Angular components (your website's building blocks) that know how to display the [Content Data](01_content_Data_.md) for that type. It also provides helper directives to make displaying individual property values very easy.

## Key Concepts

1.  **`CmsComponent`**: This is a base Angular class that any component designed to render a specific [Content Type](02_content_type_.md) on the front-end should extend. Think of it as the "view component" for your [Content Type](02_content_type_.md). It receives the piece of [Content Data](01_content_data_.md) it needs to render via an `@Input`.
2.  **Rendering Directives (`cmsText`, `cmsImage`, `cmsContentArea`, etc.)**: These are special Angular directives provided by typijs-cms. You use them directly in the HTML template of your `CmsComponent`s to automatically display the *value* of a specific property. They handle the basic task of taking a property value and rendering it correctly (e.g., displaying text, setting an `<img>` src, rendering a list of blocks).
3.  **`CmsPageRender`**: This is a core typijs-cms component, often placed in your main application shell. Its job is to figure out which page needs to be displayed based on the current URL, load the corresponding [Content Data](01_content_data_.md) ([Chapter 7: Content Loading](07_content_loading_.md)), find the correct Angular component registered for that page's [Content Type](02_content_type_.md), and render it.
4.  **`CmsContentRenderFactoryResolver` and `CmsContentRenderFactory`**: Similar to the editor rendering factories we saw in [Chapter 5: Property Rendering (Editor)](05_property_rendering__editor__.md), these are services used by `CmsPageRender` (or other rendering logic) to look up and create the correct *front-end rendering component* (your `CmsComponent` that extends `CmsComponent`) based on the [Content Type](02_content_type_.md).

## Use Case: Displaying a Standard Page

Let's revisit our "About Us" page, which is an instance of the `StandardPage` [Content Type](02_content_type_.md). How is it displayed to a visitor?

Recall the `StandardPage` blueprint from [Chapter 2: Content Type](02_content_type_.md):

```typescript
// simplified-standard-page.pagetype.ts
import { PageType, Property, UIHint } from '@typijs/core';
import { PageData } from '@typijs/core';

@PageType({
    displayName: 'Standard Page',
    description: 'A basic page template'
    // We will add componentRef here soon!
})
export class StandardPage extends PageData {
    @Property({
        displayName: 'Page Title',
        displayType: UIHint.Text
    })
    pageTitle: string;

    @Property({
        displayName: 'Main Content',
        displayType: UIHint.XHtml
    })
    mainBody: string;
}
```

To display this on the front-end, we need an Angular component specifically designed to render a `StandardPage`. Let's call it `StandardPageComponent`.

1.  **Define the View Component:** We create an Angular component (`StandardPageComponent`) that extends `CmsComponent` and is strongly typed to receive `StandardPage` [Content Data](01_content_data_.md).
    ```typescript
    // cms-demo\src\app\pages\standard\standard-page.component.ts (Simplified)
    import { Component } from '@angular/core';
    import { CmsComponent } from '@typijs/core'; // Import the base class
    import { StandardPage } from './standard.pagetype'; // Import the Page Type class

    @Component({
        selector: 'app-standard-page', // Your standard Angular component selector
        template: `
            <div class="container">
                <!-- Use cmsText directive to render the pageTitle property -->
                <h1 [cmsText]="currentContent.pageTitle"></h1>

                <!-- Use cmsText directive to render the mainBody (XHTML) property -->
                <!-- cmsText can handle simple HTML from XHTML property -->
                <div [cmsText]="currentContent.mainBody"></div>

                <!-- Example if StandardPage had an Image property -->
                <!-- <img [cmsImage]="currentContent.headerImage"> -->

                <!-- Example if StandardPage had a ContentArea property -->
                <!-- <div [cmsContentArea]="currentContent.mainContentArea"></div> -->
            </div>
        `
        // ... styles ...
    })
    // Extend CmsComponent, telling it this component renders StandardPage data
    export class StandardPageComponent extends CmsComponent<StandardPage> {
        // The currentContent property is automatically available here
        // thanks to extending CmsComponent and Angular's @Input
        // this.currentContent will hold the specific StandardPageData for the page being viewed.
    }
    ```
    **Explanation:** `StandardPageComponent` is just a regular Angular component, but it gets the specific `StandardPage` [Content Data](01_content_data_.md) passed to it via the `currentContent` input (which it inherits from `CmsComponent`). Its template uses special typijs-cms directives (`cmsText`, `cmsImage`, `cmsContentArea`) to bind directly to the properties of `currentContent`. For example, `<h1 [cmsText]="currentContent.pageTitle"></h1>` means "take the value of the `pageTitle` property from `currentContent` and use the `cmsText` directive to render it inside this `<h1>` tag."

2.  **Connect the Content Type to the View Component:** We tell the `StandardPage` [Content Type](02_content_type_.md) blueprint which Angular component should be used to render it. This is done using the `componentRef` property in the `@PageType` decorator.
    ```typescript
    // simplified-standard-page.pagetype.ts (Updated)
    import { PageType, Property, UIHint } from '@typijs/core';
    import { PageData } from '@typijs/core';
    import { StandardPageComponent } from './standard-page.component'; // Import the component

    @PageType({
        displayName: 'Standard Page',
        description: 'A basic page template',
        componentRef: StandardPageComponent // <-- Register the rendering component here
    })
    export class StandardPage extends PageData {
        @Property({
            displayName: 'Page Title',
            displayType: UIHint.Text
        })
        pageTitle: string;

        @Property({
            displayName: 'Main Content',
            displayType: UIHint.XHtml
        })
        mainBody: string;
    }
    ```
    **Explanation:** By adding `componentRef: StandardPageComponent` to the `@PageType` decorator, we create the link. When the CMS needs to render a piece of [Content Data](01_content_data_.md) whose `contentType` is `StandardPage`, it knows to use the `StandardPageComponent`.

3.  **The Rendering Process:** When a user visits `/about-us`:
    *   The `CmsPageRender` component (typically in your app's root template) detects the URL.
    *   It uses the [Content Loading](07_content_loading_.md) mechanism ([Chapter 7: Content Loading](07_content_loading_.md)) to fetch the `StandardPage` [Content Data](01_content_data_.md) object associated with `/about-us` from the CMS backend.
    *   It looks at the `contentType` property of the loaded [Content Data](01_content_data_.md) object (`'StandardPage'`).
    *   It uses the `CmsContentRenderFactoryResolver` to find the correct factory that knows how to render `'StandardPage'` content.
    *   The factory (registered internally by typijs based on your `@PageType` decorator) knows that `StandardPage` is rendered by `StandardPageComponent` (because of `componentRef`).
    *   The factory creates an instance of `StandardPageComponent`.
    *   The `CmsPageRender` component inserts this `StandardPageComponent` into the page's HTML and passes the loaded `StandardPage` [Content Data](01_content_data_.md) object to its `currentContent` input.
    *   The `StandardPageComponent` renders its template. The rendering directives (`cmsText`, etc.) within the template display the values from `currentContent.pageTitle`, `currentContent.mainBody`, etc.

And voilà! The visitor sees the rendered page content.

```mermaid
sequenceDiagram
    participant User (Visitor Browser)
    participant Application Shell (e.g., app.component.html)
    participant CmsPageRender
    participant Content Loading Service
    participant CMS Backend (API)
    participant CmsContentRenderFactoryResolver
    participant StandardPageRenderFactory (Internal)
    participant StandardPageComponent (Your Angular View)

    User (Visitor Browser)->>Application Shell (e.g., app.component.html): Request /about-us
    Application Shell (e.g., app.component.html)->>CmsPageRender: Route matches CmsPageRender
    CmsPageRender->>CmsPageRender: Get URL (/about-us)
    CmsPageRender->>Content Loading Service: Load Page Data by URL (/about-us)
    Content Loading Service->>CMS Backend (API): Request Page Data for /about-us
    CMS Backend (API)-->>Content Loading Service: Return StandardPage Content Data
    Content Loading Service-->>CmsPageRender: Return StandardPage Content Data
    CmsPageRender->>CmsPageRender: Get contentType from Data ('StandardPage')
    CmsPageRender->>CmsContentRenderFactoryResolver: resolveContentRenderFactory('Page') (based on data type)
    CmsContentRenderFactoryResolver->>StandardPageRenderFactory (Internal): Find factory for Page Type 'StandardPage' (using componentRef metadata)
    StandardPageRenderFactory (Internal)->>StandardPageRenderFactory (Internal): Create instance of StandardPageComponent
    StandardPageRenderFactory (Internal)-->>CmsPageRender: Return StandardPageComponent instance
    CmsPageRender->>Application Shell (e.g., app.component.html): Insert StandardPageComponent into DOM
    CmsPageRender->>StandardPageComponent (Your Angular View): Bind StandardPage Data to @Input currentContent
    StandardPageComponent (Your Angular View)->>StandardPageComponent (Your Angular View): Render template, using cmsText, cmsImage etc.
    StandardPageComponent (Your Angular View)-->>User (Visitor Browser): Display final HTML
```

## Looking at the Code (Simplified)

Let's look at the parts that make this work.

The base `CmsComponent` you extend:

```typescript
// core\src\bases\cms-component.ts (Simplified)
import { Input, Directive } from '@angular/core';
import { ContentData } from '../services/content/models/content-data'; // From Chapter 1

@Directive() // It's a base class, not rendered directly
export abstract class CmsComponent<T extends ContentData> {
    // This is the crucial input! It receives the Content Data for this component.
    @Input() currentContent: T;

    // Methods like getProperty are helpers to easily access properties,
    // but you can also access them directly via this.currentContent.propertyName
    getProperty<K extends keyof T>(propertyName: K): any {
         return this.currentContent ? this.currentContent[propertyName] : undefined;
    }
    // ... other helper methods omitted ...
}
```
**Explanation:** By extending `CmsComponent`, your page/block rendering component automatically gets a `currentContent` input property typed to the specific [Content Data](01_content_data_.md) class (like `StandardPage`). Angular's binding mechanism and the `CmsPageRender`/factories ensure the correct data is passed here.

Example Rendering Directives: These directives take the *value* of a property and render it. They are different from the editor properties that take the `property` definition and `formGroup`.

`cmsText`: Used for properties like text, textarea, and even XHTML if the content doesn't need complex HTML rendering.

```typescript
// core\src\renders\text\text-render-as-directive.ts (Simplified)
import { Input, Directive, TemplateRef, ViewContainerRef } from '@angular/core';

@Directive({
    selector: '[cmsText]', // Use as an attribute: <h1 [cmsText]="..."></h1>
})
export class TextRenderDirective {
    // The input property name matches the selector: [cmsText]="someValue" -> cmsText input receives someValue
    @Input() cmsText: string;

    // Optional: Use ViewContainerRef/TemplateRef if the directive modifies the host element's content
    // Simplified for clarity - the actual directive template sets innerHTML or text content
    constructor(private elementRef: ElementRef) {}

    ngOnInit() {
       // The directive logic sets the text content or innerHTML of the element it's on
       this.elementRef.nativeElement.innerHTML = this.cmsText; // Simplified
    }
}
```
**Explanation:** The `cmsText` directive simply takes the string value from its input (`currentContent.pageTitle` or `currentContent.mainBody` in our example) and sets the text content or inner HTML of the element it's attached to (`<h1>` or `<div>`).

`cmsImage`: Used for properties defined with `UIHint.Image`.

```typescript
// core\src\renders\image\image-render.directive.ts (Simplified)
import { Input, Directive, HostBinding, OnInit } from '@angular/core';
import { CmsImage } from '../../types/cms-image'; // Assuming CmsImage is a type for image data

@Directive({
    selector: 'img[cmsImage]', // Only applies to <img> tags
})
export class ImageRenderDirective implements OnInit {
    // Bind to standard HTML attributes using @HostBinding
    @HostBinding('attr.src') src: string;
    @HostBinding('attr.alt') alt: string;

    // Input receives the value of the Image property
    @Input() cmsImage: CmsImage; // Assuming CmsImage has src and alt properties

    ngOnInit() {
        if (this.cmsImage) {
            // Logic to get the correct URL (maybe add base path)
            this.src = this.cmsImage.src; // Simplified
            this.alt = this.cmsImage.alt; // Simplified
        }
    }
}
```
**Explanation:** The `cmsImage` directive is applied to an `<img>` tag. It takes the value of an image property (which is expected to be an object like `CmsImage` containing `src` and `alt`) and uses `@HostBinding` to automatically set the `src` and `alt` attributes of the `<img>` element, making the image appear on the page.

`cmsContentArea`: Used for properties defined with `UIHint.ContentArea`. This property type holds a list of references to other blocks ([Chapter 1: Content Data](01_content_data_.md) instances). Rendering this is more complex as it needs to load and render each block in the list. The `cmsContentArea` directive acts as a wrapper for another component or directive that handles the actual rendering of the list of blocks.

```typescript
// core\src\renders\content-area\content-area-as-directive.ts (Simplified)
import { Component, Input } from '@angular/core';
import { ContentReference } from '../../types/content-reference'; // Type for content references

@Component({
    selector: '[cmsContentArea]', // Use as an attribute: <div [cmsContentArea]="..."></div>
    template: `
        <!-- contentArea is another internal typijs component/directive that renders the list -->
        <ng-container [contentArea]="contentAreaItems"></ng-container>
        <ng-content></ng-content>
        `
})
export class ContentAreaRenderDirective {
    // Input receives the value of the ContentArea property (a list of references)
    @Input('cmsContentArea') contentAreaItems: Array<ContentReference>;

    // The template uses a separate component/directive called 'contentArea'
    // and passes the list of items to it. The 'contentArea' logic
    // then iterates through the list, loads each block's data, finds
    // the correct rendering component for that block type, and renders it.
}
```
**Explanation:** The `cmsContentArea` directive is a bit of a facade. When you give it a list of content references (the value of a `ContentArea` property), its template delegates the actual rendering of *each item* in that list to another internal typijs mechanism (represented here by the `<ng-container [contentArea]="contentAreaItems">`). This internal mechanism handles fetching the data for each block and finding the appropriate rendering component for *that block's* type using the factory pattern again.

The overall entry point on the front-end is often `CmsPageRender`:

```typescript
// core\src\renders\page-render.ts (Simplified)
import { Component, ViewChild, ViewContainerRef, OnInit, OnDestroy } from '@angular/core';
import { CmsContentRenderFactoryResolver } from './content-render.factory'; // The resolver for front-end components
import { PageService } from '../services/content/page.service'; // For loading page data
import { Page } from '../services/content/models/page.model'; // Page data type
import { InsertPointDirective } from './insert-point.directive'; // Helper to find where to insert component

@Component({
    selector: 'cms-page', // Your main app shell might use this: <cms-page></cms-page>
    template: `<ng-template cmsInsertPoint></ng-template>` // Where the page component will be inserted
})
export class CmsPageRender implements OnInit, OnDestroy {
    @ViewChild(InsertPointDirective, { static: true, read: ViewContainerRef }) pageContainerRef: ViewContainerRef;

    constructor(
        private cmsContentRenderFactoryResolver: CmsContentRenderFactoryResolver,
        private pageService: PageService // Injects the service to load pages
    ) { }

    ngOnInit() {
        // 1. Determine which page to load (based on URL or editor parameters)
        // ... logic omitted for simplicity ...

        // 2. Load the page data
        this.pageService.getPageByLinkUrl('/about-us').subscribe((currentPage: Page) => { // Simplified load logic
            if (currentPage) {
                // 3. Get the factory that can render this Content Type (e.g., StandardPage)
                const pageRenderFactory = this.cmsContentRenderFactoryResolver.resolveContentRenderFactory('Page'); // Resolve factory for generic 'Page' type

                // 4. Create the specific component instance (e.g., StandardPageComponent)
                // The factory uses the componentRef from the @PageType metadata internally
                const pageComponentRef = pageRenderFactory.createContentComponent(currentPage, this.pageContainerRef);

                // 5. The created component (StandardPageComponent) is now in the DOM
                // And the currentPage data has been passed to its currentContent input.
            }
        });
    }

    ngOnDestroy() { /* ... cleanup ... */ }
}
```
**Explanation:** `CmsPageRender` is responsible for the top-level task of getting the right page data and rendering the correct component. It uses `PageService` (covered in [Chapter 7: Content Loading](07_content_loading_.md)) to fetch the data. Then it uses the `CmsContentRenderFactoryResolver` to find the factory capable of creating the *component* for the loaded page's [Content Type](02_content_type_.md). The factory uses the `componentRef` registered in the `@PageType` decorator to know *which* component to create (e.g., `StandardPageComponent`). The `createContentComponent` method creates and inserts the component into the `pageContainerRef` (the `cmsInsertPoint`) and passes the loaded `currentPage` data to the component's `currentContent` input.

## Conclusion

In this chapter, we learned how typijs-cms renders your content on the front-end website. The core ideas are:
1.  Defining Angular components that extend `CmsComponent` to serve as views for your [Content Type](02_content_type_.md)s.
2.  Registering these view components with your [Content Type](02_content_type_.md) using the `componentRef` in the `@PageType` or `@BlockType` decorator.
3.  Using specific rendering directives like `cmsText`, `cmsImage`, and `cmsContentArea` within your view component's template to easily display individual property values from the `currentContent` input.
4.  Understanding that `CmsPageRender` and the rendering factory resolver handle the overall process of loading content and selecting/creating the correct view component based on the content type.

We now understand how content data is structured, organized, edited, and finally displayed to website visitors. But how does the data actually *get* from the CMS backend to the front-end components? That's the topic of the next chapter: **Content Loading**.

[Chapter 7: Content Loading](07_content_loading_.md)

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)