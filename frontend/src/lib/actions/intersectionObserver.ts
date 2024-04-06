let lastItemObserver: IntersectionObserver;

function getLastItemObserver(options?: IntersectionObserverInit) {
    if (lastItemObserver) return;

    lastItemObserver = new IntersectionObserver((entries) => {
        // we only observe the last card. Thus fetch it
        const lastItem = entries[0];
        // if last card isn't visible, do nothing
        if (!lastItem.isIntersecting) return;

        // otherwise, if last card is within some threshold, dispatch a new
        // custom event so that we fetch some more data
        const enterEvent = new CustomEvent("intersecting");
        lastItem.target.dispatchEvent(enterEvent);
    }, options);
}

export function observeLast(lastItem: HTMLElement, options?: IntersectionObserverInit) {
    getLastItemObserver(options);
    
    lastItemObserver.observe(lastItem);

    return {
        destroy() {
            lastItemObserver.unobserve(lastItem);
        }
    }
}